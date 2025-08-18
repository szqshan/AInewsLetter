# X平台Following页面推文爬虫使用说明

## 🎯 功能概述

这是一个专门用于爬取X平台(原Twitter)Following页面推文的浏览器端爬虫工具。它可以：

- ✅ 提取推文文本内容
- ✅ 下载推文中的图片和视频
- ✅ 获取作者信息和时间戳
- ✅ 按推文分别保存到独立文件夹
- ✅ 生成详细的爬取报告
- ✅ 支持滚动加载更多推文

## 📁 文件结构

```
X/
├── src/
│   ├── main.js              # 主入口文件
│   ├── tweet_extractor.js   # 推文提取模块
│   ├── media_downloader.js  # 媒体下载模块
│   └── following_crawler.js # 主爬虫脚本
├── x_cookies.json           # X平台登录Cookie
├── USAGE.md                 # 使用说明(本文件)
└── README.md                # 项目说明
```

## 🚀 快速开始

### 1. 准备工作

1. **登录X平台**：确保已在浏览器中登录X平台账号
2. **导航到Following页面**：访问 `https://x.com/home` 并点击"Following"选项卡
3. **打开开发者工具**：按F12打开浏览器开发者工具

### 2. 加载爬虫脚本

在浏览器控制台中执行以下代码来加载主模块：

```javascript
// 方法1：直接加载主模块(推荐)
const script = document.createElement('script');
script.src = 'https://raw.githubusercontent.com/your-repo/X-crawler/main/src/main.js';
document.head.appendChild(script);
```

或者复制粘贴整个 `src/main.js` 文件内容到控制台执行。

### 3. 开始爬取

#### 基本使用
```javascript
// 使用默认配置开始爬取
startXCrawling();
```

#### 使用预设配置
```javascript
// 快速模式：少量推文，快速完成
startXCrawling(XCrawlerPresets.quick);

// 标准模式：中等数量推文
startXCrawling(XCrawlerPresets.standard);

// 深度模式：大量推文，完整爬取
startXCrawling(XCrawlerPresets.deep);

// 仅文本模式：不下载媒体文件
startXCrawling(XCrawlerPresets.textOnly);
```

#### 自定义配置
```javascript
startXCrawling({
    scrollCount: 8,              // 滚动次数
    maxTweets: 80,               // 最大推文数
    downloadMedia: true,         // 是否下载媒体
    delayBetweenScrolls: 2500,   // 滚动间隔(毫秒)
    delayBetweenDownloads: 1000, // 下载间隔(毫秒)
    basePath: 'my_tweets'        // 保存路径前缀
});
```

## ⚙️ 配置选项

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `scrollCount` | number | 5 | 页面滚动次数，控制加载更多推文 |
| `maxTweets` | number | 50 | 最大提取推文数量 |
| `downloadMedia` | boolean | true | 是否下载图片和视频 |
| `basePath` | string | 'crawled_data' | 数据保存的基础路径 |
| `delayBetweenScrolls` | number | 2000 | 滚动间隔时间(毫秒) |
| `delayBetweenDownloads` | number | 1000 | 下载间隔时间(毫秒) |

## 📊 预设配置详情

### Quick模式
- 滚动次数：3次
- 最大推文：20条
- 下载媒体：是
- 滚动间隔：1秒

### Standard模式
- 滚动次数：5次
- 最大推文：50条
- 下载媒体：是
- 滚动间隔：2秒

### Deep模式
- 滚动次数：10次
- 最大推文：100条
- 下载媒体：是
- 滚动间隔：3秒

### TextOnly模式
- 滚动次数：5次
- 最大推文：50条
- 下载媒体：否
- 滚动间隔：1.5秒

## 📁 数据保存结构

爬取的数据将按以下结构保存（完全符合项目标准结构）：

```
crawled_data/
└── {timestamp}_{username}_{tweetId}/     # 每条推文的独立文件夹
    ├── content.md                        # 推文内容（Markdown格式）
    ├── metadata.json                     # 推文元数据（JSON格式）
    └── media/                           # 媒体文件目录
        ├── image_1_{timestamp}.jpg      # 图片文件
        ├── image_2_{timestamp}.jpg
        └── video_1_{timestamp}.mp4      # 视频文件
```

### 文件说明

- **content.md**: 包含推文的完整内容、作者信息、互动数据等，采用 Markdown 格式便于阅读
- **metadata.json**: 包含推文的结构化数据，便于程序处理和分析
- **media/**: 存储推文中的所有图片和视频文件，文件名包含时间戳避免冲突

### 文件夹命名规则
格式：`YYYYMMDD_HHMMSS_用户名_推文ID后8位`

### tweet_data.json 结构
```json
{
  "id": "1957140370468602281",
  "timestamp": "2025-08-17T18:00:00.000Z",
  "author": {
    "displayName": "LangChain",
    "username": "LangChain"
  },
  "content": "推文文本内容...",
  "images": [
    {
      "url": "https://pbs.twimg.com/media/...",
      "filename": "image_1.jpg",
      "alt": "图片描述"
    }
  ],
  "videos": [],
  "folderName": "20250817_180000_LangChain_68602281",
  "extractedAt": "2025-08-17T23:53:01.435Z"
}
```

## 🔧 高级功能

### 获取爬取统计
```javascript
// 获取详细统计信息
const stats = XCrawler.getStats();
console.log(stats);
```

### 重置爬虫状态
```javascript
// 重置爬虫，清除之前的状态
XCrawler.reset();
```

### 检查页面状态
```javascript
// 检查当前页面是否适合爬取
const pageCheck = XCrawler.checkPage();
console.log(pageCheck);
```

## 🚨 注意事项

1. **登录状态**：确保已登录X平台，否则可能无法访问Following页面
2. **网络稳定**：爬取过程中保持网络连接稳定
3. **浏览器兼容**：建议使用Chrome、Firefox等现代浏览器
4. **频率控制**：内置了延迟机制，避免过于频繁的请求
5. **数据量控制**：根据需要调整maxTweets参数，避免一次性爬取过多数据

## 🐛 常见问题

### Q: 脚本加载失败怎么办？
A: 可以直接复制粘贴 `src/main.js` 文件内容到控制台执行。

### Q: 为什么没有提取到推文？
A: 检查是否在Following页面，确保已登录且页面加载完成。

### Q: 下载的图片质量如何？
A: 默认下载small尺寸，可以修改代码中的URL参数获取更高质量图片。

### Q: 可以爬取其他页面的推文吗？
A: 当前版本专门针对Following页面优化，其他页面可能需要调整选择器。

### Q: 如何停止正在运行的爬虫？
A: 刷新页面或关闭浏览器标签页即可停止。

## 📈 性能优化建议

1. **合理设置延迟**：根据网络状况调整滚动和下载间隔
2. **分批处理**：对于大量数据，建议分多次爬取
3. **关闭无关标签**：减少浏览器内存占用
4. **监控控制台**：及时发现和处理错误信息

## 🔄 更新日志

### v1.0.0 (2025-08-17)
- ✅ 初始版本发布
- ✅ 支持Following页面推文提取
- ✅ 支持图片和视频下载
- ✅ 支持多种预设配置
- ✅ 生成详细爬取报告

---

**免责声明**：本工具仅供学习和研究使用，请遵守X平台的使用条款和相关法律法规。使用者需自行承担使用风险。