"""
main.py — B站自动点赞脚本入口

使用方法：
    python main.py

流程：
    1. 打开浏览器并导航至 B站
    2. 等待用户手动登录账号
    3. 滚动首页收集视频链接
    4. 逐一打开视频，观看 20 秒后点赞
    5. 完成后打印统计结果
"""

import os
import sys

from loguru import logger
from playwright.sync_api import sync_playwright

import config
from liker import wait_for_login, get_homepage_video_links, like_video


# ------------------------------------------------------------------ #
#  日志初始化
# ------------------------------------------------------------------ #

def _setup_logging() -> None:
    os.makedirs("logs", exist_ok=True)
    # 控制台：简洁输出
    logger.remove()
    logger.add(
        sys.stderr,
        format="<green>{time:HH:mm:ss}</green> | <level>{level:<8}</level> | {message}",
        level="INFO",
        colorize=True,
    )
    # 文件：详细记录
    logger.add(
        config.LOG_FILE,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level:<8} | {message}",
        rotation="10 MB",
        retention="30 days",
        encoding="utf-8",
        level="DEBUG",
    )


# ------------------------------------------------------------------ #
#  主流程
# ------------------------------------------------------------------ #

def main() -> None:
    _setup_logging()

    print()
    print("╔══════════════════════════════════════════╗")
    print("║      B站自动点赞脚本  v1.0               ║")
    print(f"║  计划点赞视频数：{config.VIDEO_COUNT:<3}  观看时长：{config.WATCH_DURATION}s／视频  ║")
    print("╚══════════════════════════════════════════╝")
    print()

    logger.info("脚本启动")

    with sync_playwright() as pw:
        # ---- 启动浏览器 ----
        browser = pw.chromium.launch(
            headless=config.HEADLESS,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-web-security",
            ],
        )

        context = browser.new_context(
            viewport={"width": config.VIEWPORT_WIDTH, "height": config.VIEWPORT_HEIGHT},
            user_agent=config.USER_AGENT,
            locale="zh-CN",
            timezone_id="Asia/Shanghai",
        )

        # 注入反检测脚本，隐藏 webdriver 特征
        context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3] });
            window.chrome = { runtime: {} };
        """)

        page = context.new_page()

        # ---- 步骤 1：等待手动登录 ----
        try:
            wait_for_login(page)
        except TimeoutError as e:
            logger.error(str(e))
            browser.close()
            sys.exit(1)

        # ---- 步骤 2：收集首页视频链接 ----
        logger.info("开始扫描首页视频...")
        try:
            video_links = get_homepage_video_links(page, config.VIDEO_COUNT)
        except Exception as e:
            logger.error(f"收集视频链接失败: {e}")
            browser.close()
            sys.exit(1)

        if not video_links:
            logger.error("未能收集到任何视频链接，脚本退出")
            browser.close()
            sys.exit(1)

        print(f"\n🎯 共获取到 {len(video_links)} 个视频，开始逐一点赞...\n")

        # ---- 步骤 3：逐一观看并点赞 ----
        liked_count = 0
        failed_count = 0

        for idx, url in enumerate(video_links, start=1):
            print(f"[{idx:02d}/{len(video_links)}] {url}")
            success = like_video(page, url)
            if success:
                liked_count += 1
            else:
                failed_count += 1

        # ---- 完成统计 ----
        print()
        print("╔══════════════════════════════════════════╗")
        print(f"║  运行完成！                               ║")
        print(f"║  ✅ 成功点赞：{liked_count:<3} 个                       ║")
        print(f"║  ❌ 失败/跳过：{failed_count:<3} 个                     ║")
        print("╚══════════════════════════════════════════╝")
        print()
        logger.info(f"运行结束 — 成功: {liked_count}, 失败: {failed_count}")

        browser.close()


if __name__ == "__main__":
    main()
