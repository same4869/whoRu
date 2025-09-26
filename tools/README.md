# Tools 工具集

这个目录包含用于处理文件的实用工具脚本。

## 工具列表

### 1. Markdown文件日期重命名工具 (`add_date_to_md_filename.py`)

从Markdown文件的YAML前置数据中提取发布日期，并将日期添加到文件名最前面，使文件能够按时间顺序排序。

**功能特点：**
- 从MD文件的YAML前置数据中提取`publish_date`字段
- 支持多种日期格式解析（如：2024年08月10日、2024-08-10等）
- 转换为标准的YYYY-MM-DD格式作为文件名前缀
- 预览模式确保安全操作
- 自动跳过已包含日期前缀的文件
- 支持文件名中已有日期前缀的更新

**使用方法：**
```bash
# 预览模式（不实际重命名）
python add_date_to_md_filename.py

# 执行重命名
python add_date_to_md_filename.py -e
```

**处理效果：**
- 原文件名：`财富自由的终极密码！越早做到这几点，越容易更早实现财富自由。.zh.md`
- 新文件名：`2024-08-10_财富自由的终极密码！越早做到这几点，越容易更早实现财富自由。.zh.md`

### 2. VTT文件日期重命名工具 (`batch_rename_with_dates.py`)

为VTT字幕文件添加日期前缀的批量处理工具。

**功能特点：**
- 从VTT文件内容中提取视频发布时间
- 批量处理，支持大量文件
- 高效的文件读取（只读取前几行）
- 预览和执行模式

**使用方法：**
```bash
# 预览模式
python batch_rename_with_dates.py

# 执行重命名  
python batch_rename_with_dates.py -e
```

## 目标目录

- **MD文件处理目录**：`D:\xwang\git_work_wx\whoRu\output_result_md_linkai`
- **VTT文件处理目录**：`D:\xwang\git_work_wx\whoRu\output_result`

## 注意事项

1. **备份重要文件**：重命名前建议备份重要文件
2. **预览优先**：建议先使用预览模式查看重命名计划
3. **文件冲突**：如果目标文件名已存在，脚本会跳过该文件
4. **编码支持**：脚本使用UTF-8编码，支持中文文件名和内容

## 技术细节

### 支持的日期格式

- `2024年08月10日`（中文格式）
- `2024-08-10`（标准格式）
- `2024/08/10`（斜杠格式）
- `08/10/2024`（美式格式）

### YAML前置数据示例

```yaml
---
title: 财富自由的终极密码
publish_date: 2024年08月10日
topics: 比特币, 投资策略, 市场分析
word_count: 1713
processed_by: LinkAI
processed_at: 2025-09-26 16:15:41
---
```

### 输出格式

所有日期都统一转换为 `YYYY-MM-DD` 格式，确保文件按时间顺序排序。
