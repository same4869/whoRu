"""
Telegram频道网页爬虫（备用方案）
不需要API credentials，但功能有限
仅适用于公开频道
"""
import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime
import time
import sys
import io

# 修复Windows中文编码问题
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

class TelegramWebScraper:
    def __init__(self):
        self.base_url = "https://t.me/s/"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
        }
    
    def scrape_channel(self, channel_username, output_dir='tg/output'):
        """
        爬取公开频道的内容（网页版）
        
        参数:
            channel_username: 频道用户名
            output_dir: 输出目录
        """
        # 清理频道名称
        if 'https://t.me/' in channel_username:
            channel_username = channel_username.split('/')[-1]
        if channel_username.startswith('@'):
            channel_username = channel_username[1:]
        
        url = f"{self.base_url}{channel_username}"
        print(f"📡 正在访问: {url}")
        
        try:
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 获取频道标题
            channel_title_elem = soup.find('div', class_='tgme_channel_info_header_title')
            channel_title = channel_title_elem.get_text(strip=True) if channel_title_elem else channel_username
            
            print(f"📌 频道名称: {channel_title}")
            
            # 查找所有消息
            messages = soup.find_all('div', class_='tgme_widget_message_wrap')
            print(f"📊 找到 {len(messages)} 条消息（最近的消息）")
            
            messages_data = []
            
            for msg in messages:
                message_div = msg.find('div', class_='tgme_widget_message')
                if not message_div:
                    continue
                
                # 提取消息ID
                msg_link = message_div.get('data-post', '')
                msg_id = msg_link.split('/')[-1] if msg_link else ''
                
                # 提取日期时间
                time_elem = message_div.find('time')
                msg_date = time_elem.get('datetime', '') if time_elem else ''
                
                # 提取文本内容
                text_elem = message_div.find('div', class_='tgme_widget_message_text')
                msg_text = text_elem.get_text(strip=True) if text_elem else ''
                
                # 提取浏览量
                views_elem = message_div.find('span', class_='tgme_widget_message_views')
                views = views_elem.get_text(strip=True) if views_elem else '0'
                
                if msg_text:  # 只保存有文本的消息
                    messages_data.append({
                        'id': msg_id,
                        'date': msg_date,
                        'text': msg_text,
                        'views': views,
                    })
            
            # 创建输出目录
            os.makedirs(output_dir, exist_ok=True)
            
            # 保存为JSON
            json_file = os.path.join(output_dir, f'{channel_username}_web_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'channel': channel_username,
                    'title': channel_title,
                    'scrape_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'message_count': len(messages_data),
                    'messages': messages_data
                }, f, ensure_ascii=False, indent=2)
            print(f"💾 JSON文件已保存: {json_file}")
            
            # 保存为Markdown
            md_file = os.path.join(output_dir, f'{channel_username}_web_{datetime.now().strftime("%Y%m%d_%H%M%S")}.md')
            with open(md_file, 'w', encoding='utf-8') as f:
                f.write(f"# {channel_title}\n\n")
                f.write(f"**频道**: @{channel_username}\n\n")
                f.write(f"**爬取时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                f.write(f"**消息数量**: {len(messages_data)} (仅显示最近的消息)\n\n")
                f.write(f"**说明**: 此数据通过网页爬取获得，仅包含最近的公开消息。如需完整历史记录，请使用API方式。\n\n")
                f.write("---\n\n")
                
                for msg in reversed(messages_data):
                    f.write(f"## 消息 #{msg['id']}\n\n")
                    f.write(f"**时间**: {msg['date']}\n\n")
                    f.write(f"**浏览量**: {msg['views']}\n\n")
                    f.write(f"{msg['text']}\n\n")
                    f.write("---\n\n")
            
            print(f"💾 Markdown文件已保存: {md_file}")
            print(f"\n⚠️  注意: 网页爬取只能获取最近的部分消息（通常20条左右）")
            print(f"    如需完整历史记录，建议使用API方式（tg_channel_scraper.py）")
            
            return messages_data
            
        except requests.exceptions.RequestException as e:
            print(f"❌ 网络请求错误: {str(e)}")
            return None
        except Exception as e:
            print(f"❌ 解析错误: {str(e)}")
            return None
    
    def scrape_multiple_channels(self, channel_list, output_dir='tg/output'):
        """批量爬取多个频道"""
        results = {}
        for channel in channel_list:
            print(f"\n{'='*50}")
            result = self.scrape_channel(channel, output_dir)
            results[channel] = result
            time.sleep(3)  # 避免请求过快
        return results


def main():
    """主函数示例"""
    scraper = TelegramWebScraper()
    
    # 爬取单个频道
    scraper.scrape_channel('jmhbzsk', output_dir='tg/output')
    
    # 或者批量爬取
    # channels = ['jmhbzsk', 'other_channel']
    # scraper.scrape_multiple_channels(channels, output_dir='tg/output')


if __name__ == '__main__':
    main()

