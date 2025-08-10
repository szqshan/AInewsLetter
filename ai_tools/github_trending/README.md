# GitHub Trending AI Tools 爬虫技术文档

## 目标网站信息

- **网站名称**: GitHub Trending
- **网站地址**: https://github.com/trending
- **网站类型**: 代码托管平台趋势页面
- **数据更新频率**: 实时更新
- **访问限制**: 相对宽松，但需要注意频率控制

## 爬虫方案概述

### 技术架构
- **爬虫类型**: 网页爬虫 + GitHub API
- **主要技术**: Python + requests + BeautifulSoup4 + GitHub API
- **数据格式**: HTML + JSON → Markdown
- **特色功能**: AI相关仓库识别和热度分析

### 核心功能
1. **趋势仓库**: 获取GitHub每日/每周/每月趋势仓库
2. **AI筛选**: 基于关键词和标签筛选AI相关项目
3. **仓库详情**: 获取仓库描述、星数、语言等信息
4. **作者信息**: 提取仓库作者和贡献者信息
5. **热度分析**: 基于多维度指标评估项目热度

## 爬取方式详解

### 1. GitHub Trending页面结构

#### 主要URL格式
```
# 总体趋势
https://github.com/trending

# 按语言筛选
https://github.com/trending/python
https://github.com/trending/javascript
https://github.com/trending/jupyter-notebook

# 按时间范围
https://github.com/trending?since=daily
https://github.com/trending?since=weekly
https://github.com/trending?since=monthly

# 组合筛选
https://github.com/trending/python?since=weekly
```

#### URL参数说明
- `since`: 时间范围 (daily, weekly, monthly)
- 路径中的语言: 编程语言筛选
- `spoken_language_code`: 自然语言筛选

### 2. 页面HTML结构分析

#### 仓库列表结构
```html
<article class="Box-row">
  <h2 class="h3 lh-condensed">
    <a href="/author/repo-name" data-hydro-click="...">
      <span class="text-normal">author /</span>
      repo-name
    </a>
  </h2>
  
  <p class="col-9 color-fg-muted my-1 pr-4">
    Repository description goes here...
  </p>
  
  <div class="f6 color-fg-muted mt-2">
    <span class="d-inline-block ml-0 mr-3">
      <span class="repo-language-color" style="background-color: #3572A5;"></span>
      <span itemprop="programmingLanguage">Python</span>
    </span>
    
    <a class="Link--muted d-inline-block mr-3" href="/author/repo/stargazers">
      <svg class="octicon octicon-star" viewBox="0 0 16 16" width="16" height="16">
        <!-- star icon -->
      </svg>
      1,234
    </a>
    
    <a class="Link--muted d-inline-block mr-3" href="/author/repo/network/members">
      <svg class="octicon octicon-repo-forked" viewBox="0 0 16 16" width="16" height="16">
        <!-- fork icon -->
      </svg>
      567
    </a>
    
    <span class="d-inline-block float-sm-right">
      <svg class="octicon octicon-star" viewBox="0 0 16 16" width="16" height="16">
        <!-- star icon -->
      </svg>
      89 stars today
    </span>
  </div>
</article>
```

#### 关键CSS选择器
```python
SELECTORS = {
    'repo_articles': 'article.Box-row',
    'repo_link': 'h2.h3.lh-condensed a[href]',
    'repo_description': 'p.col-9.color-fg-muted.my-1.pr-4',
    'programming_language': 'span[itemprop="programmingLanguage"]',
    'star_count': 'a[href*="/stargazers"]',
    'fork_count': 'a[href*="/network/members"]',
    'stars_today': 'span.d-inline-block.float-sm-right',
    'language_color': 'span.repo-language-color',
    'topics': 'a.topic-tag.topic-tag-link'
}
```

### 3. 数据提取算法

#### 仓库基本信息提取
```python
def extract_repo_info(article_element):
    repo_info = {}
    
    # 提取仓库名称和链接
    repo_link = article_element.select_one('h2.h3.lh-condensed a[href]')
    if repo_link:
        href = repo_link.get('href')
        repo_info['url'] = f"https://github.com{href}"
        
        # 解析作者和仓库名
        path_parts = href.strip('/').split('/')
        if len(path_parts) >= 2:
            repo_info['author'] = path_parts[0]
            repo_info['name'] = path_parts[1]
            repo_info['full_name'] = f"{path_parts[0]}/{path_parts[1]}"
    
    # 提取描述
    description_element = article_element.select_one('p.col-9.color-fg-muted.my-1.pr-4')
    if description_element:
        repo_info['description'] = description_element.get_text(strip=True)
    
    # 提取编程语言
    language_element = article_element.select_one('span[itemprop="programmingLanguage"]')
    if language_element:
        repo_info['language'] = language_element.get_text(strip=True)
        
        # 提取语言颜色
        color_element = article_element.select_one('span.repo-language-color')
        if color_element:
            style = color_element.get('style', '')
            color_match = re.search(r'background-color:\s*([^;]+)', style)
            if color_match:
                repo_info['language_color'] = color_match.group(1).strip()
    
    return repo_info
```

#### 统计数据提取
```python
def extract_repo_stats(article_element):
    stats = {
        'stars': 0,
        'forks': 0,
        'stars_today': 0
    }
    
    # 提取总星数
    star_link = article_element.select_one('a[href*="/stargazers"]')
    if star_link:
        star_text = star_link.get_text(strip=True)
        stars = parse_github_number(star_text)
        stats['stars'] = stars
    
    # 提取Fork数
    fork_link = article_element.select_one('a[href*="/network/members"]')
    if fork_link:
        fork_text = fork_link.get_text(strip=True)
        forks = parse_github_number(fork_text)
        stats['forks'] = forks
    
    # 提取今日新增星数
    stars_today_element = article_element.select_one('span.d-inline-block.float-sm-right')
    if stars_today_element:
        today_text = stars_today_element.get_text(strip=True)
        today_match = re.search(r'(\d+(?:,\d+)*)\s*stars?\s*today', today_text)
        if today_match:
            stats['stars_today'] = parse_github_number(today_match.group(1))
    
    return stats

def parse_github_number(text):
    """解析GitHub数字格式 (支持k, m后缀)"""
    if not text:
        return 0
    
    # 移除逗号
    text = text.replace(',', '')
    
    # 处理k, m后缀
    if text.lower().endswith('k'):
        return int(float(text[:-1]) * 1000)
    elif text.lower().endswith('m'):
        return int(float(text[:-1]) * 1000000)
    else:
        # 提取纯数字
        number_match = re.search(r'\d+', text)
        if number_match:
            return int(number_match.group())
    
    return 0
```

### 4. AI相关仓库识别

#### 关键词匹配策略
```python
AI_KEYWORDS = {
    'core_ai': [
        'artificial intelligence', 'machine learning', 'deep learning',
        'neural network', 'ai', 'ml', 'dl', 'nn'
    ],
    'frameworks': [
        'tensorflow', 'pytorch', 'keras', 'scikit-learn', 'pandas',
        'numpy', 'opencv', 'transformers', 'huggingface'
    ],
    'domains': [
        'computer vision', 'natural language processing', 'nlp', 'cv',
        'reinforcement learning', 'rl', 'generative ai', 'llm',
        'large language model', 'chatbot', 'gpt', 'bert'
    ],
    'applications': [
        'image recognition', 'object detection', 'face recognition',
        'speech recognition', 'text generation', 'image generation',
        'recommendation system', 'anomaly detection'
    ]
}

def is_ai_related(repo_info):
    """判断仓库是否与AI相关"""
    text_to_check = [
        repo_info.get('name', ''),
        repo_info.get('description', ''),
        ' '.join(repo_info.get('topics', []))
    ]
    
    combined_text = ' '.join(text_to_check).lower()
    
    # 计算匹配分数
    score = 0
    matched_keywords = []
    
    for category, keywords in AI_KEYWORDS.items():
        category_matches = 0
        for keyword in keywords:
            if keyword in combined_text:
                category_matches += 1
                matched_keywords.append(keyword)
        
        # 不同类别的权重
        weights = {
            'core_ai': 3,
            'frameworks': 2,
            'domains': 2,
            'applications': 1
        }
        
        score += category_matches * weights.get(category, 1)
    
    # 判断阈值
    is_ai = score >= 3
    
    return {
        'is_ai_related': is_ai,
        'ai_score': score,
        'matched_keywords': matched_keywords
    }
```

### 5. GitHub API增强数据

#### API调用获取详细信息
```python
import requests
from datetime import datetime

class GitHubAPIClient:
    def __init__(self, token=None):
        self.token = token
        self.base_url = 'https://api.github.com'
        self.headers = {
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'AI-Newsletter-Spider/1.0'
        }
        if token:
            self.headers['Authorization'] = f'token {token}'
    
    def get_repo_details(self, owner, repo):
        """获取仓库详细信息"""
        url = f"{self.base_url}/repos/{owner}/{repo}"
        
        try:
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"API request failed: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"API request error: {e}")
            return None
    
    def get_repo_topics(self, owner, repo):
        """获取仓库标签"""
        url = f"{self.base_url}/repos/{owner}/{repo}/topics"
        headers = {**self.headers, 'Accept': 'application/vnd.github.mercy-preview+json'}
        
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                return response.json().get('names', [])
            return []
        except Exception as e:
            logger.error(f"Topics request error: {e}")
            return []
    
    def get_repo_languages(self, owner, repo):
        """获取仓库使用的编程语言"""
        url = f"{self.base_url}/repos/{owner}/{repo}/languages"
        
        try:
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                return response.json()
            return {}
        except Exception as e:
            logger.error(f"Languages request error: {e}")
            return {}
```

#### 数据增强处理
```python
def enhance_repo_with_api(repo_info, api_client):
    """使用API增强仓库信息"""
    if not repo_info.get('author') or not repo_info.get('name'):
        return repo_info
    
    # 获取详细信息
    api_data = api_client.get_repo_details(repo_info['author'], repo_info['name'])
    if api_data:
        repo_info.update({
            'created_at': api_data.get('created_at'),
            'updated_at': api_data.get('updated_at'),
            'pushed_at': api_data.get('pushed_at'),
            'size': api_data.get('size'),
            'open_issues_count': api_data.get('open_issues_count'),
            'watchers_count': api_data.get('watchers_count'),
            'subscribers_count': api_data.get('subscribers_count'),
            'network_count': api_data.get('network_count'),
            'license': api_data.get('license', {}).get('name') if api_data.get('license') else None,
            'default_branch': api_data.get('default_branch'),
            'has_wiki': api_data.get('has_wiki'),
            'has_pages': api_data.get('has_pages'),
            'has_downloads': api_data.get('has_downloads')
        })
    
    # 获取标签
    topics = api_client.get_repo_topics(repo_info['author'], repo_info['name'])
    repo_info['topics'] = topics
    
    # 获取语言分布
    languages = api_client.get_repo_languages(repo_info['author'], repo_info['name'])
    repo_info['languages'] = languages
    
    return repo_info
```

## 热度评分算法

### 综合热度计算
```python
def calculate_trending_score(repo_info):
    """计算仓库热度分数"""
    factors = {
        'stars_today': repo_info.get('stars_today', 0),
        'total_stars': repo_info.get('stars', 0),
        'forks': repo_info.get('forks', 0),
        'watchers': repo_info.get('watchers_count', 0),
        'open_issues': repo_info.get('open_issues_count', 0),
        'recency': calculate_repo_recency(repo_info),
        'activity': calculate_repo_activity(repo_info),
        'ai_relevance': repo_info.get('ai_score', 0)
    }
    
    # 权重配置
    weights = {
        'stars_today': 0.25,    # 今日新增星数最重要
        'total_stars': 0.20,    # 总星数
        'forks': 0.15,          # Fork数
        'watchers': 0.10,       # 关注者
        'open_issues': 0.05,    # 活跃度指标
        'recency': 0.10,        # 项目新鲜度
        'activity': 0.10,       # 活跃度
        'ai_relevance': 0.05    # AI相关性
    }
    
    # 归一化处理
    normalized_factors = {
        'stars_today': min(factors['stars_today'] / 100, 10),
        'total_stars': min(factors['total_stars'] / 10000, 10),
        'forks': min(factors['forks'] / 1000, 10),
        'watchers': min(factors['watchers'] / 1000, 10),
        'open_issues': min(factors['open_issues'] / 100, 10),
        'recency': factors['recency'],
        'activity': factors['activity'],
        'ai_relevance': min(factors['ai_relevance'], 10)
    }
    
    # 计算加权分数
    score = sum(normalized_factors[key] * weights[key] for key in normalized_factors)
    
    return min(score, 10)  # 限制最高分为10

def calculate_repo_recency(repo_info):
    """计算项目新鲜度"""
    created_at = repo_info.get('created_at')
    if not created_at:
        return 5  # 默认中等分数
    
    try:
        created_date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
        days_since_creation = (datetime.now(created_date.tzinfo) - created_date).days
        
        if days_since_creation <= 30:
            return 10  # 新项目
        elif days_since_creation <= 365:
            return 8   # 较新项目
        elif days_since_creation <= 1095:  # 3年
            return 6   # 成熟项目
        else:
            return 4   # 老项目
    except:
        return 5

def calculate_repo_activity(repo_info):
    """计算项目活跃度"""
    pushed_at = repo_info.get('pushed_at')
    if not pushed_at:
        return 3  # 默认较低分数
    
    try:
        pushed_date = datetime.fromisoformat(pushed_at.replace('Z', '+00:00'))
        days_since_push = (datetime.now(pushed_date.tzinfo) - pushed_date).days
        
        if days_since_push <= 7:
            return 10  # 非常活跃
        elif days_since_push <= 30:
            return 8   # 活跃
        elif days_since_push <= 90:
            return 6   # 一般活跃
        elif days_since_push <= 365:
            return 4   # 不太活跃
        else:
            return 2   # 不活跃
    except:
        return 3
```

## 反爬虫应对策略

### 1. 请求头配置
```python
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Cache-Control': 'no-cache',
    'Pragma': 'no-cache',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Upgrade-Insecure-Requests': '1'
}
```

### 2. 访问频率控制
```python
RATE_LIMIT_CONFIG = {
    'web_requests_per_minute': 20,  # 网页请求频率
    'api_requests_per_hour': 5000,  # API请求频率（有token）
    'delay_between_requests': 3,    # 请求间隔
    'random_delay_range': (2, 8),   # 随机延迟
    'max_retries': 3,
    'backoff_factor': 2
}
```

### 3. 会话管理
```python
class GitHubSession:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self.last_request_time = 0
        self.request_count = 0
    
    def get(self, url, **kwargs):
        # 频率控制
        self._rate_limit()
        
        try:
            response = self.session.get(url, **kwargs)
            self.request_count += 1
            
            if response.status_code == 429:  # Rate limited
                retry_after = int(response.headers.get('Retry-After', 60))
                logger.warning(f"Rate limited, waiting {retry_after} seconds")
                time.sleep(retry_after)
                return self.get(url, **kwargs)
            
            return response
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            return None
    
    def _rate_limit(self):
        now = time.time()
        time_since_last = now - self.last_request_time
        
        min_interval = 60 / RATE_LIMIT_CONFIG['web_requests_per_minute']
        if time_since_last < min_interval:
            sleep_time = min_interval - time_since_last
            time.sleep(sleep_time)
        
        # 添加随机延迟
        min_delay, max_delay = RATE_LIMIT_CONFIG['random_delay_range']
        random_delay = random.uniform(min_delay, max_delay)
        time.sleep(random_delay)
        
        self.last_request_time = time.time()
```

## 配置参数

### 爬取配置
```python
GITHUB_TRENDING_CONFIG = {
    'base_url': 'https://github.com/trending',
    'time_ranges': ['daily', 'weekly'],  # 不包含monthly以减少重复
    'languages': [
        'python', 'javascript', 'typescript', 'jupyter-notebook',
        'go', 'rust', 'cpp', 'java', 'swift'
    ],
    'max_pages': 3,  # 每个分类最多爬取页数
    'min_stars': 10,  # 最小星数过滤
    'github_token': None,  # GitHub API token
    'use_api_enhancement': True
}
```

### AI识别配置
```python
AI_FILTER_CONFIG = {
    'min_ai_score': 3,  # 最小AI相关性分数
    'required_keywords': [],  # 必须包含的关键词
    'excluded_keywords': ['tutorial', 'course', 'book'],  # 排除的关键词
    'language_preferences': {
        'python': 1.2,  # Python项目加权
        'jupyter-notebook': 1.1,
        'r': 1.1
    }
}
```

## 数据输出格式

### JSON格式
```json
{
  "repo_id": "github_trending_001",
  "full_name": "openai/gpt-4",
  "name": "gpt-4",
  "author": "openai",
  "description": "GPT-4 implementation and examples",
  "url": "https://github.com/openai/gpt-4",
  "language": "Python",
  "language_color": "#3572A5",
  "languages": {
    "Python": 85.2,
    "JavaScript": 10.1,
    "Shell": 4.7
  },
  "stats": {
    "stars": 15420,
    "forks": 2341,
    "watchers": 890,
    "open_issues": 45,
    "stars_today": 127
  },
  "dates": {
    "created_at": "2023-03-15T10:30:00Z",
    "updated_at": "2024-01-15T14:22:00Z",
    "pushed_at": "2024-01-15T14:22:00Z"
  },
  "topics": [
    "artificial-intelligence",
    "machine-learning",
    "gpt",
    "language-model"
  ],
  "ai_analysis": {
    "is_ai_related": true,
    "ai_score": 8.5,
    "matched_keywords": [
      "artificial intelligence",
      "gpt",
      "language model"
    ]
  },
  "trending_score": 9.2,
  "quality_score": 8.7,
  "license": "MIT",
  "has_wiki": true,
  "has_pages": true
}
```

## 常见问题与解决方案

### 1. 页面结构变化
**问题**: GitHub更新Trending页面结构
**解决**: 
- 定期检查CSS选择器有效性
- 实现多套解析规则备用
- 添加结构变化自动检测

### 2. API限制
**问题**: GitHub API请求限制
**解决**: 
- 使用Personal Access Token提高限额
- 实现智能缓存机制
- 优先级队列处理重要仓库

### 3. 重复数据
**问题**: 同一仓库在不同时间段出现
**解决**: 
- 基于仓库全名去重
- 保留最新的统计数据
- 合并不同时间段的趋势信息

### 4. AI识别准确性
**问题**: 误判非AI项目为AI相关
**解决**: 
- 优化关键词匹配算法
- 增加上下文分析
- 人工标注样本训练分类器

## 维护建议

### 定期检查项目
1. **页面结构**: 监控GitHub Trending页面变化
2. **API变化**: 关注GitHub API更新
3. **关键词更新**: 定期更新AI相关关键词库
4. **数据质量**: 检查AI识别准确性

### 优化方向
1. **智能分类**: 基于机器学习的项目分类
2. **趋势预测**: 预测项目未来热度
3. **社区分析**: 分析项目社区活跃度
4. **技术栈分析**: 深度分析项目技术栈

## 相关资源

- [GitHub Trending](https://github.com/trending)
- [GitHub API文档](https://docs.github.com/en/rest)
- [GitHub搜索语法](https://docs.github.com/en/search-github/searching-on-github)
- [开源项目评估标准](https://opensource.guide/)