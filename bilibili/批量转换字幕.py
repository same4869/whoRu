"""
简易批量字幕转文本工具
双击运行，自动处理当前目录及子目录下的所有SRT文件
"""
import os
from pathlib import Path
from srt_to_txt import SrtToTextConverter


def main():
    print("=" * 70)
    print("  B站字幕批量转文本工具")
    print("=" * 70)
    print()
    
    # 获取当前目录
    current_dir = Path(__file__).parent
    
    print(f"当前目录: {current_dir}")
    print()
    
    # 用户选择
    print("请选择操作：")
    print("1. 转换当前目录的SRT文件")
    print("2. 转换指定目录的SRT文件")
    print("3. 递归转换（包括子目录）")
    print()
    
    choice = input("请输入选择 (1-3): ").strip()
    
    if choice == '1':
        target_dir = current_dir
        recursive = False
    elif choice == '2':
        dir_path = input("请输入目录路径: ").strip()
        target_dir = Path(dir_path)
        if not target_dir.exists():
            print(f"错误：目录不存在 - {dir_path}")
            input("\n按回车键退出...")
            return
        recursive = False
    elif choice == '3':
        dir_path = input("请输入目录路径（留空使用当前目录）: ").strip()
        if dir_path:
            target_dir = Path(dir_path)
            if not target_dir.exists():
                print(f"错误：目录不存在 - {dir_path}")
                input("\n按回车键退出...")
                return
        else:
            target_dir = current_dir
        recursive = True
    else:
        print("无效选择！")
        input("\n按回车键退出...")
        return
    
    print()
    print("=" * 70)
    
    # 查找SRT文件
    if recursive:
        srt_files = list(target_dir.rglob('*.srt'))
    else:
        srt_files = list(target_dir.glob('*.srt'))
    
    if not srt_files:
        print(f"未找到SRT文件")
        input("\n按回车键退出...")
        return
    
    print(f"找到 {len(srt_files)} 个SRT文件")
    print()
    
    # 配置选项
    print("转换选项：")
    merge = input("是否合并为段落？(y/N): ").strip().lower() == 'y'  # 默认不合并
    punct = input("是否自动添加标点？(Y/n): ").strip().lower() != 'n'
    
    print()
    print("开始转换...")
    print("=" * 70)
    
    # 创建转换器
    converter = SrtToTextConverter(
        merge_lines=merge,
        add_punctuation=punct,
        remove_duplicates=True
    )
    
    # 批量转换
    success = 0
    failed = 0
    
    for idx, srt_file in enumerate(srt_files, 1):
        print(f"\n[{idx}/{len(srt_files)}] {srt_file.name}")
        
        # 输出到同目录
        txt_file = srt_file.parent / f"{srt_file.stem}.txt"
        
        if converter.convert_file(str(srt_file), str(txt_file)):
            success += 1
        else:
            failed += 1
    
    print()
    print("=" * 70)
    print(f"转换完成！")
    print(f"成功: {success} | 失败: {failed}")
    print("=" * 70)
    
    input("\n按回车键退出...")


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"\n发生错误: {e}")
        input("\n按回车键退出...")

