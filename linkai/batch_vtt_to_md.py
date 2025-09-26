#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VTT到Markdown的批量处理器
支持指定处理数量：0表示全部处理，其他数字表示处理前N个文件

使用方法：
python batch_vtt_to_md.py 5    # 处理前5个文件
python batch_vtt_to_md.py 0    # 处理所有文件
python batch_vtt_to_md.py      # 默认处理所有文件
"""

import os
import sys
import glob
import requests
import json
import time
import re
from pathlib import Path
from datetime import datetime
import argparse

# 添加父目录到路径，以便导入原有的解析函数
sys.path.append(str(Path(__file__).parent.parent))
from call_ai_translate_vtt_to_md import parse_vtt_file

# LinkAI API 配置
API_KEY = "Link_vMAvrW4rezbFYKimorUYy7rJeFOjh3mDNBQu8QrFRm"
BASE_URL = "https://api.link-ai.tech/v1"
CHAT_URL = f"{BASE_URL}/chat/completions"

# 文件路径配置
VTT_FOLDER = r'D:\xwang\git_work_wx\whoRu\output_result'
MD_FOLDER = r'D:\xwang\git_work_wx\whoRu\output_result_md_linkai'

# 处理配置
BATCH_SIZE = 5  # 每批处理的文件数量
DELAY_BETWEEN_REQUESTS = 1  # 请求间隔（秒）
BATCH_DELAY = 3  # 批次间隔（秒）

# 系统提示词
SYSTEM_PROMPT = """你是一位专业的内容编辑和翻译专家。请将用户提供的繁体中文视频字幕转换为流畅、自然的简体中文文章。

请严格遵守以下要求：
1. **完整转换**：将所有繁体中文转换为简体中文，不遗漏任何内容
2. **智能分段**：将口语化的短句合并成自然的段落，改善可读性
3. **保持原意**：保持原始内容的完整性和准确性，不添加或删除信息
4. **格式优化**：
   - 使用合适的标题和段落结构
   - 添加必要的标点符号
   - 去除口语化的冗余词汇（如"这个"、"那个"等过度使用）
5. **内容结构**：
   - 开头部分：欢迎语和节目介绍
   - 主要内容：按逻辑分段组织
   - 结尾部分：总结和互动提醒

直接输出整理后的文章内容，不要添加任何解释或标记。"""

def call_linkai_api(messages):
    """调用LinkAI API"""
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }
    
    body = {
        "messages": messages,
        "stream": False,
        "temperature": 0.3
    }
    
    try:
        response = requests.post(CHAT_URL, json=body, headers=headers, timeout=60)
        
        if response.status_code == 200:
            result = response.json()
            if 'choices' in result and len(result['choices']) > 0:
                return result['choices'][0]['message']['content']
            else:
                print(f"API响应格式异常: {result}")
                return None
        else:
            print(f"API调用失败: {response.status_code}")
            print(f"错误信息: {response.text}")
            return None
            
    except Exception as e:
        print(f"API调用异常: {e}")
        return None

def process_text_with_ai(text, title, publish_date):
    """使用AI处理文本，转换为高质量的简体中文文章"""
    user_prompt = f"""请将以下视频字幕内容转换为高质量的简体中文文章：

标题：{title}
发布时间：{publish_date}

字幕内容：
{text}

请按照要求输出整理后的文章内容。"""

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt}
    ]
    
    return call_linkai_api(messages)

def extract_key_topics(title, content):
    """提取关键主题"""
    topics = []
    
    # 加密货币相关
    crypto_keywords = {
        '比特币': ['比特币', 'BTC', 'Bitcoin'],
        '以太坊': ['以太坊', '以太币', 'ETH', 'Ethereum'], 
        '爱达币': ['爱达币', '愛達币', 'ADA', 'Cardano'],
        '狗狗币': ['狗狗币', 'DOGE', 'Dogecoin'],
        'XRP': ['XRP', 'Ripple'],
        'Solana': ['Solana', 'SOL']
    }
    
    for topic, keywords in crypto_keywords.items():
        if any(keyword.lower() in title.lower() or keyword.lower() in content.lower() 
               for keyword in keywords):
            topics.append(topic)
    
    # 投资相关
    investment_keywords = ['投资', '买入', '卖出', '持有', 'DCA', '定投', '策略']
    if any(keyword in content for keyword in investment_keywords):
        topics.append('投资策略')
    
    # 市场分析
    market_keywords = ['牛市', '熊市', '行情', '走势', '分析', '预测', '市场']
    if any(keyword in content for keyword in market_keywords):
        topics.append('市场分析')
    
    return topics if topics else ['加密货币']

def process_single_vtt_file(vtt_file_path):
    """处理单个VTT文件"""
    try:
        filename = os.path.basename(vtt_file_path)
        print(f"📝 处理: {filename}")
        
        # 解析VTT文件
        result = parse_vtt_file(vtt_file_path)
        if not result or not result[0]:
            print(f"  ❌ VTT解析失败")
            return False
        
        text, timestamp_info = result
        
        # 获取基本信息
        title = timestamp_info.get('title', '未知标题') if timestamp_info else os.path.splitext(filename)[0]
        publish_date = timestamp_info.get('publish_date', '未知日期') if timestamp_info else '未知日期'
        
        # 使用AI处理内容
        processed_content = process_text_with_ai(text, title, publish_date)
        
        if not processed_content:
            print(f"  ❌ AI处理失败")
            return False
        
        # 提取主题
        topics = extract_key_topics(title, processed_content)
        
        # 生成最终的MD内容
        md_content = f"""---
title: {title}
publish_date: {publish_date}
topics: {', '.join(topics)}
word_count: {len(processed_content)}
processed_by: LinkAI
processed_at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
---

# {title}

**发布时间**: {publish_date}  
**主要话题**: {', '.join(topics)}

---

{processed_content}

---

*本文由LinkAI智能助手整理发布，内容仅供参考*
"""
        
        # 保存MD文件
        md_filename = f"{os.path.splitext(filename)[0]}.md"
        md_file_path = os.path.join(MD_FOLDER, md_filename)
        
        with open(md_file_path, 'w', encoding='utf-8') as f:
            f.write(md_content)
        
        print(f"  ✅ 完成: {len(processed_content)}字符")
        return True
        
    except Exception as e:
        print(f"  ❌ 处理出错: {e}")
        return False

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='VTT到Markdown批量处理器')
    parser.add_argument('count', type=int, nargs='?', default=0, 
                       help='处理文件数量：0表示全部，其他数字表示前N个文件')
    
    args = parser.parse_args()
    process_count = args.count
    
    start_time = datetime.now()
    print("=== VTT到Markdown批量处理器 ===")
    print(f"开始时间: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"输入目录: {VTT_FOLDER}")
    print(f"输出目录: {MD_FOLDER}")
    
    # 确保输出目录存在
    os.makedirs(MD_FOLDER, exist_ok=True)
    
    # 获取所有VTT文件
    vtt_files = glob.glob(os.path.join(VTT_FOLDER, "*.vtt"))
    print(f"找到 {len(vtt_files)} 个VTT文件")
    
    # 检查已处理的文件
    existing_md_files = set()
    if os.path.exists(MD_FOLDER):
        existing_md_files = set(os.path.splitext(f)[0] for f in os.listdir(MD_FOLDER) if f.endswith('.md'))
    
    # 过滤出未处理的文件
    unprocessed_files = []
    for vtt_file in vtt_files:
        base_name = os.path.splitext(os.path.basename(vtt_file))[0]
        if base_name not in existing_md_files:
            unprocessed_files.append(vtt_file)
    
    print(f"需要处理 {len(unprocessed_files)} 个新文件")
    
    if not unprocessed_files:
        print("✅ 所有文件都已处理完成！")
        return
    
    # 根据参数确定处理的文件
    if process_count == 0:
        files_to_process = unprocessed_files
        print(f"🚀 全量处理模式：处理所有 {len(files_to_process)} 个文件")
    else:
        files_to_process = unprocessed_files[:process_count]
        print(f"🎯 限量处理模式：处理前 {len(files_to_process)} 个文件")
    
    # 预估时间
    estimated_time = len(files_to_process) * 20 / 60
    print(f"预估处理时间：约 {estimated_time:.1f} 分钟")
    print(f"API调用次数：{len(files_to_process)} 次")
    
    # 开始处理
    print(f"\n🚀 开始处理...")
    
    success_count = 0
    total_files = len(files_to_process)
    
    for i in range(0, total_files, BATCH_SIZE):
        batch_files = files_to_process[i:i+BATCH_SIZE]
        batch_num = i // BATCH_SIZE + 1
        total_batches = (total_files + BATCH_SIZE - 1) // BATCH_SIZE
        
        print(f"\n🔄 批次 {batch_num}/{total_batches} (文件 {i+1}-{min(i+BATCH_SIZE, total_files)})")
        
        for j, vtt_file in enumerate(batch_files):
            if process_single_vtt_file(vtt_file):
                success_count += 1
            
            # 请求间隔
            if j < len(batch_files) - 1:
                time.sleep(DELAY_BETWEEN_REQUESTS)
        
        # 显示进度
        progress = (i + len(batch_files)) / total_files * 100
        elapsed_time = (datetime.now() - start_time).total_seconds() / 60
        print(f"  📊 进度: {progress:.1f}% ({i + len(batch_files)}/{total_files}) | 用时: {elapsed_time:.1f}分钟")
        
        # 批次间隔
        if i + BATCH_SIZE < total_files:
            print(f"  💤 休息 {BATCH_DELAY} 秒...")
            time.sleep(BATCH_DELAY)
    
    end_time = datetime.now()
    total_time = (end_time - start_time).total_seconds() / 60
    
    print(f"\n=== 处理完成 ===")
    print(f"✅ 成功处理: {success_count} 个文件")
    print(f"❌ 处理失败: {total_files - success_count} 个文件")
    print(f"⏱️ 总用时: {total_time:.1f} 分钟")
    print(f"📁 输出目录: {MD_FOLDER}")
    print(f"结束时间: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()
