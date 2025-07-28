# AI Newsletter 项目

## 🎯 项目概述

AI Newsletter 是一个智能AI资讯聚合平台，自动采集各大AI网站的最新资讯，为用户提供个性化的AI新闻推荐。

**核心流程**：数据采集 → 数据存储 → API接口 → 前端展示

## 🏗️ 技术架构

### 后端技术栈（需讨论确认）
- **编程语言**：Python 3.9+ (需要确认是否可以使用python)
- **Web框架**：Flask (轻量级、简单易学) (需求确认框架我们自己定是否可以)
- **数据库**：PostgreSQL 13+ (功能强大的关系型数据库)
- **数据库操作**：原生SQL + psycopg2 (直接使用SQL语句操作数据库)
- **数据采集**：requests + BeautifulSoup4 (待讨论)

### 前端技术栈(还需讨论)
- **框架**：Vue.js 3 + Element Plus
- **构建工具**：Vite
- **HTTP客户端**：Axios
- **路由**：Vue Router 4

### 数据采集目标
- **机器之心** (jiqizhixin.com) - AI新闻、技术文章、行业动态
- **量子位** (qbitai.com) - AI资讯、技术解读、产品评测
- **GitHub Trending** - 热门AI项目、开源工具
- **arXiv论文** - 最新AI论文摘要

## 📋 开发顺序

### 🔧 第一阶段：基础架构和数据采集

#### 第1步: 基础架构
- 项目结构搭建
- 数据库设计和创建 (PostgreSQL)
- Flask应用初始化
- 基础配置和环境设置

#### 第2步: 数据采集系统
- 爬虫框架搭建 (requests + BeautifulSoup4)
- 多站点爬虫实现：
  - 机器之心 (jiqizhixin.com)
  - 量子位 (qbitai.com) 
  - GitHub Trending
  - arXiv论文
- 数据清洗和去重 (基于URL去重)
- JSON格式数据存储到数据库
- 数据打标签，分类，提取关键词，

### 🎨 第二阶段：API接口和推荐系统 

#### 第1步: API接口开发
- 文章CRUD API (增删改查)
- 文章列表API (分页、排序、筛选)
- 分类和标签管理API
- 搜索功能API
- 浏览统计API

#### 第2步: 推荐系统
- 推荐算法实现 (基于热度和内容)
- 热门文章排序 (结合阅读量、时间衰减)
- 推荐API接口
- 性能优化

### 🚀 第三阶段：前端开发和整合
1. **前端页面开发** - Vue.js 3 + Element Plus界面
2. **API对接** - 前端调用后端接口获取数据
3. **交互功能** - 搜索、筛选、分页等功能
4. **响应式设计** - 适配移动端和桌面端
5. **整体测试** - 前后端联调测试
6. **部署上线** - 项目部署和文档完善


## 📁 项目结构

```
ai-newsletter/
├── backend/                    # 后端代码
│   ├── app.py                  # Flask主程序文件
│   ├── database.py             # 数据库连接和SQL操作
│   ├── api.py                  # API接口
│   ├── crawler/                # 数据采集模块
│   │   ├── __init__.py         # 爬虫模块初始化
│   │   ├── base_crawler.py     # 爬虫基类
│   │   ├── jiqizhixin.py       # 机器之心爬虫
│   │   ├── qbitai.py           # 量子位爬虫
│   │   ├── github.py           # GitHub Trending爬虫
│   │   ├── arxiv.py            # arXiv爬虫
│   │   └── utils.py            # 爬虫工具函数
│   ├── config.py               # 配置文件
│   ├── requirements.txt        # 依赖包列表
│   └── README.md               # 后端说明文档
├── frontend/                   # 前端代码
│   ├── src/                    # 源码
│   ├── public/                 # 静态资源
│   └── package.json            # 前端依赖
└── docs/                       # 文档
    ├── Backend_Development_Plan.md
    └── Frontend_Development_Plan.md
```

**开发原则：先跑通核心流程，再完善细节功能！** 🚀