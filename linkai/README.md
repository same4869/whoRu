# LinkAI VTT处理工具集

## 功能说明

本目录包含两个核心工具：

### 1. 批量VTT转Markdown处理器 (`batch_vtt_to_md.py`)

将VTT字幕文件转换为高质量的简体中文Markdown文章。

**使用方法：**
```bash
# 处理前5个文件
python batch_vtt_to_md.py 5

# 处理前10个文件  
python batch_vtt_to_md.py 10

# 处理所有文件
python batch_vtt_to_md.py 0
# 或
python batch_vtt_to_md.py
```

**功能特点：**
- 使用LinkAI API进行高质量翻译和内容整理
- 自动提取视频标题和发布日期
- 智能识别主题标签
- 生成带YAML front matter的Markdown文件
- 支持断点续传（跳过已处理的文件）
- 批量处理，自动管理API调用频率

### 2. VTT文件日期重命名工具 (`add_date_to_filename.py`)

为VTT文件添加日期前缀，使文件能够按时间顺序排序。

**使用方法：**
```bash
# 预览模式（不实际重命名）
python add_date_to_filename.py

# 执行重命名
python add_date_to_filename.py -e
```

**功能特点：**
- 从VTT文件内容中提取发布日期
- 添加YYYY-MM-DD格式的日期前缀
- 预览模式确保安全操作
- 自动跳过已包含日期的文件

### 3. Markdown文件合并工具 (`merge_md_files.py`)

将大量Markdown文件按日期范围合并，每个合并文件控制在指定行数以内。

**使用方法：**
```bash
# 预览模式（默认1000行限制）
python merge_md_files.py

# 执行合并
python merge_md_files.py -e

# 自定义行数限制
python merge_md_files.py -e -l 800
```

**功能特点：**
- 按日期范围智能分组合并
- 控制每个合并文件的行数（默认1000行）
- 生成包含目录的合并文件
- 保留原文件的YAML前置数据
- 文件名包含日期范围和文章数量
- 预览模式确保安全操作

## 工作流程建议

1. **首先重命名文件**（可选）：
   ```bash
   python add_date_to_filename.py -e
   ```

2. **然后批量处理**：
   ```bash
   # 先测试少量文件
   python batch_vtt_to_md.py 3
   
   # 确认效果后处理全部
   python batch_vtt_to_md.py 0
   ```

3. **最后合并文件**（可选）：
   ```bash
   # 预览合并计划
   python merge_md_files.py
   
   # 执行合并
   python merge_md_files.py -e
   ```

## 输出目录

- VTT文件目录：`D:\xwang\git_work_wx\whoRu\output_result`
- Markdown输出目录：`D:\xwang\git_work_wx\whoRu\output_result_md_linkai`
- 合并文件输出目录：`D:\xwang\git_work_wx\whoRu\output_result_md_merged`

## 注意事项

- 需要有效的LinkAI API密钥
- 处理大量文件时会产生API费用
- 建议先小批量测试，确认效果后再全量处理
- 脚本会自动跳过已处理的文件，支持断点续传
