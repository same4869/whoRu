#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Markdown文件合并工具
按日期范围合并文档，每个合并文件控制在1000行左右

使用方法：
python merge_md_files.py           # 预览模式
python merge_md_files.py -e        # 执行合并
python merge_md_files.py -l 800    # 自定义行数限制
"""

import os
import glob
import re
import argparse
from datetime import datetime, timedelta
from pathlib import Path
import yaml

# 配置
MD_FOLDER = r'D:\xwang\git_work_wx\whoRu\linkai\wechat_xiaotudachengzi_result'
MERGED_FOLDER = r'D:\xwang\git_work_wx\whoRu\linkai\wechat_xiaotudachengzi_result_merged'
DEFAULT_MAX_LINES = 3000

def extract_date_from_filename(filename):
    """从文件名中提取日期"""
    # 匹配 YYYY-MM-DD 格式
    date_match = re.search(r'(\d{4})-(\d{2})-(\d{2})', filename)
    if date_match:
        year, month, day = date_match.groups()
        try:
            return datetime(int(year), int(month), int(day))
        except ValueError:
            return None
    return None

def count_lines_in_file(file_path):
    """统计文件行数"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return sum(1 for line in f)
    except Exception:
        return 0

def read_md_file(file_path):
    """读取Markdown文件内容"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return content
    except Exception as e:
        print(f"  ❌ 读取文件失败 {file_path}: {e}")
        return None

def extract_frontmatter_and_content(content):
    """分离YAML前置数据和正文内容"""
    if content.startswith('---'):
        parts = content.split('---', 2)
        if len(parts) >= 3:
            frontmatter = parts[1].strip()
            main_content = parts[2].strip()
            return frontmatter, main_content
    
    return None, content

def analyze_files():
    """分析所有Markdown文件"""
    print("=== 文件分析 ===")
    
    # 获取所有MD文件
    md_files = glob.glob(os.path.join(MD_FOLDER, "*.md"))
    print(f"找到 {len(md_files)} 个Markdown文件")
    
    file_info = []
    total_lines = 0
    
    for md_file in md_files:
        filename = os.path.basename(md_file)
        date = extract_date_from_filename(filename)
        lines = count_lines_in_file(md_file)
        
        file_info.append({
            'path': md_file,
            'filename': filename,
            'date': date,
            'lines': lines
        })
        
        total_lines += lines
    
    # 按日期排序
    file_info.sort(key=lambda x: x['date'] if x['date'] else datetime.min)
    
    print(f"总行数: {total_lines}")
    print(f"平均每文件: {total_lines // len(file_info) if file_info else 0} 行")
    
    # 显示日期范围
    dated_files = [f for f in file_info if f['date']]
    if dated_files:
        earliest = min(f['date'] for f in dated_files)
        latest = max(f['date'] for f in dated_files)
        print(f"日期范围: {earliest.strftime('%Y-%m-%d')} 到 {latest.strftime('%Y-%m-%d')}")
        print(f"有日期的文件: {len(dated_files)} 个")
        print(f"无日期的文件: {len(file_info) - len(dated_files)} 个")
    
    return file_info, total_lines

def group_files_by_lines(file_info, max_lines_per_group):
    """按行数限制分组文件"""
    groups = []
    current_group = []
    current_lines = 0
    
    for file_data in file_info:
        # 如果添加这个文件会超过限制，且当前组不为空，则开始新组
        if current_lines + file_data['lines'] > max_lines_per_group and current_group:
            groups.append(current_group)
            current_group = [file_data]
            current_lines = file_data['lines']
        else:
            current_group.append(file_data)
            current_lines += file_data['lines']
    
    # 添加最后一组
    if current_group:
        groups.append(current_group)
    
    return groups

def generate_group_filename(group, group_index):
    """生成合并文件的文件名"""
    dated_files = [f for f in group if f['date']]
    
    if dated_files:
        # 按日期排序
        dated_files.sort(key=lambda x: x['date'])
        start_date = dated_files[0]['date']
        end_date = dated_files[-1]['date']
        
        if start_date == end_date:
            # 同一天的文件
            return f"合集_{start_date.strftime('%Y-%m-%d')}_{len(group)}篇.md"
        else:
            # 日期范围
            return f"合集_{start_date.strftime('%Y-%m-%d')}_至_{end_date.strftime('%Y-%m-%d')}_{len(group)}篇.md"
    else:
        # 无日期文件
        return f"合集_无日期文件_{group_index+1}_{len(group)}篇.md"

def create_merged_content(group, group_filename):
    """创建合并文件的内容"""
    # 统计信息
    total_files = len(group)
    total_lines = sum(f['lines'] for f in group)
    dated_files = [f for f in group if f['date']]
    
    # 创建文件头部
    header = f"""# {os.path.splitext(group_filename)[0]}

**合并信息:**
- 文件数量: {total_files} 篇
- 总行数: {total_lines} 行
- 合并时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
    
    if dated_files:
        dated_files.sort(key=lambda x: x['date'])
        start_date = dated_files[0]['date']
        end_date = dated_files[-1]['date']
        header += f"- 日期范围: {start_date.strftime('%Y-%m-%d')} 至 {end_date.strftime('%Y-%m-%d')}\n"
    
    header += f"""
---

## 目录

"""
    
    # 创建目录
    for i, file_data in enumerate(group, 1):
        title = os.path.splitext(file_data['filename'])[0]
        date_str = file_data['date'].strftime('%Y-%m-%d') if file_data['date'] else '未知日期'
        header += f"{i}. [{title}](#{i}-{title.replace(' ', '-').replace('#', '').replace('?', '').replace('!', '')}) ({date_str}, {file_data['lines']}行)\n"
    
    header += "\n---\n\n"
    
    # 合并文件内容
    merged_content = header
    
    for i, file_data in enumerate(group, 1):
        print(f"    合并: {file_data['filename']}")
        
        content = read_md_file(file_data['path'])
        if not content:
            continue
        
        # 分离前置数据和正文
        frontmatter, main_content = extract_frontmatter_and_content(content)
        
        # 添加文件分隔符和标题
        merged_content += f"\n\n## {i}. {os.path.splitext(file_data['filename'])[0]}\n\n"
        
        # 如果有前置数据，添加为信息框
        if frontmatter:
            try:
                fm_data = yaml.safe_load(frontmatter)
                if isinstance(fm_data, dict):
                    merged_content += "**文章信息:**\n"
                    for key, value in fm_data.items():
                        if key in ['title', 'publish_date', 'topics', 'word_count']:
                            merged_content += f"- {key}: {value}\n"
                    merged_content += "\n"
            except:
                pass
        
        # 添加正文内容
        merged_content += main_content
        merged_content += "\n\n---\n"
    
    return merged_content

def merge_files(file_info, max_lines_per_group, dry_run=True):
    """执行文件合并"""
    print(f"\n=== {'预览' if dry_run else '执行'}合并操作 ===")
    print(f"最大行数限制: {max_lines_per_group}")
    
    # 按行数分组
    groups = group_files_by_lines(file_info, max_lines_per_group)
    print(f"将分为 {len(groups)} 个合并文件")
    
    if not dry_run:
        # 确保输出目录存在
        os.makedirs(MERGED_FOLDER, exist_ok=True)
    
    for i, group in enumerate(groups):
        group_lines = sum(f['lines'] for f in group)
        group_filename = generate_group_filename(group, i)
        
        print(f"\n📁 合并文件 {i+1}/{len(groups)}: {group_filename}")
        print(f"   包含 {len(group)} 个文件，共 {group_lines} 行")
        
        if dry_run:
            # 预览模式：只显示文件列表
            for file_data in group[:5]:  # 只显示前5个
                date_str = file_data['date'].strftime('%Y-%m-%d') if file_data['date'] else '无日期'
                print(f"   - {file_data['filename'][:50]}... ({date_str}, {file_data['lines']}行)")
            if len(group) > 5:
                print(f"   ... 还有 {len(group) - 5} 个文件")
        else:
            # 执行模式：实际合并
            try:
                merged_content = create_merged_content(group, group_filename)
                output_path = os.path.join(MERGED_FOLDER, group_filename)
                
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(merged_content)
                
                actual_lines = len(merged_content.split('\n'))
                print(f"   ✅ 成功创建: {output_path}")
                print(f"   📄 实际行数: {actual_lines}")
                
            except Exception as e:
                print(f"   ❌ 合并失败: {e}")
    
    if not dry_run:
        print(f"\n🎉 合并完成！")
        print(f"📁 输出目录: {MERGED_FOLDER}")
        print(f"📊 生成 {len(groups)} 个合并文件")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='Markdown文件合并工具')
    parser.add_argument('-e', '--execute', action='store_true', 
                       help='执行合并（默认为预览模式）')
    parser.add_argument('-l', '--lines', type=int, default=DEFAULT_MAX_LINES,
                       help=f'每个合并文件的最大行数（默认{DEFAULT_MAX_LINES}）')
    
    args = parser.parse_args()
    
    print("=== Markdown文件合并工具 ===")
    print(f"模式: {'执行' if args.execute else '预览'}")
    print(f"输入目录: {MD_FOLDER}")
    print(f"输出目录: {MERGED_FOLDER}")
    print("=" * 50)
    
    # 分析文件
    file_info, total_lines = analyze_files()
    
    if not file_info:
        print("\n❌ 没有找到Markdown文件。")
        return
    
    # 预估合并后的文件数
    estimated_groups = (total_lines + args.lines - 1) // args.lines
    print(f"\n📊 预估将生成 {estimated_groups} 个合并文件")
    
    # 执行合并
    merge_files(file_info, args.lines, dry_run=not args.execute)
    
    if not args.execute:
        print(f"\n💡 如需执行合并，请运行: python merge_md_files.py -e")
        print(f"💡 自定义行数限制: python merge_md_files.py -e -l 800")

if __name__ == "__main__":
    main()
