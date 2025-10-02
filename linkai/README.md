# LinkAI VTT处理工具集

## 功能说明

本目录包含四个核心工具：

### 1. 通用VTT转Markdown处理器 (`batch_vtt_to_md.py`)

将各种主题的VTT字幕文件转换为高质量的简体中文Markdown文章。

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
- **🌟 通用主题识别**：支持9大内容分类
  - 科技、教育、生活、商业、投资理财、职场、文化、健康医疗、新闻时事
  - 智能内容分析：自动识别教程指南、经验分享、评测推荐等内容类型
  - 最多3个主题标签，避免标签过多
- 生成带YAML front matter的Markdown文件
- 支持断点续传（跳过已处理的文件）
- 批量处理，自动管理API调用频率
- **🔥 智能重试机制**
  - API超时或连接失败时自动重试（最多3次）
  - 增加超时时间至120秒，减少超时错误
  - 详细的错误统计和重试报告
  - 区分不同错误类型（超时、连接、其他）

### 2. 微信公众号文章批量爬取器 (`wechat_article_crawler.py`)

从Excel文件中读取微信公众号文章链接，批量获取文章内容并保存为Markdown格式。

**使用方法：**
```bash
# 处理所有文章
python wechat_article_crawler.py filename.xlsx

# 从第10行开始，处理20篇文章
python wechat_article_crawler.py filename.xlsx --start 10 --count 20

# 每次最多处理50篇（分批处理）
python wechat_article_crawler.py filename.xlsx --max-batch 50

# 自定义输出文件夹和延时
python wechat_article_crawler.py filename.xlsx --output custom_folder --delay 3,8
```

**功能特点：**
- 从Excel文件读取文章链接、标题、摘要、发布时间
- 自动获取微信公众号文章完整内容
- 生成有序的Markdown文件（序号+日期+标题）
- **🔥 断点续传**：已处理的文章自动跳过，支持中断后继续
- **⚡ 批量控制**：可控制起始位置、处理数量、最大批次
- **🛡️ 智能重试**：网络异常时自动重试
- **⏰ 频率控制**：可配置请求间隔，避免被限制
- **📁 文件结构**：输入 `wechat/data_setup/filename.xlsx`，输出 `wechat_filename/001_2024-01-01_文章标题.md`

**Excel文件格式要求：**
必须包含以下列：`链接`、`标题`、`摘要`、`发布时间`

### 3. 微信文章内容优化处理器 (`batch_md_processor.py`)

对已爬取的微信公众号文章进行AI内容优化和格式整理。

**使用方法：**
```bash
# 处理所有文章
python batch_md_processor.py wechat_huibenmamahaitong

# 处理第10-50篇文章
python batch_md_processor.py wechat_huibenmamahaitong --start 10 --end 50

# 处理前20篇文章
python batch_md_processor.py wechat_huibenmamahaitong --count 20

# 自定义输出目录和延时
python batch_md_processor.py wechat_huibenmamahaitong --output custom_result --delay 5,15
```

**功能特点：**
- 使用专业的育儿内容编辑提示词进行AI优化
- **🔥 内容优化**：强化育儿干货知识，弱化个人隐私描述
- **📝 格式整理**：智能分段，改善可读性，去除口语化冗余
- **🛡️ 智能重试**：API异常时自动重试，支持密钥自动切换
- **⚡ 批量控制**：可指定序号范围、处理数量
- **🔄 断点续传**：已处理文件自动跳过，支持中断后继续
- **📁 文件结构**：输入 `wechat_folder/001_date_title.md`，输出 `wechat_folder_result/001_date_title.md`

**处理效果：**
- 将口语化内容转换为流畅的书面语
- 优化段落结构和逻辑组织
- 保持原始信息完整性
- 强化育儿知识点，弱化个人隐私

### 4. VTT文件日期重命名工具 (`add_date_to_filename.py`)

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

## 📁 文件说明

- `batch_vtt_to_md.py`: VTT到Markdown的批量处理器
- `wechat_article_crawler.py`: 微信公众号文章批量爬取器
- `batch_md_processor.py`: 微信文章内容优化处理器（新增）
- `merge_md_files.py`: Markdown文件合并工具
- `api_keys.txt`: LinkAI API密钥列表
- `requirements.txt`: 项目依赖包列表
- `README.md`: 项目说明文档

## 注意事项

- 需要有效的LinkAI API密钥
- 处理大量文件时会产生API费用
- 建议先小批量测试，确认效果后再全量处理
- 脚本会自动跳过已处理的文件，支持断点续传
- **新增**：微信文章处理器使用专业育儿编辑提示词，适合育儿类内容优化

## 重试机制说明

**智能重试配置：**
- 最大重试次数：3次
- 重试间隔：5秒
- API超时时间：120秒（从原来的60秒增加）

**处理的错误类型：**
- ⏰ **超时错误**：API调用超过120秒
- 🌐 **连接错误**：网络连接失败
- ❓ **其他错误**：API响应格式异常、HTTP错误等

**重试逻辑：**
1. 遇到错误时自动重试，最多3次
2. 每次重试间隔5秒，避免过于频繁
3. 重试成功后继续处理下一个文件
4. 3次重试失败后跳过当前文件，继续处理
5. 处理完成后显示详细的重试统计报告

**示例输出：**
```
📊 重试统计:
  🔄 总重试次数: 8
  ⏰ 超时错误: 5
  🌐 连接错误: 2
  ❓ 其他错误: 1
```

## 主题分类系统

**9大主要分类：**

1. **科技**：科技、技术、AI、人工智能、机器人、自动化、数字化、互联网、软件、硬件、编程、开发
2. **教育**：教育、学习、培训、课程、教学、知识、技能、学校、大学、考试、学术
3. **生活**：生活、日常、家庭、健康、美食、旅行、运动、娱乐、时尚、购物
4. **商业**：商业、创业、企业、管理、营销、销售、品牌、商务、合作、发展
5. **投资理财**：投资、理财、金融、股票、基金、保险、银行、经济、财富、资产
6. **职场**：职场、工作、求职、简历、面试、职业、晋升、技能、能力、经验
7. **文化**：文化、艺术、历史、传统、民俗、音乐、电影、书籍、文学、哲学
8. **健康医疗**：健康、医疗、养生、疾病、治疗、药物、医院、医生、保健、营养
9. **新闻时事**：新闻、时事、政治、社会、国际、政策、法律、环境、气候、事件

**智能内容分析（备用分类）：**
- **深度内容**：内容长度超过2000字符
- **教程指南**：包含"如何"、"怎么"、"方法"、"技巧"、"教程"等关键词
- **经验分享**：包含"分享"、"经验"、"心得"、"感受"、"体验"等关键词
- **评测推荐**：包含"评测"、"测评"、"对比"、"推荐"、"选择"等关键词
- **综合内容**：无法归类的其他内容

**分类特点：**
- 最多返回3个主题标签，避免标签冗余
- 优先匹配具体分类，再使用备用分类
- 基于标题和内容的综合分析
