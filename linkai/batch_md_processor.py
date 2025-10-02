#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
微信文章Markdown批量处理器
对已爬取的微信公众号文章进行内容优化和格式整理

功能特点：
- 批量处理指定文件夹中的Markdown文件
- 使用LinkAI API进行内容优化和格式整理
- 智能API密钥管理：自动从api_keys.txt读取密钥，积分不足时自动切换
- 支持断点续传，避免重复处理
- 可控制处理范围（起始序号到结束序号）
- 智能重试机制处理API异常
- 详细的处理统计和进度报告

使用方法：
python batch_md_processor.py wechat_huibenmamahaitong           # 处理所有文章
python batch_md_processor.py wechat_huibenmamahaitong --start 10 --end 50    # 处理第10-50篇
python batch_md_processor.py wechat_huibenmamahaitong --count 20              # 处理前20篇
python batch_md_processor.py wechat_huibenmamahaitong --skip-existing         # 跳过已处理的文件

输出结构：
- 输入：wechat_huibenmamahaitong/001_2015-06-01_文章标题.md
- 输出：wechat_huibenmamahaitong_result/001_2015-06-01_文章标题.md
"""

import os
import sys
import glob
import re
import argparse
import time
from pathlib import Path
from datetime import datetime
import logging

# 导入API相关模块
sys.path.append(str(Path(__file__).parent))
from batch_vtt_to_md import (
    load_api_keys, get_next_api_key, switch_to_next_api_key, 
    call_linkai_api, current_api_key
)

# 配置参数
DEFAULT_MAX_BATCH = 10000
DEFAULT_DELAY = (3, 8)  # 请求间隔范围（秒）
MAX_RETRIES = 3

# 处理提示词
PROCESSING_PROMPT = """你是一位专业的内容编辑和育儿专家。请将用户提供的文章转换为流畅、自然的简体中文文章。

请严格遵守以下要求：
1. **完整转换**：将所有内容进行转换，不遗漏主要内容，尽可能保留源文档所有内容信息
2. **隐私去除**：强化育儿相关的通用干货和知识，弱化涉及到个人生活隐私的详细描述
3. **智能分段**：将口语化的短句合并成自然的段落，改善可读性
4. **保持原意**：保持原始内容的完整性和准确性，不添加或删除信息
5. **格式优化**：
   - 使用合适的标题和段落结构
   - 添加必要的标点符号
   - 去除口语化的冗余词汇（如"这个"、"那个"等过度使用）
6. **内容结构**：
   - 开头部分：引言或导入部分
   - 主要内容：按逻辑分段组织，保持内容的连贯性
   - 结尾部分：总结或结论

直接输出整理后的文章内容，不要添加任何解释或标记。"""

class MarkdownProcessor:
    def __init__(self, input_folder, output_folder=None, delay_range=DEFAULT_DELAY):
        """
        初始化Markdown处理器
        
        Args:
            input_folder: 输入文件夹路径
            output_folder: 输出文件夹路径（可选）
            delay_range: 请求间隔范围（秒）
        """
        self.input_folder = input_folder
        self.output_folder = output_folder or f"{input_folder}_result"
        self.delay_range = delay_range
        
        # 统计信息
        self.stats = {
            'total_processed': 0,
            'success_count': 0,
            'failed_count': 0,
            'skipped_count': 0,
            'start_time': None
        }
        
        # 设置日志
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        print(f"📁 输入目录: {self.input_folder}")
        print(f"📁 输出目录: {self.output_folder}")
    
    def get_md_files(self):
        """获取所有Markdown文件"""
        pattern = os.path.join(self.input_folder, "*.md")
        md_files = glob.glob(pattern)
        md_files.sort()  # 按文件名排序
        return md_files
    
    def extract_file_number(self, filename):
        """从文件名中提取序号"""
        basename = os.path.basename(filename)
        match = re.match(r'^(\d+)_', basename)
        return int(match.group(1)) if match else 0
    
    def read_md_content(self, file_path):
        """读取Markdown文件内容"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return content
        except Exception as e:
            self.logger.error(f"读取文件失败 {file_path}: {e}")
            return None
    
    def extract_article_content(self, md_content):
        """从Markdown内容中提取正文"""
        try:
            # 分割内容
            sections = md_content.split('\n## ')
            
            # 提取标题
            title_match = re.match(r'^# (.+)', md_content)
            title = title_match.group(1) if title_match else "未知标题"
            
            # 提取正文内容
            article_content = ""
            for section in sections:
                if section.startswith('正文内容'):
                    # 移除"正文内容"标题和后续的分隔线
                    content_lines = section.split('\n')[1:]  # 跳过标题行
                    content_lines = [line for line in content_lines if not line.startswith('---')]
                    article_content = '\n'.join(content_lines).strip()
                    break
            
            if not article_content:
                # 如果没找到正文内容部分，使用整个内容
                article_content = md_content
            
            return title, article_content
            
        except Exception as e:
            self.logger.error(f"解析Markdown内容失败: {e}")
            return "未知标题", md_content
    
    def process_content_with_ai(self, title, content):
        """使用AI处理文章内容"""
        try:
            # 构建消息
            user_content = f"标题：{title}\n\n内容：\n{content}"
            
            messages = [
                {"role": "system", "content": PROCESSING_PROMPT},
                {"role": "user", "content": user_content}
            ]
            
            # 调用API
            result = call_linkai_api(messages)
            return result
            
        except Exception as e:
            self.logger.error(f"AI处理失败: {e}")
            return None
    
    def create_processed_md(self, original_md, title, processed_content):
        """创建处理后的Markdown文件"""
        try:
            # 提取原始文件的元信息
            sections = original_md.split('\n## ')
            
            # 构建新的Markdown内容
            new_md = f"# {title}\n\n"
            
            # 添加文章信息部分（如果存在）
            for section in sections:
                if section.startswith('文章信息'):
                    new_md += f"## {section}\n\n"
                    break
            
            # 添加处理后的内容
            new_md += f"## 正文内容\n\n{processed_content}\n\n"
            new_md += "---\n*本文档已通过AI优化处理*\n"
            
            return new_md
            
        except Exception as e:
            self.logger.error(f"创建处理后的Markdown失败: {e}")
            return f"# {title}\n\n{processed_content}"
    
    def save_processed_file(self, output_path, content):
        """保存处理后的文件"""
        try:
            # 确保输出目录存在
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
            
        except Exception as e:
            self.logger.error(f"保存文件失败 {output_path}: {e}")
            return False
    
    def process_single_file(self, file_path):
        """处理单个文件"""
        try:
            filename = os.path.basename(file_path)
            file_number = self.extract_file_number(filename)
            output_path = os.path.join(self.output_folder, filename)
            
            print(f"\n📄 处理第 {file_number} 篇: {filename[:50]}...")
            
            # 检查文件是否已存在（断点续传）
            if os.path.exists(output_path):
                print(f"    ✅ 文件已存在，跳过: {filename}")
                return 'skipped'
            
            # 读取原始内容
            original_content = self.read_md_content(file_path)
            if not original_content:
                print(f"    ❌ 读取文件失败")
                return 'failed'
            
            # 提取文章内容
            title, article_content = self.extract_article_content(original_content)
            
            if not article_content.strip():
                print(f"    ⚠️  文章内容为空，跳过处理")
                return 'skipped'
            
            # 使用AI处理内容（带重试）
            processed_content = None
            for attempt in range(MAX_RETRIES):
                try:
                    print(f"    🤖 AI处理中...")
                    processed_content = self.process_content_with_ai(title, article_content)
                    if processed_content:
                        break
                    elif attempt < MAX_RETRIES - 1:
                        print(f"    🔄 第 {attempt + 1} 次重试...")
                        time.sleep(3)
                except Exception as e:
                    if attempt < MAX_RETRIES - 1:
                        print(f"    🔄 重试中... ({attempt + 1}/{MAX_RETRIES}): {e}")
                        time.sleep(3)
                    else:
                        print(f"    ❌ 重试失败: {e}")
            
            if not processed_content:
                print(f"    ❌ AI处理失败")
                return 'failed'
            
            # 创建新的Markdown内容
            new_md_content = self.create_processed_md(original_content, title, processed_content)
            
            # 保存文件
            if self.save_processed_file(output_path, new_md_content):
                print(f"    ✅ 处理完成: {filename}")
                return 'success'
            else:
                print(f"    ❌ 保存失败")
                return 'failed'
                
        except Exception as e:
            print(f"    ❌ 处理异常: {e}")
            return 'failed'
    
    def get_random_delay(self):
        """获取随机延时"""
        import random
        return random.uniform(self.delay_range[0], self.delay_range[1])
    
    def process_files(self, start_num=None, end_num=None, count=None, skip_existing=True):
        """批量处理文件"""
        # 获取所有MD文件
        md_files = self.get_md_files()
        if not md_files:
            print(f"❌ 在目录 {self.input_folder} 中未找到Markdown文件")
            return False
        
        print(f"📊 找到 {len(md_files)} 个Markdown文件")
        
        # 过滤文件
        filtered_files = []
        for file_path in md_files:
            file_number = self.extract_file_number(file_path)
            
            # 按序号范围过滤
            if start_num is not None and file_number < start_num:
                continue
            if end_num is not None and file_number > end_num:
                continue
                
            filtered_files.append(file_path)
        
        # 按数量限制
        if count is not None:
            filtered_files = filtered_files[:count]
        
        if not filtered_files:
            print(f"❌ 没有符合条件的文件")
            return False
        
        # 显示处理计划
        start_file = self.extract_file_number(filtered_files[0])
        end_file = self.extract_file_number(filtered_files[-1])
        
        print(f"\n📋 处理计划:")
        print(f"   总文件数: {len(md_files)}")
        print(f"   处理范围: 第 {start_file} - {end_file} 篇")
        print(f"   处理数量: {len(filtered_files)} 个文件")
        print(f"   输出目录: {self.output_folder}")
        
        # 开始处理
        self.stats['start_time'] = datetime.now()
        
        for i, file_path in enumerate(filtered_files):
            result = self.process_single_file(file_path)
            
            # 更新统计
            self.stats['total_processed'] += 1
            if result == 'success':
                self.stats['success_count'] += 1
            elif result == 'failed':
                self.stats['failed_count'] += 1
            elif result == 'skipped':
                self.stats['skipped_count'] += 1
            
            # 延时避免频繁请求
            if i < len(filtered_files) - 1:  # 最后一个不需要延时
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
        print(f"📈 总处理: {self.stats['total_processed']} 个文件")
        print(f"✅ 成功: {self.stats['success_count']} 个")
        print(f"⏭️  跳过: {self.stats['skipped_count']} 个")
        print(f"❌ 失败: {self.stats['failed_count']} 个")
        print(f"📁 输出目录: {self.output_folder}")
        print(f"=" * 50)

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='微信文章Markdown批量处理器')
    parser.add_argument('input_folder', help='输入文件夹路径')
    parser.add_argument('--output', help='输出文件夹路径（默认：输入文件夹_result）')
    parser.add_argument('--start', type=int, help='起始序号')
    parser.add_argument('--end', type=int, help='结束序号')
    parser.add_argument('--count', type=int, help='处理文件数量')
    parser.add_argument('--delay', type=str, default='3,8', 
                       help='请求延时范围（秒），格式: min,max（默认: 3,8）')
    parser.add_argument('--skip-existing', action='store_true', 
                       help='跳过已存在的文件（默认开启）')
    
    args = parser.parse_args()
    
    # 检查输入文件夹是否存在
    if not os.path.exists(args.input_folder):
        print(f"❌ 输入文件夹不存在: {args.input_folder}")
        sys.exit(1)
    
    # 解析延时参数
    try:
        delay_min, delay_max = map(float, args.delay.split(','))
        delay_range = (delay_min, delay_max)
    except:
        delay_range = DEFAULT_DELAY
        print(f"⚠️  延时参数格式错误，使用默认值: {DEFAULT_DELAY}")
    
    # 初始化API密钥
    global current_api_key
    current_api_key = get_next_api_key()
    if not current_api_key:
        print("❌ 错误：没有可用的API密钥，请检查 api_keys.txt 文件")
        sys.exit(1)
    
    # 创建处理器实例
    processor = MarkdownProcessor(
        input_folder=args.input_folder,
        output_folder=args.output,
        delay_range=delay_range
    )
    
    # 开始处理
    try:
        success = processor.process_files(
            start_num=args.start,
            end_num=args.end,
            count=args.count,
            skip_existing=args.skip_existing
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
