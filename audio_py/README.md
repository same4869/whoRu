# 音频转文本转Markdown自动化工具

一键将音频文件转录为文本，并通过AI整理为高质量的Markdown文章。

## 📋 目录

- [快速开始](#-快速开始)
- [功能特点](#-功能特点)
- [使用方法](#-使用方法)
- [配置说明](#-配置说明)
- [使用示例](#-使用示例)
- [常见问题](#-常见问题)
- [高级技巧](#-高级技巧)

---

## 🚀 快速开始

### 一分钟上手

```bash
# 1. 安装Whisper（首次使用）
pip install openai-whisper

# 2. 准备音频文件
# 将音频文件（E373.m4a等）放入 ../audios 目录

# 3. 配置API密钥
# 在 ../linkai/api_keys.txt 添加LinkAI密钥

# 4. 运行处理
cd audio_py
python audio_transcribe.py

# 完成！查看结果：
# - 转录文本: ../audios_txt/E373.txt
# - 整理文章: ./audio_md/E373.md
```

### 常用命令

```bash
# 处理所有音频
python audio_transcribe.py

# 只处理前5个文件（测试）
python audio_transcribe.py -n 5

# 处理E10到E20
python audio_transcribe.py -r 10-20

# 只做AI整理（跳过转录）
python audio_transcribe.py --skip-whisper
```

---

## ✨ 功能特点

- 🎤 **自动转录**：使用Whisper AI将音频转为文字
- 🤖 **AI整理**：通过LinkAI将文本整理为结构化文章
- 📝 **智能重命名**：自动清理文件名（去除中文，只保留编号）
- 🎯 **灵活筛选**：支持按数量或范围处理文件
- ⚡ **断点续传**：自动跳过已处理文件
- 🧹 **自动清理**：处理完成后清理临时文件

### 支持格式

**输入**：mp3、mp4、m4a、wav、flac、aac  
**输出**：Markdown（带YAML frontmatter）

---

## 📁 目录结构

```
whoRu/
├── audios/                    # 音频文件输入目录
│   ├── E373.m4a
│   └── E374.反直觉理财....m4a
├── audios_txt/                # Whisper转录文本输出（自动创建）
│   ├── E373.txt
│   └── E374.txt
├── audio_py/                  # 脚本目录（当前目录）
│   ├── audio_transcribe.py   # 主脚本
│   ├── README.md             # 本文档
│   ├── audio_md/             # Markdown输出（自动创建）
│   │   ├── E373.md
│   │   └── E374.md
│   └── temp_audios/          # 临时文件（自动清理）
└── linkai/
    ├── batch_txt_to_md.py    # AI文本处理脚本
    └── api_keys.txt          # API密钥
```

---

## 🎯 使用方法

### 1. 环境准备

#### 安装Whisper
```bash
pip install openai-whisper
```

#### 准备API密钥
在 `linkai/api_keys.txt` 文件中添加LinkAI API密钥（每行一个）：
```
your-api-key-1
your-api-key-2
```

### 2. 准备音频文件

将音频文件放入 `audios` 目录：

✅ **正确格式**：
- `E373.m4a`
- `E374.反直觉理财：不做预算.m4a`
- `e375.mp3`（自动转大写）

❌ **错误格式**：
- `audio123.m4a`（缺少E前缀）
- `373.m4a`（缺少E前缀）

### 3. 运行处理

```bash
cd audio_py

# 处理所有音频文件
python audio_transcribe.py

# 只处理前5个文件
python audio_transcribe.py -n 5

# 处理E10到E20范围
python audio_transcribe.py -r 10-20

# 范围优先级高于数量
python audio_transcribe.py -r 10-20 -n 5  # 实际处理E10-E20

# 跳过Whisper转录，直接处理现有txt
python audio_transcribe.py --skip-whisper

# 保留临时文件（调试用）
python audio_transcribe.py --keep-temp
```

### 4. 查看结果

```bash
# 转录文本
cat ../audios_txt/E373.txt

# 整理文章
cat audio_md/E373.md
```

---

## ⚙️ 配置说明

### 命令行参数

| 参数 | 说明 | 默认值 | 示例 |
|------|------|--------|------|
| `-n`, `--number` | 处理文件数量 | -1（全部） | `-n 5` |
| `-r`, `--range` | 处理范围（E编号） | 无 | `-r 10-20` |
| `--skip-whisper` | 跳过Whisper转录 | False | `--skip-whisper` |
| `--keep-temp` | 保留临时文件 | False | `--keep-temp` |

### 脚本内配置

在 `audio_transcribe.py` 中可修改：

```python
# Whisper配置
WHISPER_MODEL = 'small'       # 模型大小：tiny, base, small, medium, large
WHISPER_LANGUAGE = 'Chinese'  # 转录语言
WHISPER_OUTPUT_FORMAT = 'txt' # 输出格式

# 目录配置
AUDIO_FOLDER = r'../audios'          # 音频输入
TXT_FOLDER = r'../audios_txt'        # 文本输出
MD_FOLDER = r'./audio_md'            # Markdown输出
```

### Whisper模型选择

| 模型 | 大小 | 速度 | 准确度 | 推荐场景 |
|------|------|------|--------|----------|
| tiny | 39 MB | 最快 | 低 | 快速测试 |
| base | 74 MB | 快 | 中 | 日常使用 |
| **small** | 244 MB | 中 | 高 | **推荐**（平衡） |
| medium | 769 MB | 慢 | 很高 | 高质量要求 |
| large | 1550 MB | 最慢 | 最高 | 专业场景 |

---

## 📚 使用示例

### 示例1：处理单个音频文件

```bash
# 测试处理1个文件
python audio_transcribe.py -n 1
```

### 示例2：批量处理

```bash
# 先测试3个
python audio_transcribe.py -n 3

# 满意后处理全部
python audio_transcribe.py
```

### 示例3：处理特定范围

```bash
# 只处理E370-E375
python audio_transcribe.py -r 370-375
```

### 示例4：断点续传

```bash
# 第一次运行（处理了3个文件后中断）
python audio_transcribe.py
# Ctrl+C 中断

# 第二次运行（自动跳过已处理的文件）
python audio_transcribe.py
# 自动跳过已有的txt和md文件
```

### 示例5：只做AI整理

```bash
# 已经有txt文件，只需要AI整理
python audio_transcribe.py --skip-whisper
```

### 示例6：分批处理

```bash
# 100个文件，分5批处理
python audio_transcribe.py -r 1-20
python audio_transcribe.py -r 21-40
python audio_transcribe.py -r 41-60
python audio_transcribe.py -r 61-80
python audio_transcribe.py -r 81-100
```

---

## ❓ 常见问题

### Q1: 提示"Whisper未安装"？

```bash
pip install openai-whisper

# 验证安装
whisper --help
```

### Q2: 找不到音频文件？

检查：
1. 文件在 `../audios` 目录
2. 文件名包含`E`和数字（如E373）
3. 扩展名是mp3/mp4/m4a等支持格式

### Q3: API密钥错误？

检查 `linkai/api_keys.txt`：
1. 文件存在
2. 包含有效密钥
3. 每行一个密钥

### Q4: 处理太慢？

降低模型大小：
```python
# 在 audio_transcribe.py 中修改
WHISPER_MODEL = 'base'  # 改为base（快2倍）或tiny（快5倍）
```

### Q5: 内存不足？

使用更小的模型：
```python
WHISPER_MODEL = 'tiny'  # 最小模型，内存占用最少
```

### Q6: 转录质量不好？

使用更大的模型：
```python
WHISPER_MODEL = 'medium'  # 或 'large'
```

### Q7: 文件命名问题？

脚本会自动处理：
- `E373.反直觉理财.m4a` → `E373.m4a`
- `e374.mp3` → `E374.mp3`（自动大写）
- `Episode375.m4a` → `E375.m4a`

---

## 💡 高级技巧

### 1. 处理时间预估

| 音频时长 | Whisper转录 | AI整理 | 总计 |
|---------|------------|--------|------|
| 30分钟  | 3-8分钟    | 20秒   | 约5分钟 |
| 60分钟  | 6-15分钟   | 30秒   | 约10分钟 |
| 10个1小时 | 60-150分钟 | 5分钟  | 约2小时 |

💡 **建议**：在空闲时段批量处理

### 2. 性能优化

```python
# 方式1：降低模型
WHISPER_MODEL = 'base'  # 速度提升2倍

# 方式2：使用GPU（如果可用）
# Whisper会自动检测并使用GPU
```

### 3. 并行处理

```bash
# 分成两批，开两个终端同时处理
# 终端1
python audio_transcribe.py -r 1-50

# 终端2
python audio_transcribe.py -r 51-100
```

### 4. 调试模式

```bash
# 保留临时文件查看
python audio_transcribe.py -n 1 --keep-temp

# 查看临时文件
ls temp_audios/

# 手动测试Whisper
whisper temp_audios/E373.m4a --language Chinese --model small
```

### 5. 重新整理文章

```bash
# 保留转录，重新AI整理
# 1. 删除旧的md文件
rm audio_md/*.md

# 2. 重新整理
python audio_transcribe.py --skip-whisper
```

### 6. 处理工作流

```bash
# 完整流程
# 1. 准备音频
cp ~/Downloads/*.m4a ../audios/

# 2. 检查文件
ls ../audios/

# 3. 测试处理
python audio_transcribe.py -n 1

# 4. 批量处理
python audio_transcribe.py

# 5. 添加日期（可选）
cd ../tools
python add_date_to_md_filename.py -e

# 6. 合并文章（可选）
cd ../linkai
python merge_md_files.py -e
```

---

## 📊 处理流程

```
┌─────────────┐
│  音频文件   │ (audios/*.m4a)
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ 文件名清理  │ (去除中文，保留E编号)
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Whisper转录 │ → audios_txt/E373.txt
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  AI整理文章 │ (batch_txt_to_md.py)
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Markdown   │ → audio_md/E373.md
└─────────────┘
```

---

## 📝 输出格式

### Whisper转录输出（txt）

```
大家好，欢迎收听本期节目。今天我们要聊的话题是...
[完整的转录文本]
```

### AI整理输出（md）

```markdown
---
title: E373
publish_date: 2024年10月29日
topics: 投资理财, 商业
word_count: 5000
processed_by: LinkAI
processed_at: 2024-10-29 15:30:00
---

# E373

**发布时间**: 2024年10月29日  
**主要话题**: 投资理财, 商业

---

## 核心观点

[AI整理后的结构化内容]

---

*本文由LinkAI智能助手整理发布，内容仅供参考*
```

---

## 🔗 相关工具

本项目中的其他工具：

- `linkai/batch_vtt_to_md.py` - VTT字幕转Markdown
- `linkai/batch_txt_to_md.py` - TXT文本转Markdown
- `tools/add_date_to_md_filename.py` - 为MD文件添加日期
- `linkai/merge_md_files.py` - 合并MD文件

---

## 🚨 注意事项

1. **硬件要求**：Whisper需要较好的CPU/GPU，推荐至少8GB内存
2. **时间成本**：音频转录很耗时，建议晚上或闲时处理
3. **API成本**：每个文件消耗一次LinkAI API调用
4. **存储空间**：临时文件和输出文件会占用额外空间
5. **文件备份**：处理前建议备份原始音频文件

---

## 📞 获取帮助

### 命令行帮助
```bash
python audio_transcribe.py --help
```

### 查看日志
脚本会输出详细的处理日志，包括：
- 文件处理进度
- Whisper转录状态
- API调用结果
- 错误信息

---

## 📅 更新日志

### v1.0.0 (2024-10-29)
- ✨ 首次发布
- 🎤 支持Whisper自动转录
- 🤖 集成LinkAI智能整理
- 🎯 支持范围和数量筛选
- 🧹 自动清理临时文件

---

**祝使用愉快！🎉**
