#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TXT到Markdown的通用批量处理器
支持处理各种类型的文本文件，自动转换为高质量的简体中文文章

功能特点：
- 通用主题识别：支持科技、教育、生活、商业、投资理财、职场、文化、健康医疗、新闻时事等9大分类
- 智能内容分析：根据内容特征自动分类（教程指南、经验分享、评测推荐等）
- 智能API密钥管理：自动从api_keys.txt读取密钥，积分不足时自动切换
- 智能重试机制：API超时或连接失败时自动重试，406错误自动切换密钥
- 详细错误统计：记录各种错误类型和重试次数
- 增强的错误处理：区分超时、连接错误、积分不足等不同问题
- 多编码支持：自动检测UTF-8、GBK、GB2312等多种文件编码

默认路径：
- 输入目录：../output_result（与VTT处理器共用同一目录）
- 输出目录：../output_result_md_linkai

使用方法：
python batch_txt_to_md.py           # 处理output_result目录下所有TXT文件
python batch_txt_to_md.py 5         # 只处理前5个TXT文件
python batch_txt_to_md.py --input ../my_folder --output ../my_output  # 自定义目录

配置参数：
- 最大重试次数：3次
- 重试间隔：5秒
- API超时时间：120秒
- 主题标签数量：最多3个

https://docs.link-ai.tech/platform/funds/price
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

# LinkAI API 配置
BASE_URL = "https://api.link-ai.tech/v1"
CHAT_URL = f"{BASE_URL}/chat/completions"

# API密钥管理
API_KEYS_FILE = "api_keys.txt"
DEPRECATED_KEYS_FILE = "deprecated_apikeys.txt"
current_api_key = None

# 文件路径配置
TXT_FOLDER = r'../output_result'  # TXT文件输入目录（与VTT文件共用）
MD_FOLDER = r'../output_result_md_linkai'  # MD文件输出目录（与VTT处理器共用）

# 处理配置
BATCH_SIZE = 5  # 每批处理的文件数量
DELAY_BETWEEN_REQUESTS = 1  # 请求间隔（秒）
BATCH_DELAY = 3  # 批次间隔（秒）

# 重试配置
MAX_RETRIES = 3  # 最大重试次数
RETRY_DELAY = 5  # 重试间隔（秒）
API_TIMEOUT = 120  # API超时时间（秒）

# 全局统计变量
retry_stats = {
    'total_retries': 0,
    'timeout_errors': 0,
    'connection_errors': 0,
    'other_errors': 0
}

# 系统提示词
SYSTEM_PROMPT = """你是一位专业的内容编辑和公众号大V,频道名称是MoonClub。请将用户提供的文本转换为流畅、自然的简体中文文章。

以下是你的详细人设和写作风格：
写作风格
标题
*   **制造紧迫感和悬念：** 标题中大量使用**极端或情绪化的词汇**（如“终极密码！”、“最大骗局”、“彻底失败”、“颠覆认知”）来引发好奇和点击。
*   **突出痛点与承诺：** 直接指出受众关心的问题（如“死薪水30歲賺600萬”、“为什么普通人不能上杠杆交易”），并承诺提供“终极密码”、“最详细”、“从0到1教学”的解决方案。
*   **结合数字量化刺激：** 标题中植入具体的数字，如收益率（“10～15%”）、亏损金额（“欠了10w块”）或财富目标（“30岁赚600万”），增强冲击力。
排版
*   **模块化排版：** 使用**粗体小标题**对内容进行清晰划分（如“引言”、“总结”、“注意事项”等）。这使得读者可以快速定位感兴趣的内容，提高了手机上的阅读效率。
*   **教程的保姆级流程：** 详细列出具体案例和可操作方式，极大地增强了内容的实用性。
*   **重点信息加粗：** 对核心观点、关键数字或操作步骤进行**粗体强调**，方便读者快速抓取核心信息。
风格
*   **长期主义的核心思想贯穿始终：** 不断重复和强调**“长期投资、长期持有”**的理念。这为账号建立了稳定和可信赖的基调，区别于追求短期暴利的投机内容。
*   **使用圈内黑话：** 运用投资圈或网络流行词汇（如“韭菜”、“薅羊毛”）来增加亲切感和共鸣。
*   **风险与机遇并重：** 在分享高收益机会（如比特币）的同时，**强调风险警示**（如杠杆交易的血泪教训、C2C出金的黑钱风险）。这增加了内容的客观性和可信度。
引导
*   **强烈的行动呼吁（CTA）：** 结尾或文章关键处持续呼吁读者**点赞、订阅、评论**。在微信公众号中，应鼓励读者“点赞、在看、分享”和“留言交流”。
*   **引导社群互动：** 邀请读者在评论区留言、分享经验、或关注喜马拉雅，小宇宙等音频节目。


请严格遵守以下要求：
1. **合理归纳**：将所有内容进行归纳，不遗漏任何内容，字数过多可以适当总结删减，严格控制整篇文章但不能超过2500字。
2. **智能分段**：将文本合理分段，形成自然的段落结构，改善可读性
3. **保持原意**：保持原始内容的完整性和准确性，不添加或删除信息
4. **格式优化**：
   - 使用合适的标题和段落结构
   - 添加必要的标点符号
   - 去除冗余词汇和不必要的重复
5. **内容结构**：
   - 开头部分：引言或导入部分
   - 主要内容：按逻辑分段组织，保持内容的连贯性
   - 结尾部分：总结或结论
   - 不要分太多小节，3-5个为宜，不要再分子小节
   - 适当口语化，不用太官方，像个朋友聊天一样娓娓道来而不是单纯说教灌输理论

规则：输出一篇可以直接发布到微信公众号的文章，不要超过2500字，要符合公众号的风格和规则，里面不要出现欢迎收听这种明显的问题，不要添加任何解释或标记。"""

def load_api_keys():
    """加载API密钥列表"""
    try:
        with open(API_KEYS_FILE, 'r', encoding='utf-8') as f:
            keys = [line.strip() for line in f if line.strip()]
        return keys
    except FileNotFoundError:
        print(f"❌ 错误：找不到API密钥文件 {API_KEYS_FILE}")
        return []

def save_api_keys(keys):
    """保存API密钥列表"""
    with open(API_KEYS_FILE, 'w', encoding='utf-8') as f:
        for key in keys:
            f.write(key + '\n')

def move_key_to_deprecated(api_key):
    """将无积分的API密钥移动到废弃文件"""
    try:
        # 读取现有的废弃密钥
        deprecated_keys = []
        if os.path.exists(DEPRECATED_KEYS_FILE):
            with open(DEPRECATED_KEYS_FILE, 'r', encoding='utf-8') as f:
                deprecated_keys = [line.strip() for line in f if line.strip()]
        
        # 添加新的废弃密钥
        if api_key not in deprecated_keys:
            deprecated_keys.append(api_key)
            with open(DEPRECATED_KEYS_FILE, 'w', encoding='utf-8') as f:
                for key in deprecated_keys:
                    f.write(key + '\n')
            print(f"🗑️  已将无积分的API密钥移动到 {DEPRECATED_KEYS_FILE}")
    except Exception as e:
        print(f"⚠️  移动废弃密钥时出错: {e}")

def get_next_api_key():
    """获取下一个可用的API密钥"""
    global current_api_key
    
    api_keys = load_api_keys()
    if not api_keys:
        print("❌ 错误：没有可用的API密钥")
        return None
    
    current_api_key = api_keys[0]
    print(f"🔑 使用API密钥: {current_api_key[:20]}...")
    return current_api_key

def switch_to_next_api_key():
    """切换到下一个API密钥"""
    global current_api_key
    
    api_keys = load_api_keys()
    if not api_keys:
        print("❌ 错误：没有可用的API密钥")
        return None
    
    if current_api_key and current_api_key in api_keys:
        # 移动当前密钥到废弃文件
        move_key_to_deprecated(current_api_key)
        
        # 从可用密钥列表中移除
        api_keys.remove(current_api_key)
        save_api_keys(api_keys)
        
        print(f"🔄 API密钥 {current_api_key[:20]}... 积分不足，切换到下一个")
    
    if api_keys:
        current_api_key = api_keys[0]
        print(f"🔑 切换到新的API密钥: {current_api_key[:20]}...")
        return current_api_key
    else:
        print("❌ 错误：所有API密钥都已用完积分")
        current_api_key = None
        return None

def call_linkai_api(messages, retry_count=0):
    """调用LinkAI API，带重试机制和自动密钥切换"""
    global current_api_key
    
    # 确保有可用的API密钥
    if not current_api_key:
        current_api_key = get_next_api_key()
        if not current_api_key:
            return None
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {current_api_key}"
    }
    
    body = {
        "messages": messages,
        "stream": False,
        "temperature": 0.3,
        "model": "LinkAI-4.1-nano"
    }
    
    for attempt in range(MAX_RETRIES):
        try:
            if attempt > 0:
                retry_stats['total_retries'] += 1
                print(f"    🔄 第 {attempt + 1} 次重试...")
                time.sleep(RETRY_DELAY)
            
            response = requests.post(CHAT_URL, json=body, headers=headers, timeout=API_TIMEOUT)
            
            if response.status_code == 200:
                result = response.json()
                if 'choices' in result and len(result['choices']) > 0:
                    if attempt > 0:
                        print(f"    ✅ 重试成功！")
                    return result['choices'][0]['message']['content']
                else:
                    print(f"    ❌ API响应格式异常: {result}")
                    if attempt == MAX_RETRIES - 1:
                        retry_stats['other_errors'] += 1
                        return None
                    continue
            elif response.status_code == 406:
                print(f"    💳 API密钥积分不足 (406错误)")
                # 切换到下一个API密钥
                new_key = switch_to_next_api_key()
                if new_key:
                    # 更新请求头中的密钥
                    headers["Authorization"] = f"Bearer {new_key}"
                    print(f"    🔄 已切换API密钥，重新尝试...")
                    continue
                else:
                    print(f"    ❌ 所有API密钥都已用完积分")
                    retry_stats['other_errors'] += 1
                    return None
            else:
                print(f"    ❌ API调用失败: {response.status_code}")
                print(f"    错误信息: {response.text}")
                if attempt == MAX_RETRIES - 1:
                    retry_stats['other_errors'] += 1
                    return None
                continue
                
        except requests.exceptions.Timeout:
            retry_stats['timeout_errors'] += 1
            print(f"    ⏰ API超时 (超过{API_TIMEOUT}秒)")
            if attempt == MAX_RETRIES - 1:
                print(f"    ❌ 已重试 {MAX_RETRIES} 次，仍然超时，跳过此文件")
                return None
            continue
        except requests.exceptions.ConnectionError:
            retry_stats['connection_errors'] += 1
            print(f"    🌐 网络连接错误")
            if attempt == MAX_RETRIES - 1:
                print(f"    ❌ 已重试 {MAX_RETRIES} 次，仍然连接失败，跳过此文件")
                return None
            continue
        except Exception as e:
            retry_stats['other_errors'] += 1
            print(f"    ❌ API调用异常: {e}")
            if attempt == MAX_RETRIES - 1:
                print(f"    ❌ 已重试 {MAX_RETRIES} 次，仍然失败，跳过此文件")
                return None
            continue
    
    return None

def extract_date_from_filename(filename):
    """从文件名中提取日期"""
    # 匹配 YYYY-MM-DD 格式
    date_match = re.search(r'(\d{4})-(\d{2})-(\d{2})', filename)
    if date_match:
        year, month, day = date_match.groups()
        return f"{year}年{month}月{day}日"
    
    # 匹配 YYYYMMDD 格式
    date_match = re.search(r'(\d{4})(\d{2})(\d{2})', filename)
    if date_match:
        year, month, day = date_match.groups()
        return f"{year}年{month}月{day}日"
    
    return datetime.now().strftime('%Y年%m月%d日')

def process_text_with_ai(text, title, publish_date):
    """使用AI处理文本，转换为高质量的简体中文文章"""
    user_prompt = f"""请将以下文本内容转换为高质量的简体中文文章：

标题：{title}
发布时间：{publish_date}

文本内容：
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
    
    # 通用主题关键词分类
    topic_categories = {
        '科技': ['科技', '技术', 'AI', '人工智能', '机器人', '自动化', '数字化', '互联网', '软件', '硬件', '编程', '开发'],
        '教育': ['教育', '学习', '培训', '课程', '教学', '知识', '技能', '学校', '大学', '考试', '学术'],
        '生活': ['生活', '日常', '家庭', '健康', '美食', '旅行', '运动', '娱乐', '时尚', '购物'],
        '商业': ['商业', '创业', '企业', '管理', '营销', '销售', '品牌', '商务', '合作', '发展'],
        '投资理财': ['投资', '理财', '金融', '股票', '基金', '保险', '银行', '经济', '财富', '资产'],
        '职场': ['职场', '工作', '求职', '简历', '面试', '职业', '晋升', '技能', '能力', '经验'],
        '文化': ['文化', '艺术', '历史', '传统', '民俗', '音乐', '电影', '书籍', '文学', '哲学'],
        '健康医疗': ['健康', '医疗', '养生', '疾病', '治疗', '药物', '医院', '医生', '保健', '营养'],
        '新闻时事': ['新闻', '时事', '政治', '社会', '国际', '政策', '法律', '环境', '气候', '事件']
    }
    
    # 检查标题和内容中的关键词
    text_to_check = (title + ' ' + content).lower()
    
    for category, keywords in topic_categories.items():
        if any(keyword.lower() in text_to_check for keyword in keywords):
            topics.append(category)
    
    # 如果没有找到任何分类，根据内容长度和特征自动分类
    if not topics:
        if len(content) > 2000:
            topics.append('深度内容')
        elif any(word in text_to_check for word in ['如何', '怎么', '方法', '技巧', '教程']):
            topics.append('教程指南')
        elif any(word in text_to_check for word in ['分享', '经验', '心得', '感受', '体验']):
            topics.append('经验分享')
        elif any(word in text_to_check for word in ['评测', '测评', '对比', '推荐', '选择']):
            topics.append('评测推荐')
        else:
            topics.append('综合内容')
    
    return topics[:3]  # 最多返回3个主题标签

def read_txt_file(txt_file_path):
    """读取TXT文件内容，自动检测编码"""
    encodings = ['utf-8', 'gbk', 'gb2312', 'utf-16', 'ascii']
    
    for encoding in encodings:
        try:
            with open(txt_file_path, 'r', encoding=encoding) as f:
                content = f.read()
            return content
        except (UnicodeDecodeError, UnicodeError):
            continue
        except Exception as e:
            print(f"  ⚠️ 读取文件时出错（编码：{encoding}）: {e}")
            continue
    
    print(f"  ❌ 无法识别文件编码")
    return None

def process_single_txt_file(txt_file_path):
    """处理单个TXT文件"""
    try:
        filename = os.path.basename(txt_file_path)
        print(f"📝 处理: {filename}")
        
        # 读取TXT文件
        text = read_txt_file(txt_file_path)
        if not text:
            print(f"  ❌ TXT读取失败")
            return False
        
        # 文本太短，跳过
        if len(text.strip()) < 100:
            print(f"  ⚠️ 文本内容过短（少于100字符），跳过")
            return False
        
        # 从文件名提取标题和日期
        base_name = os.path.splitext(filename)[0]
        title = base_name
        publish_date = extract_date_from_filename(filename)
        
        # 如果文本开头有明显的标题（单独一行，比较短），则使用它
        lines = text.strip().split('\n')
        if lines and len(lines[0]) < 100 and len(lines[0]) > 5:
            potential_title = lines[0].strip()
            if not potential_title.startswith('#'):
                title = potential_title
        
        # 使用AI处理内容
        print(f"  🤖 调用AI处理内容...")
        processed_content = process_text_with_ai(text, title, publish_date)
        
        if not processed_content:
            print(f"  ❌ AI处理最终失败，跳过此文件")
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
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    global TXT_FOLDER, MD_FOLDER, current_api_key
    
    parser = argparse.ArgumentParser(description='TXT到Markdown批量处理器')
    parser.add_argument('count', type=int, nargs='?', default=0, 
                       help='处理文件数量：0表示全部，其他数字表示前N个文件')
    parser.add_argument('--input', type=str, default=TXT_FOLDER,
                       help=f'输入目录（默认：{TXT_FOLDER}）')
    parser.add_argument('--output', type=str, default=MD_FOLDER,
                       help=f'输出目录（默认：{MD_FOLDER}）')
    
    args = parser.parse_args()
    process_count = args.count
    
    # 更新文件夹路径
    TXT_FOLDER = args.input
    MD_FOLDER = args.output
    
    # 初始化API密钥
    current_api_key = get_next_api_key()
    if not current_api_key:
        print("❌ 错误：没有可用的API密钥，请检查 api_keys.txt 文件")
        return
    
    start_time = datetime.now()
    print("=== TXT到Markdown批量处理器 ===")
    print(f"开始时间: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"输入目录: {TXT_FOLDER}")
    print(f"输出目录: {MD_FOLDER}")
    
    # 确保输出目录存在
    os.makedirs(MD_FOLDER, exist_ok=True)
    
    # 获取所有TXT文件
    txt_files = glob.glob(os.path.join(TXT_FOLDER, "*.txt"))
    print(f"找到 {len(txt_files)} 个TXT文件")
    
    if not txt_files:
        print(f"⚠️ 在 {TXT_FOLDER} 目录下没有找到TXT文件")
        print(f"💡 提示：")
        print(f"   - 将TXT文件放到 {TXT_FOLDER} 目录")
        print(f"   - 或使用 --input 参数指定其他目录")
        print(f"   - 注意：此脚本只处理 .txt 文件（VTT文件请使用 batch_vtt_to_md.py）")
        return
    
    # 检查已处理的文件
    existing_md_files = set()
    if os.path.exists(MD_FOLDER):
        existing_md_files = set(os.path.splitext(f)[0] for f in os.listdir(MD_FOLDER) if f.endswith('.md'))
    
    # 过滤出未处理的文件
    unprocessed_files = []
    for txt_file in txt_files:
        base_name = os.path.splitext(os.path.basename(txt_file))[0]
        if base_name not in existing_md_files:
            unprocessed_files.append(txt_file)
    
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
        
        for j, txt_file in enumerate(batch_files):
            if process_single_txt_file(txt_file):
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
    
    # 显示重试统计
    if retry_stats['total_retries'] > 0:
        print(f"\n📊 重试统计:")
        print(f"  🔄 总重试次数: {retry_stats['total_retries']}")
        print(f"  ⏰ 超时错误: {retry_stats['timeout_errors']}")
        print(f"  🌐 连接错误: {retry_stats['connection_errors']}")
        print(f"  ❓ 其他错误: {retry_stats['other_errors']}")
    else:
        print(f"🎉 所有API调用一次成功，无需重试！")
    
    print(f"\n📁 输出目录: {MD_FOLDER}")
    print(f"结束时间: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()

