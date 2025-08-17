# 🤖 Claude Newsroom 新闻爬虫

> 简化版新闻爬虫工具，每天定时从Claude官方newsroom爬取新闻并存储到本地，集成现有MinIO存储架构

## 📋 项目概述

### 🎯 核心功能
- ✅ **爬虫脚本**: 从Claude newsroom爬取新闻并本地存储 
- ✅ **媒体下载**: 自动下载图片等媒体文件
- ✅ **上传脚本**: 单独的上传脚本，集成到现有MinIO存储架构
- ✅ **定时调度**: 支持每日自动爬取和上传
- ✅ **增量更新**: 智能检测新增内容，避免重复爬取
- ✅ **数据清洗**: 自动提取标题、分类、日期等结构化信息

### 🌐 数据源
**Claude官方新闻室**: https://www.anthropic.com/news

## ✅ 已完成功能

### 🕷️ 爬虫功能 (spider.py)
- **HTML解析**: 基于BeautifulSoup的稳定解析器
- **智能提取**: 自动识别标题、分类、日期、正文内容
- **媒体下载**: 自动下载并本地存储图片文件
- **错误处理**: 网络超时、解析失败的优雅处理
- **增量爬取**: 基于文章URL避免重复下载
- **可配置**: 支持自定义爬取数量、延迟等参数

### 📤 上传功能 (uploader.py)
- **MinIO集成**: 上传到对象存储
- **PostgreSQL**: 保存结构化元数据
- **Elasticsearch**: 全文搜索索引
- **批量处理**: 支持批量上传所有本地文章

### 🎮 运行脚本 (run_crawler.py)
- **一键运行**: 同时执行爬取和上传
- **灵活模式**: 支持仅爬取或仅上传
- **参数控制**: 可控制文章数量、强制更新等

## 🗂️ 项目目录结构

```
ai_news/Claude_newsroom/
├── 📄 spider.py                    # 主爬虫脚本
├── 📄 uploader.py                  # 上传脚本
├── 📄 config.json                  # 配置文件
├── 📄 requirements.txt             # 依赖包
├── 📄 README.md                    # 说明文档
├── 📊 crawled_data/                # 本地数据存储
│   └── articles/                   # 新闻文章目录
│       └── {news_id}/             # 按新闻ID组织
│           ├── content.md         # Markdown内容
│           ├── metadata.json      # 元数据
│           └── media/             # 媒体文件
│               ├── images/        # 图片
│               └── videos/        # 视频
└── 📄 run_daily.sh                # 定时运行脚本
```

## 🔧 核心脚本功能

### 1. spider.py - 主爬虫脚本
- 爬取 https://www.anthropic.com/news
- 解析新闻列表和详细内容
- 下载媒体文件到本地
- 生成标准化 content.md 和 metadata.json
- 支持增量更新和断点续传

### 2. uploader.py - 上传脚本
- 扫描 crawled_data 目录
- 上传到现有 MinIO 存储系统
- 集成 PostgreSQL 元数据记录
- 建立 Elasticsearch 索引
- 复用现有存储架构 API

## 🚀 使用方式

### 基础命令
```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 爬取新闻
python spider.py --max-results 20

# 3. 上传到存储系统
python uploader.py --source crawled_data

# 4. 定时任务 (每天执行)
./run_daily.sh
```

### 高级参数
```bash
# 爬取最新10篇新闻并下载媒体
python spider.py --max-results 10 --download-media

# 增量爬取 (只获取新增内容)
python spider.py --incremental

# 上传指定目录到MinIO
python uploader.py --source crawled_data --bucket claude-newsroom
```

## ⚙️ 配置文件

### config.json
```json
{
  "crawler": {
    "base_url": "https://www.anthropic.com/news",
    "output_dir": "crawled_data",
    "max_results": 50,
    "download_media": true,
    "delay": 2,
    "user_agent": "Mozilla/5.0 (Claude News Crawler)"
  },
  "media": {
    "download_images": true,
    "download_videos": true,
    "max_file_size": "50MB",
    "supported_formats": ["jpg", "png", "gif", "webp", "mp4", "webm"]
  },
  "storage": {
    "bucket_name": "claude-newsroom",
    "minio_api": "http://localhost:9011",
    "public_base_url": "http://60.205.160.74:9000",
    "source_id": "claude_newsroom"
  }
}
```

## 📊 数据格式标准

### content.md 格式
```markdown
# {新闻标题}

## 基本信息
- **新闻ID**: {唯一标识}
- **发布日期**: {发布日期}
- **更新时间**: {最后更新时间}
- **作者**: {作者信息}
- **分类**: {新闻分类}

## 链接
- **原文链接**: {Anthropic官网链接}
- **媒体文件**: {本地媒体文件列表}

## 摘要
{新闻摘要内容}

## 正文内容
{完整新闻内容，包含本地媒体文件引用}

## 处理信息
- **爬取时间**: {处理时间戳}
- **字数统计**: {字数}
- **媒体文件数**: {媒体文件数量}
- **内容哈希**: {文件哈希}
```

### metadata.json 结构
```json
{
  "id": "unique_news_identifier",
  "title": "新闻标题",
  "url": "https://www.anthropic.com/news/article-url",
  "publish_date": "2025-01-17T10:00:00Z",
  "author": "Anthropic Team",
  "category": "product_update",
  "tags": ["Claude", "AI", "Product"],
  "summary": "新闻摘要",
  "content_hash": "sha256_hash",
  "media_files": [
    {
      "type": "image",
      "original_url": "https://example.com/image.jpg",
      "local_path": "media/images/image_001.jpg",
      "file_size": 1024576
    }
  ],
  "crawl_info": {
    "crawl_time": "2025-01-17T09:30:00Z",
    "processing_time": 15.5
  }
}
```

## 🔍 存储架构集成

### 三层存储设计
参考arXiv爬虫存储架构，实现完整数据流：

```
📊 数据流向: 爬虫 → 本地存储 → MinIO对象存储 → PostgreSQL元数据 → Elasticsearch索引
```

### 存储服务配置
| 服务 | 地址 | 用途 | 状态 |
|------|------|------|------|
| **MinIO对象存储** | `60.205.160.74:9000` | 文件存储 | ✅ 运行中 |
| **PostgreSQL数据库** | `60.205.160.74:5432` | 元数据存储 | ✅ 运行中 |
| **Elasticsearch搜索** | `60.205.160.74:9200` | 全文检索 | ✅ 运行中 |
| **MinIO连接器API** | `localhost:9011` | 数据管理接口 | ✅ 运行中 |

## 📅 定时任务配置

### Cron任务设置
```bash
# 每天上午9点自动爬取
0 9 * * * cd /path/to/Claude_newsroom && python spider.py --incremental

# 每天下午6点自动上传
0 18 * * * cd /path/to/Claude_newsroom && python uploader.py --source crawled_data
```

### run_daily.sh 脚本
```bash
#!/bin/bash
# 每日自动运行脚本

# 1. 爬取新闻
echo "开始爬取Claude新闻..."
python spider.py --incremental --max-results 20

# 2. 上传到存储系统
echo "上传到存储系统..."
python uploader.py --source crawled_data

echo "每日任务完成！"
```

## 🎯 技术特点

### 1. 简洁设计
- **最小化目录**: 只有2个核心脚本 + 配置文件
- **功能完整**: 爬取、存储、上传一条龙
- **易于维护**: 代码集中，逻辑清晰

### 2. 架构复用
- **集成现有MinIO架构**: 复用arXiv爬虫的成熟存储方案
- **标准化数据格式**: 与现有系统完美兼容
- **API接口复用**: 使用现有MinIO连接器服务

### 3. 自动化支持
- **增量爬取**: 智能检测新增内容
- **定时调度**: 支持cron定时任务
- **错误恢复**: 断点续传和重试机制

## 📦 依赖包

### requirements.txt
```
playwright>=1.40.0
aiohttp>=3.9.0
aiofiles>=23.2.0
beautifulsoup4>=4.12.0
markdownify>=0.11.6
requests>=2.31.0
python-dateutil>=2.8.2
```

## 🚀 快速开始

1. **环境准备**
   ```bash
   pip install -r requirements.txt
   playwright install chromium
   ```

2. **启动MinIO连接器**
   ```bash
   cd ../../../m1n10C0nnect0r/minio-file-manager/backend
   python run.py
   ```

3. **运行爬虫**
   ```bash
   python spider.py --max-results 10
   python uploader.py --source crawled_data
   ```

## 📈 项目状态

- **开发状态**: 🔄 方案设计完成，待开发
- **存储架构**: ✅ 已集成现有MinIO系统
- **数据格式**: ✅ 已标准化
- **部署方式**: ✅ 支持本地和定时任务

---

**联系方式**: 参考项目根目录技术文档  
**更新时间**: 2025-01-17