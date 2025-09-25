import os
import webvtt
import tiktoken
import time
from typing import List, Optional

"""
批量VTT字幕翻译器 - 测试版本
===============================================
这是一个测试版本，使用模拟API来验证整个处理流程
"""

# ==================== 配置区 ====================

INPUT_FOLDER = 'output_result'
OUTPUT_FOLDER = 'translated_md_test'
MAX_TOKENS_PER_CHUNK = 2500

# 模拟翻译提示词（用于测试）
SYSTEM_PROMPT = """
你是一位顶级的翻译家和内容编辑。
你的任务是：将用户提供的中文视频字幕，整理成一篇流畅、自然、连贯的简体中文文章。

请严格遵守以下核心原则：
1. **全文整理与合并**：
   - 必须保留所有重要内容，不能省略关键信息。
   - **关键指令**：请智能地将原文中语义连贯的多行短句，合并成符合中文阅读习惯的自然段落。

2. **内容优化**：
   - 去除重复的口语化表达和填充词
   - 修正语法错误，使表达更加规范
   - 保持原意的同时，让文章更加流畅易读

3. **格式要求**：
   - 使用 Markdown 格式输出
   - 对关键词进行 **加粗** 以提高可读性
   - 合理分段，确保逻辑清晰

4. **直接输出**：请直接开始输出最终整理好的中文文章，不要包含任何解释或标签。
"""

class TestVTTTranslator:
    def __init__(self):
        self.tokenizer = self._get_tokenizer()
        
    def _get_tokenizer(self) -> Optional[any]:
        """获取tokenizer用于文本分片"""
        try:
            return tiktoken.get_encoding("cl100k_base")
        except Exception as e:
            print(f"获取 tokenizer 失败: {e}")
            return None
    
    def parse_vtt_file(self, file_path: str) -> Optional[str]:
        """解析VTT文件，提取文本内容"""
        try:
            captions = webvtt.read(file_path)
            texts = []
            for caption in captions:
                text = caption.text.strip()
                if text:
                    texts.append(text)
            
            full_text = "\n".join(texts)
            return full_text
        except Exception as e:
            print(f"解析VTT文件 {os.path.basename(file_path)} 时出错: {e}")
            return None
    
    def split_text_into_chunks(self, text: str) -> List[str]:
        """将文本分片处理，避免超过token限制"""
        if not self.tokenizer:
            print("Tokenizer 不可用，将尝试一次性处理。")
            return [text]
        
        tokens = self.tokenizer.encode(text)
        if len(tokens) <= MAX_TOKENS_PER_CHUNK:
            return [text]
        
        print(f"文本过长 ({len(tokens)} tokens)，正在分片处理...")
        chunks = []
        current_chunk_tokens = []
        
        lines = text.split('\n')
        for line in lines:
            if not line.strip():
                continue
                
            line_tokens = self.tokenizer.encode(line + "\n")
            
            if len(current_chunk_tokens) + len(line_tokens) > MAX_TOKENS_PER_CHUNK:
                if current_chunk_tokens:
                    chunks.append(self.tokenizer.decode(current_chunk_tokens))
                    current_chunk_tokens = []
            
            current_chunk_tokens.extend(line_tokens)
        
        if current_chunk_tokens:
            chunks.append(self.tokenizer.decode(current_chunk_tokens))
        
        print(f"文本成功分成了 {len(chunks)} 个片段。")
        return chunks
    
    def mock_api_call(self, text_chunk: str) -> str:
        """模拟API调用 - 用于测试"""
        print("模拟API处理中...")
        time.sleep(0.5)  # 模拟网络延迟
        
        # 简单的文本处理模拟
        lines = text_chunk.split('\n')
        processed_lines = []
        current_paragraph = []
        
        for line in lines:
            line = line.strip()
            if not line:
                if current_paragraph:
                    processed_lines.append(' '.join(current_paragraph))
                    current_paragraph = []
                continue
            
            current_paragraph.append(line)
            
            # 每3-5句合并成一段
            if len(current_paragraph) >= 4:
                processed_lines.append(' '.join(current_paragraph))
                current_paragraph = []
        
        # 处理剩余的句子
        if current_paragraph:
            processed_lines.append(' '.join(current_paragraph))
        
        # 添加一些基本的格式化
        result = '\n\n'.join(processed_lines)
        
        # 模拟添加一些关键词加粗
        keywords = ['加密貨幣', '比特幣', '以太幣', '區塊鏈', '交易', '投資', 'BTC', 'ETH', 'ADA']
        for keyword in keywords:
            if keyword in result:
                result = result.replace(keyword, f'**{keyword}**', 1)  # 只替换第一个
        
        return result
    
    def process_file(self, vtt_file_path: str) -> bool:
        """处理单个VTT文件"""
        filename = os.path.basename(vtt_file_path)
        print(f"\n--- 正在处理文件: {filename} ---")
        
        # 解析VTT文件
        text_content = self.parse_vtt_file(vtt_file_path)
        if not text_content:
            print(f"无法解析文件: {filename}")
            return False
        
        print(f"✓ 提取到 {len(text_content)} 个字符的文本内容")
        
        # 显示前200个字符作为预览
        preview = text_content[:200].replace('\n', ' ')
        print(f"内容预览: {preview}...")
        
        # 分片处理
        chunks = self.split_text_into_chunks(text_content)
        processed_chunks = []
        
        for i, chunk in enumerate(chunks):
            print(f"正在处理片段 {i+1}/{len(chunks)}...")
            translated_chunk = self.mock_api_call(chunk)
            processed_chunks.append(translated_chunk)
        
        # 合并所有处理后的片段
        final_content = "\n\n---\n\n".join(processed_chunks)
        
        # 添加文件头信息
        header = f"# {os.path.splitext(filename)[0]}\n\n*由批量VTT字幕翻译器处理*\n\n---\n\n"
        final_content = header + final_content
        
        # 保存结果
        output_filename = f"{os.path.splitext(filename)[0]}.md"
        output_path = os.path.join(OUTPUT_FOLDER, output_filename)
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(final_content)
            print(f"✓ 处理完成！文件已保存至: {output_path}")
            return True
            
        except IOError as e:
            print(f"✗ 保存文件失败: {e}")
            return False
    
    def batch_process(self):
        """批量处理所有VTT文件"""
        print("=" * 60)
        print("批量VTT字幕翻译器 - 测试模式")
        print("=" * 60)
        print(f"输入文件夹: {INPUT_FOLDER}")
        print(f"输出文件夹: {OUTPUT_FOLDER}")
        print("使用模拟API进行测试")
        print("=" * 60)
        
        # 检查输入文件夹
        if not os.path.isdir(INPUT_FOLDER):
            print(f"错误：输入文件夹不存在 -> {INPUT_FOLDER}")
            return
        
        # 创建输出文件夹
        if not os.path.isdir(OUTPUT_FOLDER):
            try:
                os.makedirs(OUTPUT_FOLDER)
                print(f"✓ 已创建输出文件夹: {OUTPUT_FOLDER}")
            except OSError as e:
                print(f"错误：无法创建输出文件夹 {OUTPUT_FOLDER}。错误信息: {e}")
                return
        
        # 获取所有VTT文件
        vtt_files = [f for f in os.listdir(INPUT_FOLDER) if f.lower().endswith('.vtt')]
        
        if not vtt_files:
            print(f"在 {INPUT_FOLDER} 文件夹中没有找到VTT文件")
            return
        
        print(f"✓ 找到 {len(vtt_files)} 个VTT文件")
        
        # 处理统计
        success_count = 0
        failed_count = 0
        
        # 逐个处理文件
        for i, filename in enumerate(sorted(vtt_files), 1):
            print(f"\n[进度: {i}/{len(vtt_files)}]")
            vtt_path = os.path.join(INPUT_FOLDER, filename)
            
            if self.process_file(vtt_path):
                success_count += 1
            else:
                failed_count += 1
        
        # 输出最终统计
        print("\n" + "=" * 60)
        print("🎉 批量处理完成！")
        print(f"✅ 成功处理: {success_count} 个文件")
        print(f"❌ 处理失败: {failed_count} 个文件")
        print(f"📊 总计文件: {len(vtt_files)} 个")
        print(f"📁 输出目录: {OUTPUT_FOLDER}")
        print("=" * 60)
        
        # 显示生成的文件
        if success_count > 0:
            print("\n生成的文件:")
            try:
                output_files = os.listdir(OUTPUT_FOLDER)
                for f in sorted(output_files):
                    if f.endswith('.md'):
                        file_path = os.path.join(OUTPUT_FOLDER, f)
                        file_size = os.path.getsize(file_path)
                        print(f"  📄 {f} ({file_size} bytes)")
            except Exception as e:
                print(f"无法列出输出文件: {e}")

def main():
    """主程序入口"""
    print("🚀 开始测试批量VTT字幕翻译器...")
    
    translator = TestVTTTranslator()
    translator.batch_process()
    
    print("\n💡 测试完成！如果测试结果满意，可以配置真实的API进行正式处理。")

if __name__ == '__main__':
    main()
