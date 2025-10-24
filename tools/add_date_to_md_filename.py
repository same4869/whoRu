#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
为Markdown文件添加发布日期到文件名
从MD文件的YAML前置数据中提取publish_date，并添加到文件名最前面

使用方法：
python add_date_to_md_filename.py        # 预览模式
python add_date_to_md_filename.py -e     # 执行重命名
"""

import os
import glob
import re
import yaml
import argparse
from datetime import datetime

# 配置
MD_FOLDER = r'D:\xwang\git_work_wx\whoRu\output_result_md_linkai'

def extract_yaml_frontmatter(file_path):
    """从MD文件中提取YAML前置数据"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查是否以YAML前置数据开始
        if not content.startswith('---'):
            return None
        
        # 分割内容获取YAML部分
        parts = content.split('---', 2)
        if len(parts) < 3:
            return None
        
        yaml_content = parts[1].strip()
        
        # 解析YAML
        try:
            yaml_data = yaml.safe_load(yaml_content)
            return yaml_data
        except yaml.YAMLError:
            return None
            
    except Exception as e:
        print(f"  ❌ 读取文件出错 {file_path}: {e}")
        return None

def parse_publish_date(date_str):
    """解析发布日期字符串，转换为YYYY-MM-DD格式"""
    if not date_str:
        return None
    
    # 处理各种可能的日期格式
    date_patterns = [
        (r'(\d{4})年(\d{1,2})月(\d{1,2})日', '%Y-%m-%d'),  # 2024年08月10日
        (r'(\d{4})-(\d{1,2})-(\d{1,2})', '%Y-%m-%d'),      # 2024-08-10
        (r'(\d{4})/(\d{1,2})/(\d{1,2})', '%Y-%m-%d'),      # 2024/08/10
        (r'(\d{1,2})/(\d{1,2})/(\d{4})', '%m-%d-%Y'),      # 08/10/2024
    ]
    
    for pattern, format_type in date_patterns:
        match = re.search(pattern, str(date_str))
        if match:
            if format_type == '%Y-%m-%d':
                year, month, day = match.groups()
                return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
            elif format_type == '%m-%d-%Y':
                month, day, year = match.groups()
                return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
    
    return None

def is_date_in_filename(filename):
    """检查文件名是否已包含日期前缀"""
    # 检查是否以 YYYY-MM-DD 格式开头
    return bool(re.match(r'^\d{4}-\d{2}-\d{2}_', filename))

def create_new_filename(original_filename, date_str):
    """创建包含日期前缀的新文件名"""
    name_without_ext = os.path.splitext(original_filename)[0]
    ext = os.path.splitext(original_filename)[1]
    
    # 如果文件名已经有日期前缀，先移除
    if is_date_in_filename(original_filename):
        # 移除现有的日期前缀
        name_without_ext = re.sub(r'^\d{4}-\d{2}-\d{2}_', '', name_without_ext)
    
    # 添加新的日期前缀
    new_filename = f"{date_str}_{name_without_ext}{ext}"
    
    return new_filename

def analyze_md_files():
    """分析所有Markdown文件"""
    print("=== Markdown文件日期分析 ===")
    print(f"分析目录: {MD_FOLDER}")
    
    # 获取所有MD文件
    md_files = glob.glob(os.path.join(MD_FOLDER, "*.md"))
    print(f"找到 {len(md_files)} 个Markdown文件")
    
    files_with_date = []  # 已有日期前缀的文件
    files_with_extractable_date = []  # 可以提取日期的文件
    files_no_date_info = []  # 无法获取日期的文件
    
    print("\n分析文件日期信息...")
    
    for i, md_file in enumerate(md_files):
        filename = os.path.basename(md_file)
        
        if i % 50 == 0:  # 每50个文件显示一次进度
            print(f"  进度: {i+1}/{len(md_files)}")
        
        # 检查文件名是否已包含日期前缀
        if is_date_in_filename(filename):
            files_with_date.append((md_file, filename))
            continue
        
        # 尝试从YAML前置数据中提取日期
        yaml_data = extract_yaml_frontmatter(md_file)
        
        if yaml_data and 'publish_date' in yaml_data:
            publish_date = yaml_data['publish_date']
            parsed_date = parse_publish_date(publish_date)
            
            if parsed_date:
                files_with_extractable_date.append((md_file, filename, parsed_date, publish_date))
            else:
                files_no_date_info.append((md_file, filename, f"日期格式无法解析: {publish_date}"))
        else:
            files_no_date_info.append((md_file, filename, "无YAML前置数据或无publish_date字段"))
    
    # 输出分析结果
    print(f"\n=== 分析结果 ===")
    print(f"[OK] 已有日期前缀: {len(files_with_date)} 个文件")
    print(f"[可提取] 可提取日期: {len(files_with_extractable_date)} 个文件")
    print(f"[无日期] 无日期信息: {len(files_no_date_info)} 个文件")
    
    # 显示无日期信息的文件
    if files_no_date_info:
        print(f"\n[警告] 无法获取日期的文件:")
        for md_file, filename, reason in files_no_date_info[:10]:  # 只显示前10个
            print(f"  - {filename[:60]}... ({reason})")
        if len(files_no_date_info) > 10:
            print(f"  ... 还有 {len(files_no_date_info) - 10} 个文件")
    
    # 显示一些可提取日期的示例
    if files_with_extractable_date:
        print(f"\n[示例] 可提取日期的文件示例:")
        for md_file, filename, parsed_date, original_date in files_with_extractable_date[:5]:
            print(f"  - {filename[:50]}...")
            print(f"    原始日期: {original_date} -> 解析后: {parsed_date}")
    
    return files_with_extractable_date, files_no_date_info

def rename_files_with_dates(files_with_dates, dry_run=True):
    """重命名文件，添加日期前缀"""
    print(f"\n=== {'预览' if dry_run else '执行'}重命名操作 ===")
    
    if not files_with_dates:
        print("没有需要重命名的文件。")
        return
    
    success_count = 0
    error_count = 0
    
    for md_file, original_filename, date_str, original_date in files_with_dates:
        try:
            new_filename = create_new_filename(original_filename, date_str)
            old_path = md_file
            new_path = os.path.join(os.path.dirname(md_file), new_filename)
            
            if dry_run:
                print(f"  [预览] {original_filename[:50]}...")
                print(f"     -> {new_filename[:60]}...")
                print(f"     (日期: {original_date} -> {date_str})")
            else:
                # 检查新文件名是否已存在
                if os.path.exists(new_path):
                    print(f"  [跳过] {original_filename} (目标文件已存在)")
                    continue
                
                # 执行重命名
                os.rename(old_path, new_path)
                print(f"  [成功] {original_filename[:40]}... -> {new_filename[:50]}...")
                success_count += 1
                
        except Exception as e:
            print(f"  [失败] 重命名失败 {original_filename}: {e}")
            error_count += 1
    
    if not dry_run:
        print(f"\n=== 重命名完成 ===")
        print(f"[成功] 成功: {success_count} 个文件")
        print(f"[失败] 失败: {error_count} 个文件")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='Markdown文件日期重命名工具')
    parser.add_argument('-e', '--execute', action='store_true', 
                       help='执行重命名（默认为预览模式）')
    
    args = parser.parse_args()
    
    print("=== Markdown文件日期重命名工具 ===")
    print(f"模式: {'执行' if args.execute else '预览'}")
    print(f"处理目录: {MD_FOLDER}")
    print("=" * 60)
    
    # 分析文件
    files_with_dates, files_no_date = analyze_md_files()
    
    if not files_with_dates:
        print("\n[完成] 所有文件都已包含日期前缀或无法提取日期。")
        return
    
    # 预览或执行重命名
    if args.execute:
        print(f"\n[警告] 即将重命名 {len(files_with_dates)} 个文件")
        rename_files_with_dates(files_with_dates, dry_run=False)
    else:
        print(f"\n[预览] 预览重命名 {len(files_with_dates)} 个文件")
        rename_files_with_dates(files_with_dates, dry_run=True)
        print(f"\n[提示] 如需执行重命名，请运行: python add_date_to_md_filename.py -e")

if __name__ == "__main__":
    main()
