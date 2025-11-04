"""
B站视频/字幕下载器配置文件
"""
import os

# ==================== 基础配置 ====================

# Cookie文件路径（用于登录状态）
COOKIE_FILE = os.path.join(os.path.dirname(__file__), "bilibili_cookies.txt")

# 默认输出目录
DEFAULT_OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "downloads")

# ==================== 下载配置 ====================

# 下载模式：'both' | 'video_only' | 'subtitle_only'
DOWNLOAD_MODE = 'both'

# 字幕语言优先级（B站实际使用的语言代码）
# 注意：B站有时候会用不同的语言代码，建议多配置几个
# ai-zh: AI中文, zh-Hans/zh-CN: 简中, zh-Hant/zh-TW: 繁中
SUBTITLE_LANGS = ['ai-zh', 'zh-Hans', 'zh-CN', 'zh-Hant', 'zh-TW', 'chi', 'zh']

# 是否下载所有可用字幕（如果True，会忽略SUBTITLE_LANGS并下载所有字幕）
# 注意：开启后可能会下载英文、日文、弹幕等所有内容
# 建议：保持False，只下载中文字幕
DOWNLOAD_ALL_SUBTITLES = False

# 视频质量优先级
VIDEO_QUALITY = 'best'  # 'best' | '1080p' | '720p' | '480p'

# 最大下载数量（0表示不限制）
MAX_DOWNLOAD_COUNT = 0

# 是否跳过已存在的文件
SKIP_EXISTING = True

# ==================== 高级配置 ====================

# 下载速率限制（如：'1M' 表示1MB/s，None表示不限制）
RATE_LIMIT = None

# 并发下载数
CONCURRENT_DOWNLOADS = 1

# 重试次数
MAX_RETRIES = 3

# 超时时间（秒）
TIMEOUT = 300

# 批量下载时每个视频之间的延迟（秒），防止触发风控
DOWNLOAD_DELAY = 2  # 建议2-5秒

# ==================== 文件命名配置 ====================

# 视频文件命名模板
# 可用变量：{title}, {id}, {uploader}, {upload_date}
VIDEO_FILENAME_TEMPLATE = '%(title)s-%(id)s.%(ext)s'

# 字幕文件命名模板
SUBTITLE_FILENAME_TEMPLATE = '%(title)s-%(id)s.%(ext)s'

# ==================== 日志配置 ====================

# 日志级别：'DEBUG' | 'INFO' | 'WARNING' | 'ERROR'
LOG_LEVEL = 'INFO'

# 是否保存日志文件
SAVE_LOG_FILE = True

# 日志文件路径
LOG_FILE = os.path.join(os.path.dirname(__file__), "logs", "download.log")

# ==================== yt-dlp配置 ====================

# 代理设置（如需要）
PROXY = None  # 例如：'http://127.0.0.1:7890'

# User-Agent
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'

# 额外的yt-dlp参数
EXTRA_YT_DLP_OPTS = {}

