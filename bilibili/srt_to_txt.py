"""
字幕文件转纯文本工具
支持将SRT字幕文件转换为纯文本，去除时间戳和序号
"""
import os
import re
import argparse
from pathlib import Path
from typing import List


class SrtToTextConverter:
    """SRT字幕转文本转换器"""
    
    def __init__(self, 
                 merge_lines: bool = False,  # 默认不合并，保持换行
                 add_punctuation: bool = True,
                 remove_duplicates: bool = True):
        """
        初始化转换器
        
        Args:
            merge_lines: 是否合并多行为段落
            add_punctuation: 是否在句尾添加标点
            remove_duplicates: 是否去除重复的句子
        """
        self.merge_lines = merge_lines
        self.add_punctuation = add_punctuation
        self.remove_duplicates = remove_duplicates
    
    def parse_srt(self, srt_path: str) -> List[str]:
        """
        解析SRT文件，提取文本内容
        
        Args:
            srt_path: SRT文件路径
            
        Returns:
            文本内容列表
        """
        texts = []
        
        try:
            with open(srt_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            # 尝试其他编码
            try:
                with open(srt_path, 'r', encoding='gbk') as f:
                    content = f.read()
            except:
                print(f"错误：无法读取文件 {srt_path}")
                return []
        
        # 分割字幕块
        blocks = content.strip().split('\n\n')
        
        for block in blocks:
            lines = block.strip().split('\n')
            
            # 跳过空块
            if not lines:
                continue
            
            # SRT格式：
            # 1. 序号
            # 2. 时间戳
            # 3. 字幕文本（可能多行）
            
            text_lines = []
            for line in lines:
                # 跳过序号（纯数字）
                if line.strip().isdigit():
                    continue
                
                # 跳过时间戳（包含 --> 的行）
                if '-->' in line:
                    continue
                
                # 跳过空行
                if not line.strip():
                    continue
                
                # 收集文本
                text_lines.append(line.strip())
            
            # 合并文本行
            if text_lines:
                text = ' '.join(text_lines)
                
                # 清理多余空格
                text = re.sub(r'\s+', ' ', text).strip()
                
                if text:
                    texts.append(text)
        
        return texts
    
    def process_texts(self, texts: List[str]) -> str:
        """
        处理文本列表，合并和格式化
        
        Args:
            texts: 文本列表
            
        Returns:
            处理后的文本
        """
        if not texts:
            return ""
        
        # 去除重复
        if self.remove_duplicates:
            seen = set()
            unique_texts = []
            for text in texts:
                if text not in seen:
                    seen.add(text)
                    unique_texts.append(text)
            texts = unique_texts
        
        # 保持分行还是合并为段落
        if self.merge_lines:
            # 合并所有行为一个段落
            result = ''.join(texts)
            
            # 添加标点
            if self.add_punctuation:
                # 如果句尾没有标点，添加句号
                result = re.sub(r'([^。！？\.\!\?])(\s|$)', r'\1。\2', result)
            
            return result
        else:
            # 保持分行（默认）
            if self.add_punctuation:
                processed = []
                for text in texts:
                    # 如果句尾没有标点，添加句号
                    if text and text[-1] not in '。！？.,!?；：':
                        text += '。'
                    processed.append(text)
                texts = processed
            
            return '\n'.join(texts)
    
    def convert_file(self, srt_path: str, output_path: str = None) -> bool:
        """
        转换单个SRT文件为文本
        
        Args:
            srt_path: SRT文件路径
            output_path: 输出文件路径（可选）
            
        Returns:
            是否成功
        """
        # 解析SRT
        texts = self.parse_srt(srt_path)
        
        if not texts:
            print(f"警告：{srt_path} 中没有找到有效文本")
            return False
        
        # 处理文本
        result = self.process_texts(texts)
        
        # 确定输出路径
        if output_path is None:
            # 默认：原文件名.txt
            srt_file = Path(srt_path)
            output_path = srt_file.parent / f"{srt_file.stem}.txt"
        
        # 写入文件
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(result)
            
            print(f"[OK] 转换成功: {srt_path}")
            print(f"     输出: {output_path}")
            print(f"     字数: {len(result)}")
            return True
        
        except Exception as e:
            print(f"错误：写入文件失败 - {e}")
            return False
    
    def convert_directory(self, directory: str, output_dir: str = None) -> dict:
        """
        批量转换目录中的所有SRT文件
        
        Args:
            directory: 输入目录
            output_dir: 输出目录（可选）
            
        Returns:
            统计信息
        """
        dir_path = Path(directory)
        
        if not dir_path.exists():
            print(f"错误：目录不存在 - {directory}")
            return {'success': 0, 'failed': 0}
        
        # 查找所有SRT文件
        srt_files = list(dir_path.glob('*.srt'))
        
        if not srt_files:
            print(f"警告：{directory} 中没有找到SRT文件")
            return {'success': 0, 'failed': 0}
        
        print(f"找到 {len(srt_files)} 个SRT文件")
        print("=" * 60)
        
        # 创建输出目录
        if output_dir:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
        
        # 批量转换
        stats = {'success': 0, 'failed': 0}
        
        for srt_file in srt_files:
            # 确定输出文件路径
            if output_dir:
                txt_file = Path(output_dir) / f"{srt_file.stem}.txt"
            else:
                txt_file = srt_file.parent / f"{srt_file.stem}.txt"
            
            # 转换
            if self.convert_file(str(srt_file), str(txt_file)):
                stats['success'] += 1
            else:
                stats['failed'] += 1
            
            print()
        
        print("=" * 60)
        print(f"转换完成！成功: {stats['success']} | 失败: {stats['failed']}")
        
        return stats


def main():
    """命令行入口"""
    parser = argparse.ArgumentParser(
        description='SRT字幕文件转纯文本工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  # 转换单个文件
  python srt_to_txt.py -f video.srt
  
  # 转换单个文件并指定输出
  python srt_to_txt.py -f video.srt -o output.txt
  
  # 批量转换目录中的所有SRT文件
  python srt_to_txt.py -d ./downloads
  
  # 批量转换并输出到指定目录
  python srt_to_txt.py -d ./downloads -o ./texts
  
  # 保持分行（不合并段落）
  python srt_to_txt.py -f video.srt --no-merge
  
  # 不添加标点
  python srt_to_txt.py -f video.srt --no-punctuation
        """
    )
    
    # 输入参数（互斥）
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument('-f', '--file', help='SRT文件路径')
    input_group.add_argument('-d', '--directory', help='包含SRT文件的目录')
    
    # 可选参数
    parser.add_argument('-o', '--output',
                       help='输出文件/目录路径（默认：与输入同目录）')
    
    parser.add_argument('--merge',
                       action='store_true',
                       help='合并为段落（默认保持分行）')
    
    parser.add_argument('--no-punctuation',
                       action='store_true',
                       help='不自动添加标点')
    
    parser.add_argument('--keep-duplicates',
                       action='store_true',
                       help='保留重复的句子')
    
    args = parser.parse_args()
    
    # 创建转换器
    converter = SrtToTextConverter(
        merge_lines=args.merge,  # 默认False（保持分行）
        add_punctuation=not args.no_punctuation,
        remove_duplicates=not args.keep_duplicates
    )
    
    # 执行转换
    if args.file:
        # 单文件转换
        success = converter.convert_file(args.file, args.output)
        exit(0 if success else 1)
    
    elif args.directory:
        # 批量转换
        stats = converter.convert_directory(args.directory, args.output)
        exit(0 if stats['success'] > 0 else 1)


if __name__ == '__main__':
    main()

