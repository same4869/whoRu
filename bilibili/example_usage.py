"""
B站下载器使用示例
展示如何在Python代码中使用下载器
"""

from bili_downloader import BiliDownloader


def example_1_download_single_video():
    """示例1：下载单个视频（视频+字幕）"""
    print("=" * 60)
    print("示例1：下载单个视频")
    print("=" * 60)
    
    downloader = BiliDownloader(
        download_mode='both',  # 下载视频和字幕
        output_dir='./downloads/单个视频'
    )
    
    video_url = 'https://www.bilibili.com/video/BV1xx411c7mD'
    downloader.download_video(video_url)


def example_2_download_subtitle_only():
    """示例2：仅下载视频字幕"""
    print("=" * 60)
    print("示例2：仅下载字幕")
    print("=" * 60)
    
    downloader = BiliDownloader(
        download_mode='subtitle_only',  # 仅下载字幕
        output_dir='./downloads/字幕'
    )
    
    video_url = 'https://www.bilibili.com/video/BV1xx411c7mD'
    downloader.download_video(video_url)


def example_3_download_up_videos():
    """示例3：下载UP主的视频（限制数量）"""
    print("=" * 60)
    print("示例3：下载UP主视频")
    print("=" * 60)
    
    downloader = BiliDownloader(
        download_mode='both',
        max_count=10,  # 只下载前10个
        output_dir='./downloads/UP主名称'
    )
    
    user_space_url = 'https://space.bilibili.com/123456'
    downloader.download_user_videos(user_space_url)


def example_4_batch_download_multiple_ups():
    """示例4：批量下载多个UP主的视频"""
    print("=" * 60)
    print("示例4：批量下载多个UP主")
    print("=" * 60)
    
    # UP主列表：(URL, 输出目录名称, 最大数量)
    up_list = [
        ('https://space.bilibili.com/111', 'UP主1', 5),
        ('https://space.bilibili.com/222', 'UP主2', 10),
        ('https://space.bilibili.com/333', 'UP主3', 3),
    ]
    
    for url, name, count in up_list:
        print(f"\n正在下载：{name}")
        
        downloader = BiliDownloader(
            download_mode='both',
            max_count=count,
            output_dir=f'./downloads/{name}'
        )
        
        downloader.download_user_videos(url)
        
        print(f"{name} 下载完成！\n")


def example_5_download_with_custom_cookie():
    """示例5：使用自定义Cookie文件"""
    print("=" * 60)
    print("示例5：使用自定义Cookie")
    print("=" * 60)
    
    downloader = BiliDownloader(
        download_mode='both',
        cookie_file='./my_custom_cookies.txt',  # 自定义Cookie文件
        output_dir='./downloads/需要登录的视频'
    )
    
    video_url = 'https://www.bilibili.com/video/BV1xx411c7mD'
    downloader.download_video(video_url)


def example_6_download_to_categorized_folders():
    """示例6：按类别下载到不同文件夹"""
    print("=" * 60)
    print("示例6：分类下载")
    print("=" * 60)
    
    # 教程类视频
    tutorial_videos = [
        'https://www.bilibili.com/video/BV1xx411c7mD',
        'https://www.bilibili.com/video/BV1yy411c7mD',
    ]
    
    # 娱乐类视频
    entertainment_videos = [
        'https://www.bilibili.com/video/BV1zz411c7mD',
    ]
    
    # 下载教程视频
    print("\n下载教程类视频...")
    tutorial_downloader = BiliDownloader(
        download_mode='both',
        output_dir='./downloads/教程'
    )
    for url in tutorial_videos:
        tutorial_downloader.download_video(url)
    
    # 下载娱乐视频（只要字幕）
    print("\n下载娱乐类视频字幕...")
    entertainment_downloader = BiliDownloader(
        download_mode='subtitle_only',
        output_dir='./downloads/娱乐'
    )
    for url in entertainment_videos:
        entertainment_downloader.download_video(url)


def example_7_smart_download():
    """示例7：智能下载（自动识别URL类型）"""
    print("=" * 60)
    print("示例7：智能下载")
    print("=" * 60)
    
    downloader = BiliDownloader(
        download_mode='both',
        max_count=5
    )
    
    # 可以是视频URL或UP主URL，downloader会自动识别
    urls = [
        'https://www.bilibili.com/video/BV1xx411c7mD',  # 单个视频
        'https://space.bilibili.com/123456',  # UP主主页
    ]
    
    for url in urls:
        downloader.download_from_url(url)


if __name__ == '__main__':
    # 取消注释来运行相应的示例
    
    # example_1_download_single_video()
    # example_2_download_subtitle_only()
    # example_3_download_up_videos()
    # example_4_batch_download_multiple_ups()
    # example_5_download_with_custom_cookie()
    # example_6_download_to_categorized_folders()
    # example_7_smart_download()
    
    print("请取消注释要运行的示例函数")

