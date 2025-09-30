# 微信公众号文章爬取工具

发现有个用的
https://docs.wxdown.online/tutorials/export-article-links.html


简洁、高效的微信公众号文章爬取工具，支持智能重试和实时保存。

## 功能特性

- ✅ **智能重试**: 频率控制错误自动等待10分钟，网络错误递增重试
- ✅ **实时保存**: 每获取一批文章立即保存，数据永不丢失  
- ✅ **随机延时**: 10-30秒随机间隔，避免被检测
- ✅ **无限重试**: 每个请求最多重试10000次，确保成功
- ✅ **配置简单**: URL和Cookie预设在配置文件中

## 快速开始

### 1. 安装依赖
```bash
pip install requests
```

### 2. 运行爬虫
```bash
# 测试模式（只获取2批数据）
python run.py --test

# 获取所有文章
python run.py
```

## 文件说明

- `mp_client.py`: 核心爬虫客户端
- `config.py`: 配置文件（URL和Cookie）
- `run.py`: 主运行脚本
- `wechat_articles.csv`: 输出的文章数据

## 更新配置

如需更新Cookie或URL，编辑 `config.py` 文件：

```python
CONFIG = {
    "url": "你的新URL",
    "cookie": "你的新Cookie",
    "rate_limit_delay": (10.0, 30.0),  # 可调整延时范围
}
```

## 输出格式

CSV文件包含以下字段：
- `title`: 文章标题
- `link`: 文章链接  
- `create_time`: 创建时间
- `update_time`: 更新时间

## 注意事项

1. Cookie会过期，需要定期更新
2. 建议先用测试模式验证配置正确性
3. 程序会自动处理频率控制，无需人工干预
4. 所有数据实时保存，程序中断不会丢失已获取的数据

