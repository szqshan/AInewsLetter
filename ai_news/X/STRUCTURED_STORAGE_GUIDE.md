# 📁 X.com 推文结构化存储系统

## 🎯 系统概述

本系统将爬取的 X.com 推文数据从简单的 JSON 格式转换为标准化的结构化存储格式，每条推文都有独立的文件夹，包含完整的内容、元数据和媒体文件。

## 📂 存储结构

每条推文按照以下标准结构存储：

```
crawled_data/structured/
├── tweet_1_1957148807562723809/
│   ├── content.md          # 推文内容（Markdown格式）
│   ├── metadata.json       # 推文元数据（JSON格式）
│   └── media/              # 媒体文件夹
│       ├── image_1.jpg     # 图片文件
│       └── image_2.jpg
├── tweet_2_1950805500037398957/
│   ├── content.md
│   ├── metadata.json
│   └── media/
│       └── image_1.jpg
└── ...
```

## 📄 文件说明

### content.md
包含推文的完整内容，采用 Markdown 格式，包括：
- 作者信息
- 推文文本内容
- 基本信息（发布时间、链接等）
- 互动数据（回复、转发、点赞数）
- 媒体文件引用
- 爬取时间戳

### metadata.json
包含推文的结构化元数据，包括：
- 推文ID和平台信息
- 作者详细信息
- 内容统计信息
- 时间戳信息
- 互动数据
- URL信息
- 媒体文件信息
- 自动提取的标签、提及和话题标签

### media/
存储推文中的所有媒体文件：
- 图片文件（JPG格式）
- 自动命名为 `image_1.jpg`, `image_2.jpg` 等
- 保持原始质量

## 🚀 使用方法

### 1. 爬取推文数据

首先使用爬虫获取推文数据：

```bash
# 爬取 Following 页面推文
node src\scrape_following_tweets.js 10
```

### 2. 转换为结构化存储

将 JSON 数据转换为结构化存储：

```bash
# 转换指定的 JSON 文件
node src\convert_to_structured_storage.js "crawled_data\following_tweets_2025-08-18T00-42-19-800Z.json"

# 查看可用的 JSON 文件
node src\convert_to_structured_storage.js
```

### 3. 查看统计信息

查看转换后的数据统计：

```bash
# 显示详细统计信息
node src\show_structured_stats.js

# 显示目录结构
node src\show_structured_stats.js structure
```

## 📊 功能特性

### 🔄 数据转换
- ✅ JSON 到结构化存储的完整转换
- ✅ 自动创建标准化文件夹结构
- ✅ 智能文件命名和组织
- ✅ 错误处理和日志记录

### 📝 内容处理
- ✅ Markdown 格式的可读性内容
- ✅ 完整的元数据提取
- ✅ 自动标签识别（AI、ML、PyTorch等）
- ✅ 提及和话题标签提取

### 🖼️ 媒体管理
- ✅ 自动下载和保存图片
- ✅ 标准化文件命名
- ✅ 下载失败处理
- ✅ 媒体文件统计

### 📈 统计分析
- ✅ 推文数量统计
- ✅ 作者和平台分析
- ✅ 内容长度统计
- ✅ 媒体文件统计
- ✅ 标签热度分析

## 🛠️ 技术实现

### 核心组件

1. **TweetStorageConverter** - 主转换器
   - 负责 JSON 到结构化存储的转换
   - 处理文件创建和媒体下载
   - 提供错误处理和日志记录

2. **StructuredStorageStats** - 统计分析器
   - 分析转换后的数据
   - 生成统计报告
   - 展示目录结构

### 关键特性

- **模块化设计**：每个功能独立封装
- **错误恢复**：媒体下载失败不影响整体转换
- **可扩展性**：易于添加新的数据处理功能
- **标准化**：遵循统一的文件命名和组织规范

## 📋 数据示例

### content.md 示例

```markdown
# Vaibhav (VB) Srivastav (@reach_vb)

## 推文内容

NVIDIA ON A ROLL! Canary 1B and Parakeet TDT (0.6B) SoTA ASR models - Multilingual, Open Source

- 1B and 600M parameters
- 25 languages
- automatic language detection and translation
- word and sentence timestamps
- transcribe up to 3 hours of audio in one go

## 基本信息

- **发布时间**: 2025-08-17T18:33:32.000Z
- **推文链接**: [查看原推文](https://x.com/reach_vb/status/1957148807562723809)
- **用户**: Vaibhav (VB) Srivastav (@reach_vb)

## 互动数据

- **回复数**: 0
- **转发数**: 0
- **点赞数**: 0

## 媒体文件

![图片1](./media/image_1.jpg)
![图片2](./media/image_2.jpg)

---

*爬取时间: 2025-08-18T00:42:15.152Z*
```

### metadata.json 示例

```json
{
  "id": "1957148807562723809",
  "platform": "X (Twitter)",
  "type": "tweet",
  "author": {
    "username": "Vaibhav (VB) Srivastav",
    "handle": "@reach_vb"
  },
  "content": {
    "text": "NVIDIA ON A ROLL! Canary 1B and Parakeet TDT...",
    "length": 276
  },
  "timestamps": {
    "published": "2025-08-17T18:33:32.000Z",
    "scraped": "2025-08-18T00:42:15.152Z"
  },
  "engagement": {
    "replies": 0,
    "retweets": 0,
    "likes": 0
  },
  "urls": {
    "original": "https://x.com/reach_vb/status/1957148807562723809",
    "media": [
      "https://pbs.twimg.com/profile_images/1509901130670747666/JFlrSzB4_normal.jpg",
      "https://pbs.twimg.com/media/GykwBVQXIAAkbcm?format=jpg&name=small"
    ]
  },
  "media": {
    "count": 2,
    "types": ["image"]
  },
  "tags": ["AI"],
  "mentions": [],
  "hashtags": []
}
```

## 🎯 使用场景

### 📊 数据分析
- 推文内容分析
- 作者影响力研究
- 话题趋势分析
- 媒体内容统计

### 📚 内容管理
- 推文内容归档
- 媒体文件管理
- 搜索和检索
- 内容分类

### 🔍 研究应用
- 社交媒体研究
- 内容传播分析
- 用户行为研究
- AI/ML 数据集构建

## 🚨 注意事项

1. **存储空间**：每条推文包含媒体文件，需要足够的存储空间
2. **网络连接**：媒体文件下载需要稳定的网络连接
3. **版权问题**：请遵守相关版权法律法规
4. **隐私保护**：注意保护用户隐私信息

## 🔧 故障排除

### 常见问题

1. **转换失败**
   - 检查 JSON 文件路径是否正确
   - 确保有足够的磁盘空间
   - 检查文件权限

2. **媒体下载失败**
   - 检查网络连接
   - 媒体 URL 可能已失效
   - 系统会创建 `.failed` 文件记录失败信息

3. **统计信息不准确**
   - 确保所有推文都已正确转换
   - 检查 metadata.json 文件是否完整

## 📈 未来扩展

- 支持视频文件下载
- 添加更多数据分析功能
- 支持其他社交媒体平台
- 集成机器学习分析
- 添加 Web 界面

---

**开发者**: AI Assistant  
**版本**: 1.0  
**更新时间**: 2025-08-18  
**许可证**: MIT License