# ============================================================
# B站自动点赞脚本 - 配置文件
# ============================================================

# 每个视频的观看时长（秒）
WATCH_DURATION = 20

# 每次运行点赞的视频数量
VIDEO_COUNT = 20

# 两次操作之间的随机等待时间范围（秒）
MIN_WAIT = 1.0
MAX_WAIT = 3.0

# 是否显示浏览器窗口（False = 无头模式，不推荐，容易被检测）
HEADLESS = False

# 等待手动登录的超时时间（秒）
LOGIN_TIMEOUT = 180

# 页面加载超时时间（秒）
PAGE_TIMEOUT = 30

# 日志文件路径
LOG_FILE = "logs/liked_videos.log"

# 浏览器窗口大小
VIEWPORT_WIDTH = 1280
VIEWPORT_HEIGHT = 800

# User-Agent（模拟正常 Chrome 浏览器）
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)
