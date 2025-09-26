#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量为VTT文件添加日期前缀
让文件能够按时间顺序排序
"""

import os
import glob
import re
import shutil
from datetime import datetime

VTT_FOLDER = r'../output_result'
BACKUP_FOLDER = r'../output_result_backup'

def extract_date_from_vtt_content(file_path):
    """从VTT文件内容中提取日期"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            # 只读取前几行，提高效率
            for line_num, line in enumerate(f):
                if line_num > 10:  # 只检查前10行
                    break
                
                # 查找日期信息
                date_match = re.search(r'# 视频发布时间: (.+)', line)
                if date_match:
                    date_str = date_match.group(1).strip()
                    # 解析格式：2024年12月26日 -> 2024-12-26
                    parse_match = re.search(r'(\d{4})年(\d{1,2})月(\d{1,2})日', date_str)
                    if parse_match:
                        year, month, day = parse_match.groups()
                        return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
        
        return None
    except Exception as e:
        print(f"  ❌ 读取文件出错: {e}")
        return None

def create_new_filename(original_filename, date_str):
    """创建包含日期的新文件名"""
    name_without_ext = os.path.splitext(original_filename)[0]
    ext = os.path.splitext(original_filename)[1]
    
    # 格式：YYYY-MM-DD_原文件名.vtt
    new_filename = f"{date_str}_{name_without_ext}{ext}"
    
    return new_filename

def batch_rename_files(dry_run=True):
    """批量重命名文件"""
    print("=== 批量日期重命名工具 ===")
    print(f"处理目录: {VTT_FOLDER}")
    
    # 获取所有VTT文件
    vtt_files = glob.glob(os.path.join(VTT_FOLDER, "*.vtt"))
    print(f"找到 {len(vtt_files)} 个VTT文件")
    
    if dry_run:
        print(f"\n🔍 预览模式 - 不会实际重命名文件")
    else:
        print(f"\n⚠️ 执行模式 - 将实际重命名文件")
    
    print("-" * 80)
    
    success_files = []
    failed_files = []
    
    for i, vtt_file in enumerate(vtt_files):
        original_filename = os.path.basename(vtt_file)
        
        # 显示进度
        if i % 50 == 0 or i == len(vtt_files) - 1:
            print(f"进度: {i+1}/{len(vtt_files)} ({(i+1)/len(vtt_files)*100:.1f}%)")
        
        # 提取日期
        date_str = extract_date_from_vtt_content(vtt_file)
        
        if not date_str:
            failed_files.append((original_filename, "无法提取日期"))
            continue
        
        # 创建新文件名
        new_filename = create_new_filename(original_filename, date_str)
        new_file_path = os.path.join(VTT_FOLDER, new_filename)
        
        # 检查是否会覆盖现有文件
        if os.path.exists(new_file_path):
            failed_files.append((original_filename, "目标文件已存在"))
            continue
        
        if dry_run:
            success_files.append((original_filename, new_filename, date_str))
        else:
            try:
                # 执行重命名
                os.rename(vtt_file, new_file_path)
                success_files.append((original_filename, new_filename, date_str))
            except Exception as e:
                failed_files.append((original_filename, f"重命名失败: {e}"))
    
    # 输出结果
    print(f"\n=== 处理结果 ===")
    print(f"✅ 成功: {len(success_files)} 个文件")
    print(f"❌ 失败: {len(failed_files)} 个文件")
    
    # 显示失败的文件
    if failed_files:
        print(f"\n⚠️ 失败的文件:")
        for filename, reason in failed_files[:10]:  # 只显示前10个
            print(f"  - {filename[:50]}... ({reason})")
        if len(failed_files) > 10:
            print(f"  ... 还有 {len(failed_files) - 10} 个失败文件")
    
    # 显示一些成功的示例
    if success_files:
        print(f"\n✅ 重命名示例:")
        for i, (old_name, new_name, date) in enumerate(success_files[:5]):
            print(f"  {i+1}. {old_name[:40]}...")
            print(f"     -> {new_name[:50]}...")
            print(f"     (日期: {date})")
        
        if len(success_files) > 5:
            print(f"  ... 还有 {len(success_files) - 5} 个文件")
    
    return success_files, failed_files

def create_backup():
    """创建备份目录"""
    if not os.path.exists(BACKUP_FOLDER):
        os.makedirs(BACKUP_FOLDER)
        print(f"📁 创建备份目录: {BACKUP_FOLDER}")
    return BACKUP_FOLDER

def main():
    """主函数"""
    print("VTT文件批量日期重命名工具")
    print("=" * 50)
    
    # 预览重命名
    success_files, failed_files = batch_rename_files(dry_run=True)
    
    if not success_files:
        print("\n❌ 没有文件可以重命名。")
        return
    
    print(f"\n📊 预计重命名 {len(success_files)} 个文件")
    
    # 询问是否执行
    choice = input(f"\n是否执行批量重命名？这将重命名 {len(success_files)} 个文件 (y/n): ")
    
    if choice.lower() == 'y':
        # 建议备份
        backup_choice = input("是否先创建备份目录？(推荐) (y/n): ")
        if backup_choice.lower() == 'y':
            create_backup()
            print("💡 请手动复制重要文件到备份目录")
        
        # 最终确认
        confirm = input(f"\n⚠️ 最后确认：将重命名 {len(success_files)} 个文件，确定执行？(y/n): ")
        
        if confirm.lower() == 'y':
            print("\n🚀 开始执行批量重命名...")
            batch_rename_files(dry_run=False)
            print("\n🎉 批量重命名完成！")
            print("📁 现在文件可以按日期顺序排序了")
        else:
            print("用户取消操作。")
    else:
        print("用户取消操作。")

if __name__ == "__main__":
    main()
