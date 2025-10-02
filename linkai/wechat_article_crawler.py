#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
微信公众号文章批量爬取器
从Excel文件中读取文章链接，批量获取文章内容并保存为Markdown格式

功能特点：
- 从Excel文件读取文章链接、标题、摘要、发布时间
- 批量获取微信公众号文章内容
- 自动生成有序的Markdown文件（序号+时间+标题）
- 支持断点续传，避免重复处理
- 可控制每次处理的最大行数
- 智能重试机制处理网络异常

使用方法：
python wechat_article_crawler.py filename.xlsx           # 处理所有文章
python wechat_article_crawler.py filename.xlsx --start 10 --count 20  # 从第10行开始，处理20篇文章
python wechat_article_crawler.py filename.xlsx --max-batch 50         # 每次最多处理50篇

文件结构：
- 输入：wechat/data_setup/filename.xlsx
- 输出：wechat_filename/001_2024-01-01_文章标题.md
"""

import os
import sys
import pandas as pd
import requests
import time
import re
import argparse
from pathlib import Path
from datetime import datetime
from urllib.parse import urlparse
import html
from bs4 import BeautifulSoup

# 添加父目录到路径
sys.path.append(str(Path(__file__).parent.parent))

# 配置参数
EXCEL_FOLDER = r'../wechat/data_setup'
OUTPUT_BASE_FOLDER = r'.'
DEFAULT_MAX_BATCH = 10000
DEFAULT_DELAY = (2, 5)  # 请求间隔范围（秒）
DEFAULT_TIMEOUT = 30
MAX_RETRIES = 3

# 请求头配置
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'Accept-Encoding': 'gzip, deflate',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
}

class WeChatArticleCrawler:
    def __init__(self, excel_filename, output_folder=None, delay_range=DEFAULT_DELAY):
        """
        初始化微信文章爬虫
        
        Args:
            excel_filename: Excel文件名（不含路径）
            output_folder: 输出文件夹名（可选）
            delay_range: 请求间隔范围（秒）
        """
        self.excel_filename = excel_filename
        self.excel_path = os.path.join(EXCEL_FOLDER, excel_filename)
        
        # 设置输出文件夹
        if output_folder:
            self.output_folder = output_folder
        else:
            # 从Excel文件名生成输出文件夹名
            name_without_ext = os.path.splitext(excel_filename)[0]
            self.output_folder = f"wechat_{name_without_ext}"
        
        self.output_path = os.path.join(OUTPUT_BASE_FOLDER, self.output_folder)
        self.delay_range = delay_range
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        
        # 统计信息
        self.stats = {
            'total_processed': 0,
            'success_count': 0,
            'failed_count': 0,
            'skipped_count': 0,
            'start_time': None
        }
        
        print(f"📁 Excel文件: {self.excel_path}")
        print(f"📁 输出目录: {self.output_path}")
    
    def load_excel_data(self):
        """加载Excel数据"""
        try:
            if not os.path.exists(self.excel_path):
                raise FileNotFoundError(f"Excel文件不存在: {self.excel_path}")
            
            # 读取Excel文件
            df = pd.read_excel(self.excel_path)
            print(f"📊 加载Excel数据成功，共 {len(df)} 行记录")
            
            # 检查必要的列
            required_columns = ['链接', '标题', '摘要', '发布时间']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                print(f"⚠️  缺少必要的列: {missing_columns}")
                print(f"📋 可用的列: {list(df.columns)}")
                # 如果缺少列，尝试使用相似的列名
                if '发布时间' not in df.columns and '创建时间' in df.columns:
                    print("⚠️  使用'创建时间'替代'发布时间'")
                    df['发布时间'] = df['创建时间']
            
            return df
            
        except Exception as e:
            print(f"❌ 加载Excel文件失败: {e}")
            return None
    
    def sanitize_filename(self, filename):
        """清理文件名，移除不合法字符"""
        # 移除或替换不合法字符
        filename = re.sub(r'[<>:"/\\|?*]', '', filename)
        filename = filename.replace('\n', ' ').replace('\r', ' ')
        # 限制文件名长度
        if len(filename) > 100:
            filename = filename[:97] + '...'
        return filename.strip()
    
    def format_date(self, date_str):
        """格式化日期字符串"""
        try:
            if pd.isna(date_str):
                return "未知日期"
            
            # 尝试解析不同的日期格式
            if isinstance(date_str, str):
                # 移除可能的时间部分，只保留日期
                date_str = re.sub(r'\s+\d{2}:\d{2}:\d{2}', '', date_str)
                date_str = date_str.strip()
                
                # 尝试解析
                try:
                    dt = pd.to_datetime(date_str)
                    return dt.strftime('%Y-%m-%d')
                except:
                    return date_str[:10] if len(date_str) >= 10 else date_str
            elif isinstance(date_str, datetime):
                return date_str.strftime('%Y-%m-%d')
            else:
                return str(date_str)
        except:
            return "未知日期"
    
    def generate_filename(self, index, title, publish_time):
        """生成文件名"""
        # 格式化序号（3位数字）
        serial = f"{index:03d}"
        
        # 格式化日期
        formatted_date = self.format_date(publish_time)
        
        # 清理标题
        clean_title = self.sanitize_filename(title)
        
        # 生成文件名
        filename = f"{serial}_{formatted_date}_{clean_title}.md"
        return filename
    
    def extract_article_content(self, url):
        """提取文章内容"""
        try:
            print(f"    📖 获取文章内容...")
            
            response = self.session.get(url, timeout=DEFAULT_TIMEOUT)
            response.raise_for_status()
            response.encoding = 'utf-8'
            
            # 使用BeautifulSoup解析HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 查找文章内容区域
            content_area = soup.find('div', {'class': 'rich_media_content'})
            if not content_area:
                # 尝试其他可能的选择器
                content_area = soup.find('div', {'id': 'js_content'})
            
            if content_area:
                # 提取文本内容
                content = content_area.get_text(separator='\n', strip=True)
                # 清理多余的空行
                content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)
                return content.strip()
            else:
                print(f"    ⚠️  未找到文章内容区域")
                return None
                
        except requests.RequestException as e:
            print(f"    ❌ 网络请求失败: {e}")
            return None
        except Exception as e:
            print(f"    ❌ 解析文章内容失败: {e}")
            return None
    
    def create_markdown_content(self, title, summary, publish_time, url, content):
        """创建Markdown内容"""
        md_content = f"""# {title}

## 文章信息
- **发布时间**: {self.format_date(publish_time)}
- **原文链接**: {url}

## 摘要
{summary}

## 正文内容

{content if content else '获取文章内容失败'}

---
*本文档由自动化工具生成*
"""
        return md_content
    
    def save_article(self, filename, title, summary, publish_time, url, content):
        """保存文章为Markdown文件"""
        try:
            # 确保输出目录存在
            os.makedirs(self.output_path, exist_ok=True)
            
            # 生成文件路径
            file_path = os.path.join(self.output_path, filename)
            
            # 创建Markdown内容
            md_content = self.create_markdown_content(title, summary, publish_time, url, content)
            
            # 保存文件
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(md_content)
            
            print(f"    ✅ 已保存: {filename}")
            return True
            
        except Exception as e:
            print(f"    ❌ 保存文件失败: {e}")
            return False
    
    def process_article(self, index, row):
        """处理单篇文章"""
        try:
            url = row.get('链接', '')
            title = row.get('标题', f'文章{index}')
            summary = row.get('摘要', '暂无摘要')
            publish_time = row.get('发布时间', '')
            
            print(f"\n📄 处理第 {index} 篇文章: {title[:50]}...")
            
            # 检查URL是否有效
            if not url or pd.isna(url):
                print(f"    ⚠️  链接为空，跳过")
                return 'skipped'
            
            # 生成文件名
            filename = self.generate_filename(index, title, publish_time)
            file_path = os.path.join(self.output_path, filename)
            
            # 检查文件是否已存在（断点续传）
            if os.path.exists(file_path):
                print(f"    ✅ 文件已存在，跳过: {filename}")
                return 'skipped'
            
            # 提取文章内容（带重试）
            content = None
            for attempt in range(MAX_RETRIES):
                try:
                    content = self.extract_article_content(url)
                    if content:
                        break
                    elif attempt < MAX_RETRIES - 1:
                        print(f"    🔄 第 {attempt + 1} 次重试...")
                        time.sleep(2)
                except Exception as e:
                    if attempt < MAX_RETRIES - 1:
                        print(f"    🔄 重试中... ({attempt + 1}/{MAX_RETRIES})")
                        time.sleep(2)
                    else:
                        print(f"    ❌ 重试失败: {e}")
            
            # 保存文章
            if self.save_article(filename, title, summary, publish_time, url, content):
                return 'success'
            else:
                return 'failed'
                
        except Exception as e:
            print(f"    ❌ 处理文章失败: {e}")
            return 'failed'
    
    def get_random_delay(self):
        """获取随机延时"""
        import random
        return random.uniform(self.delay_range[0], self.delay_range[1])
    
    def process_articles(self, start_index=1, max_count=None, max_batch=DEFAULT_MAX_BATCH):
        """批量处理文章"""
        # 加载数据
        df = self.load_excel_data()
        if df is None:
            return False
        
        # 计算处理范围
        total_articles = len(df)
        if start_index > total_articles:
            print(f"❌ 起始位置 {start_index} 超出总记录数 {total_articles}")
            return False
        
        # 计算实际处理数量
        end_index = start_index + (max_count if max_count else total_articles) - 1
        end_index = min(end_index, total_articles)
        end_index = min(end_index, start_index + max_batch - 1)
        
        process_count = end_index - start_index + 1
        
        print(f"\n📋 处理计划:")
        print(f"   总记录数: {total_articles}")
        print(f"   处理范围: 第 {start_index} - {end_index} 行")
        print(f"   处理数量: {process_count} 篇文章")
        print(f"   输出目录: {self.output_path}")
        
        # 开始处理
        self.stats['start_time'] = datetime.now()
        
        for i in range(start_index - 1, end_index):  # 转换为0基索引
            row = df.iloc[i]
            result = self.process_article(i + 1, row)  # 显示为1基索引
            
            # 更新统计
            self.stats['total_processed'] += 1
            if result == 'success':
                self.stats['success_count'] += 1
            elif result == 'failed':
                self.stats['failed_count'] += 1
            elif result == 'skipped':
                self.stats['skipped_count'] += 1
            
            # 延时避免频繁请求
            if i < end_index - 1:  # 最后一个不需要延时
                delay = self.get_random_delay()
                print(f"    ⏰ 等待 {delay:.1f} 秒...")
                time.sleep(delay)
        
        # 显示统计结果
        self.print_statistics()
        return True
    
    def print_statistics(self):
        """打印统计信息"""
        end_time = datetime.now()
        elapsed_time = end_time - self.stats['start_time']
        
        print(f"\n" + "=" * 50)
        print(f"📊 处理完成统计")
        print(f"=" * 50)
        print(f"⏰ 开始时间: {self.stats['start_time'].strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"⏰ 结束时间: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"⏱️  总耗时: {elapsed_time}")
        print(f"📈 总处理: {self.stats['total_processed']} 篇")
        print(f"✅ 成功: {self.stats['success_count']} 篇")
        print(f"⏭️  跳过: {self.stats['skipped_count']} 篇")
        print(f"❌ 失败: {self.stats['failed_count']} 篇")
        print(f"📁 输出目录: {self.output_path}")
        print(f"=" * 50)

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='微信公众号文章批量爬取器')
    parser.add_argument('excel_file', help='Excel文件名（在wechat/data_setup目录下）')
    parser.add_argument('--start', type=int, default=1, help='起始行号（默认: 1）')
    parser.add_argument('--count', type=int, help='处理文章数量（默认: 全部）')
    parser.add_argument('--max-batch', type=int, default=DEFAULT_MAX_BATCH, 
                       help=f'每次最大处理数量（默认: {DEFAULT_MAX_BATCH}）')
    parser.add_argument('--output', help='自定义输出文件夹名')
    parser.add_argument('--delay', type=str, default='2,5', 
                       help='请求延时范围（秒），格式: min,max（默认: 2,5）')
    
    args = parser.parse_args()
    
    # 解析延时参数
    try:
        delay_min, delay_max = map(float, args.delay.split(','))
        delay_range = (delay_min, delay_max)
    except:
        delay_range = DEFAULT_DELAY
        print(f"⚠️  延时参数格式错误，使用默认值: {DEFAULT_DELAY}")
    
    # 创建爬虫实例
    crawler = WeChatArticleCrawler(
        excel_filename=args.excel_file,
        output_folder=args.output,
        delay_range=delay_range
    )
    
    # 开始处理
    try:
        success = crawler.process_articles(
            start_index=args.start,
            max_count=args.count,
            max_batch=args.max_batch
        )
        
        if success:
            print("\n🎉 处理完成！")
        else:
            print("\n❌ 处理失败！")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⚠️  用户中断处理")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 程序异常: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
