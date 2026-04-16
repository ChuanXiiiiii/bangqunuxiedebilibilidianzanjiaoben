"""
liker.py — B站自动点赞核心逻辑

功能：
  1. 打开 B站首页，等待用户手动登录
  2. 滚动首页收集视频链接
  3. 逐一打开视频，观看指定时长后点赞
"""

import random
import time

from loguru import logger
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeout

import config

# ------------------------------------------------------------------ #
#  点赞按钮候选选择器（按优先级排列，B站页面结构可能变化）
# ------------------------------------------------------------------ #
_LIKE_SELECTORS = [
    ".video-like",
    '[aria-label="点赞"]',
    ".like-info",
    ".toolbar-left-item--like",
    ".video-toolbar-left .toolbar-left-item:first-child",
    "text=点赞",
]

# 登录成功后才会出现的元素
_LOGIN_INDICATORS = [
    ".bili-avatar",
    ".header-avatar-wrap",
    ".nav-user-center",
    ".avatar-link",
]


# ------------------------------------------------------------------ #
#  工具函数
# ------------------------------------------------------------------ #

def _wait_random(min_s: float = None, max_s: float = None) -> None:
    """随机等待一段时间，模拟人类操作节奏"""
    lo = min_s if min_s is not None else config.MIN_WAIT
    hi = max_s if max_s is not None else config.MAX_WAIT
    time.sleep(random.uniform(lo, hi))


def _is_logged_in(page: Page) -> bool:
    """判断当前页面是否已处于登录状态"""
    try:
        for sel in _LOGIN_INDICATORS:
            el = page.query_selector(sel)
            if el and el.is_visible():
                return True
    except Exception:
        pass
    return False


# ------------------------------------------------------------------ #
#  登录等待
# ------------------------------------------------------------------ #

def wait_for_login(page: Page) -> None:
    """
    导航到 B站首页，等待用户手动完成登录。
    登录成功后函数返回；超时则抛出异常。
    """
    logger.info("导航到 B站首页，等待手动登录...")
    page.goto("https://www.bilibili.com/", wait_until="domcontentloaded",
              timeout=config.PAGE_TIMEOUT * 1000)
    _wait_random(1, 2)

    # 若已登录直接跳过
    if _is_logged_in(page):
        logger.info("检测到已登录状态，直接继续")
        return

    # 尝试点击登录入口（让用户更容易看到登录界面）
    for sel in [".header-login-entry", ".login-btn", "[href*='login']"]:
        try:
            btn = page.query_selector(sel)
            if btn and btn.is_visible():
                btn.click()
                break
        except Exception:
            pass

    print("\n" + "=" * 60)
    print("  📱  请在弹出的浏览器窗口中手动登录 B站账号")
    print(f"      脚本将等待最多 {config.LOGIN_TIMEOUT} 秒...")
    print("=" * 60 + "\n")

    deadline = time.time() + config.LOGIN_TIMEOUT
    while time.time() < deadline:
        if _is_logged_in(page):
            logger.info("✅ 登录成功！")
            print("✅ 登录成功，脚本自动继续...\n")
            _wait_random(1, 2)
            return
        time.sleep(2)

    raise TimeoutError(
        f"在 {config.LOGIN_TIMEOUT} 秒内未检测到登录，脚本终止。"
    )


# ------------------------------------------------------------------ #
#  收集首页视频链接
# ------------------------------------------------------------------ #

def get_homepage_video_links(page: Page, count: int) -> list:
    """
    刷新首页并向下滚动，收集指定数量的视频链接。
    返回去重后的 URL 列表。
    """
    logger.info("前往 B站首页收集视频链接...")
    page.goto("https://www.bilibili.com/", wait_until="domcontentloaded",
              timeout=config.PAGE_TIMEOUT * 1000)
    _wait_random(2, 3)

    collected: dict[str, bool] = {}  # url -> True（用 dict 保持插入顺序 + 去重）
    max_scrolls = 20
    scroll_idx = 0

    while len(collected) < count and scroll_idx < max_scrolls:
        elements = page.query_selector_all('a[href*="/video/BV"]')
        for el in elements:
            try:
                href = el.get_attribute("href") or ""
                # 补全协议
                if href.startswith("//"):
                    href = "https:" + href
                elif href.startswith("/"):
                    href = "https://www.bilibili.com" + href
                # 去掉查询参数，只保留干净的视频地址
                clean = href.split("?")[0].split("#")[0]
                if "/video/BV" in clean and clean not in collected:
                    collected[clean] = True
            except Exception:
                continue

        logger.debug(f"第 {scroll_idx + 1} 次滚动后已收集 {len(collected)} 条链接")

        if len(collected) < count:
            page.evaluate("window.scrollBy(0, window.innerHeight * 1.5)")
            _wait_random(1.5, 2.5)

        scroll_idx += 1

    result = list(collected.keys())[:count]
    logger.info(f"共收集到 {len(result)} 个视频链接")
    return result


# ------------------------------------------------------------------ #
#  点赞单个视频
# ------------------------------------------------------------------ #

def like_video(page: Page, url: str) -> bool:
    """
    打开视频页面 → 等待播放器加载 → 观看指定时长 → 点赞。
    返回 True 表示点赞成功，False 表示失败/跳过。
    """
    try:
        logger.info(f"→ 打开视频: {url}")
        page.goto(url, wait_until="domcontentloaded",
                  timeout=config.PAGE_TIMEOUT * 1000)
        _wait_random(1, 2)

        # 等待播放器出现（最多 15 秒）
        player_loaded = False
        for player_sel in [".bpx-player-ctrl-play", "#bilibili-player", ".bilibili-player-video"]:
            try:
                page.wait_for_selector(player_sel, timeout=15_000)
                player_loaded = True
                break
            except PlaywrightTimeout:
                continue

        if not player_loaded:
            logger.warning(f"  ⚠  播放器未加载，仍继续等待...")

        # ---- 观看计时 ----
        logger.info(f"  ⏱  观看 {config.WATCH_DURATION} 秒...")
        time.sleep(config.WATCH_DURATION)

        # ---- 尝试点赞 ----
        success = _try_click_like(page)

        if success:
            logger.success(f"  ✅ 点赞成功: {url}")
        else:
            logger.warning(f"  ⚠  未能点赞: {url}")

        _wait_random()
        return success

    except PlaywrightTimeout:
        logger.error(f"  ❌ 页面加载超时: {url}")
        return False
    except Exception as exc:
        logger.error(f"  ❌ 发生错误: {url} — {exc}")
        return False


def _try_click_like(page: Page) -> bool:
    """
    尝试多种策略找到并点击点赞按钮。
    如果视频已被点赞则直接返回 True。
    """
    # 稍微向下滚动，确保工具栏进入视口
    try:
        page.evaluate("window.scrollBy(0, 350)")
        time.sleep(0.5)
    except Exception:
        pass

    # --- 策略 1：遍历 CSS 选择器 ---
    for sel in _LIKE_SELECTORS:
        try:
            el = page.query_selector(sel)
            if el and el.is_visible():
                # 检测是否已点赞（class 中含 on / active / liked）
                cls = el.get_attribute("class") or ""
                if any(k in cls for k in ("on", "active", "liked")):
                    logger.info("  ℹ  该视频已点过赞，跳过重复操作")
                    return True
                el.scroll_into_view_if_needed()
                time.sleep(0.3)
                el.click()
                time.sleep(0.8)
                logger.debug(f"  使用选择器点赞: {sel}")
                return True
        except Exception as exc:
            logger.debug(f"  选择器 {sel} 失败: {exc}")
            continue

    # --- 策略 2：键盘快捷键 L ---
    try:
        # 先点击页面主体，确保焦点在页面上
        page.keyboard.press("Escape")   # 关掉可能的弹窗
        time.sleep(0.2)
        page.keyboard.press("l")        # B站点赞快捷键
        time.sleep(0.8)
        logger.debug("  使用键盘快捷键 L 点赞")
        return True
    except Exception as exc:
        logger.debug(f"  键盘快捷键失败: {exc}")

    return False
