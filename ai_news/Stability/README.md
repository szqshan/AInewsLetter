# 🕷️ Stability AI 爬虫

专门爬取 Stability AI 官网新闻和研究文章的爬虫程序。

## 📋 功能特性

- ✅ 爬取 Stability AI 新闻页面 (`/news`)
- ✅ 爬取 Stability AI 研究页面 (`/research`)
- ✅ 自动下载文章图片到本地
- ✅ 生成标准化的 Markdown 和 JSON 格式数据
- ✅ 增量更新 (跳过已爬取的文章)
- ✅ 错误重试和异常处理
- ✅ 可配置的爬取参数

## 🚀 快速开始

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 运行爬虫
```bash
# 基础用法 - 爬取20篇文章
python run_crawler.py

# 测试模式 - 只爬取3篇文章
python run_crawler.py --test

# 指定文章数量
python run_crawler.py --max 50

# 不下载图片
python run_crawler.py --no-images

# 强制重新爬取
python run_crawler.py --force
```

### 3. 查看结果
爬取的数据保存在 `crawled_data/stability_articles/` 目录下：

```
crawled_data/
└── stability_articles/
    ├── article-slug-1/
    │   ├── content.md          # Markdown格式内容
    │   ├── metadata.json       # 文章元数据
    │   └── media/              # 图片文件
    │       ├── image_1.jpg
    │       └── image_2.png
    └── article-slug-2/
        ├── content.md
        ├── metadata.json
        └── media/
```

## ⚙️ 配置选项

编辑 `config.json` 文件自定义爬取行为：

```json
{
  "crawler": {
    "delay": 3,                 // 请求间隔 (秒)
    "timeout": 30,              // 请求超时 (秒)
    "max_retries": 3,           // 最大重试次数
    "max_articles": 50          // 最大文章数量
  },
  "media": {
    "download_images": true,    // 是否下载图片
    "image_timeout": 20,        // 图片下载超时
    "max_file_size": 20971520   // 最大文件大小 (20MB)
  },
  "filter": {
    "skip_duplicates": true,    // 跳过重复文章
    "min_content_length": 100   // 最小内容长度
  }
}
```

## 📊 数据格式

### Markdown 文件 (content.md)
```markdown
# 文章标题

**分类**: news  
**发布日期**: Aug 12  
**作者**: Savannah Martin  
**来源**: https://stability.ai/news/...  
**爬取时间**: 2025-01-07 12:00:00

---

文章正文内容...

## 相关媒体

![图片描述](media/image_1.jpg)
```

### 元数据文件 (metadata.json)
```json
{
  "url": "原始文章URL",
  "title": "文章标题",
  "content": "正文内容",
  "metadata": {
    "date": "发布日期",
    "author": "作者",
    "tags": ["标签1", "标签2"]
  },
  "images": [
    {
      "url": "原始图片URL",
      "alt": "图片描述",
      "local_filename": "image_1.jpg",
      "local_path": "media/image_1.jpg",
      "downloaded": true
    }
  ],
  "page_type": "news",
  "crawl_time": "2025-01-07T12:00:00",
  "word_count": 1234,
  "content_hash": "md5hash",
  "slug": "article-slug"
}
```

## 🔧 命令行参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--max N` | 最大爬取文章数量 | 20 |
| `--config FILE` | 配置文件路径 | config.json |
| `--crawl-only` | 只爬取，不上传 | False |
| `--upload-only` | 只上传，不爬取 | False |
| `--no-images` | 不下载图片 | False |
| `--force` | 强制重新爬取 | False |
| `--test` | 测试模式 (3篇文章) | False |
| `--verbose` | 详细输出 | False |

## 📈 爬取统计

运行完成后会显示爬取统计：

```
============================================================
CRAWLING SUMMARY
============================================================
Total articles processed: 20
Successfully crawled: 18
Failed: 2
Data saved to: crawled_data/stability_articles
============================================================
```

## 🐛 故障排除

### 常见问题

1. **网络连接错误**
   - 检查网络连接
   - 可能需要使用代理

2. **爬取失败**
   - 网站可能有反爬措施
   - 增加请求间隔 (`delay`)
   - 检查 User-Agent

3. **图片下载失败**
   - 图片URL可能已失效
   - 检查网络连接
   - 增加图片超时时间

### 调试模式

```bash
# 详细输出
python run_crawler.py --verbose --test

# 只爬取不下载图片
python run_crawler.py --test --no-images
```

## 📝 开发说明

- 基于 requests + BeautifulSoup
- 遵循网站 robots.txt
- 包含请求间隔和重试机制
- 支持增量更新
- 标准化数据格式

## 📄 许可证

本项目仅用于学习和研究目的。请遵守 Stability AI 网站的使用条款。