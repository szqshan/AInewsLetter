# AI Newsletter 后端开发方案

## 项目目标
开发一个AI资讯聚合平台，提供文章列表、详情、分类、标签、搜索等功能。
一句话说清楚开发流程：数据采集 -> 数据存储 -> API接口 -> 前端展示

## 🎯 后端架构概述

**AI Newsletter 后端**采用前后端分离架构，提供**RESTful API**服务，支持数据采集、用户管理、个性化推荐等核心功能。

### 核心功能模块
- 📰 **内容管理系统**：文章增删改查、分类管理
- 🕷️ **数据采集系统**：从各种网站抓取AI资讯
- 🎯 **推荐系统**：根据用户喜好推荐文章
- 📊 **数据分析**：统计用户行为，优化推荐

## 🏗️ 后端技术架构

### 技术栈说明
- **编程语言**：Python 3.9+  （需要确认是否可以使用python）
- **Web框架**：Flask (轻量级、简单易学)  （需求确认框架我们自己定是否可以）
- **数据库**：PostgreSQL 13+ (功能强大的关系型数据库)
- **数据库操作**：原生SQL + psycopg2 (直接使用SQL语句操作数据库)
- **数据采集**： (爬虫工具requests + BeautifulSoup4)（待讨论）


### 项目结构 (简化版)
```
backend/
├── app.py              # 主程序文件
├── database.py         # 数据库连接和SQL操作
├── api.py              # API接口
├── crawler/            # 数据采集模块
│   ├── __init__.py     # 爬虫模块初始化
│   ├── base_crawler.py # 爬虫基类
│   ├── jiqizhixin.py   # 机器之心爬虫
│   ├── qbitai.py       # 量子位爬虫
│   ├── github.py       # GitHub Trending爬虫
│   ├── arxiv.py        # arXiv爬虫
│   └── utils.py        # 爬虫工具函数
├── config.py           # 配置文件
├── requirements.txt    # 依赖包列表
└── README.md           # 说明文档
```
 
## 🔄 数据采集系统
### 数据采集需求
#### 🎯 采集目标网站
1. **机器之心** (jiqizhixin.com)
   - 采集内容：AI新闻、技术文章、行业动态
   - 分类：AI新闻、AI论文解读、行业分析

2. **量子位** (qbitai.com)
   - 采集内容：AI资讯、技术解读、产品评测
   - 分类：AI新闻、AI工具、技术分析

3. **GitHub Trending**
   - 采集内容：热门AI项目、开源工具
   - 分类：AI工具、开源项目

4. **arXiv论文**
   - 采集内容：最新AI论文摘要
   - 分类：AI论文、学术研究

#### 🛠️ 采集技术方案(具体方案根据数据源再讨论)
- **爬虫工具**：requests + BeautifulSoup4(待讨论)
- **数据格式**：JSON格式存储
- **采集频率**：每天定时采集
- **数据清洗**：去重、格式化、分类标记

#### 💾 数据存储流程
##### 1. 数据映射关系
```python
# 采集的JSON数据格式
crawled_data = {
    "title": "文章标题",           # -> articles.title
    "summary": "文章摘要",         # -> articles.summary  
    "content": "文章内容",         # -> articles.content
    "url": "文章链接",             # -> articles.url
    "category": "文章分类",        # -> articles.category
    "author": "作者信息",          # -> articles.author
    "source": "来源网站",          # -> articles.source
    "publish_date": "发布时间",    # -> articles.publish_date
    "tags": ["标签1", "标签2"]     # -> articles.tags (JSONB)
}
```

##### 2. 存储策略
- **去重处理**：根据URL去重，避免重复存储
- **数据清洗**：标题长度限制、内容格式化
- **分类映射**：将网站分类映射到标准分类
- **质量评分**：根据内容长度、来源等计算初始评分

##### 3. SQL插入示例
```sql
INSERT INTO articles (
    title, summary, content, url, category, 
    tags, author, source, publish_date, quality_score
) VALUES (
    %s, %s, %s, %s, %s, 
    %s, %s, %s, %s, %s
) ON CONFLICT (url) DO NOTHING;  -- 避免重复插入
```

## 💾 数据库设计

### 数据库表结构设计

**数据库**：PostgreSQL 13+  
**操作方式**：原生SQL语句
### 1. 文章表 (articles)
```sql
CREATE TABLE articles (
    id SERIAL PRIMARY KEY,              -- 文章ID，自增主键
    title VARCHAR(500) NOT NULL,        -- 文章标题，不能为空，最大500字符
    summary TEXT,                       -- 文章摘要，文本类型
    content TEXT,                       -- 文章内容，文本类型
    url VARCHAR(1000) NOT NULL UNIQUE,  -- 文章URL，不能为空且唯一，最大1000字符
    category VARCHAR(50) NOT NULL,      -- 'agent', 'news', 'papers', 'coding', 'tools'
    tags JSONB DEFAULT '[]',            -- 文章标签，JSON数组格式
    author VARCHAR(200),                -- 作者名称，最大200字符
    source VARCHAR(100) NOT NULL,       -- 数据来源
    publish_date TIMESTAMP,             -- 文章发布时间
    view_count INTEGER DEFAULT 0,       -- 浏览次数，默认0
    like_count INTEGER DEFAULT 0,       -- 点赞数，默认0

    quality_score FLOAT DEFAULT 0.0,    -- 内容质量评分
    is_active BOOLEAN DEFAULT TRUE,     -- 文章状态，默认激活
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  -- 记录创建时间
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP   -- 记录更新时间
);

-- 索引
-- 为文章分类创建索引,加速按分类查询
CREATE INDEX idx_articles_category ON articles(category);

-- 为文章来源创建索引,加速按来源网站筛选
CREATE INDEX idx_articles_source ON articles(source);

-- 为发布日期创建降序索引,优化按时间排序和筛选
CREATE INDEX idx_articles_publish_date ON articles(publish_date DESC);

-- 为质量评分创建降序索引,用于按质量排序推荐
CREATE INDEX idx_articles_quality_score ON articles(quality_score DESC);

-- 为文章URL创建索引,加速URL查重和定位
CREATE INDEX idx_articles_url ON articles(url);

### 2. 文章浏览记录表 (article_views)
```sql
-- 创建文章浏览记录表
CREATE TABLE article_views (
    id SERIAL PRIMARY KEY,                -- 浏览记录ID，自增主键
    article_id INTEGER REFERENCES articles(id) ON DELETE CASCADE,  -- 关联的文章ID，级联删除
    ip_address INET,                      -- 访问者IP地址
    user_agent TEXT,                      -- 访问者浏览器信息
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP  -- 浏览时间戳
);

-- 索引
-- 为文章ID创建索引，加速按文章ID查询浏览记录
CREATE INDEX idx_views_article_id ON article_views(article_id);

-- 为创建时间创建降序索引，优化按时间查询和统计浏览量
CREATE INDEX idx_views_created_at ON article_views(created_at DESC);

-- 为IP地址创建索引，用于分析用户访问行为和防爬虫
CREATE INDEX idx_views_ip_address ON article_views(ip_address);
```

## 🎯 个性化推荐系统（后续开发）

### 功能需求
- **浏览行为分析**：记录文章浏览次数和热度
- **内容推荐**：基于文章热度和分类推荐相关文章
- **热门内容**：展示全站热门文章

### 推荐策略
- **内容过滤**：基于文章内容特征推荐
- **热度排序**：结合阅读量等指标
- **时间衰减**：新文章权重更高
- **分类推荐**：基于文章分类推荐相关内容

## 📊 API接口设计

### 文章相关API
- **GET /api/articles** - 获取文章列表
  - 参数：category, page, per_page, sort_by
  - 返回：文章列表、分页信息
  - 排序：发布时间、浏览量、点赞数

- **GET /api/articles/{id}** - 获取文章详情
  - 返回：文章完整内容
  - 功能：记录浏览行为

## 📋 开发计划

### 第一阶段：基础架构和数据采集

#### 第1步: 基础架构
- 项目结构搭建
- 数据库设计和创建
- Flask应用初始化
- 基础配置和环境设置

#### 第2步: 数据采集系统
- 爬虫框架搭建
- 多站点爬虫实现（机器之心、量子位、GitHub Trending、arXiv）
- 数据清洗和去重
- 数据存储到数据库

#### 第3步: 数据验证和优化
- 数据采集测试
- 数据质量检查
- 采集频率优化
- 错误处理机制

### 第二阶段：API接口和推荐系统

#### 第1步: API接口开发
- 文章CRUD API
- 分类和标签管理API
- 搜索功能API
- 浏览统计API

#### 第2步: 推荐系统
- 推荐算法实现
- 热门文章排序
- 推荐API接口
- 性能优化

#### 第3步: 测试和优化
- API接口测试
- 性能优化
- 错误处理
- 文档完善

**卧槽！** 后端开发计划安排得明明白白，按步骤搞定所有核心功能！

---

**总结：AI Newsletter 后端开发方案**
- 🏗️ **架构清晰**：模块化设计，易于维护和扩展
- 🚀 **性能优秀**：数据库优化，异步任务
- 🕷️ **数据丰富**：多渠道采集，智能去重，质量评分
- 🎯 **推荐精准**：基于热度和内容的推荐算法
- 📊 **接口完善**：RESTful API，文档齐全，易于对接

**功能强大，架构合理！** 🚀