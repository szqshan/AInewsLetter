# X (Twitter) 爬虫系统

## 🚀 功能特性

- **Following 页面爬取**: 专门爬取用户 Following 页面的推文内容
- **灵活时间过滤**: 支持多种时间过滤方式
  - 年份过滤 (如: 2024)
  - 日期范围过滤 (如: 2025-08-01 到 2025-08-20)
  - 年份范围过滤 (如: 2024-2025)
  - 相对时间过滤 (如: 最近7天)
  - 特定日期过滤 (如: 2025-08-18)
- **智能时间识别**: 自动解析推文时间戳，过滤无效或缺失时间的推文
- **防重复机制**: 避免重复爬取相同推文，提高效率
- **双重存储格式**: 
  - 传统JSON格式（向后兼容）
  - 结构化存储格式（每篇推文独立文件夹，包含content.md、metadata.json和media文件夹）
- **模块化设计**: JavaScript 爬虫脚本 + Python 包装层，易于扩展
- **数据标准化**: 统一的 JSON 格式输出和 Markdown 内容生成
- **一键运行**: 简单的命令行接口，支持多种参数配置

## 📁 项目结构

```
X/
├── src/                          # JavaScript 爬虫脚本目录
│   ├── scrape_following_tweets.js # Following 页面爬虫
│   ├── scrape_2025_tweets.js     # 2025年推文专项爬虫
│   ├── login_with_cookies.js     # Cookie 登录脚本
│   ├── export_browser_cookies.js # Cookie 导出工具
│   └── ...
├── crawled_data/                 # 爬取数据存储目录
│   ├── 博主名_爬取时间/           # 单条推文目录（结构化存储）
│   │   ├── content.md             # 推文内容（Markdown格式）
│   │   ├── metadata.json         # 推文元数据（JSON格式）
│   │   └── media/                 # 媒体文件目录
│   │       └── image_*.jpg        # 下载的图片文件
│   ├── following_tweets_*.json   # 传统JSON格式（向后兼容）
│   ├── tweets/                   # 常规推文数据
│   │   └── following_xxx/        # Following 推文目录
│   └── tweets_2025/              # 2025年推文汇总
│       ├── tweets_2025_xxx.json  # 推文数据汇总
│       └── report_2025_xxx.json  # 统计报告
├── spider.py                     # 主爬虫类
├── run_crawler.py               # 一键运行脚本
├── run_2025_crawler.py          # 2025年推文爬虫启动器
├── requirements.txt             # Python 依赖
├── package.json                 # Node.js 依赖
└── README.md                    # 说明文档
```

## 🛠️ 安装依赖

### Python 依赖
```bash
pip install -r requirements.txt
```

### Node.js 依赖
```bash
npm install
```

## 🎯 使用方法

### 常规Following页面爬取
```bash
# 爬取 Following 页面（默认）
python run_crawler.py

# 指定最大爬取数量
python run_crawler.py --max 10

# 使用npm脚本
npm run crawl-following
```

### 时间过滤爬取推文

```bash
# 1. 年份过滤
node src/scrape_following_tweets.js 10 2024
node src/scrape_following_tweets.js 20 2025

# 2. 日期范围过滤 (需要用引号包围JSON)
node src/scrape_following_tweets.js 10 '{"startDate":"2025-08-01","endDate":"2025-08-20"}'

# 3. 年份范围过滤
node src/scrape_following_tweets.js 15 '{"startYear":2024,"endYear":2025}'

# 4. 最近几天过滤
node src/scrape_following_tweets.js 10 '{"days":7}'

# 5. 特定日期过滤
node src/scrape_following_tweets.js 5 "2025-08-18"

# 使用npm脚本（默认爬取2025年推文）
npm run crawl-following-year
```

### 参数说明

#### Following推文爬虫 (scrape_following_tweets.js)
- `数量`: 最大爬取推文数量（必需参数）
- `时间过滤器`: 时间过滤条件（可选参数），支持以下格式：
  - **年份**: 直接输入4位数字，如 `2024`、`2025`
  - **特定日期**: 输入日期字符串，如 `"2025-08-18"`
  - **日期范围**: JSON格式，如 `'{"startDate":"2025-08-01","endDate":"2025-08-20"}'`
  - **年份范围**: JSON格式，如 `'{"startYear":2024,"endYear":2025}'`
  - **相对时间**: JSON格式，如 `'{"days":7}'` (最近7天)

**注意**: 在PowerShell中使用JSON格式时，需要用单引号包围整个JSON字符串。

## 📊 数据格式

### 常规Following推文数据

每条推文会生成两个文件：

#### metadata.json
```json
{
  "url": "https://x.com/following",
  "text": "推文内容",
  "author": "作者名称",
  "timestamp": "2025-08-14T20:08:00.000Z",
  "images": [],
  "links": [],
  "crawl_time": "2025-08-18T03:01:24.641337",
  "tweet_id": "following_1755471684585",
  "content_hash": "874a7b6e9468ded3862873c8482bec17"
}
```

#### content.md
```markdown
# 作者名称 的推文

**作者**: 作者名称
**发布时间**: Aug 15
**时间戳**: 2025-08-14T20:08:00.000Z
**来源**: https://x.com/following
**爬取时间**: 2025-08-18T03:01:24.641337

---

推文内容...
```

### 📂 结构化存储格式说明

从v2.0版本开始，爬虫支持结构化存储格式，每篇推文保存为独立文件夹，包含以下文件：

#### 文件夹结构
```
crawled_data/Vaibhav (VB) Srivastav_2025-08-18T01-52-30/
├── content.md         # 推文内容（Markdown格式）
├── metadata.json      # 推文元数据（JSON格式）
└── media/             # 媒体文件目录
    ├── image_1.jpg    # 推文图片1
    └── image_2.jpg    # 推文图片2
```

**文件夹命名规则**: `博主名_爬取时间`
- 博主名：推文作者的用户名（自动清理非法字符）
- 爬取时间：格式为 `YYYY-MM-DDTHH-MM-SS`

#### metadata.json 格式
```json
{
  "id": "1957148807562723809",
  "text": "推文内容文本",
  "username": "用户显示名",
  "handle": "@username",
  "timestamp": "2025-08-17T18:33:32.000Z",
  "url": "https://x.com/username/status/1957148807562723809",
  "engagement": {
    "replies": 0,
    "retweets": 0,
    "likes": 0
  },
  "media": {
    "images_count": 2,
    "images_urls": ["图片URL列表"]
  },
  "scraped_at": "2025-08-18T01:48:11.640Z",
  "filter_applied": 2025,
  "source": "X_Following_Scraper",
  "version": "2.0"
}
```

#### content.md 格式
```markdown
# 用户显示名 的推文

**发布时间**: 2025/8/17 22:33:32  
**用户**: 用户显示名 (@username)  
**推文ID**: 1957148807562723809  
**链接**: [查看原推文](https://x.com/username/status/1957148807562723809)

## 推文内容

推文内容文本...

## 互动数据

- 💬 回复: 0
- 🔄 转推: 0
- ❤️ 点赞: 0

## 媒体文件

![图片1](./media/image_1.jpg)
![图片2](./media/image_2.jpg)

---
*爬取时间: 2025/8/18 05:48:11*
```



#### 汇总数据 (crawled_data/tweets_2025/)

**tweets_2025_xxx.json** - 所有2025年推文的完整数据
**report_2025_xxx.json** - 详细统计报告
```json
{
  "summary": {
    "total_tweets": 500,
    "target_year": 2025,
    "scraped_at": "2025-01-18T15:45:30.123Z",
    "date_range": {
      "earliest": 1704067200000,
      "latest": 1735689600000
    }
  },
  "authors": {
    "@username1": {
      "username": "显示名1",
      "tweet_count": 25,
      "total_engagement": 1500
    }
  },
  "engagement_stats": {
    "total_likes": 15000,
    "total_retweets": 8000,
    "total_replies": 3000
  }
}
```

## 🔧 Cookie 配置

1. 使用 `export_browser_cookies.js` 导出浏览器 Cookie
2. 将导出的 Cookie 保存到 `x_cookies.json` 文件
3. 确保 Cookie 包含有效的 `auth_token` 等认证信息

## ⚙️ 工作原理

1. 自动导航到 X (Twitter) 主页
2. 点击 "Following" 标签页
3. 爬取关注用户的最新推文
4. 保存为结构化数据格式

## 📝 注意事项

- 需要有效的 X (Twitter) cookies 才能访问完整内容
- 建议适当设置爬取间隔，避免被限制
- 爬取的数据仅供学习和研究使用