# Papers with Code 爬虫技术文档

## 目标网站信息

- **网站名称**: Papers with Code
- **网站地址**: https://paperswithcode.com/
- **网站类型**: 机器学习论文与代码聚合平台
- **数据更新频率**: 实时更新
- **访问限制**: 相对宽松，有API支持

## 爬虫方案概述

### 技术架构
- **爬虫类型**: 网页爬虫 + API调用
- **主要技术**: Python + requests + BeautifulSoup4 + Papers with Code API
- **数据格式**: HTML + JSON → Markdown
- **特色功能**: 论文与代码关联、性能基准追踪

### 核心功能
1. **最新论文**: 获取最新发布的机器学习论文
2. **代码关联**: 提取论文对应的开源代码仓库
3. **性能基准**: 获取模型在各种任务上的性能数据
4. **任务分类**: 按机器学习任务分类论文
5. **趋势分析**: 追踪研究领域发展趋势

## 爬取方式详解

### 1. 网站URL结构

#### 主要页面类型
```
# 最新论文
https://paperswithcode.com/latest

# 按任务分类
https://paperswithcode.com/task/image-classification
https://paperswithcode.com/task/object-detection
https://paperswithcode.com/task/machine-translation

# 按数据集分类
https://paperswithcode.com/dataset/imagenet
https://paperswithcode.com/dataset/coco

# 论文详情页
https://paperswithcode.com/paper/attention-is-all-you-need

# 方法页面
https://paperswithcode.com/method/transformer
https://paperswithcode.com/method/resnet

# 排行榜
https://paperswithcode.com/sota/image-classification-on-imagenet
```

#### API端点
```
# 论文API
https://paperswithcode.com/api/v1/papers/
https://paperswithcode.com/api/v1/papers/{paper_id}/

# 仓库API
https://paperswithcode.com/api/v1/repos/
https://paperswithcode.com/api/v1/repos/{repo_id}/

# 任务API
https://paperswithcode.com/api/v1/tasks/
https://paperswithcode.com/api/v1/tasks/{task_id}/

# 数据集API
https://paperswithcode.com/api/v1/datasets/
```

### 2. 页面结构分析

#### 最新论文页面
```html
<div class="infinite-container">
  <div class="row infinite-item">
    <div class="col-lg-9">
      <div class="paper-card">
        <h1>
          <a href="/paper/paper-title-slug">
            Paper Title
          </a>
        </h1>
        
        <p class="authors">
          <span class="author-span">
            <a href="/author/author-name">Author Name</a>
          </span>
        </p>
        
        <p class="paper-abstract">
          Abstract text goes here...
        </p>
        
        <div class="paper-tasks">
          <span class="badge badge-light">
            <a href="/task/image-classification">Image Classification</a>
          </span>
        </div>
        
        <div class="item-strip-content">
          <div class="entity-stars">
            <a href="/paper/paper-title-slug">
              <span class="stars-accumulated">★ 42</span>
            </a>
          </div>
          
          <div class="code-table">
            <a href="https://github.com/author/repo" class="code-table-link">
              <img src="/static/images/github-icon.svg" alt="GitHub">
              Official Code
            </a>
          </div>
        </div>
      </div>
    </div>
  </div>
</div>
```

#### 论文详情页面
```html
<div class="paper-title">
  <h1>Paper Title</h1>
</div>

<div class="paper-authors">
  <span class="authors">
    <a href="/author/author1">Author One</a>,
    <a href="/author/author2">Author Two</a>
  </span>
</div>

<div class="paper-abstract">
  <h2>Abstract</h2>
  <p>Abstract content...</p>
</div>

<div class="paper-implementations">
  <h2>Code</h2>
  <div class="code-table">
    <div class="row">
      <div class="col-md-6">
        <a href="https://github.com/author/repo" class="code-table-link">
          <div class="code-table-stars">★ 1,234</div>
          <div class="code-table-title">Official Implementation</div>
          <div class="code-table-subtitle">PyTorch</div>
        </a>
      </div>
    </div>
  </div>
</div>

<div class="paper-tasks">
  <h2>Tasks</h2>
  <div class="task-list">
    <a href="/task/image-classification" class="task-link">
      Image Classification
    </a>
  </div>
</div>
```

#### 关键CSS选择器
```python
SELECTORS = {
    'paper_cards': 'div.paper-card',
    'paper_title': 'h1 a[href^="/paper/"]',
    'paper_authors': 'p.authors .author-span a',
    'paper_abstract': 'p.paper-abstract',
    'paper_tasks': 'div.paper-tasks .badge a',
    'paper_stars': 'span.stars-accumulated',
    'code_links': 'div.code-table a.code-table-link',
    'github_links': 'a[href*="github.com"]',
    'arxiv_links': 'a[href*="arxiv.org"]',
    'next_page': 'a[rel="next"]'
}
```

### 3. 数据提取算法

#### 论文基本信息提取
```python
def extract_paper_info(paper_card):
    paper_info = {}
    
    # 提取标题和链接
    title_element = paper_card.select_one('h1 a[href^="/paper/"]')
    if title_element:
        paper_info['title'] = title_element.get_text(strip=True)
        paper_info['url'] = urljoin(base_url, title_element.get('href'))
        
        # 从URL提取论文slug
        href = title_element.get('href')
        slug_match = re.search(r'/paper/([^/]+)', href)
        if slug_match:
            paper_info['slug'] = slug_match.group(1)
    
    # 提取作者信息
    author_elements = paper_card.select('p.authors .author-span a')
    authors = []
    for author_element in author_elements:
        author_name = author_element.get_text(strip=True)
        author_url = urljoin(base_url, author_element.get('href'))
        authors.append({
            'name': author_name,
            'url': author_url
        })
    paper_info['authors'] = authors
    
    # 提取摘要
    abstract_element = paper_card.select_one('p.paper-abstract')
    if abstract_element:
        paper_info['abstract'] = abstract_element.get_text(strip=True)
    
    # 提取任务标签
    task_elements = paper_card.select('div.paper-tasks .badge a')
    tasks = []
    for task_element in task_elements:
        task_name = task_element.get_text(strip=True)
        task_url = urljoin(base_url, task_element.get('href'))
        tasks.append({
            'name': task_name,
            'url': task_url
        })
    paper_info['tasks'] = tasks
    
    # 提取星数
    stars_element = paper_card.select_one('span.stars-accumulated')
    if stars_element:
        stars_text = stars_element.get_text(strip=True)
        stars_match = re.search(r'★\s*(\d+)', stars_text)
        if stars_match:
            paper_info['stars'] = int(stars_match.group(1))
    
    return paper_info
```

#### 代码仓库信息提取
```python
def extract_code_repositories(paper_card):
    repositories = []
    
    code_links = paper_card.select('div.code-table a.code-table-link')
    for link in code_links:
        repo_info = {}
        
        # 提取仓库URL
        repo_url = link.get('href')
        if repo_url:
            repo_info['url'] = repo_url
            
            # 判断仓库类型
            if 'github.com' in repo_url:
                repo_info['platform'] = 'GitHub'
                # 提取GitHub仓库信息
                github_match = re.search(r'github\.com/([^/]+)/([^/]+)', repo_url)
                if github_match:
                    repo_info['owner'] = github_match.group(1)
                    repo_info['name'] = github_match.group(2)
            elif 'gitlab.com' in repo_url:
                repo_info['platform'] = 'GitLab'
            else:
                repo_info['platform'] = 'Other'
        
        # 提取星数
        stars_element = link.select_one('div.code-table-stars')
        if stars_element:
            stars_text = stars_element.get_text(strip=True)
            stars_match = re.search(r'★\s*([\d,]+)', stars_text)
            if stars_match:
                stars_str = stars_match.group(1).replace(',', '')
                repo_info['stars'] = int(stars_str)
        
        # 提取标题和描述
        title_element = link.select_one('div.code-table-title')
        if title_element:
            repo_info['title'] = title_element.get_text(strip=True)
        
        subtitle_element = link.select_one('div.code-table-subtitle')
        if subtitle_element:
            repo_info['framework'] = subtitle_element.get_text(strip=True)
        
        repositories.append(repo_info)
    
    return repositories
```

### 4. API数据增强

#### Papers with Code API客户端
```python
class PapersWithCodeAPI:
    def __init__(self):
        self.base_url = 'https://paperswithcode.com/api/v1'
        self.headers = {
            'User-Agent': 'AI-Newsletter-Spider/1.0',
            'Accept': 'application/json'
        }
    
    def get_paper_details(self, paper_id):
        """获取论文详细信息"""
        url = f"{self.base_url}/papers/{paper_id}/"
        
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
    
    def get_paper_repositories(self, paper_id):
        """获取论文相关代码仓库"""
        url = f"{self.base_url}/papers/{paper_id}/repositories/"
        
        try:
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                return response.json().get('results', [])
            return []
        except Exception as e:
            logger.error(f"Repositories request error: {e}")
            return []
    
    def get_latest_papers(self, page=1, items_per_page=50):
        """获取最新论文列表"""
        url = f"{self.base_url}/papers/"
        params = {
            'page': page,
            'items_per_page': items_per_page,
            'ordering': '-published'
        }
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            logger.error(f"Latest papers request error: {e}")
            return None
    
    def search_papers(self, query, page=1):
        """搜索论文"""
        url = f"{self.base_url}/papers/"
        params = {
            'q': query,
            'page': page
        }
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            logger.error(f"Search papers request error: {e}")
            return None
```

#### 数据增强处理
```python
def enhance_paper_with_api(paper_info, api_client):
    """使用API增强论文信息"""
    paper_slug = paper_info.get('slug')
    if not paper_slug:
        return paper_info
    
    # 获取API详细信息
    api_data = api_client.get_paper_details(paper_slug)
    if api_data:
        paper_info.update({
            'arxiv_id': api_data.get('arxiv_id'),
            'url_abs': api_data.get('url_abs'),
            'url_pdf': api_data.get('url_pdf'),
            'published': api_data.get('published'),
            'conference': api_data.get('conference'),
            'conference_url': api_data.get('conference_url'),
            'proceeding': api_data.get('proceeding')
        })
    
    # 获取代码仓库信息
    repositories = api_client.get_paper_repositories(paper_slug)
    if repositories:
        enhanced_repos = []
        for repo in repositories:
            enhanced_repo = {
                'url': repo.get('url'),
                'is_official': repo.get('is_official', False),
                'description': repo.get('description'),
                'stars': repo.get('stars', 0),
                'framework': repo.get('framework')
            }
            enhanced_repos.append(enhanced_repo)
        
        paper_info['repositories'] = enhanced_repos
    
    return paper_info
```

### 5. 任务和基准数据提取

#### 任务分类提取
```python
def extract_task_information(task_url):
    """提取任务相关信息"""
    response = requests.get(task_url, headers=HEADERS)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    task_info = {}
    
    # 提取任务描述
    description_element = soup.select_one('.task-description')
    if description_element:
        task_info['description'] = description_element.get_text(strip=True)
    
    # 提取相关数据集
    dataset_elements = soup.select('.dataset-list a')
    datasets = []
    for dataset_element in dataset_elements:
        dataset_name = dataset_element.get_text(strip=True)
        dataset_url = urljoin(base_url, dataset_element.get('href'))
        datasets.append({
            'name': dataset_name,
            'url': dataset_url
        })
    task_info['datasets'] = datasets
    
    # 提取SOTA结果
    sota_elements = soup.select('.sota-table tbody tr')
    sota_results = []
    for row in sota_elements:
        cells = row.select('td')
        if len(cells) >= 3:
            result = {
                'model': cells[0].get_text(strip=True),
                'metric_value': cells[1].get_text(strip=True),
                'paper': cells[2].get_text(strip=True)
            }
            sota_results.append(result)
    task_info['sota_results'] = sota_results
    
    return task_info
```

#### 性能基准追踪
```python
def track_performance_benchmarks(paper_info):
    """追踪论文在各种基准上的性能"""
    benchmarks = []
    
    for task in paper_info.get('tasks', []):
        task_info = extract_task_information(task['url'])
        
        # 查找该论文在SOTA表中的表现
        paper_title = paper_info.get('title', '').lower()
        for sota_result in task_info.get('sota_results', []):
            if paper_title in sota_result.get('paper', '').lower():
                benchmark = {
                    'task': task['name'],
                    'model': sota_result['model'],
                    'metric_value': sota_result['metric_value'],
                    'rank': len([r for r in task_info['sota_results'] 
                               if r == sota_result]) + 1
                }
                benchmarks.append(benchmark)
    
    paper_info['benchmarks'] = benchmarks
    return paper_info
```

## 数据质量评估

### 论文质量评分算法
```python
def calculate_pwc_quality_score(paper_info):
    """计算Papers with Code平台论文质量分数"""
    factors = {
        'code_availability': assess_code_availability(paper_info),
        'community_interest': assess_community_interest(paper_info),
        'benchmark_performance': assess_benchmark_performance(paper_info),
        'task_relevance': assess_task_relevance(paper_info),
        'recency': assess_paper_recency(paper_info)
    }
    
    weights = {
        'code_availability': 0.3,    # 代码可用性最重要
        'community_interest': 0.25,  # 社区关注度
        'benchmark_performance': 0.2, # 基准性能
        'task_relevance': 0.15,      # 任务相关性
        'recency': 0.1               # 时效性
    }
    
    score = sum(factors[key] * weights[key] for key in factors)
    return min(score, 10)

def assess_code_availability(paper_info):
    """评估代码可用性"""
    repositories = paper_info.get('repositories', [])
    if not repositories:
        return 2  # 无代码
    
    score = 5  # 基础分
    
    for repo in repositories:
        if repo.get('is_official', False):
            score += 3  # 官方代码加分
        
        stars = repo.get('stars', 0)
        if stars > 1000:
            score += 2
        elif stars > 100:
            score += 1
        
        if repo.get('platform') == 'GitHub':
            score += 1  # GitHub平台加分
    
    return min(score, 10)

def assess_community_interest(paper_info):
    """评估社区关注度"""
    stars = paper_info.get('stars', 0)
    
    if stars >= 100:
        return 10
    elif stars >= 50:
        return 8
    elif stars >= 20:
        return 6
    elif stars >= 10:
        return 4
    elif stars >= 5:
        return 3
    else:
        return 2

def assess_benchmark_performance(paper_info):
    """评估基准性能"""
    benchmarks = paper_info.get('benchmarks', [])
    if not benchmarks:
        return 5  # 默认中等分数
    
    # 基于排名计算分数
    avg_rank = sum(b.get('rank', 10) for b in benchmarks) / len(benchmarks)
    
    if avg_rank <= 3:
        return 10  # 前三名
    elif avg_rank <= 5:
        return 8   # 前五名
    elif avg_rank <= 10:
        return 6   # 前十名
    else:
        return 4   # 其他
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
    'DNT': '1',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1'
}
```

### 2. 访问频率控制
```python
RATE_LIMIT_CONFIG = {
    'web_requests_per_minute': 40,  # 网页请求频率
    'api_requests_per_minute': 60,  # API请求频率
    'delay_between_requests': 1.5,  # 请求间隔
    'random_delay_range': (1, 3),   # 随机延迟
    'max_retries': 3,
    'backoff_factor': 1.5
}
```

### 3. 智能重试机制
```python
def smart_retry_request(url, max_retries=3):
    for attempt in range(max_retries):
        try:
            response = requests.get(url, headers=HEADERS, timeout=30)
            
            if response.status_code == 200:
                return response
            elif response.status_code == 429:  # Rate limited
                wait_time = 2 ** attempt * 30  # 指数退避
                logger.warning(f"Rate limited, waiting {wait_time} seconds")
                time.sleep(wait_time)
            elif response.status_code >= 500:  # Server error
                logger.warning(f"Server error {response.status_code}, retrying...")
                time.sleep(2 ** attempt * 5)
            else:
                logger.error(f"HTTP {response.status_code}: {url}")
                break
                
        except requests.exceptions.RequestException as e:
            logger.warning(f"Request failed (attempt {attempt + 1}): {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt * 2)
    
    return None
```

## 配置参数

### 爬取配置
```python
PAPERS_WITH_CODE_CONFIG = {
    'base_url': 'https://paperswithcode.com',
    'api_base_url': 'https://paperswithcode.com/api/v1',
    'max_pages': 10,
    'papers_per_page': 50,
    'target_tasks': [
        'image-classification',
        'object-detection',
        'machine-translation',
        'language-modelling',
        'question-answering'
    ],
    'use_api': True,
    'download_pdfs': False,
    'track_benchmarks': True
}
```

### 质量过滤配置
```python
QUALITY_FILTERS = {
    'min_stars': 5,
    'require_code': True,
    'min_quality_score': 6.0,
    'preferred_frameworks': ['PyTorch', 'TensorFlow', 'JAX'],
    'exclude_tasks': ['tutorial', 'survey']
}
```

## 数据输出格式

### JSON格式
```json
{
  "paper_id": "pwc_001",
  "slug": "attention-is-all-you-need",
  "title": "Attention Is All You Need",
  "authors": [
    {
      "name": "Ashish Vaswani",
      "url": "https://paperswithcode.com/author/ashish-vaswani"
    }
  ],
  "abstract": "The dominant sequence transduction models...",
  "url": "https://paperswithcode.com/paper/attention-is-all-you-need",
  "arxiv_id": "1706.03762",
  "url_pdf": "https://arxiv.org/pdf/1706.03762.pdf",
  "published": "2017-06-12",
  "conference": "NIPS 2017",
  "tasks": [
    {
      "name": "Machine Translation",
      "url": "https://paperswithcode.com/task/machine-translation"
    }
  ],
  "repositories": [
    {
      "url": "https://github.com/tensorflow/tensor2tensor",
      "platform": "GitHub",
      "is_official": true,
      "stars": 13500,
      "framework": "TensorFlow",
      "title": "Official Implementation"
    }
  ],
  "benchmarks": [
    {
      "task": "Machine Translation",
      "model": "Transformer",
      "metric_value": "28.4 BLEU",
      "rank": 1
    }
  ],
  "stars": 156,
  "quality_score": 9.2,
  "crawl_timestamp": "2024-01-15T10:30:00Z"
}
```

## 常见问题与解决方案

### 1. API限制
**问题**: API请求频率限制
**解决**: 
- 实现智能缓存机制
- 优先使用网页爬取
- 分批处理请求

### 2. 代码仓库失效
**问题**: 论文对应的代码仓库链接失效
**解决**: 
- 定期验证链接有效性
- 搜索替代实现
- 标记失效状态

### 3. 基准数据不一致
**问题**: 不同时间爬取的基准数据不一致
**解决**: 
- 记录数据快照时间
- 实现版本控制
- 提供历史数据对比

### 4. 任务分类变化
**问题**: Papers with Code更新任务分类体系
**解决**: 
- 定期同步任务列表
- 实现分类映射
- 保持向后兼容

## 维护建议

### 定期检查项目
1. **API变化**: 监控API接口变化
2. **页面结构**: 检查网页结构更新
3. **数据质量**: 验证爬取数据准确性
4. **代码仓库**: 检查代码链接有效性

### 优化方向
1. **智能推荐**: 基于用户兴趣推荐论文
2. **趋势分析**: 分析研究领域发展趋势
3. **影响力评估**: 结合多维度数据评估论文影响力
4. **代码质量评估**: 评估开源代码质量

## 相关资源

- [Papers with Code](https://paperswithcode.com/)
- [Papers with Code API文档](https://paperswithcode.com/api/v1/docs/)
- [机器学习基准数据集](https://paperswithcode.com/datasets)
- [SOTA追踪](https://paperswithcode.com/sota)