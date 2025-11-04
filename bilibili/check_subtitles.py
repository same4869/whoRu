"""
检查B站视频是否有字幕的工具
"""
import sys
import argparse
from bili_downloader import BiliDownloader


def check_subtitle(url: str):
    """检查单个视频的字幕"""
    print(f"正在检查视频字幕...")
    print(f"URL: {url}\n")
    
    downloader = BiliDownloader()
    result = downloader.check_video_subtitles(url)
    
    if 'error' in result:
        print(f"❌ 错误: {result['error']}")
        return False
    
    print(f"视频标题: {result['title']}")
    print(f"视频ID: BV{result['id']}")
    print(f"\n字幕状态: {'[OK] 有字幕' if result['has_subtitles'] else '[X] 无字幕'}")
    
    if result['has_subtitles']:
        if result['subtitles']:
            print(f"\n人工字幕: {', '.join(result['subtitles'])}")
        if result['automatic_captions']:
            print(f"自动字幕: {', '.join(result['automatic_captions'])}")
    
    return result['has_subtitles']


def main():
    parser = argparse.ArgumentParser(
        description='检查B站视频是否有字幕',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  python check_subtitles.py -v https://www.bilibili.com/video/BV1xx411c7mD
        """
    )
    
    parser.add_argument('-v', '--video', required=True, help='视频URL')
    
    args = parser.parse_args()
    
    has_subtitles = check_subtitle(args.video)
    
    sys.exit(0 if has_subtitles else 1)


if __name__ == '__main__':
    main()

