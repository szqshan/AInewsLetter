# 🤖 Claude Newsroom 新闻爬虫

> 基于HTML解析的稳定爬虫工具，从Claude官方newsroom爬取新闻并存储到本地，支持MinIO存储架构集成

## 📋 项目概述

### 🎯 核心功能
- ✅ **智能爬取**: 从Claude newsroom自动爬取最新新闻
- ✅ **媒体下载**: 自动下载并本地存储图片文件
- ✅ **数据清洗**: 自动提取标题、分类、日期等结构化信息
- ✅ **增量更新**: 智能检测新增内容，避免重复爬取
- ✅ **存储集成**: 支持上传到MinIO + PostgreSQL + Elasticsearch
- ✅ **定时调度**: 支持每日自动爬取和上传

### 🌐 数据源
**Claude官方新闻室**: https://www.anthropic.com/news

## ✅ 已验证功能

### 🕷️ 爬虫功能 (spider.py)
- **HTML解析**: 基于BeautifulSoup的稳定解析器
- **智能提取**: 自动识别标题、分类、日期、正文内容
- **媒体下载**: 自动下载并本地存储图片文件
- **错误处理**: 网络超时、解析失败的优雅处理
- **增量爬取**: 基于文章URL避免重复下载
- **可配置**: 支持自定义爬取数量、延迟等参数

### 📤 上传功能 (uploader.py)
- **MinIO集成**: 上传到对象存储系统
- **PostgreSQL**: 保存结构化元数据
- **Elasticsearch**: 建立全文搜索索引
- **批量处理**: 支持批量上传所有本地文章

### 🎮 运行脚本 (run_crawler.py)
- **一键运行**: 同时执行爬取和上传
- **灵活模式**: 支持仅爬取或仅上传
- **参数控制**: 可控制文章数量、强制更新等

## 🗂️ 项目目录结构

```
ai_news/Claude_newsroom/
├── 📄 spider.py                    # 主爬虫脚本
├── 📄 uploader.py                  # MinIO上传脚本
├── 📄 run_crawler.py               # 一键运行脚本
├── 📄 config.json                  # 配置文件
├── 📄 requirements.txt             # 依赖包
├── 📄 README.md                    # 说明文档
└── 📊 crawled_data/                # 本地数据存储
    └── articles/                   # 新闻文章目录
        └── {slug}/                 # 按文章slug组织
            ├── content.md          # Markdown内容
            ├── metadata.json       # 元数据JSON
            └── media/              # 媒体文件目录
                ├── *.jpg           # 图片文件
                ├── *.png           # 图片文件
                └── *.svg           # 矢量图文件
```

## 🚀 使用方式

### 快速开始
```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 测试爬取（推荐先试用）
python spider.py --max 3

# 3. 一键运行（爬取+上传）
python run_crawler.py --max 10
```

### 基础命令
```bash
# 爬取新闻（默认最多50篇）
python spider.py

# 上传数据到MinIO
python uploader.py

# 一键执行（推荐）
python run_crawler.py
```

### 高级参数
```bash
# 限制爬取数量
python spider.py --max 10

# 强制更新已存在文章
python spider.py --force

# 使用自定义配置
python spider.py --config custom.json

# 仅爬取不上传
python run_crawler.py --crawl-only --max 20

# 仅上传不爬取  
python run_crawler.py --upload-only
```

### 实际运行示例
```bash
# 测试运行 - 只爬3篇文章
python spider.py --max 3

# 正式运行 - 爬取最新20篇文章
python run_crawler.py --max 20

# 强制更新所有文章
python run_crawler.py --force --max 50
```

## ⚙️ 配置文件 (config.json)

```json
{
  "crawler": {
    "delay": 2,                    // 请求间隔（秒）
    "timeout": 30,                 // 请求超时（秒）
    "max_articles": 50             // 最大爬取数量
  },
  "media": {
    "download_images": true,       // 是否下载图片
    "image_timeout": 15,           // 图片下载超时
    "max_image_size": 10485760     // 最大图片大小（10MB）
  },
  "storage": {
    "data_dir": "crawled_data",    // 数据存储目录
    "articles_dir": "articles"     // 文章子目录
  }
}
```

## 📊 数据格式

### metadata.json 格式
```json
{
  "url": "https://www.anthropic.com/news/claude-opus-4-1",
  "title": "Claude Opus 4.1",
  "category": "Announcements",
  "date": "Aug 5, 2025",
  "content": "文章正文内容...",
  "images": [
    {
      "url": "原始图片URL",
      "alt": "图片描述",
      "filename": "本地文件名",
      "local_path": "本地存储路径"
    }
  ],
  "crawl_time": "2025-08-17T15:23:32.976308",
  "slug": "claude-opus-4-1"
}
```

### content.md 格式
```markdown
# Claude Opus 4.1

**分类**: Announcements  
**发布日期**: Aug 5, 2025  
**来源**: https://www.anthropic.com/news/claude-opus-4-1  
**爬取时间**: 2025-08-17T15:23:32.976308

---

文章正文内容（Markdown格式）...

## 相关图片

![图片描述](media/image.jpg)
```

## 🔄 定时任务设置

### Linux/Mac Cron
```bash
# 每天早上8点执行
0 8 * * * cd /path/to/Claude_newsroom && python run_crawler.py --max 20

# 编辑crontab
crontab -e
```

### Windows 任务计划
```batch
# 创建批处理文件 run_daily.bat
cd /d "D:\path\to\spider\ai_news\Claude_newsroom"
python run_crawler.py --max 20

# 然后在任务计划程序中设置定时执行
```

## 🔧 MinIO存储架构集成

### 存储层次
1. **本地存储**: `crawled_data/` 目录
2. **MinIO对象存储**: `claude-newsroom` bucket
3. **PostgreSQL**: 元数据表 `claude_newsroom_articles`
4. **Elasticsearch**: 全文搜索索引 `claude_newsroom_articles`

### 上传流程
```
本地文章 → MinIO对象存储 → PostgreSQL元数据 → Elasticsearch索引
```

## 📈 运行日志示例

```
🤖 Claude Newsroom 爬虫启动
目标: https://www.anthropic.com/news
找到 50 篇新闻

[1/3] 处理文章...
正在爬取: https://www.anthropic.com/news/claude-opus-4-1
下载图片: a97733b3607b54a30778eb89de08afd9e02b9fb3-1000x1000.svg
下载图片: image_e02d270d.jpg
保存文章: Claude Opus 4.1

[2/3] 处理文章...
正在爬取: https://www.anthropic.com/news/the-anthropic-economic-index
下载图片: c1ef4c0b6882dfe985555b52999d370ea88a3c50-1000x1000.svg
保存文章: The Anthropic Economic Index

✅ 爬取完成!
成功: 3 篇
失败: 0 篇
数据保存位置: crawled_data\articles
```

## 🛠️ 技术特点

### 稳定性设计
- **HTML解析**: 使用BeautifulSoup，兼容性强
- **重试机制**: 网络请求失败自动重试
- **增量更新**: 避免重复爬取相同文章
- **优雅降级**: 单个文章失败不影响整体流程

### 可扩展性
- **模块化设计**: 爬虫、上传、配置分离
- **可配置参数**: 支持自定义各种爬取参数
- **存储抽象**: 易于集成其他存储系统
- **格式标准**: 生成标准化的Markdown和JSON

## 🐛 常见问题

### Q: 爬虫运行很慢？
A: 可以调整 `config.json` 中的 `delay` 参数，但建议保持2秒以上避免被限制。

### Q: 图片下载失败？
A: 检查网络连接，或在 `config.json` 中设置 `download_images: false` 跳过图片下载。

### Q: MinIO上传失败？
A: 确保MinIO连接器服务正常运行，或使用 `--crawl-only` 参数仅爬取数据。

### Q: 如何查看爬取的数据？
A: 数据保存在 `crawled_data/articles/` 目录下，每篇文章一个文件夹。

## 📝 开发说明

### 依赖包
- `requests`: HTTP请求
- `beautifulsoup4`: HTML解析
- `lxml`: XML解析器
- `python-dateutil`: 日期解析

### 代码结构
- **spider.py**: 核心爬虫逻辑
- **uploader.py**: 存储系统集成
- **run_crawler.py**: 便捷运行脚本
- **config.json**: 配置管理

---

## 🎉 使用总结

Claude Newsroom爬虫已经完成开发并验证可用，主要特点：

1. **✅ 已验证可用**: 能成功爬取Claude官方新闻
2. **✅ 数据完整**: 自动提取标题、分类、日期、正文、图片
3. **✅ 存储规范**: 生成标准化Markdown和JSON格式
4. **✅ 易于使用**: 支持一键运行和灵活配置
5. **✅ 集成友好**: 可集成到现有MinIO存储架构

开始使用：`python spider.py --max 3` 🚀
