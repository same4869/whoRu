# 批量VTT字幕翻译器使用说明

## 功能特点

✨ **多API支持**：集成4种免费大模型API选项
🚀 **智能分片**：自动处理长文本，避免token限制  
🔄 **自动重试**：网络异常自动重试，提高成功率
📝 **格式优化**：输出格式化的Markdown文件
🎯 **批量处理**：一键处理整个文件夹的字幕文件

## 支持的免费API

### 1. Ollama (推荐 - 完全免费)
- **优势**：完全免费，本地运行，隐私安全
- **安装**：访问 [https://ollama.ai/](https://ollama.ai/) 下载安装
- **模型推荐**：`qwen2.5:7b` 或 `llama3.1:8b`

```bash
# 安装ollama后，下载模型
ollama pull qwen2.5:7b
# 或
ollama pull llama3.1:8b
```

### 2. DeepSeek API (免费额度)
- **优势**：效果好，每月有免费额度
- **注册**：[https://platform.deepseek.com/](https://platform.deepseek.com/)
- **免费额度**：每月足够个人使用

### 3. 智谱清言 GLM (免费额度)
- **优势**：中文效果好，有免费额度
- **注册**：[https://open.bigmodel.cn/](https://open.bigmodel.cn/)
- **模型**：`glm-4-flash`

### 4. 自定义API
- 支持任何兼容OpenAI格式的API端点

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置API

编辑 `batch_vtt_translator.py` 文件的配置区：

```python
# 选择API提供商
API_PROVIDER = 'ollama'  # 可选: 'deepseek', 'ollama', 'glm', 'custom'

# 如果使用DeepSeek，填入API密钥
DEEPSEEK_CONFIG = {
    'api_key': 'YOUR_DEEPSEEK_API_KEY',  # 替换为您的密钥
    # ...其他配置
}

# 如果使用智谱GLM，填入API密钥
GLM_CONFIG = {
    'api_key': 'YOUR_GLM_API_KEY',  # 替换为您的密钥
    # ...其他配置
}
```

### 3. 运行脚本

```bash
python batch_vtt_translator.py
```

## 详细配置说明

### API选择建议

| API | 成本 | 效果 | 速度 | 推荐指数 |
|-----|------|------|------|----------|
| Ollama | 免费 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| DeepSeek | 免费额度 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| 智谱GLM | 免费额度 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |

### 配置参数说明

```python
# 文件路径配置
INPUT_FOLDER = 'output_result'    # VTT文件输入文件夹
OUTPUT_FOLDER = 'translated_md'   # Markdown文件输出文件夹

# 处理参数
MAX_TOKENS_PER_CHUNK = 2500      # 每个分片的最大token数
REQUEST_TIMEOUT = 300            # API请求超时时间(秒)
RETRY_ATTEMPTS = 3               # 失败重试次数
RETRY_DELAY = 2                  # 重试间隔(秒)
```

## 使用流程

1. **准备VTT文件**：确保 `output_result` 文件夹中有VTT字幕文件
2. **选择API**：根据需要修改 `API_PROVIDER` 配置
3. **配置密钥**：如果使用需要密钥的API，请填入相应配置
4. **运行脚本**：执行 `python batch_vtt_translator.py`
5. **查看结果**：处理完成的Markdown文件会保存在 `translated_md` 文件夹

## 输出示例

脚本会将VTT字幕文件转换为格式化的Markdown文章：

**输入文件**：`加密貨幣短線交易真的能賺錢嗎？.zh.vtt`
**输出文件**：`加密貨幣短線交易真的能賺錢嗎？.zh.md`

输出内容会是整理后的文章格式，包含：
- 自然的段落划分
- 关键词**加粗**处理
- 流畅的中文表达
- 清晰的逻辑结构

## 故障排除

### 常见问题

1. **API调用失败**
   - 检查网络连接
   - 验证API密钥是否正确
   - 确认API额度是否用完

2. **Ollama连接失败**
   - 确认ollama服务正在运行：`ollama serve`
   - 检查模型是否已下载：`ollama list`
   - 验证端口是否正确（默认11434）

3. **文件解析错误**
   - 确认VTT文件格式正确
   - 检查文件编码是否为UTF-8

4. **内存不足**
   - 减小 `MAX_TOKENS_PER_CHUNK` 值
   - 逐个处理大文件

### 性能优化建议

- **Ollama**：使用7B模型在大多数电脑上都能流畅运行
- **网络API**：设置合理的重试间隔，避免触发限流
- **大文件**：适当调整分片大小，平衡处理效果和速度

## 高级用法

### 自定义提示词

可以修改 `SYSTEM_PROMPT` 来调整输出风格：

```python
SYSTEM_PROMPT = """
你的自定义提示词...
"""
```

### 批量处理特定文件

可以修改代码来处理特定类型或名称的文件：

```python
# 只处理包含特定关键词的文件
vtt_files = [f for f in os.listdir(INPUT_FOLDER) 
             if f.lower().endswith('.vtt') and 'bitcoin' in f.lower()]
```

## 技术支持

如果遇到问题，请检查：
1. Python版本（推荐3.8+）
2. 依赖包版本
3. API服务状态
4. 网络连接情况

---

**注意**：使用任何API服务时，请遵守相应的使用条款和限制。
