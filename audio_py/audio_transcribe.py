#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
音频转文本转Markdown自动化工具
支持mp3、mp4、m4a等音频格式，使用Whisper转录后通过AI整理为高质量文章

主要功能：
1. 自动重命名音频文件（去除中文，只保留编号）
2. 使用Whisper转录音频为文本
3. 调用LinkAI处理文本生成Markdown文章
4. 支持指定处理个数或范围
5. 自动跳过已处理文件

使用方法：
python audio_transcribe.py              # 处理所有音频文件
python audio_transcribe.py -n 5         # 只处理前5个文件
python audio_transcribe.py -r 10-20     # 只处理E10到E20
python audio_transcribe.py -r 10-20 -n 5  # 范围优先，处理E10-E20
python audio_transcribe.py --skip-whisper # 跳过Whisper转录，直接处理现有txt

配置说明：
- 音频目录：../audios
- 文本输出：../audios_txt
- Markdown输出：./audio_md
- Whisper模型：small (可在代码中修改)
"""

import os
import sys
import glob
import re
import shutil
import subprocess
import argparse
from pathlib import Path
from datetime import datetime

# 添加父目录到路径
sys.path.append(str(Path(__file__).parent.parent))

# 目录配置
AUDIO_FOLDER = r'../audios'
TXT_FOLDER = r'../audios_txt'
MD_FOLDER = r'./audio_md'
TEMP_AUDIO_FOLDER = r'./temp_audios'

# Whisper配置
WHISPER_MODEL = 'small'  # tiny, base, small, medium, large
WHISPER_LANGUAGE = 'Chinese'
WHISPER_OUTPUT_FORMAT = 'txt'

# 支持的音频格式
AUDIO_EXTENSIONS = ['.mp3', '.mp4', '.m4a', '.wav', '.flac', '.aac']

def extract_episode_number(filename):
    """从文件名中提取集数编号"""
    # 匹配 E 后面跟数字的模式，如 E373, E10 等
    match = re.search(r'E(\d+)', filename, re.IGNORECASE)
    if match:
        return int(match.group(1))
    return None

def clean_filename(filename):
    """清理文件名，去除中文字符，只保留编号和扩展名"""
    # 提取 E编号
    match = re.search(r'(E\d+)', filename, re.IGNORECASE)
    if not match:
        return None
    
    episode_prefix = match.group(1).upper()  # E373
    
    # 获取文件扩展名
    ext = os.path.splitext(filename)[1]
    
    # 返回清理后的文件名
    return f"{episode_prefix}{ext}"

def get_audio_files():
    """获取所有音频文件"""
    audio_files = []
    
    if not os.path.exists(AUDIO_FOLDER):
        print(f"❌ 音频目录不存在: {AUDIO_FOLDER}")
        return []
    
    for ext in AUDIO_EXTENSIONS:
        pattern = os.path.join(AUDIO_FOLDER, f"*{ext}")
        audio_files.extend(glob.glob(pattern))
    
    return audio_files

def filter_files_by_range(files, start, end):
    """根据范围过滤文件"""
    filtered = []
    for file in files:
        filename = os.path.basename(file)
        episode_num = extract_episode_number(filename)
        if episode_num and start <= episode_num <= end:
            filtered.append((file, episode_num))
    
    # 按集数排序
    filtered.sort(key=lambda x: x[1])
    return [f[0] for f in filtered]

def prepare_audio_file(audio_file):
    """准备音频文件：重命名并复制到临时目录"""
    original_filename = os.path.basename(audio_file)
    clean_name = clean_filename(original_filename)
    
    if not clean_name:
        print(f"  ⚠️ 无法提取集数编号，跳过: {original_filename}")
        return None
    
    # 确保临时目录存在
    os.makedirs(TEMP_AUDIO_FOLDER, exist_ok=True)
    
    # 复制到临时目录
    temp_file = os.path.join(TEMP_AUDIO_FOLDER, clean_name)
    
    if os.path.exists(temp_file):
        print(f"  📝 临时文件已存在: {clean_name}")
    else:
        print(f"  📝 重命名: {original_filename} -> {clean_name}")
        shutil.copy2(audio_file, temp_file)
    
    return temp_file

def transcribe_with_whisper(audio_file):
    """使用Whisper转录音频"""
    filename = os.path.basename(audio_file)
    base_name = os.path.splitext(filename)[0]
    
    # 检查是否已经转录过
    txt_file = os.path.join(TXT_FOLDER, f"{base_name}.txt")
    if os.path.exists(txt_file):
        print(f"  ✅ 文本文件已存在，跳过转录: {base_name}.txt")
        return txt_file
    
    # 确保输出目录存在
    os.makedirs(TXT_FOLDER, exist_ok=True)
    
    # 构建Whisper命令
    cmd = [
        'whisper',
        audio_file,
        '--language', WHISPER_LANGUAGE,
        '--model', WHISPER_MODEL,
        '--fp16', 'False',
        '--output_format', WHISPER_OUTPUT_FORMAT,
        '--output_dir', TXT_FOLDER
    ]
    
    print(f"  🎤 开始转录: {filename}")
    print(f"  命令: {' '.join(cmd)}")
    
    try:
        # 执行Whisper
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='ignore')
        
        if result.returncode == 0:
            print(f"  ✅ 转录完成: {base_name}.txt")
            return txt_file
        else:
            print(f"  ❌ 转录失败:")
            print(f"  错误信息: {result.stderr}")
            return None
            
    except FileNotFoundError:
        print(f"  ❌ Whisper未安装或未添加到PATH")
        print(f"  请安装: pip install openai-whisper")
        return None
    except Exception as e:
        print(f"  ❌ 转录出错: {e}")
        return None

def process_txt_to_md():
    """调用batch_txt_to_md.py处理txt文件"""
    print("\n" + "="*60)
    print("步骤2/2: 使用AI处理文本生成Markdown")
    print("="*60)
    
    # 确保输出目录存在
    os.makedirs(MD_FOLDER, exist_ok=True)
    
    # 获取linkai目录的绝对路径
    script_dir = os.path.dirname(os.path.abspath(__file__))
    linkai_dir = os.path.join(os.path.dirname(script_dir), 'linkai')
    
    # 转换为绝对路径
    txt_folder_abs = os.path.abspath(os.path.join(script_dir, TXT_FOLDER))
    md_folder_abs = os.path.abspath(os.path.join(script_dir, MD_FOLDER))
    
    # 构建命令
    cmd = [
        'python',
        'batch_txt_to_md.py',
        '--input', txt_folder_abs,
        '--output', md_folder_abs
    ]
    
    print(f"\n调用脚本: batch_txt_to_md.py")
    print(f"工作目录: {linkai_dir}")
    print(f"输入目录: {txt_folder_abs}")
    print(f"输出目录: {md_folder_abs}")
    print(f"\n执行命令: {' '.join(cmd)}\n")
    
    try:
        # 在linkai目录执行batch_txt_to_md.py
        result = subprocess.run(cmd, cwd=linkai_dir)
        
        if result.returncode == 0:
            print(f"\n✅ Markdown生成完成！")
            print(f"📁 输出目录: {md_folder_abs}")
            return True
        else:
            print(f"\n❌ Markdown生成失败")
            return False
            
    except Exception as e:
        print(f"\n❌ 处理出错: {e}")
        return False

def cleanup_temp_files():
    """清理临时文件"""
    if os.path.exists(TEMP_AUDIO_FOLDER):
        try:
            shutil.rmtree(TEMP_AUDIO_FOLDER)
            print(f"\n🧹 清理临时文件: {TEMP_AUDIO_FOLDER}")
        except Exception as e:
            print(f"\n⚠️ 清理临时文件失败: {e}")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='音频转文本转Markdown自动化工具')
    parser.add_argument('-n', '--number', type=int, default=-1,
                       help='处理文件数量：-1表示不限制（默认）')
    parser.add_argument('-r', '--range', type=str, default=None,
                       help='处理范围：如 10-20 表示处理E10到E20')
    parser.add_argument('--skip-whisper', action='store_true',
                       help='跳过Whisper转录，直接处理现有txt文件')
    parser.add_argument('--keep-temp', action='store_true',
                       help='保留临时文件（不清理）')
    
    args = parser.parse_args()
    
    start_time = datetime.now()
    print("="*60)
    print("音频转文本转Markdown自动化工具")
    print("="*60)
    print(f"开始时间: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 解析参数
    start_episode = None
    end_episode = None
    if args.range:
        try:
            parts = args.range.split('-')
            start_episode = int(parts[0])
            end_episode = int(parts[1])
            print(f"处理范围: E{start_episode} - E{end_episode}")
        except:
            print(f"❌ 范围格式错误，应为: 10-20")
            return
    elif args.number > 0:
        print(f"处理数量: 前 {args.number} 个文件")
    else:
        print(f"处理数量: 所有文件")
    
    if args.skip_whisper:
        print("模式: 跳过Whisper转录")
        process_txt_to_md()
        return
    
    print("\n" + "="*60)
    print("步骤1/2: 使用Whisper转录音频")
    print("="*60)
    
    # 获取音频文件
    audio_files = get_audio_files()
    print(f"\n找到 {len(audio_files)} 个音频文件")
    
    if not audio_files:
        print("❌ 没有找到音频文件")
        return
    
    # 根据范围过滤
    if start_episode and end_episode:
        audio_files = filter_files_by_range(audio_files, start_episode, end_episode)
        print(f"范围过滤后: {len(audio_files)} 个文件")
    elif args.number > 0:
        # 按集数排序
        files_with_num = []
        for f in audio_files:
            num = extract_episode_number(os.path.basename(f))
            if num:
                files_with_num.append((f, num))
        files_with_num.sort(key=lambda x: x[1])
        audio_files = [f[0] for f in files_with_num[:args.number]]
        print(f"数量限制后: {len(audio_files)} 个文件")
    
    if not audio_files:
        print("❌ 没有符合条件的文件")
        return
    
    # 处理每个音频文件
    success_count = 0
    total_files = len(audio_files)
    
    for i, audio_file in enumerate(audio_files, 1):
        print(f"\n[{i}/{total_files}] 处理: {os.path.basename(audio_file)}")
        
        # 准备音频文件
        temp_file = prepare_audio_file(audio_file)
        if not temp_file:
            continue
        
        # 转录
        txt_file = transcribe_with_whisper(temp_file)
        if txt_file:
            success_count += 1
    
    # 统计
    elapsed_time = (datetime.now() - start_time).total_seconds() / 60
    print(f"\n" + "="*60)
    print(f"Whisper转录完成")
    print(f"✅ 成功: {success_count}/{total_files} 个文件")
    print(f"⏱️ 用时: {elapsed_time:.1f} 分钟")
    print("="*60)
    
    # 清理临时文件
    if not args.keep_temp:
        cleanup_temp_files()
    
    # 处理txt生成md
    if success_count > 0:
        process_txt_to_md()
    
    end_time = datetime.now()
    total_time = (end_time - start_time).total_seconds() / 60
    print(f"\n" + "="*60)
    print(f"全部完成！")
    print(f"总用时: {total_time:.1f} 分钟")
    print(f"结束时间: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)

if __name__ == "__main__":
    main()

