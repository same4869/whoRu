import os
import requests
import json
import webvtt
import tiktoken
import time
import re
from typing import List, Optional, Dict, Any

"""
批量VTT字幕翻译器 - 支持多种免费大模型API
===============================================

功能说明：
- 自动处理output_result文件夹中的所有VTT字幕文件
- 支持多种免费大模型API（DeepSeek、Ollama本地、智谱GLM等）
- 智能文本分片处理，避免token限制
- 自动重试机制和错误处理
- 输出格式化的Markdown文件

支持的API：
1. DeepSeek API (免费额度)
2. Ollama 本地模型 (完全免费)
3. 智谱清言 ChatGLM (免费额度)
4. 自定义API端点

使用方法：
1. 修改下面配置区的参数
2. 选择合适的API提供商
3. 运行脚本即可
"""

# ==================== 配置区 (请在这里修改) ====================

# 输入输出路径配置
INPUT_FOLDER = 'output_result'  # VTT文件所在文件夹
OUTPUT_FOLDER = 'translated_md'  # 输出Markdown文件的文件夹

# API配置 - 选择其中一种
API_PROVIDER = 'deepseek'  # 可选: 'deepseek', 'ollama', 'glm', 'custom'

# DeepSeek API 配置 (免费额度每月足够个人使用)
DEEPSEEK_CONFIG = {
    'api_url': 'https://api.deepseek.com/v1/chat/completions',
    'api_key': 'sk-6eca119bc7ef4537a9ef07da241e7c1c',  # 在 https://platform.deepseek.com/ 获取
    'model': 'deepseek-chat'
}

# Ollama 本地配置 (完全免费，需要本地安装ollama)
OLLAMA_CONFIG = {
    'api_url': 'http://127.0.0.1:11434/v1/chat/completions',
    'model': 'qwen2.5:7b'  # 或其他已安装的模型，如 'llama3.1:8b'
}

# 智谱清言 GLM 配置 (有免费额度)
GLM_CONFIG = {
    'api_url': 'https://open.bigmodel.cn/api/paas/v4/chat/completions',
    'api_key': 'YOUR_GLM_API_KEY',  # 在 https://open.bigmodel.cn/ 获取
    'model': 'glm-4-flash'
}

# 自定义API配置
CUSTOM_CONFIG = {
    'api_url': 'http://127.0.0.1:1234/v1/chat/completions',
    'api_key': '',  # 如果需要的话
    'model': 'local-model'
}

# 处理参数
MAX_TOKENS_PER_CHUNK = 2500  # 每个分片的最大token数
REQUEST_TIMEOUT = 300  # API请求超时时间(秒)
RETRY_ATTEMPTS = 3  # 失败重试次数
RETRY_DELAY = 2  # 重试间隔(秒)

# 翻译提示词
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

# =============================================================

class VTTTranslator:
    def __init__(self):
        self.tokenizer = self._get_tokenizer()
        self.api_config = self._get_api_config()
        
    def _get_tokenizer(self) -> Optional[Any]:
        """获取tokenizer用于文本分片"""
        try:
            return tiktoken.get_encoding("cl100k_base")
        except Exception as e:
            print(f"获取 tokenizer 失败: {e}")
            return None
    
    def _get_api_config(self) -> Dict[str, Any]:
        """根据选择的API提供商返回配置"""
        configs = {
            'deepseek': DEEPSEEK_CONFIG,
            'ollama': OLLAMA_CONFIG,
            'glm': GLM_CONFIG,
            'custom': CUSTOM_CONFIG
        }
        return configs.get(API_PROVIDER, OLLAMA_CONFIG)
    
    def parse_vtt_file(self, file_path: str) -> Optional[str]:
        """解析VTT文件，提取文本内容"""
        try:
            captions = webvtt.read(file_path)
            # 提取所有字幕文本，去除时间戳
            texts = []
            for caption in captions:
                text = caption.text.strip()
                if text:  # 只添加非空文本
                    texts.append(text)
            
            # 合并所有文本
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
        
        # 按行分割，保持语义完整性
        lines = text.split('\n')
        for line in lines:
            if not line.strip():
                continue
                
            line_tokens = self.tokenizer.encode(line + "\n")
            
            # 如果添加这行会超过限制，则保存当前chunk并开始新的
            if len(current_chunk_tokens) + len(line_tokens) > MAX_TOKENS_PER_CHUNK:
                if current_chunk_tokens:
                    chunks.append(self.tokenizer.decode(current_chunk_tokens))
                    current_chunk_tokens = []
            
            current_chunk_tokens.extend(line_tokens)
        
        # 添加最后一个chunk
        if current_chunk_tokens:
            chunks.append(self.tokenizer.decode(current_chunk_tokens))
        
        print(f"文本成功分成了 {len(chunks)} 个片段。")
        return chunks
    
    def clean_model_output(self, raw_text: str) -> str:
        """清理模型输出，移除不需要的标签"""
        # 移除可能的思考标签
        cleaned_text = re.sub(r'^\s*<think>.*?</think>\s*', '', raw_text, flags=re.DOTALL)
        # 移除其他可能的标签
        cleaned_text = re.sub(r'^\s*```.*?\n', '', cleaned_text)
        cleaned_text = re.sub(r'\n```\s*$', '', cleaned_text)
        return cleaned_text.strip()
    
    def call_api(self, text_chunk: str) -> Optional[str]:
        """调用API处理文本块"""
        headers = {"Content-Type": "application/json"}
        
        # 根据API提供商设置认证头
        if API_PROVIDER in ['deepseek', 'glm'] and self.api_config.get('api_key'):
            headers["Authorization"] = f"Bearer {self.api_config['api_key']}"
        
        payload = {
            "model": self.api_config['model'],
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": text_chunk}
            ],
            "temperature": 0.7,
            "stream": False
        }
        
        for attempt in range(RETRY_ATTEMPTS):
            try:
                print(f"正在调用API... (尝试 {attempt + 1}/{RETRY_ATTEMPTS})")
                response = requests.post(
                    self.api_config['api_url'], 
                    headers=headers, 
                    data=json.dumps(payload), 
                    timeout=REQUEST_TIMEOUT
                )
                response.raise_for_status()
                
                response_json = response.json()
                raw_output = response_json['choices'][0]['message']['content']
                cleaned_output = self.clean_model_output(raw_output)
                return cleaned_output
                
            except requests.exceptions.Timeout:
                print(f"API调用超时 (超过{REQUEST_TIMEOUT}秒)")
                if attempt < RETRY_ATTEMPTS - 1:
                    print(f"等待{RETRY_DELAY}秒后重试...")
                    time.sleep(RETRY_DELAY)
                    
            except requests.exceptions.RequestException as e:
                print(f"API调用出错: {e}")
                if attempt < RETRY_ATTEMPTS - 1:
                    print(f"等待{RETRY_DELAY}秒后重试...")
                    time.sleep(RETRY_DELAY)
                    
            except (KeyError, json.JSONDecodeError) as e:
                print(f"API响应解析错误: {e}")
                if attempt < RETRY_ATTEMPTS - 1:
                    print(f"等待{RETRY_DELAY}秒后重试...")
                    time.sleep(RETRY_DELAY)
        
        print(f"API调用失败，已重试{RETRY_ATTEMPTS}次")
        return None
    
    def process_file(self, vtt_file_path: str) -> bool:
        """处理单个VTT文件"""
        filename = os.path.basename(vtt_file_path)
        print(f"\n--- 正在处理文件: {filename} ---")
        
        # 解析VTT文件
        text_content = self.parse_vtt_file(vtt_file_path)
        if not text_content:
            print(f"无法解析文件: {filename}")
            return False
        
        print(f"提取到 {len(text_content)} 个字符的文本内容")
        
        # 分片处理
        chunks = self.split_text_into_chunks(text_content)
        processed_chunks = []
        
        for i, chunk in enumerate(chunks):
            print(f"正在处理片段 {i+1}/{len(chunks)}...")
            translated_chunk = self.call_api(chunk)
            
            if not translated_chunk:
                print(f"片段 {i+1} 处理失败，跳过整个文件 {filename}")
                return False
            
            processed_chunks.append(translated_chunk)
            
            # 避免API调用过于频繁
            if i < len(chunks) - 1:
                time.sleep(1)
        
        # 合并所有处理后的片段
        final_content = "\n\n".join(processed_chunks)
        
        # 保存结果
        output_filename = f"{os.path.splitext(filename)[0]}.md"
        output_path = os.path.join(OUTPUT_FOLDER, output_filename)
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(final_content.strip())
            print(f"✓ 处理完成！文件已保存至: {output_path}")
            return True
            
        except IOError as e:
            print(f"✗ 保存文件失败: {e}")
            return False
    
    def batch_process(self):
        """批量处理所有VTT文件"""
        print("=" * 60)
        print("批量VTT字幕翻译器")
        print("=" * 60)
        print(f"使用API: {API_PROVIDER}")
        print(f"输入文件夹: {INPUT_FOLDER}")
        print(f"输出文件夹: {OUTPUT_FOLDER}")
        print("=" * 60)
        
        # 检查输入文件夹
        if not os.path.isdir(INPUT_FOLDER):
            print(f"错误：输入文件夹不存在 -> {INPUT_FOLDER}")
            return
        
        # 创建输出文件夹
        if not os.path.isdir(OUTPUT_FOLDER):
            try:
                os.makedirs(OUTPUT_FOLDER)
                print(f"已创建输出文件夹: {OUTPUT_FOLDER}")
            except OSError as e:
                print(f"错误：无法创建输出文件夹 {OUTPUT_FOLDER}。错误信息: {e}")
                return
        
        # 获取所有VTT文件
        vtt_files = [f for f in os.listdir(INPUT_FOLDER) if f.lower().endswith('.vtt')]
        
        if not vtt_files:
            print(f"在 {INPUT_FOLDER} 文件夹中没有找到VTT文件")
            return
        
        print(f"找到 {len(vtt_files)} 个VTT文件")
        
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
        print("批量处理完成！")
        print(f"成功处理: {success_count} 个文件")
        print(f"处理失败: {failed_count} 个文件")
        print(f"总计文件: {len(vtt_files)} 个")
        print("=" * 60)

def main():
    """主程序入口"""
    # 检查API配置
    if API_PROVIDER == 'deepseek' and not DEEPSEEK_CONFIG.get('api_key'):
        print("错误：请先配置DeepSeek API密钥")
        print("获取地址：https://platform.deepseek.com/")
        return
    
    if API_PROVIDER == 'glm' and not GLM_CONFIG.get('api_key'):
        print("错误：请先配置智谱GLM API密钥")
        print("获取地址：https://open.bigmodel.cn/")
        return
    
    if API_PROVIDER == 'ollama':
        print("注意：使用Ollama需要本地安装并运行ollama服务")
        print("安装地址：https://ollama.ai/")
    
    # 开始批量处理
    translator = VTTTranslator()
    translator.batch_process()

if __name__ == '__main__':
    main()
