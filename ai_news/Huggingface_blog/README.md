# 🤖 Hugging Face博客爬虫

基于API优先策略和HTML补充的混合爬取方案，用于爬取Hugging Face中文博客内容。

## 📋 项目特性

- ✅ **API优先策略**: 使用Posts API高效获取最新博客动态
- ✅ **HTML页面补充**: 确保历史文章的完整性
- ✅ **媒体文件下载**: 自动下载文章中的图片资源
- ✅ **标准化存储**: Markdown + JSON格式，便于后续处理
- ✅ **增量更新**: 智能去重，避免重复爬取
- ✅ **多运行模式**: 支持API模式、HTML模式、混合模式
- ✅ **灵活配置**: JSON配置文件，支持自定义参数
- ✅ **详细日志**: 完整的运行状态记录

## 🚀 快速开始

### 1. 环境准备

```bash
# 克隆或下载项目
cd huggingface_blog_crawler

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置设置

配置文件 `config.json` 包含所有运行参数，可根据需要调整：

```json
{
  "crawler": {
    "delay": 2,           // 请求间隔（秒）
    "max_articles": 200,  // 最大爬取数量
    "timeout": 30         // 请求超时时间
  },
  "media": {
    "download_images": true,  // 是否下载图片
    "max_file_size": 10485760 // 最大文件大小
  }
}
```

### 3. 运行爬虫

```bash
# 基本运行（混合模式）
python run_crawler.py

# 仅使用API模式（推荐）
python run_crawler.py --api-only --max 50

# 仅使用HTML模式
python run_crawler.py --html-only

# 测试模式（仅爬取5篇）
python run_crawler.py --test

# 强制重新爬取
python run_crawler.py --force

# 详细输出
python run_crawler.py --verbose
```

## 📁 数据存储结构

爬取的数据按以下结构存储：

```
crawled_data/
└── huggingface_articles/
    └── {article-slug}/
        ├── content.md      # Markdown格式文章内容
        ├── metadata.json   # 文章元数据
        └── media/          # 媒体文件目录
            ├── image_001.png
            ├── image_002.jpg
            └── ...
```

### 文章内容格式

#### content.md
```markdown
# 文章标题

**来源**: https://huggingface.co/blog/zh/article-slug
**爬取时间**: 2024-08-17T10:30:00
**字数**: 1500

---

文章正文内容...

## 相关媒体

![图片描述](media/image_001.png)
```

#### metadata.json
```json
{
  "url": "https://huggingface.co/blog/zh/article-slug",
  "title": "文章标题",
  "slug": "article-slug",
  "content": "文章文本内容...",
  "images": [
    {
      "url": "https://huggingface.co/blog/assets/...",
      "alt": "图片描述",
      "local_path": "media/image_001.png"
    }
  ],
  "crawl_time": "2024-08-17T10:30:00.000000",
  "word_count": 1500,
  "content_hash": "abc123..."
}
```

## 🔧 运行模式

### 1. 混合模式（默认）
```bash
python run_crawler.py
```
- 优先使用API获取最新文章
- 使用HTML解析补充历史文章
- 合并去重，确保完整性

### 2. API模式
```bash
python run_crawler.py --api-only
```
- 仅使用Posts API
- 速度快，获取最新和热门内容
- 可能遗漏部分历史文章

### 3. HTML模式
```bash
python run_crawler.py --html-only
```
- 仅使用HTML页面解析
- 更全面，包含所有历史文章
- 速度较慢

## ⚙️ 配置参数

### API配置
```json
{
  "api": {
    "posts_endpoint": "https://huggingface.co/api/posts",
    "default_params": {
      "limit": 100,
      "sort": "trending"
    },
    "time_range": {
      "since": "2024-01-01",
      "until": null
    }
  }
}
```

### 爬虫配置
```json
{
  "crawler": {
    "delay": 2,           // 请求间隔
    "timeout": 30,        // 超时时间
    "max_retries": 3,     // 重试次数
    "max_articles": 200   // 最大文章数
  }
}
```

### 媒体文件配置
```json
{
  "media": {
    "download_images": true,
    "download_videos": false,
    "image_timeout": 15,
    "max_file_size": 10485760,
    "allowed_extensions": [".jpg", ".jpeg", ".png", ".gif", ".svg", ".webp"]
  }
}
```

### 过滤配置
```json
{
  "filter": {
    "skip_duplicates": true,        // 跳过重复文章
    "min_content_length": 200,      // 最小内容长度
    "exclude_patterns": [],         // 排除模式
    "include_languages": ["zh", "en"] // 包含语言
  }
}
```

## 📊 工具函数

项目包含丰富的工具函数（`utils.py`）：

### 文章处理
- `ArticleUtils.clean_text()`: 文本清理
- `ArticleUtils.extract_keywords()`: 关键词提取
- `ArticleUtils.calculate_reading_time()`: 阅读时间计算

### 文件处理
- `FileUtils.safe_filename()`: 安全文件名生成
- `FileUtils.get_file_hash()`: 文件哈希计算
- `FileUtils.backup_file()`: 文件备份

### 数据验证
- `DataValidator.validate_article_data()`: 文章数据验证
- `DataValidator.validate_config()`: 配置文件验证

### 报告生成
- `ReportGenerator.generate_crawl_report()`: 爬取报告
- `ReportGenerator.generate_article_index()`: 文章索引

## 🔍 故障排除

### 常见问题

1. **网络连接失败**
   ```bash
   # 检查网络连接
   ping huggingface.co
   
   # 增加超时时间
   python run_crawler.py --config config.json  # 修改timeout参数
   ```

2. **请求被限制**
   ```bash
   # 增加请求间隔
   # 在config.json中设置 "delay": 3
   ```

3. **内容解析失败**
   ```bash
   # 使用详细模式查看错误
   python run_crawler.py --verbose
   ```

4. **存储空间不足**
   ```bash
   # 禁用图片下载
   # 在config.json中设置 "download_images": false
   ```

### 日志分析

日志文件 `crawler.log` 包含详细的运行信息：

```bash
# 查看最新日志
tail -f crawler.log

# 搜索错误信息
grep "ERROR" crawler.log

# 查看爬取统计
grep "成功爬取" crawler.log
```

## 📈 性能优化

### 建议设置

1. **小规模测试**
   ```bash
   python run_crawler.py --test  # 仅5篇文章
   ```

2. **大规模爬取**
   ```json
   {
     "crawler": {
       "delay": 1,
       "timeout": 60,
       "max_articles": 1000
     }
   }
   ```

3. **仅更新最新文章**
   ```bash
   python run_crawler.py --api-only --max 20
   ```

## 🔒 注意事项

1. **遵守网站规则**: 保持合理的请求频率，避免给服务器造成压力
2. **数据使用**: 爬取的数据仅供学习和研究使用
3. **版权声明**: 尊重原作者版权，注明数据来源
4. **定期更新**: 网站结构可能变化，需要及时更新解析规则

## 📝 更新日志

### v1.0.0 (2024-08-17)
- 初始版本发布
- 实现API优先的混合爬取策略
- 支持媒体文件下载
- 标准化数据存储格式
- 增量更新机制

## 🤝 贡献指南

欢迎提交Issue和Pull Request！

1. Fork项目
2. 创建功能分支
3. 提交改动
4. 发起Pull Request

## 📄 许可证

本项目采用MIT许可证，详见LICENSE文件。

---

**开发团队**: AI爬虫项目组  
**技术栈**: Python + requests + BeautifulSoup  
**文档版本**: v1.0  
**最后更新**: 2024-08-17