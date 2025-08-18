# Google Research Blog RSS 爬虫

🤖 一个专门用于爬取 Google Research Blog 的 RSS 订阅爬虫，自动获取最新的 AI 研究文章并按照规范的目录结构存储。

## ✨ 特性

- 🔄 **RSS 自动订阅**: 实时获取 Google Research Blog 最新文章
- 📂 **规范存储结构**: 每篇文章独立文件夹，包含内容、元数据和媒体文件
- 🖼️ **媒体文件下载**: 自动下载文章中的图片、视频等媒体资源
- 📝 **Markdown 转换**: 将 HTML 内容转换为易读的 Markdown 格式
- 🔧 **高度可配置**: 支持自定义爬取参数、过滤条件等
- 🚀 **一键运行**: 提供简单易用的命令行界面

## 📁 项目结构

```
google_ai_blog/
├── 📄 spider.py                    # 主爬虫脚本
├── 📄 run_crawler.py               # 一键运行脚本
├── 📄 config.json                  # 配置文件
├── 📋 requirements.txt             # 依赖包
├── 📄 README.md                    # 说明文档
└── 📊 crawled_data/                # 本地数据存储
    ├── article_20240118_abc123/    # 文章1文件夹
    │   ├── content.md              # Markdown内容
    │   ├── metadata.json           # 元数据JSON
    │   └── media/                  # 媒体文件目录
    │       ├── image1.png          # 图片文件
    │       └── document1.pdf       # PDF文档
    ├── article_20240119_def456/    # 文章2文件夹
    │   ├── content.md              # Markdown内容
    │   ├── metadata.json           # 元数据JSON
    │   └── media/                  # 媒体文件目录
    │       └── image2.jpg          # 图片文件
    └── ...                         # 更多文章
```

## 🚀 快速开始

### 1. 环境准备

```bash
# 克隆或下载项目
git clone <repository-url>
cd google_ai_blog

# 安装依赖
pip install -r requirements.txt
```

### 2. 运行爬虫

#### 🎯 一键运行（推荐）

```bash
# 交互模式 - 提供菜单选择
python run_crawler.py

# 直接运行爬虫
python run_crawler.py run

# 查看数据统计
python run_crawler.py status

# 查看配置信息
python run_crawler.py config
```

#### ⚡ 直接调用

```bash
# 使用主爬虫脚本
python spider.py
```

### 3. 查看结果

爬取完成后，文章将保存在 `crawled_data/` 目录下，每篇文章都有独立的文件夹：

```
crawled_data/
└── article_20240118_abc123/
    ├── content.md          # 文章内容（Markdown格式）
    ├── metadata.json       # 文章元数据
    └── media/             # 媒体文件
        ├── image1.png
        └── document1.pdf
```

## ⚙️ 配置说明

编辑 `config.json` 文件可以自定义爬虫行为：

```json
{
  "rss": {
    "url": "https://research.google/blog/rss/",
    "base_url": "https://research.google/blog/"
  },
  "crawler": {
    "max_articles_per_run": 20,     // 每次最多爬取文章数
    "request_delay": 2,             // 请求间隔（秒）
    "timeout": 30                   // 请求超时时间
  },
  "storage": {
    "data_directory": "crawled_data",  // 数据存储目录
    "save_markdown": true,             // 保存Markdown格式
    "save_metadata": true              // 保存元数据
  },
  "media": {
    "download_enabled": true,          // 是否下载媒体文件
    "max_file_size": 10485760,         // 最大文件大小(10MB)
    "allowed_extensions": [            // 允许的文件扩展名
      "jpg", "jpeg", "png", "gif", 
      "pdf", "mp4", "avi", "mov"
    ]
  }
}
```

## 📋 数据格式

### Markdown 文件 (content.md)

```markdown
# 文章标题

[文章内容，已转换为Markdown格式]

## 相关链接
- [论文链接](https://arxiv.org/...)
- [代码仓库](https://github.com/...)

![图片描述](media/image1.png)
```

### 元数据文件 (metadata.json)

```json
{
  "title": "文章标题",
  "url": "https://research.google/blog/...",
  "summary": "文章摘要",
  "author": "Google Research Team",
  "published_date": "2024-01-18T10:00:00Z",
  "crawled_date": "2024-01-18T12:00:00Z",
  "word_count": 1500,
  "article_id": "article_20240118_abc123",
  "images": [
    {
      "url": "https://...",
      "local_path": "media/image1.png",
      "alt": "图片描述"
    }
  ],
  "links": [
    {
      "url": "https://arxiv.org/...",
      "text": "论文链接",
      "type": "paper"
    }
  ]
}
```

## 🔧 高级功能

### 自定义过滤

在配置文件中设置过滤条件：

```json
{
  "filtering": {
    "min_quality_score": 5.0,
    "exclude_keywords": ["advertisement"],
    "include_keywords": ["machine learning", "AI"]
  }
}
```

### 媒体文件管理

- 自动识别和下载图片、PDF、视频等文件
- 支持文件大小限制和格式过滤
- 本地存储，避免外链失效

### 内容处理

- HTML 到 Markdown 的智能转换
- 自动提取文章中的外部链接
- 识别和分类不同类型的链接（论文、代码、演示等）

## 📊 使用示例

### 批量爬取最新文章

```bash
# 爬取最新20篇文章
python run_crawler.py run
```

### 查看爬取统计

```bash
# 显示数据统计信息
python run_crawler.py status
```

输出示例：
```
📊 数据统计:
   📁 总文章数: 15
   📝 Markdown文件: 15
   📋 元数据文件: 15
   🖼️ 媒体文件: 42
   🆕 最新文章: Advancing AI Safety Through Constitutional AI
```

### 交互模式

```bash
# 启动交互模式
python run_crawler.py
```

会显示友好的菜单界面：
```
🤖 Google Research Blog 爬虫
========================================
1. 🚀 开始爬取
2. 📊 查看数据统计  
3. ⚙️ 查看配置
4. 🔧 检查依赖
5. ❌ 退出
========================================
请选择操作 (1-5):
```

## 🔍 故障排除

### 常见问题

1. **依赖包缺失**
   ```bash
   pip install -r requirements.txt
   ```

2. **网络连接问题**
   - 检查网络连接
   - 确认可以访问 https://research.google/blog/
   - 检查防火墙设置

3. **权限问题**
   - 确保对当前目录有写入权限
   - 检查 `crawled_data` 目录的读写权限

4. **RSS 解析失败**
   - RSS 源可能临时不可用
   - 检查配置文件中的 RSS URL 是否正确

### 调试模式

修改日志级别获取更详细信息：

```json
{
  "logging": {
    "level": "DEBUG"
  }
}
```

### 检查依赖

```bash
python run_crawler.py check
```

## 📄 依赖说明

- **feedparser**: RSS 订阅解析
- **requests**: HTTP 请求处理
- **beautifulsoup4**: HTML 内容解析
- **pathlib**: 文件路径处理（Python 内置）

## 🤝 贡献指南

1. Fork 本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 📝 许可证

本项目仅供学习和研究使用。请遵守以下原则：

- ✅ 遵守目标网站的 robots.txt 和使用条款
- ✅ 合理控制爬取频率，避免对服务器造成压力  
- ✅ 尊重原作者版权，仅用于个人学习
- ❌ 不得用于商业用途或大规模数据采集

## 🙋 支持与反馈

如果遇到问题或有建议，请：

1. 查看本 README 的故障排除部分
2. 检查 `spider.log` 日志文件
3. 提交 Issue 描述问题详情

## 🔗 相关链接

- [Google Research Blog](https://research.google/blog/)
- [Google Research Blog RSS](https://research.google/blog/rss/)
- [RSS 格式说明](https://cyber.harvard.edu/rss/rss.html)

---

🎉 享受 AI 研究文章的探索之旅！