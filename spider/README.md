# AI内容聚合爬虫系统

一个全面的AI内容聚合爬虫系统，用于自动收集、分析和整理来自各种平台的AI相关内容，包括学术论文、新闻资讯和工具项目。

## 🚀 功能特性

- **多平台支持**: 支持arXiv、Google Scholar、Hugging Face、GitHub Trending等多个平台
- **智能质量评估**: 基于多维度指标自动评估内容质量
- **结构化存储**: 自动生成JSON和Markdown格式的结构化数据
- **模块化设计**: 易于扩展和维护的模块化架构
- **异步处理**: 支持并发爬取，提高效率
- **智能去重**: 自动识别和过滤重复内容
- **定时任务**: 支持定时自动运行

## 📁 项目结构

```
spider/
├── academic_papers/          # 学术论文爬虫
│   ├── arxiv/               # arXiv论文
│   ├── google_scholar/      # Google Scholar
│   ├── papers_with_code/    # Papers with Code
│   ├── semantic_scholar/    # Semantic Scholar
│   ├── acl_anthology/       # ACL Anthology
│   └── conference_papers/   # 会议论文
├── ai_news/                 # AI新闻爬虫
│   ├── huggingface_daily/   # Hugging Face每日论文
│   ├── reddit_ai/           # Reddit AI社区
│   ├── towards_datascience/ # Towards Data Science
│   ├── openai_blog/         # OpenAI博客
│   ├── google_ai_blog/      # Google AI博客
│   └── chinese_media/       # 中文AI媒体
├── ai_tools/                # AI工具爬虫
│   ├── github_trending/     # GitHub Trending
│   ├── product_hunt/        # Product Hunt
│   ├── awesome_lists/       # Awesome列表
│   └── tool_directories/    # 工具目录
├── shared/                  # 共享模块
│   ├── config.py           # 全局配置
│   ├── utils.py            # 工具函数
│   └── quality_scorer.py   # 质量评估
├── data/                    # 数据存储
│   ├── raw/                # 原始数据
│   ├── processed/          # 处理后数据
│   └── exports/            # 导出数据
├── main.py                 # 主控制脚本
├── requirements.txt        # 依赖列表
└── README.md              # 项目说明
```

## 🛠️ 安装和配置

### 1. 环境要求

- Python 3.8+
- pip 或 conda

### 2. 安装依赖

```bash
# 克隆项目
git clone <repository-url>
cd spider

# 安装依赖
pip install -r requirements.txt
```

### 3. 配置设置

编辑 `shared/config.py` 文件，根据需要调整配置参数：

```python
# 示例配置
ARXIV_CONFIG = {
    'max_results': 50,
    'categories': ['cs.AI', 'cs.LG', 'cs.CL'],
    'search_terms': ['artificial intelligence', 'machine learning']
}
```

## 🚀 使用方法

### 1. 运行所有爬虫

```bash
python main.py
```

### 2. 运行特定类型的爬虫

```bash
# 只运行学术论文爬虫
python main.py --type academic

# 只运行AI新闻爬虫
python main.py --type news

# 只运行AI工具爬虫
python main.py --type tools
```

### 3. 运行单个爬虫

```bash
# 运行arXiv爬虫
python academic_papers/arxiv/spider.py

# 运行GitHub Trending爬虫
python ai_tools/github_trending/spider.py
```

## 📊 数据输出

### 输出格式

每个爬虫都会生成两种格式的输出：

1. **JSON格式**: 结构化数据，便于程序处理
2. **Markdown格式**: 人类可读的报告格式

### 输出示例

#### JSON格式
```json
{
  "title": "Attention Is All You Need",
  "authors": "Vaswani et al.",
  "abstract": "The dominant sequence transduction models...",
  "url": "https://arxiv.org/abs/1706.03762",
  "citations": 50000,
  "quality_score": {
    "total_score": 95.5,
    "citation_score": 100,
    "venue_score": 90,
    "recency_score": 85
  },
  "scraped_at": "2024-01-15T10:30:00"
}
```

#### Markdown格式
```markdown
# arXiv AI Papers - 2024-01-15

## 1. Attention Is All You Need

**作者**: Vaswani et al.
**引用数**: 50,000
**质量评分**: 95.5/100

**摘要**: The dominant sequence transduction models...

**链接**: https://arxiv.org/abs/1706.03762
```

## 🔧 质量评估系统

系统内置智能质量评估功能，基于多个维度对内容进行评分：

### 学术论文评估
- **引用数量** (30%): 论文的影响力指标
- **发表venue** (25%): 会议/期刊的声誉
- **作者/机构** (20%): 作者和机构的权威性
- **时效性** (15%): 论文的新颖程度
- **关键词匹配** (10%): 与AI领域的相关性

### AI新闻评估
- **来源可靠性** (30%): 新闻来源的权威性
- **内容质量** (25%): 内容的深度和准确性
- **时效性** (20%): 新闻的新鲜程度
- **参与度** (15%): 用户互动指标
- **关键词匹配** (10%): 与AI领域的相关性

### AI工具评估
- **受欢迎程度** (25%): GitHub stars、下载量等
- **活跃度** (25%): 更新频率、提交活动
- **功能性** (20%): 工具的实用性和完整性
- **维护状态** (15%): 项目的维护情况
- **文档质量** (15%): 文档的完整性和清晰度

## 🔄 定时任务

可以使用系统的定时任务功能自动运行爬虫：

```python
# 示例：每天运行一次
from apscheduler.schedulers.blocking import BlockingScheduler

scheduler = BlockingScheduler()
scheduler.add_job(main, 'cron', hour=9)  # 每天9点运行
scheduler.start()
```

## 📈 监控和日志

系统提供详细的日志记录和监控功能：

- **运行日志**: 记录爬虫运行状态和错误信息
- **性能监控**: 监控爬取速度和成功率
- **数据统计**: 统计爬取的数据量和质量分布

## 🛡️ 反爬虫策略

系统内置多种反爬虫策略：

- **请求间隔**: 控制请求频率，避免被封IP
- **User-Agent轮换**: 模拟不同浏览器访问
- **代理支持**: 支持代理池轮换
- **重试机制**: 自动重试失败的请求
- **缓存机制**: 避免重复请求相同内容

## 🔧 扩展开发

### 添加新的爬虫

1. 在相应目录下创建新的爬虫文件
2. 继承基础爬虫类
3. 实现必要的方法
4. 在主控制脚本中注册新爬虫

```python
class NewSpider:
    def __init__(self):
        # 初始化代码
        pass
    
    def crawl(self):
        # 爬取逻辑
        pass
    
    def parse(self, response):
        # 解析逻辑
        pass
```

### 自定义质量评估

可以在 `shared/quality_scorer.py` 中添加自定义的评估逻辑：

```python
def custom_score_method(self, item):
    # 自定义评分逻辑
    score = 0
    # 计算分数
    return score
```

## 📝 配置说明

### 全局配置 (shared/config.py)

```python
# 项目根目录
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

# 数据存储路径
DATA_PATHS = {
    'raw': os.path.join(PROJECT_ROOT, 'data', 'raw'),
    'processed': os.path.join(PROJECT_ROOT, 'data', 'processed'),
    'exports': os.path.join(PROJECT_ROOT, 'data', 'exports')
}

# 爬虫通用配置
CRAWLER_CONFIG = {
    'request_delay': 2,  # 请求间隔（秒）
    'max_retries': 3,    # 最大重试次数
    'timeout': 30,       # 请求超时（秒）
    'user_agents': [     # User-Agent列表
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    ]
}
```

### 平台特定配置

每个平台都有独立的配置选项，可以根据需要调整：

```python
# arXiv配置
ARXIV_CONFIG = {
    'base_url': 'http://export.arxiv.org/api/query',
    'max_results': 100,
    'categories': ['cs.AI', 'cs.LG', 'cs.CL', 'cs.CV'],
    'search_terms': [
        'artificial intelligence',
        'machine learning',
        'deep learning',
        'neural network'
    ]
}

# GitHub配置
GITHUB_CONFIG = {
    'base_url': 'https://api.github.com',
    'token': None,  # GitHub API token (可选)
    'languages': ['python', 'javascript', 'typescript'],
    'min_stars': 100,
    'ai_keywords': [
        'artificial intelligence',
        'machine learning',
        'deep learning'
    ]
}
```

## 🐛 故障排除

### 常见问题

1. **请求被拒绝**
   - 检查请求间隔设置
   - 更换User-Agent
   - 使用代理

2. **解析失败**
   - 检查网站结构是否变化
   - 更新解析规则
   - 检查编码问题

3. **内存不足**
   - 减少并发数量
   - 增加分批处理
   - 优化数据结构

### 调试模式

启用调试模式获取详细日志：

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 📄 许可证

MIT License

## 🤝 贡献

欢迎提交Issue和Pull Request！

## 📞 联系方式

如有问题或建议，请通过以下方式联系：

- Email: your-email@example.com
- GitHub: https://github.com/your-username/ai-content-crawler

## 🙏 致谢

感谢所有为这个项目做出贡献的开发者和用户！

---

**注意**: 使用本系统时请遵守各平台的robots.txt和使用条款，合理控制爬取频率，尊重网站资源。