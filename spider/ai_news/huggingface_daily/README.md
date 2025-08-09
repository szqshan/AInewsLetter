# Hugging Face Daily Papers 爬虫技术文档

## 目标网站信息

- **网站名称**: Hugging Face Daily Papers
- **网站地址**: https://huggingface.co/papers
- **网站类型**: AI论文聚合平台
- **数据更新频率**: 每日更新
- **访问限制**: 相对宽松，但需要合理控制频率

## 爬虫方案概述

### 技术架构
- **爬虫类型**: API + 网页爬虫混合
- **主要技术**: Python + requests + BeautifulSoup4
- **数据格式**: JSON → Markdown
- **特色功能**: 支持论文趋势分析和热度评估

### 核心功能
1. **每日论文**: 获取每日推荐的AI论文
2. **热门论文**: 基于点赞数和评论数排序
3. **分类筛选**: 按AI领域分类筛选论文
4. **作者信息**: 提取论文作者和机构
5. **论文摘要**: 获取论文摘要和关键信息

## 爬取方式详解

### 1. 页面URL结构

#### 主要页面
```
# 每日论文首页
https://huggingface.co/papers

# 按日期浏览
https://huggingface.co/papers?date=2024-01-15

# 按分类浏览
https://huggingface.co/papers?topic=computer-vision
https://huggingface.co/papers?topic=natural-language-processing
https://huggingface.co/papers?topic=machine-learning
```

#### URL参数说明
- `date`: 指定日期 (YYYY-MM-DD格式)
- `topic`: 论文分类
- `sort`: 排序方式 (trending, recent, discussed)
- `p`: 分页参数

### 2. 页面结构分析

#### 论文卡片结构
```html
<article class="flex flex-col overflow-hidden rounded-xl border">
  <div class="flex flex-1 flex-col justify-between p-6">
    <div class="flex-1">
      <div class="flex items-center gap-x-2 text-xs">
        <time datetime="2024-01-15">Jan 15</time>
        <span class="text-gray-500">•</span>
        <span class="text-gray-500">Computer Vision</span>
      </div>
      
      <div class="group mt-3">
        <h3 class="text-xl font-semibold text-gray-900">
          <a href="/papers/2401.xxxxx">
            论文标题
          </a>
        </h3>
        <p class="mt-3 line-clamp-3 text-sm text-gray-500">
          论文摘要内容...
        </p>
      </div>
      
      <div class="mt-6 flex items-center">
        <div class="flex-shrink-0">
          <span class="text-sm font-medium text-gray-900">
            作者姓名
          </span>
        </div>
        <div class="ml-auto flex items-center space-x-4">
          <button class="flex items-center space-x-1">
            <span class="text-sm text-gray-500">👍 42</span>
          </button>
          <button class="flex items-center space-x-1">
            <span class="text-sm text-gray-500">💬 8</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</article>
```

#### 关键CSS选择器
```python
SELECTORS = {
    'paper_cards': 'article.flex.flex-col.overflow-hidden.rounded-xl.border',
    'title': 'h3.text-xl.font-semibold a',
    'abstract': 'p.mt-3.line-clamp-3.text-sm.text-gray-500',
    'authors': '.flex-shrink-0 .text-sm.font-medium.text-gray-900',
    'date': 'time[datetime]',
    'category': '.text-gray-500:not(time)',
    'likes': 'button .text-sm.text-gray-500:contains("👍")',
    'comments': 'button .text-sm.text-gray-500:contains("💬")',
    'paper_link': 'h3 a[href^="/papers/"]',
    'next_page': 'a[rel="next"]'
}
```

### 3. 数据提取算法

#### 论文基本信息提取
```python
def extract_paper_info(card_element):
    paper_info = {}
    
    # 提取标题
    title_element = card_element.select_one('h3.text-xl.font-semibold a')
    if title_element:
        paper_info['title'] = title_element.get_text(strip=True)
        paper_info['paper_url'] = urljoin(base_url, title_element.get('href'))
    
    # 提取摘要
    abstract_element = card_element.select_one('p.mt-3.line-clamp-3')
    if abstract_element:
        paper_info['abstract'] = abstract_element.get_text(strip=True)
    
    # 提取发布日期
    date_element = card_element.select_one('time[datetime]')
    if date_element:
        paper_info['date'] = date_element.get('datetime')
        paper_info['display_date'] = date_element.get_text(strip=True)
    
    # 提取分类
    category_elements = card_element.select('.text-gray-500')
    for element in category_elements:
        text = element.get_text(strip=True)
        if text not in ['•'] and not text.startswith('👍') and not text.startswith('💬'):
            if element.name != 'time':
                paper_info['category'] = text
                break
    
    return paper_info
```

#### 作者信息提取
```python
def extract_authors(card_element):
    authors = []
    author_elements = card_element.select('.flex-shrink-0 .text-sm.font-medium.text-gray-900')
    
    for author_element in author_elements:
        author_name = author_element.get_text(strip=True)
        if author_name:
            # 检查是否有作者链接
            author_link = author_element.find_parent('a')
            author_info = {
                'name': author_name,
                'profile_url': urljoin(base_url, author_link.get('href')) if author_link else None
            }
            authors.append(author_info)
    
    return authors
```

#### 互动数据提取
```python
def extract_engagement_metrics(card_element):
    metrics = {
        'likes': 0,
        'comments': 0
    }
    
    # 提取点赞数
    like_elements = card_element.select('button .text-sm.text-gray-500')
    for element in like_elements:
        text = element.get_text(strip=True)
        if '👍' in text:
            like_match = re.search(r'👍\s*(\d+)', text)
            if like_match:
                metrics['likes'] = int(like_match.group(1))
        elif '💬' in text:
            comment_match = re.search(r'💬\s*(\d+)', text)
            if comment_match:
                metrics['comments'] = int(comment_match.group(1))
    
    return metrics
```

### 4. 论文详情页爬取

#### 详情页URL格式
```
https://huggingface.co/papers/2401.xxxxx
```

#### 详情页数据提取
```python
def extract_paper_details(paper_url):
    response = requests.get(paper_url, headers=HEADERS)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    details = {}
    
    # 提取arXiv ID
    arxiv_link = soup.select_one('a[href*="arxiv.org"]')
    if arxiv_link:
        arxiv_url = arxiv_link.get('href')
        arxiv_id_match = re.search(r'arxiv\.org/abs/([\d\.]+)', arxiv_url)
        if arxiv_id_match:
            details['arxiv_id'] = arxiv_id_match.group(1)
            details['arxiv_url'] = arxiv_url
    
    # 提取PDF链接
    pdf_link = soup.select_one('a[href*=".pdf"]')
    if pdf_link:
        details['pdf_url'] = pdf_link.get('href')
    
    # 提取GitHub链接
    github_link = soup.select_one('a[href*="github.com"]')
    if github_link:
        details['github_url'] = github_link.get('href')
    
    # 提取完整摘要
    abstract_element = soup.select_one('.prose .text-gray-700')
    if abstract_element:
        details['full_abstract'] = abstract_element.get_text(strip=True)
    
    return details
```

## 数据处理与分析

### 1. 热度评分算法
```python
def calculate_trending_score(paper):
    # 基于多个维度计算热度分数
    factors = {
        'likes': paper.get('likes', 0),
        'comments': paper.get('comments', 0),
        'recency': calculate_recency_factor(paper.get('date')),
        'category_weight': get_category_weight(paper.get('category'))
    }
    
    # 权重配置
    weights = {
        'likes': 0.4,
        'comments': 0.3,
        'recency': 0.2,
        'category_weight': 0.1
    }
    
    score = 0
    for factor, value in factors.items():
        score += value * weights[factor]
    
    return min(score, 10)  # 限制最高分为10

def calculate_recency_factor(date_str):
    """计算时效性因子"""
    if not date_str:
        return 0
    
    paper_date = datetime.strptime(date_str, '%Y-%m-%d')
    days_ago = (datetime.now() - paper_date).days
    
    # 越新的论文分数越高
    if days_ago <= 1:
        return 10
    elif days_ago <= 7:
        return 8
    elif days_ago <= 30:
        return 5
    else:
        return 2

def get_category_weight(category):
    """不同分类的权重"""
    category_weights = {
        'Computer Vision': 1.2,
        'Natural Language Processing': 1.2,
        'Machine Learning': 1.1,
        'Robotics': 1.0,
        'Audio': 0.9,
        'Tabular': 0.8
    }
    return category_weights.get(category, 1.0)
```

### 2. 分类标准化
```python
CATEGORY_MAPPING = {
    'Computer Vision': 'CV',
    'Natural Language Processing': 'NLP',
    'Machine Learning': 'ML',
    'Multimodal': 'MM',
    'Robotics': 'Robotics',
    'Audio': 'Audio',
    'Tabular': 'Tabular',
    'Reinforcement Learning': 'RL'
}

def normalize_category(category):
    return CATEGORY_MAPPING.get(category, 'Other')
```

### 3. 数据去重策略
```python
def deduplicate_papers(papers):
    seen_titles = set()
    seen_arxiv_ids = set()
    unique_papers = []
    
    for paper in papers:
        # 基于标题去重
        title_key = paper.get('title', '').lower().strip()
        arxiv_id = paper.get('arxiv_id')
        
        is_duplicate = False
        
        # 检查arXiv ID重复
        if arxiv_id and arxiv_id in seen_arxiv_ids:
            is_duplicate = True
        
        # 检查标题相似度
        if not is_duplicate and title_key:
            for seen_title in seen_titles:
                if calculate_title_similarity(title_key, seen_title) > 0.9:
                    is_duplicate = True
                    break
        
        if not is_duplicate:
            unique_papers.append(paper)
            seen_titles.add(title_key)
            if arxiv_id:
                seen_arxiv_ids.add(arxiv_id)
    
    return unique_papers

def calculate_title_similarity(title1, title2):
    """计算标题相似度"""
    from difflib import SequenceMatcher
    return SequenceMatcher(None, title1, title2).ratio()
```

## 反爬虫应对策略

### 1. 请求头配置
```python
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'DNT': '1',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Cache-Control': 'max-age=0'
}
```

### 2. 访问频率控制
```python
RATE_LIMIT_CONFIG = {
    'requests_per_minute': 30,  # 每分钟最多30个请求
    'delay_between_requests': 2,  # 请求间隔2秒
    'random_delay_range': (1, 5),  # 随机延迟1-5秒
    'max_retries': 3,
    'backoff_factor': 1.5
}

class RateLimiter:
    def __init__(self, config):
        self.config = config
        self.request_times = []
    
    def wait_if_needed(self):
        now = time.time()
        
        # 清理过期的请求记录
        cutoff_time = now - 60  # 1分钟前
        self.request_times = [t for t in self.request_times if t > cutoff_time]
        
        # 检查是否超过频率限制
        if len(self.request_times) >= self.config['requests_per_minute']:
            sleep_time = 60 - (now - self.request_times[0])
            if sleep_time > 0:
                time.sleep(sleep_time)
        
        # 添加随机延迟
        min_delay, max_delay = self.config['random_delay_range']
        delay = random.uniform(min_delay, max_delay)
        time.sleep(delay)
        
        # 记录请求时间
        self.request_times.append(now)
```

### 3. 错误处理与重试
```python
def robust_request(url, max_retries=3):
    for attempt in range(max_retries):
        try:
            response = requests.get(url, headers=HEADERS, timeout=30)
            
            if response.status_code == 200:
                return response
            elif response.status_code == 429:  # Too Many Requests
                wait_time = 2 ** attempt * 60  # 指数退避
                logger.warning(f"Rate limited, waiting {wait_time} seconds")
                time.sleep(wait_time)
            elif response.status_code >= 500:  # Server Error
                logger.warning(f"Server error {response.status_code}, retrying...")
                time.sleep(2 ** attempt)
            else:
                logger.error(f"HTTP {response.status_code}: {response.text}")
                break
                
        except requests.exceptions.RequestException as e:
            logger.warning(f"Request failed (attempt {attempt + 1}): {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
    
    return None
```

## 配置参数

### 爬取配置
```python
HUGGINGFACE_CONFIG = {
    'base_url': 'https://huggingface.co/papers',
    'max_pages': 5,
    'papers_per_page': 20,
    'date_range': 7,  # 爬取最近7天的论文
    'categories': [
        'Computer Vision',
        'Natural Language Processing',
        'Machine Learning',
        'Multimodal',
        'Robotics'
    ],
    'min_engagement': {
        'likes': 5,
        'comments': 1
    }
}
```

### 质量过滤配置
```python
QUALITY_FILTERS = {
    'min_abstract_length': 100,
    'required_fields': ['title', 'abstract', 'authors'],
    'exclude_keywords': ['survey', 'review', 'tutorial'],
    'min_trending_score': 3.0,
    'max_days_old': 30
}
```

## 数据输出格式

### JSON格式
```json
{
  "paper_id": "hf_2024_01_15_001",
  "title": "Attention Is All You Need for Video Understanding",
  "abstract": "We present a novel approach...",
  "authors": [
    {
      "name": "John Doe",
      "profile_url": "https://huggingface.co/johndoe"
    }
  ],
  "category": "Computer Vision",
  "date": "2024-01-15",
  "engagement": {
    "likes": 42,
    "comments": 8
  },
  "urls": {
    "huggingface": "https://huggingface.co/papers/2401.xxxxx",
    "arxiv": "https://arxiv.org/abs/2401.xxxxx",
    "pdf": "https://arxiv.org/pdf/2401.xxxxx.pdf",
    "github": "https://github.com/author/repo"
  },
  "trending_score": 8.5,
  "quality_score": 7.2
}
```

## 常见问题与解决方案

### 1. 页面加载不完整
**问题**: 动态内容未完全加载
**解决**: 
- 增加页面加载等待时间
- 检查是否需要JavaScript渲染
- 使用Selenium作为备选方案

### 2. 分页处理失败
**问题**: 无法正确识别下一页链接
**解决**: 
- 多种分页识别策略
- 基于URL参数的分页
- 手动构造分页URL

### 3. 数据格式变化
**问题**: Hugging Face更新页面结构
**解决**: 
- 定期检查CSS选择器
- 实现多套解析规则
- 添加结构变化检测

### 4. 重复数据问题
**问题**: 同一论文在不同页面出现
**解决**: 
- 基于arXiv ID去重
- 标题相似度检测
- 维护已爬取论文列表

## 维护建议

### 定期检查项目
1. **页面结构**: 监控Hugging Face页面变化
2. **数据质量**: 检查爬取数据的完整性
3. **性能监控**: 跟踪爬取速度和成功率
4. **分类更新**: 关注新增的论文分类

### 优化方向
1. **智能分类**: 基于内容的自动分类
2. **趋势预测**: 预测论文热度趋势
3. **个性化推荐**: 基于用户兴趣的论文推荐
4. **多语言支持**: 支持中文摘要翻译

## 相关资源

- [Hugging Face Papers](https://huggingface.co/papers)
- [Hugging Face API文档](https://huggingface.co/docs)
- [arXiv API](https://arxiv.org/help/api)
- [论文质量评估标准](https://www.nature.com/articles/d41586-019-01643-3)