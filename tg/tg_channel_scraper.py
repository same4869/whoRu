"""
Telegram频道爬虫 - 使用Telethon库
需要Telegram API credentials (api_id 和 api_hash)
"""
import os
import json
from datetime import datetime
from telethon import TelegramClient
from telethon.tl.functions.messages import GetHistoryRequest
from telethon.errors import SessionPasswordNeededError
import asyncio
import sys
import io

# 修复Windows中文编码问题
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

class TelegramChannelScraper:
    def __init__(self, api_id, api_hash, phone_number):
        """
        初始化Telegram客户端
        
        参数:
            api_id: Telegram API ID
            api_hash: Telegram API Hash
            phone_number: 您的手机号码（国际格式，如 +86xxxxxxxxxx）
        """
        self.api_id = api_id
        self.api_hash = api_hash
        self.phone_number = phone_number
        self.client = TelegramClient('session_name', api_id, api_hash)
        
    async def start_client(self):
        """启动Telegram客户端并登录"""
        await self.client.start(phone=self.phone_number)
        print("✅ 成功连接到Telegram")
        
    async def scrape_channel(self, channel_username, limit=None, output_dir='tg/output'):
        """
        爬取指定频道的所有消息
        
        参数:
            channel_username: 频道用户名（如 'jmhbzsk' 或 'https://t.me/jmhbzsk'）
            limit: 爬取消息数量限制，None表示爬取全部
            output_dir: 输出目录
        """
        # 清理频道名称
        if 'https://t.me/' in channel_username:
            channel_username = channel_username.split('/')[-1]
        if channel_username.startswith('@'):
            channel_username = channel_username[1:]
            
        print(f"📡 开始爬取频道: @{channel_username}")
        
        try:
            # 获取频道实体
            channel = await self.client.get_entity(channel_username)
            print(f"📌 频道名称: {channel.title}")
            
            # 创建输出目录
            os.makedirs(output_dir, exist_ok=True)
            
            messages_data = []
            message_count = 0
            
            # 获取消息历史
            async for message in self.client.iter_messages(channel, limit=limit):
                if message.text:  # 只处理文本消息
                    message_count += 1
                    
                    msg_data = {
                        'id': message.id,
                        'date': message.date.strftime('%Y-%m-%d %H:%M:%S'),
                        'text': message.text,
                        'views': message.views,
                        'forwards': message.forwards,
                        'replies': message.replies.replies if message.replies else 0,
                    }
                    
                    messages_data.append(msg_data)
                    
                    if message_count % 100 == 0:
                        print(f"⏳ 已爬取 {message_count} 条消息...")
            
            print(f"✅ 共爬取 {message_count} 条文本消息")
            
            # 保存为JSON
            json_file = os.path.join(output_dir, f'{channel_username}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(messages_data, f, ensure_ascii=False, indent=2)
            print(f"💾 JSON文件已保存: {json_file}")
            
            # 保存为Markdown
            md_file = os.path.join(output_dir, f'{channel_username}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.md')
            with open(md_file, 'w', encoding='utf-8') as f:
                f.write(f"# {channel.title}\n\n")
                f.write(f"**频道**: @{channel_username}\n\n")
                f.write(f"**爬取时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                f.write(f"**消息总数**: {message_count}\n\n")
                f.write("---\n\n")
                
                for msg in reversed(messages_data):  # 按时间正序排列
                    f.write(f"## 消息 #{msg['id']}\n\n")
                    f.write(f"**时间**: {msg['date']}\n\n")
                    f.write(f"**浏览量**: {msg['views']} | **转发**: {msg['forwards']} | **回复**: {msg['replies']}\n\n")
                    f.write(f"{msg['text']}\n\n")
                    f.write("---\n\n")
            
            print(f"💾 Markdown文件已保存: {md_file}")
            
            return messages_data
            
        except Exception as e:
            print(f"❌ 错误: {str(e)}")
            return None
    
    async def scrape_multiple_channels(self, channel_list, limit=None, output_dir='tg/output'):
        """
        批量爬取多个频道
        
        参数:
            channel_list: 频道列表
            limit: 每个频道爬取消息数量限制
            output_dir: 输出目录
        """
        for channel in channel_list:
            print(f"\n{'='*50}")
            await self.scrape_channel(channel, limit, output_dir)
            await asyncio.sleep(2)  # 避免请求过快
    
    async def close(self):
        """关闭客户端连接"""
        await self.client.disconnect()
        print("👋 已断开连接")


async def main():
    """主函数示例"""
    # ⚠️ 请在config.py中配置您的API credentials
    from config import API_ID, API_HASH, PHONE_NUMBER
    
    # 创建爬虫实例
    scraper = TelegramChannelScraper(API_ID, API_HASH, PHONE_NUMBER)
    
    try:
        # 启动客户端
        await scraper.start_client()
        
        # 爬取单个频道
        # await scraper.scrape_channel('jmhbzsk', limit=None, output_dir='tg/output')
        
        # 或者批量爬取多个频道
        channels = [
            'jmhbzsk',  # 加密货币知识库
            # 可以添加更多频道
        ]
        await scraper.scrape_multiple_channels(channels, output_dir='tg/output')
        
    finally:
        # 关闭连接
        await scraper.close()


if __name__ == '__main__':
    asyncio.run(main())

