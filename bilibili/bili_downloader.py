"""
B站视频/字幕下载器
支持下载UP主主页所有视频和单个视频的字幕
"""
import os
import sys
import logging
import argparse
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List
import re
import time

try:
    import yt_dlp
except ImportError:
    print("错误：未安装yt-dlp，请运行：pip install yt-dlp")
    sys.exit(1)

import config


class BiliDownloader:
    """B站视频/字幕下载器"""
    
    def __init__(self, 
                 download_mode: str = None,
                 output_dir: str = None,
                 max_count: int = None,
                 cookie_file: str = None):
        """
        初始化下载器
        
        Args:
            download_mode: 下载模式 'both' | 'video_only' | 'subtitle_only'
            output_dir: 输出目录
            max_count: 最大下载数量
            cookie_file: cookie文件路径
        """
        self.download_mode = download_mode or config.DOWNLOAD_MODE
        self.output_dir = output_dir or config.DEFAULT_OUTPUT_DIR
        self.max_count = max_count if max_count is not None else config.MAX_DOWNLOAD_COUNT
        self.cookie_file = cookie_file or config.COOKIE_FILE
        
        # 设置日志
        self._setup_logging()
        
        # 下载计数器
        self.download_count = 0
        self.success_count = 0
        self.failed_count = 0
        self.skipped_count = 0
        
        self.logger.info(f"初始化下载器 - 模式: {self.download_mode}, 输出目录: {self.output_dir}")
    
    def _setup_logging(self):
        """设置日志"""
        # 创建日志目录
        if config.SAVE_LOG_FILE:
            log_dir = os.path.dirname(config.LOG_FILE)
            if log_dir:
                os.makedirs(log_dir, exist_ok=True)
        
        # 配置日志格式
        log_format = '%(asctime)s - %(levelname)s - %(message)s'
        date_format = '%Y-%m-%d %H:%M:%S'
        
        # 设置根日志器
        self.logger = logging.getLogger('BiliDownloader')
        self.logger.setLevel(getattr(logging, config.LOG_LEVEL))
        
        # 清除已有的处理器
        self.logger.handlers.clear()
        
        # 控制台处理器
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(logging.Formatter(log_format, date_format))
        self.logger.addHandler(console_handler)
        
        # 文件处理器
        if config.SAVE_LOG_FILE:
            file_handler = logging.FileHandler(config.LOG_FILE, encoding='utf-8')
            file_handler.setFormatter(logging.Formatter(log_format, date_format))
            self.logger.addHandler(file_handler)
    
    def _get_yt_dlp_opts(self, is_playlist: bool = False) -> Dict[str, Any]:
        """
        获取yt-dlp配置参数
        
        Args:
            is_playlist: 是否为播放列表/UP主主页
            
        Returns:
            yt-dlp配置字典
        """
        opts = {
            'logger': self.logger,
            'no_warnings': False,
            'user_agent': config.USER_AGENT,
            'quiet': False,
            'no_color': False,
            'progress_hooks': [self._progress_hook],
        }
        
        # Cookie设置
        if os.path.exists(self.cookie_file):
            opts['cookiefile'] = self.cookie_file
            self.logger.info(f"使用Cookie文件: {self.cookie_file}")
        else:
            self.logger.warning(f"Cookie文件不存在: {self.cookie_file}")
        
        # 输出目录设置
        output_template = os.path.join(self.output_dir, config.VIDEO_FILENAME_TEMPLATE)
        opts['outtmpl'] = output_template
        
        # 下载模式配置
        if self.download_mode == 'subtitle_only':
            opts['skip_download'] = True
            opts['writesubtitles'] = True
            opts['writeautomaticsub'] = True
            
            if config.DOWNLOAD_ALL_SUBTITLES:
                opts['allsubtitles'] = True
                self.logger.info("模式: 下载所有可用字幕")
            else:
                opts['subtitleslangs'] = config.SUBTITLE_LANGS
                self.logger.info(f"模式: 下载指定语言字幕 ({', '.join(config.SUBTITLE_LANGS[:3])}...)")
            
            opts['subtitlesformat'] = 'srt'
            opts['convertsubtitles'] = 'srt'
        
        elif self.download_mode == 'video_only':
            opts['format'] = self._get_video_format()
            opts['writesubtitles'] = False
            self.logger.info("模式: 仅下载视频")
        
        else:  # both
            opts['format'] = self._get_video_format()
            opts['writesubtitles'] = True
            opts['writeautomaticsub'] = True
            opts['subtitleslangs'] = config.SUBTITLE_LANGS
            opts['subtitlesformat'] = 'srt'
            opts['convertsubtitles'] = 'srt'
            self.logger.info("模式: 下载视频和字幕")
        
        # 播放列表配置
        if is_playlist:
            opts['noplaylist'] = False
            if self.max_count > 0:
                opts['playlistend'] = self.max_count
                self.logger.info(f"限制下载数量: {self.max_count}")
        else:
            opts['noplaylist'] = True
        
        # 高级配置
        if config.SKIP_EXISTING:
            opts['overwrites'] = False
            opts['continuedl'] = True
        
        if config.RATE_LIMIT:
            opts['ratelimit'] = config.RATE_LIMIT
        
        if config.MAX_RETRIES:
            opts['retries'] = config.MAX_RETRIES
        
        if config.TIMEOUT:
            opts['socket_timeout'] = config.TIMEOUT
        
        if config.PROXY:
            opts['proxy'] = config.PROXY
        
        # 合并额外配置
        opts.update(config.EXTRA_YT_DLP_OPTS)
        
        return opts
    
    def _get_video_format(self) -> str:
        """获取视频格式选择器"""
        if config.VIDEO_QUALITY == 'best':
            return 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'
        elif config.VIDEO_QUALITY == '1080p':
            return 'bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080][ext=mp4]/best'
        elif config.VIDEO_QUALITY == '720p':
            return 'bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]/best'
        elif config.VIDEO_QUALITY == '480p':
            return 'bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/best[height<=480][ext=mp4]/best'
        else:
            return 'best'
    
    def _progress_hook(self, d: Dict[str, Any]):
        """下载进度回调"""
        if d['status'] == 'downloading':
            total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
            downloaded = d.get('downloaded_bytes', 0)
            speed = d.get('speed', 0)
            eta = d.get('eta', 0)
            
            if total > 0:
                percent = (downloaded / total) * 100
                speed_str = f"{speed/1024/1024:.2f}MB/s" if speed else "N/A"
                eta_str = f"{eta}s" if eta else "N/A"
                
                # 使用\r实现同行更新
                sys.stdout.write(
                    f"\r下载进度: {percent:.1f}% | "
                    f"已下载: {downloaded/1024/1024:.1f}MB / {total/1024/1024:.1f}MB | "
                    f"速度: {speed_str} | "
                    f"剩余时间: {eta_str}"
                )
                sys.stdout.flush()
        
        elif d['status'] == 'finished':
            filename = d.get('filename', 'Unknown')
            # 字幕下载不会显示进度，直接标记为成功
            if filename.endswith(('.srt', '.vtt', '.ass', '.json')):
                sys.stdout.write(f"[OK] 字幕: {os.path.basename(filename)}\n")
            else:
                sys.stdout.write(f"\n[OK] 完成: {os.path.basename(filename)}\n")
            sys.stdout.flush()
            self.success_count += 1
        
        elif d['status'] == 'error':
            self.logger.error(f"下载出错")
            self.failed_count += 1
    
    def _is_valid_url(self, url: str) -> bool:
        """验证URL是否为有效的B站链接"""
        patterns = [
            r'https?://space\.bilibili\.com/\d+',  # UP主主页
            r'https?://www\.bilibili\.com/video/[Bb][Vv]\w+',  # 视频页
            r'https?://b23\.tv/\w+',  # 短链接
        ]
        return any(re.match(pattern, url) for pattern in patterns)
    
    def _get_url_type(self, url: str) -> str:
        """判断URL类型"""
        if 'space.bilibili.com' in url:
            return 'user_space'
        elif 'bilibili.com/video' in url or 'b23.tv' in url:
            return 'video'
        else:
            return 'unknown'
    
    def download_from_url(self, url: str, custom_output_dir: Optional[str] = None) -> bool:
        """
        从URL下载视频/字幕
        
        Args:
            url: B站URL（UP主主页或视频页）
            custom_output_dir: 自定义输出目录
            
        Returns:
            是否成功
        """
        # 验证URL
        if not self._is_valid_url(url):
            self.logger.error(f"无效的B站URL: {url}")
            return False
        
        # 确定URL类型
        url_type = self._get_url_type(url)
        is_playlist = (url_type == 'user_space')
        
        self.logger.info(f"{'='*60}")
        self.logger.info(f"开始下载任务")
        self.logger.info(f"URL类型: {'UP主主页' if is_playlist else '单个视频'}")
        self.logger.info(f"URL: {url}")
        
        # 设置输出目录
        if custom_output_dir:
            original_output = self.output_dir
            self.output_dir = custom_output_dir
            self.logger.info(f"使用自定义输出目录: {custom_output_dir}")
        
        # 创建输出目录
        os.makedirs(self.output_dir, exist_ok=True)
        
        # 获取yt-dlp配置
        ydl_opts = self._get_yt_dlp_opts(is_playlist=is_playlist)
        
        # 如果是UP主主页，需要转换URL格式
        if is_playlist:
            # 提取UP主ID并构造视频列表URL
            match = re.search(r'space\.bilibili\.com/(\d+)', url)
            if match:
                uid = match.group(1)
                # 使用UP主投稿页URL
                url = f"https://space.bilibili.com/{uid}/video"
                self.logger.info(f"转换为投稿页URL: {url}")
        
        try:
            self.logger.info("开始解析URL...")
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # 先获取信息
                info = ydl.extract_info(url, download=False)
                
                if info is None:
                    self.logger.error("无法提取视频信息")
                    return False
                
                # 判断是否为播放列表
                if 'entries' in info:
                    entries = list(info['entries'])
                    total = len(entries)
                    self.logger.info(f"发现 {total} 个视频")
                    
                    if self.max_count > 0:
                        entries = entries[:self.max_count]
                        self.logger.info(f"限制下载前 {self.max_count} 个")
                    
                    self.logger.info(f"开始下载 {len(entries)} 个视频...")
                    
                    for idx, entry in enumerate(entries, 1):
                        if entry is None:
                            self.skipped_count += 1
                            continue
                        
                        title = entry.get('title', 'Unknown')
                        video_id = entry.get('id', 'Unknown')
                        
                        # 构造视频URL
                        video_url = entry.get('webpage_url') or entry.get('url')
                        if not video_url and video_id:
                            # 手动构造B站视频URL
                            video_url = f"https://www.bilibili.com/video/{video_id}"
                        
                        if not video_url:
                            self.logger.warning(f"跳过: 无法获取视频URL - {title}")
                            self.skipped_count += 1
                            continue
                        
                        self.logger.info(f"\n[{idx}/{len(entries)}] 下载: {title} (BV{video_id})")
                        
                        try:
                            # 直接下载，不重新提取信息（减少请求次数）
                            ydl.download([video_url])
                            
                            # 添加延迟，防止触发风控
                            if idx < len(entries) and config.DOWNLOAD_DELAY > 0:
                                self.logger.info(f"等待 {config.DOWNLOAD_DELAY} 秒...")
                                time.sleep(config.DOWNLOAD_DELAY)
                            
                        except Exception as e:
                            self.logger.error(f"下载失败: {e}")
                            self.failed_count += 1
                            # 出错后也等待一下
                            if config.DOWNLOAD_DELAY > 0:
                                time.sleep(config.DOWNLOAD_DELAY)
                            continue
                else:
                    # 单个视频
                    title = info.get('title', 'Unknown')
                    video_id = info.get('id', 'Unknown')
                    self.logger.info(f"视频标题: {title}")
                    self.logger.info(f"视频ID: BV{video_id}")
                    
                    # 下载（让yt-dlp根据配置决定下载什么）
                    ydl.download([url])
            
            self.logger.info(f"\n{'='*60}")
            self.logger.info(f"下载任务完成！")
            self.logger.info(f"成功: {self.success_count} | 失败: {self.failed_count} | 跳过: {self.skipped_count}")
            self.logger.info(f"文件保存位置: {self.output_dir}")
            self.logger.info(f"{'='*60}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"下载过程出错: {e}", exc_info=True)
            return False
        
        finally:
            # 恢复原输出目录
            if custom_output_dir:
                self.output_dir = original_output
    
    def download_video(self, video_url: str, custom_output_dir: Optional[str] = None) -> bool:
        """
        下载单个视频（快捷方法）
        
        Args:
            video_url: 视频页URL
            custom_output_dir: 自定义输出目录
            
        Returns:
            是否成功
        """
        return self.download_from_url(video_url, custom_output_dir)
    
    def download_user_videos(self, user_space_url: str, custom_output_dir: Optional[str] = None) -> bool:
        """
        下载UP主的所有视频（快捷方法）
        
        Args:
            user_space_url: UP主空间URL
            custom_output_dir: 自定义输出目录
            
        Returns:
            是否成功
        """
        return self.download_from_url(user_space_url, custom_output_dir)
    
    def check_video_subtitles(self, video_url: str) -> Dict[str, Any]:
        """
        检查视频是否有字幕
        
        Args:
            video_url: 视频URL
            
        Returns:
            字幕信息字典
        """
        opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
        }
        
        if os.path.exists(self.cookie_file):
            opts['cookiefile'] = self.cookie_file
        
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(video_url, download=False)
                
                if info is None:
                    return {
                        'has_subtitles': False,
                        'error': '无法提取视频信息'
                    }
                
                result = {
                    'title': info.get('title', 'Unknown'),
                    'id': info.get('id', 'Unknown'),
                    'has_subtitles': False,
                    'subtitles': [],
                    'automatic_captions': []
                }
                
                # 收集字幕，排除danmaku（弹幕）
                if info.get('subtitles'):
                    subs = [lang for lang in info['subtitles'].keys() if lang != 'danmaku']
                    if subs:
                        result['has_subtitles'] = True
                        result['subtitles'] = subs
                
                if info.get('automatic_captions'):
                    auto_subs = [lang for lang in info['automatic_captions'].keys() if lang != 'danmaku']
                    if auto_subs:
                        result['has_subtitles'] = True
                        result['automatic_captions'] = auto_subs
                
                return result
                
        except Exception as e:
            return {
                'has_subtitles': False,
                'error': str(e)
            }


def main():
    """命令行入口"""
    parser = argparse.ArgumentParser(
        description='B站视频/字幕下载器',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  # 下载UP主的所有视频（限制10个）
  python bili_downloader.py -u https://space.bilibili.com/12345678 -n 10
  
  # 只下载字幕
  python bili_downloader.py -v https://www.bilibili.com/video/BV1xx411c7mD -m subtitle_only
  
  # 下载到指定目录
  python bili_downloader.py -v https://www.bilibili.com/video/BV1xx411c7mD -o ./my_videos
  
  # 使用自定义cookie文件
  python bili_downloader.py -u https://space.bilibili.com/12345678 -c ./my_cookies.txt
        """
    )
    
    # URL参数（互斥）
    url_group = parser.add_mutually_exclusive_group(required=True)
    url_group.add_argument('-u', '--user', help='UP主主页URL')
    url_group.add_argument('-v', '--video', help='视频详情页URL')
    
    # 可选参数
    parser.add_argument('-m', '--mode', 
                       choices=['both', 'video_only', 'subtitle_only'],
                       default=config.DOWNLOAD_MODE,
                       help=f'下载模式 (默认: {config.DOWNLOAD_MODE})')
    
    parser.add_argument('-n', '--number',
                       type=int,
                       default=config.MAX_DOWNLOAD_COUNT,
                       help=f'最大下载数量，0表示不限制 (默认: {config.MAX_DOWNLOAD_COUNT})')
    
    parser.add_argument('-o', '--output',
                       help=f'输出目录 (默认: {config.DEFAULT_OUTPUT_DIR})')
    
    parser.add_argument('-c', '--cookie',
                       help=f'Cookie文件路径 (默认: {config.COOKIE_FILE})')
    
    args = parser.parse_args()
    
    # 创建下载器
    downloader = BiliDownloader(
        download_mode=args.mode,
        output_dir=args.output,
        max_count=args.number,
        cookie_file=args.cookie
    )
    
    # 执行下载
    url = args.user or args.video
    success = downloader.download_from_url(url)
    
    # 退出状态
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()

