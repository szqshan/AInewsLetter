# 🤖 OpenAI Newsroom 爬虫开发方案

基于标准爬虫模板制定的OpenAI官方新闻动态爬取方案

---

## 🎯 项目概述

**目标网站**: https://openai.com/newsroom/  
**数据类型**: OpenAI官方新闻、产品发布、研究论文、公司公告  
**核心功能**: 自动爬取、媒体下载、标准化存储、云端同步  
**更新频率**: 每日自动爬取  
**数据量级**: 历史200-500篇，每日新增1-3篇

---

## 🗂️ 目录结构

```
OpenAI_newsroom/
├── 📄 spider.py                    # 主爬虫脚本
├── 📄 uploader.py                  # 上传脚本
├── 📄 run_crawler.py               # 一键运行脚本
├── 📄 config.json                  # 配置文件
├── 📄 requirements.txt             # 依赖包
├── 📄 README.md                    # 说明文档
└── 📊 crawled_data/                # 本地数据存储
    └── newsroom/
        └── {文章ID}/                # 按文章ID组织
            ├── content.md           # Markdown内容
            ├── metadata.json        # 元数据JSON
            └── media/               # 媒体文件目录
                ├── images/          # 图片文件
                └── videos/          # 视频文件
```

---

## 🔍 网站分析结果

### 页面结构
- **主页面**: https://openai.com/newsroom/
- **分类页面**:
  - 产品发布: `/newsroom/product/`
  - 研究论文: `/newsroom/research/`
  - 公司公告: `/newsroom/company/`
  - 安全报告: `/newsroom/safety/`

### 数据提取选择器
```yaml
列表页面:
  文章卡片: ".card"
  文章链接: ".card a[href*='/newsroom/']"
  标题: ".card-title"
  摘要: ".card-description"
  分类: ".card-meta .category"
  发布时间: ".card-meta time"
  图片: ".card-media img"

详情页面:
  标题: "h1.hero-title, h1"
  正文: ".content-body, article"
  发布时间: "time[datetime]"
  作者: ".author-name, .byline"
  图片: ".content-body img[srcset]"
  标签: ".tags a, .category-tag"
```

---

## 🛠️ 技术实现

### 核心功能模块
1. **文章列表获取**: 自动发现并提取所有文章
2. **详情内容爬取**: 获取完整文章内容
3. **媒体文件下载**: 图片、视频等媒体资源
4. **标准化存储**: Markdown + JSON格式
5. **增量更新**: 跳过已存在文章
6. **错误处理**: 网络异常重试机制

### 反爬虫对策
- User-Agent轮换
- 2-5秒随机延迟
- 最多3个并发请求
- 指数退避重试

---

## 🚀 使用方式

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 基础配置
编辑 `config.json` 文件，配置爬取参数和存储设置。

### 3. 运行爬虫
```bash
# 爬取最新10篇文章
python run_crawler.py --max 10

# 仅爬取不上传
python run_crawler.py --crawl-only --max 10

# 仅上传不爬取
python run_crawler.py --upload-only
```

### 4. 定时任务
```bash
# Linux Cron (每天上午8点)
0 8 * * * cd /path/to/OpenAI_newsroom && python run_crawler.py --max 5

# Windows 任务计划程序
cd /d "D:\OpenAI_newsroom"
python run_crawler.py --max 5
```

---

## 📊 数据格式

### Markdown格式 (content.md)
```markdown
# 隆重推出 GPT-5

**作者**: OpenAI Team  
**发布时间**: 2025-08-07  
**分类**: product  
**来源**: [OpenAI Newsroom](https://openai.com/newsroom/gpt-5)  
**字数**: 1250  
**标签**: GPT-5, 新产品, AI模型  

---

完整文章内容...

## 相关图片

![GPT-5架构图](media/gpt5_architecture.jpg)
```

### 元数据格式 (metadata.json)
```json
{
  "url": "https://openai.com/newsroom/gpt-5",
  "title": "隆重推出 GPT-5",
  "category": "product",
  "publish_date": "2025-08-07",
  "author": "OpenAI Team",
  "content": "完整文章内容...",
  "images": [
    {
      "url": "https://openai.com/images/gpt5-hero.jpg",
      "alt": "GPT-5架构图",
      "filename": "gpt5_hero.jpg",
      "local_path": "media/gpt5_hero.jpg"
    }
  ],
  "tags": ["GPT-5", "新产品", "AI模型"],
  "word_count": 1250,
  "crawl_time": "2024-01-15T14:30:00Z"
}
```

---

## ✅ 功能验证清单

- [ ] 基础爬取：成功访问OpenAI Newsroom
- [ ] 数据提取：标题、内容、时间、分类正确
- [ ] 媒体下载：图片正常下载到本地
- [ ] 增量更新：重复运行跳过已有数据
- [ ] 错误处理：网络异常时优雅处理
- [ ] 数据格式：Markdown和JSON格式标准
- [ ] 存储集成：正常上传到MinIO系统

---

## 📋 开发计划

| 阶段 | 任务 | 预计时间 | 状态 |
|------|------|----------|------|
| 1 | 基础爬虫开发 | 1-2天 | 📋 待开始 |
| 2 | 媒体下载功能 | 0.5天 | 📋 待开始 |
| 3 | 存储集成测试 | 0.5天 | 📋 待开始 |
| 4 | 完整测试验证 | 0.5天 | 📋 待开始 |
| 5 | 文档完善 | 0.5天 | ✅ 已完成 |

---

## 🔧 技术栈

- **Python 3.8+**: 主要开发语言
- **BeautifulSoup4 + requests**: 网页爬取
- **MinIO**: 对象存储
- **PostgreSQL**: 元数据存储
- **Elasticsearch**: 搜索索引

---

## 🎯 下一步行动

方案已制定完成，包含：
- ✅ 详细的网站结构分析
- ✅ 完整的技术实现方案
- ✅ 标准化的数据格式
- ✅ 完整的使用文档
- ✅ 测试验证计划

**请确认是否开始实施开发？**

确认后我将开始编写具体的代码实现。