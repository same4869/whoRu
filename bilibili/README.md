# B站视频/字幕下载器

基于 yt-dlp 的 B站视频和字幕下载工具。

## 🚨 重要说明

**字幕 ≠ 弹幕**

- ✅ **字幕（Subtitle）**：ai-zh（AI中文）、zh-Hans（简中）等，这是真正的字幕
- ❌ **弹幕（Danmaku）**：观众发送的弹幕，不是字幕

**很多B站视频只有弹幕，没有字幕！** 特别是：
- 短视频、vlog、生活记录
- 游戏实况、娱乐剪辑  
- 个人UP主的日常内容

通常有字幕的视频：
- 知识类、教程类、讲座
- 长视频（>10分钟）
- 大UP主或官方账号的内容

## 安装

```bash
pip install -r requirements.txt
```

需要安装 ffmpeg：https://ffmpeg.org/download.html

## 快速开始

### 1. 检查视频是否有字幕（强烈推荐）

```bash
python check_subtitles.py -v https://www.bilibili.com/video/BV1xx411c7mD
```

输出示例：
```
字幕状态: [OK] 有字幕
自动字幕: ai-zh
```

或者：
```
字幕状态: [X] 无字幕
```

### 2. 下载单个视频

```bash
# 下载视频和字幕
python bili_downloader.py -v https://www.bilibili.com/video/BV1xx411c7mD

# 只下载字幕
python bili_downloader.py -v https://www.bilibili.com/video/BV1xx411c7mD -m subtitle_only

# 只下载视频
python bili_downloader.py -v https://www.bilibili.com/video/BV1xx411c7mD -m video_only
```

### 3. 下载UP主视频

```bash
# 下载UP主的所有视频
python bili_downloader.py -u https://space.bilibili.com/123456

# 限制下载数量
python bili_downloader.py -u https://space.bilibili.com/123456 -n 10

# 只下载字幕
python bili_downloader.py -u https://space.bilibili.com/123456 -m subtitle_only -n 10
```

### 4. 自定义输出目录

```bash
python bili_downloader.py -v URL -o ./my_videos
```

### 5. 使用Cookie文件（可选）

```bash
# 1. 复制示例文件
cp bilibili_cookies.txt.example bilibili_cookies.txt

# 2. 用浏览器插件导出Cookie并替换文件内容
# Chrome插件：Get cookies.txt LOCALLY

# 3. 使用
python bili_downloader.py -v URL -c ./bilibili_cookies.txt
```

## 配置

编辑 `config.py` 修改设置：

```python
# 下载模式
DOWNLOAD_MODE = 'both'  # 'both' | 'video_only' | 'subtitle_only'

# 字幕语言（只下载中文，排除英文和弹幕）
SUBTITLE_LANGS = ['ai-zh', 'zh-Hans', 'zh-CN', 'zh-Hant', 'zh-TW', 'chi', 'zh']

# 是否下载所有字幕（包括弹幕）
DOWNLOAD_ALL_SUBTITLES = False  # 建议保持False

# 视频质量
VIDEO_QUALITY = 'best'  # 'best' | '1080p' | '720p' | '480p'

# 最大下载数量
MAX_DOWNLOAD_COUNT = 0  # 0表示不限制
```

### 字幕语言配置

```python
# 只要简体中文
SUBTITLE_LANGS = ['ai-zh', 'zh-Hans', 'zh-CN']

# 只要繁体中文  
SUBTITLE_LANGS = ['zh-Hant', 'zh-TW']

# 中文+英文
SUBTITLE_LANGS = ['ai-zh', 'zh-Hans', 'ai-en', 'en']

# 下载所有（包括弹幕）
DOWNLOAD_ALL_SUBTITLES = True  # 不推荐
```

## 命令行参数

| 参数 | 说明 | 示例 |
|------|------|------|
| `-v, --video` | 视频URL | `-v https://...` |
| `-u, --user` | UP主主页URL | `-u https://space.bilibili.com/123` |
| `-m, --mode` | 下载模式：both/video_only/subtitle_only | `-m subtitle_only` |
| `-n, --number` | 最大下载数量（0=不限制） | `-n 10` |
| `-o, --output` | 输出目录 | `-o ./downloads` |
| `-c, --cookie` | Cookie文件路径 | `-c ./my_cookies.txt` |

## Python代码使用

```python
from bili_downloader import BiliDownloader

# 创建下载器
downloader = BiliDownloader(
    download_mode='both',
    max_count=10,
    output_dir='./downloads'
)

# 下载单个视频
downloader.download_video('https://www.bilibili.com/video/BV1xx411c7mD')

# 下载UP主视频
downloader.download_user_videos('https://space.bilibili.com/123456')

# 检查字幕
result = downloader.check_video_subtitles('视频URL')
print(result['has_subtitles'])  # True/False
print(result['subtitles'])  # ['ai-zh'] 或 []
```

## 常见问题

### Q: 少量下载成功，批量下载就失败？

A: **触发了B站的风控限制！**

解决方法：
1. **增加延迟**：修改 `config.py` 中的 `DOWNLOAD_DELAY`（默认2秒）
   ```python
   DOWNLOAD_DELAY = 5  # 增加到5秒
   ```

2. **分批下载**：不要一次下载太多
   ```bash
   # 分批下载，每次10个
   python bili_downloader.py -u URL -n 10 -o ./batch1
   python bili_downloader.py -u URL -n 20 -o ./batch2  # 下载11-20
   ```

3. **配置Cookie**：登录状态更不容易触发风控

### Q: 为什么下载后没有文件？

A: **最常见原因：视频没有字幕，只有弹幕！**

1. 先检查：`python check_subtitles.py -v 视频URL`
2. 如果显示无字幕，说明这个视频确实没有
3. 短视频、vlog、游戏实况等通常没有字幕
4. 建议选择知识类、教程类视频

### Q: 如何只下载中文字幕？

A: 默认配置已经是只下载中文（`config.py` 中的 `SUBTITLE_LANGS`）

### Q: danmaku是什么？

A: **danmaku是弹幕，不是字幕！** 本工具默认排除弹幕，只下载真正的字幕。

### Q: 如何下载所有字幕（包括弹幕）？

A: 修改 `config.py`：
```python
DOWNLOAD_ALL_SUBTITLES = True
```

注意：这会下载弹幕（XML格式），不推荐。

### Q: 哪些视频有字幕？

A: 
- ✅ 有字幕：知识类、教程类、长视频、大UP主内容、官方账号
- ❌ 无字幕：短视频、vlog、游戏实况、娱乐剪辑、个人日常

### Q: 下载速度慢？

A:
1. 配置Cookie文件（登录状态更稳定）
2. 检查网络连接
3. 尝试不同时间段

### Q: 字幕文件乱码？

A: 字幕已自动转换为UTF-8编码的SRT格式，使用支持UTF-8的播放器（VLC、PotPlayer）。

## 字幕转文本工具

下载的SRT字幕文件可以转换为纯文本：

### 方式1：命令行转换

```bash
# 转换单个文件
python srt_to_txt.py -f video.srt

# 批量转换目录
python srt_to_txt.py -d ./downloads

# 转换到指定目录
python srt_to_txt.py -d ./downloads -o ./texts

# 合并为段落（默认是分行）
python srt_to_txt.py -f video.srt --merge

# 不自动添加标点
python srt_to_txt.py -f video.srt --no-punctuation
```

### 方式2：交互式批量转换

```bash
# 运行交互式工具
python 批量转换字幕.py
```

会提示选择：
1. 转换当前目录
2. 转换指定目录
3. 递归转换（包括子目录）

### Python代码使用

```python
from srt_to_txt import SrtToTextConverter

# 创建转换器（默认保持分行）
converter = SrtToTextConverter(
    merge_lines=False,     # False=保持分行（默认），True=合并为段落
    add_punctuation=True,  # 自动添加标点
    remove_duplicates=True # 去除重复
)

# 转换单个文件
converter.convert_file('video.srt', 'output.txt')

# 批量转换目录
converter.convert_directory('./downloads', './texts')
```

### 转换效果

**SRT格式：**
```
1
00:00:00,260 --> 00:00:01,000
哪的呀

2
00:00:01,000 --> 00:00:02,140
哎车窗也要下来哈

3
00:00:02,140 --> 00:00:02,940
这不让停车
```

**转换后（默认 - 保持分行）：**
```
哪的呀。
哎车窗也要下来哈。
这不让停车。
```

**转换后（合并段落模式）：**
```
哪的呀。哎车窗也要下来哈。这不让停车。
```

使用 `--merge` 参数可以合并为段落：
```bash
python srt_to_txt.py -f video.srt --merge
```

## 文件结构

```
bilibili/
├── 📄 核心文件
│   ├── bili_downloader.py          # 视频/字幕下载器
│   ├── check_subtitles.py         # 字幕检查工具
│   ├── srt_to_txt.py              # 字幕转文本工具
│   ├── 批量转换字幕.py             # 交互式批量转换
│   └── config.py                  # 配置文件
│
├── 📋 配置和文档
│   ├── requirements.txt           # 依赖列表
│   ├── bilibili_cookies.txt.example  # Cookie示例
│   ├── README.md                  # 使用文档
│   └── .gitignore                 # Git忽略配置
│
├── 💡 示例
│   ├── example_usage.py           # Python代码示例
│   └── examples/                  # 示例字幕文件
│
└── 📁 运行时目录（使用后生成）
    ├── downloads/                 # 下载的视频和字幕
    ├── logs/                      # 运行日志
    └── bilibili_cookies.txt       # 你的Cookie文件（需自己创建）
```

## 注意事项

- 请遵守B站服务条款，仅下载自己有权访问的内容
- Cookie文件包含登录信息，请妥善保管
- 大量下载可能触发风控，建议适度使用
- 本工具仅供学习交流，不得用于商业用途
- **字幕 ≠ 弹幕**，很多视频没有字幕是正常的

---

**版本：v1.2** | 更新日期：2025-11-04
