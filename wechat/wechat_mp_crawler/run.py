"""
微信公众号文章爬取工具 - 简化版
"""

from mp_client import WeChatMPClient
from config import get_config
import sys


def main():
    config = get_config()
    
    # 检查命令行参数
    test_mode = False
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        test_mode = True
    
    print("=" * 50)
    print("微信公众号文章爬取工具")
    print("=" * 50)
    print(f"延时范围: {config['rate_limit_delay'][0]}-{config['rate_limit_delay'][1]}秒")
    if test_mode:
        print("模式: 测试模式 (2次请求)")
    else:
        print("模式: 获取所有文章")
    print("=" * 50)
    
    # 创建客户端并开始爬取
    client = WeChatMPClient(
        cookie=config['cookie'],
        rate_limit_delay=config['rate_limit_delay']
    )
    
    try:
        max_requests = 2 if test_mode else None
        output_file = "test_articles.csv" if test_mode else "wechat_articles.csv"
        
        total_count = client.crawl_and_save(
            url=config['url'],
            output_file=output_file,
            max_requests=max_requests
        )
        
        print(f"\n✅ 爬取完成！获取 {total_count} 篇文章，保存到 {output_file}")
        
    except KeyboardInterrupt:
        print("\n❌ 用户中断")
    except Exception as e:
        print(f"\n❌ 错误: {e}")


if __name__ == "__main__":
    main()
