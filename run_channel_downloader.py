import yt_dlp
import os
import glob
import time
from datetime import datetime

"""
YouTube 频道字幕下载器 - 优化版
===============================================

功能说明：
- 自动获取指定YouTube频道的视频列表
- 支持限制下载视频数量（只下载最新的N个视频）
- 智能选择字幕语言（优先级：简体中文 > 繁体中文 > 英文）
- 自动跳过没有合适字幕的视频
- 在字幕文件开头自动添加视频发布时间和标题信息

使用方法：
1. 修改下面配置区的参数
2. 运行脚本即可

配置说明：
- MAX_VIDEOS = 0：下载所有视频的字幕
- MAX_VIDEOS = 5：只下载最新5个视频的字幕
- MAX_VIDEOS = 10：只下载最新10个视频的字幕
"""

# ==================== 配置区 (请在这里修改) ====================

# 1. 填入你想要下载的 YouTube 频道的 "Videos" 页面 URL
CHANNEL_URL = "https://www.youtube.com/@blockchaindailynews/videos"

# 2. 定义存放最终字幕文件的输出文件夹名
OUTPUT_DIR = 'output_result'

# 3. 定义 Cookies 文件名 (用于登录验证)
COOKIE_FILE = 'www.youtube.com_cookies.txt'

# 4. 定义临时存放 URL 列表的文件名 (脚本会自动创建和覆盖)
URLS_FILE = '1.txt'

# 5. 定义下载视频数量限制 (0表示下载所有视频，大于0则只下载最新的指定数量)
MAX_VIDEOS = 0  # 修改这个数值来控制下载数量：0=下载所有，5=只下载最新5个

# =============================================================

def get_channel_video_urls(channel_url):
    """
    使用 yt-dlp 获取一个频道下的所有视频 URL。
    这相当于命令: yt-dlp --flat-playlist --print url "channel_url"
    """
    ydl_opts = {
        'extract_flat': True,  # 等同于 --flat-playlist，只提取链接，不访问视频详情
        'quiet': True,         # 不在控制台打印过多信息
    }
    
    video_urls = []
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # extract_info 会返回一个包含所有信息的字典
            result = ydl.extract_info(channel_url, download=False)
            
            if 'entries' in result:
                # 从返回结果中提取每个视频的 URL
                video_urls = [entry['url'] for entry in result['entries']]
    except Exception as e:
        print(f"错误：获取频道视频列表失败。请检查 URL 是否正确以及网络连接。")
        print(f"详细错误: {e}")
        return None
        
    return video_urls

def find_best_subtitle_language(subtitles, automatic_captions):
    """
    根据优先级查找最佳字幕语言
    优先级：简体中文 > 繁体中文 > 英文
    """
    # 定义语言优先级
    priority_languages = ['zh-CN', 'zh-Hans', 'zh', 'zh-TW', 'zh-Hant', 'en']
    
    # 合并所有可用字幕
    all_subtitles = {}
    if subtitles:
        all_subtitles.update(subtitles)
    if automatic_captions:
        # 自动字幕标记为较低优先级
        for lang, subs in automatic_captions.items():
            if lang not in all_subtitles:  # 优先使用人工字幕
                all_subtitles[lang] = subs
    
    # 按优先级查找
    for lang in priority_languages:
        if lang in all_subtitles:
            return lang, '人工字幕' if (subtitles and lang in subtitles) else '自动字幕'
    
    return None, None

def format_upload_date(upload_date):
    """
    将 yt-dlp 返回的上传日期格式化为可读格式
    upload_date 格式通常是 'YYYYMMDD'
    """
    if not upload_date:
        return "未知日期"
    
    try:
        # 将字符串转换为日期对象
        date_obj = datetime.strptime(str(upload_date), '%Y%m%d')
        # 格式化为中文日期
        return date_obj.strftime('%Y年%m月%d日')
    except (ValueError, TypeError):
        return "未知日期"

def add_timestamp_to_subtitle_file(file_path, upload_date, video_title):
    """
    在字幕文件开头添加视频发布时间信息
    """
    if not os.path.exists(file_path):
        return False
        
    try:
        # 读取原始字幕内容
        with open(file_path, 'r', encoding='utf-8') as f:
            original_content = f.read()
        
        # 创建时间戳信息
        formatted_date = format_upload_date(upload_date)
        timestamp_info = f"""# 视频发布时间: {formatted_date}
# 视频标题: {video_title}
# 
# ===============================================
# 以下为原始字幕内容
# ===============================================

"""
        
        # 将时间戳信息添加到字幕内容开头
        new_content = timestamp_info + original_content
        
        # 写回文件
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
            
        return True
        
    except Exception as e:
        print(f"添加时间戳信息失败: {e}")
        return False

def download_subtitles_from_list(urls):
    """
    根据给定的 URL 列表，下载所有视频的字幕。
    只下载优先级最高的一种语言。
    """
    # 使用 yt-dlp 的 Python API 开始下载
    success_count = 0
    failed_count = 0
    no_subtitles_count = 0
    
    # 基础配置，不指定字幕语言
    base_ydl_opts = {
        'skip_download': True,
        'ignoreerrors': True,
        'cookiefile': COOKIE_FILE,
        'writedescription': False,
        'writeinfojson': False,
        'writethumbnail': False,
    }
    
    with yt_dlp.YoutubeDL(base_ydl_opts) as ydl:
        total_urls = len(urls)
        for i, url in enumerate(urls, 1):
            print(f"--- [进度: {i}/{total_urls}] 正在处理URL: {url} ---")
            try:
                # 先获取视频信息，检查字幕
                info = ydl.extract_info(url, download=False)
                
                # 查找最佳字幕语言
                best_lang, subtitle_type = find_best_subtitle_language(
                    info.get('subtitles'), 
                    info.get('automatic_captions')
                )
                
                if best_lang:
                    video_title = info.get('title', '未知标题')
                    upload_date = info.get('upload_date')
                    print(f"发现字幕，开始下载: {video_title}")
                    print(f"选择语言: {best_lang} ({subtitle_type})")
                    print(f"发布时间: {format_upload_date(upload_date)}")
                    
                    # 记录下载前的时间，用于识别新生成的文件
                    download_start_time = time.time()
                    
                    # 配置专门的下载选项
                    download_opts = base_ydl_opts.copy()
                    download_opts.update({
                        'writesubtitles': True,
                        'writeautomaticsub': True,
                        'subtitleslangs': [best_lang],
                        'outtmpl': os.path.join(OUTPUT_DIR, '%(title)s.%(ext)s'),
                    })
                    
                    # 使用新的配置下载
                    with yt_dlp.YoutubeDL(download_opts) as download_ydl:
                        download_ydl.download([url])
                    
                    # 等待一小段时间确保文件写入完成
                    time.sleep(0.5)
                    
                    # 查找新生成的字幕文件
                    all_subtitle_files = glob.glob(os.path.join(OUTPUT_DIR, "*.vtt"))
                    
                    # 找到最新创建的字幕文件（在下载时间之后创建的）
                    new_files = [f for f in all_subtitle_files if os.path.getmtime(f) >= download_start_time - 1]
                    
                    if new_files:
                        # 如果有多个新文件，选择最新的
                        latest_file = max(new_files, key=os.path.getmtime)
                        if add_timestamp_to_subtitle_file(latest_file, upload_date, video_title):
                            print("✓ 已添加发布时间信息到字幕文件")
                        else:
                            print("⚠ 添加发布时间信息失败")
                    else:
                        print("⚠ 未找到新生成的字幕文件")
                    
                    success_count += 1
                    print("✓ 字幕下载成功")
                else:
                    print(f"⚠ 该视频没有中文或英文字幕: {info.get('title', '未知标题')}")
                    # 显示可用的语言（如果有的话）
                    available_langs = []
                    if info.get('subtitles'):
                        available_langs.extend(list(info['subtitles'].keys()))
                    if info.get('automatic_captions'):
                        available_langs.extend([f"{lang}(自动)" for lang in info['automatic_captions'].keys()])
                    if available_langs:
                        print(f"可用语言: {', '.join(available_langs[:5])}{'...' if len(available_langs) > 5 else ''}")
                    no_subtitles_count += 1
                    
            except Exception as e:
                print(f"✗ 处理过程中发生错误: {e}")
                failed_count += 1
    
    # 输出统计信息
    print(f"\n=== 下载统计 ===")
    print(f"成功下载字幕: {success_count} 个视频")
    print(f"没有合适字幕: {no_subtitles_count} 个视频") 
    print(f"处理失败: {failed_count} 个视频")
    print(f"总计处理: {total_urls} 个视频")

def main():
    """
    主函数：集成所有步骤，实现完全自动化。
    """
    print("============================================")
    print("YouTube 频道字幕下载器")
    print("============================================")

    # 步骤 1: 获取频道下的视频 URL
    if MAX_VIDEOS > 0:
        print(f"\n[步骤 1/3] 正在从频道获取视频的 URL 列表（限制数量: {MAX_VIDEOS}）...\n频道: {CHANNEL_URL}")
    else:
        print(f"\n[步骤 1/3] 正在从频道获取所有视频的 URL 列表...\n频道: {CHANNEL_URL}")
    video_urls = get_channel_video_urls(CHANNEL_URL)

    if not video_urls:
        print("\n无法获取视频列表，脚本已终止。")
        return

    print(f"成功获取到 {len(video_urls)} 个视频 URL。")
    
    # 应用视频数量限制
    if MAX_VIDEOS > 0 and len(video_urls) > MAX_VIDEOS:
        video_urls = video_urls[:MAX_VIDEOS]
        print(f"根据配置，将只下载最新的 {MAX_VIDEOS} 个视频。")
    elif MAX_VIDEOS == 0:
        print(f"将下载所有 {len(video_urls)} 个视频。")

    # 步骤 2: 将获取到的 URL 写入 urls.txt 文件
    try:
        with open(URLS_FILE, 'w', encoding='utf-8') as f:
            for url in video_urls:
                f.write(f"{url}\n")
        print(f"\n[步骤 2/3] 已将 {len(video_urls)} 个 URL 成功写入文件 '{URLS_FILE}'。")
    except Exception as e:
        print(f"\n错误：无法写入 URL 文件。详细错误: {e}")
        return

    # 步骤 3: 创建输出文件夹并开始下载字幕
    if not os.path.exists(OUTPUT_DIR):
        print(f"输出文件夹 '{OUTPUT_DIR}' 不存在，正在创建...")
        os.makedirs(OUTPUT_DIR)
        
    print(f"\n[步骤 3/3] 开始根据 '{URLS_FILE}' 中的列表下载字幕...")
    download_subtitles_from_list(video_urls)

    print(f"\n所有任务处理完毕！下载的字幕文件已全部保存在 '{OUTPUT_DIR}' 文件夹中。")

# 当直接运行此脚本文件时，执行 main() 函数
if __name__ == '__main__':
    main()