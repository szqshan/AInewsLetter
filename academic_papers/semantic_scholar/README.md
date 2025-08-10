# Semantic Scholar 学术搜索爬虫技术文档

## 目标网站信息

- **网站名称**: Semantic Scholar
- **网站地址**: https://www.semanticscholar.org/
- **网站类型**: AI驱动的学术搜索引擎
- **数据更新频率**: 实时更新
- **访问限制**: 有API支持，网页爬取需要注意频率

## 爬虫方案概述

### 技术架构
- **爬虫类型**: API优先 + 网页爬虫补充
- **主要技术**: Python + requests + Semantic Scholar API
- **数据格式**: JSON → Markdown
- **特色功能**: 语义搜索、引用分析、影响力评估

### 核心功能
1. **语义搜索**: 基于AI的智能论文搜索
2. **引用网络**: 构建论文引用关系网络
3. **影响力分析**: 基于引用数据评估论文影响力
4. **作者分析**: 分析作者学术影响力和合作网络
5. **领域趋势**: 追踪学术领域发展趋势

## 爬取方式详解

### 1. Semantic Scholar API

#### API端点概览
```
# 论文搜索
https://api.semanticscholar.org/graph/v1/paper/search

# 论文详情
https://api.semanticscholar.org/graph/v1/paper/{paper_id}

# 论文引用
https://api.semanticscholar.org/graph/v1/paper/{paper_id}/citations

# 论文参考文献
https://api.semanticscholar.org/graph/v1/paper/{paper_id}/references

# 作者信息
https://api.semanticscholar.org/graph/v1/author/{author_id}

# 作者论文
https://api.semanticscholar.org/graph/v1/author/{author_id}/papers

# 批量论文查询
https://api.semanticscholar.org/graph/v1/paper/batch
```

#### API认证和限制
```python
API_CONFIG = {
    'base_url': 'https://api.semanticscholar.org/graph/v1',
    'api_key': None,  # 可选，提高请求限制
    'rate_limit': {
        'requests_per_second': 10,  # 无API key时
        'requests_per_second_with_key': 100,  # 有API key时
        'requests_per_5_minutes': 1000
    },
    'timeout': 30
}
```

### 2. API客户端实现

#### 核心API客户端
```python
import requests
import time
from typing import List, Dict, Optional

class SemanticScholarAPI:
    def __init__(self, api_key: Optional[str] = None):
        self.base_url = 'https://api.semanticscholar.org/graph/v1'
        self.api_key = api_key
        self.session = requests.Session()
        
        # 设置请求头
        headers = {
            'User-Agent': 'AI-Newsletter-Spider/1.0',
            'Accept': 'application/json'
        }
        if api_key:
            headers['x-api-key'] = api_key
        
        self.session.headers.update(headers)
        
        # 速率限制
        self.last_request_time = 0
        self.request_interval = 0.1 if api_key else 0.11  # 10 RPS vs 9 RPS
    
    def _rate_limit(self):
        """实现速率限制"""
        now = time.time()
        time_since_last = now - self.last_request_time
        
        if time_since_last < self.request_interval:
            sleep_time = self.request_interval - time_since_last
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def _make_request(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        """发起API请求"""
        self._rate_limit()
        
        url = f"{self.base_url}/{endpoint}"
        
        try:
            response = self.session.get(url, params=params, timeout=30)
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:
                # 速率限制，等待后重试
                retry_after = int(response.headers.get('Retry-After', 60))
                logger.warning(f"Rate limited, waiting {retry_after} seconds")
                time.sleep(retry_after)
                return self._make_request(endpoint, params)
            else:
                logger.error(f"API request failed: {response.status_code} - {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error: {e}")
            return None
    
    def search_papers(self, query: str, limit: int = 100, offset: int = 0, 
                     fields: List[str] = None) -> Optional[Dict]:
        """搜索论文"""
        if fields is None:
            fields = [
                'paperId', 'title', 'abstract', 'authors', 'year', 
                'citationCount', 'referenceCount', 'influentialCitationCount',
                'fieldsOfStudy', 'journal', 'venue', 'url', 'externalIds'
            ]
        
        params = {
            'query': query,
            'limit': min(limit, 100),  # API限制每次最多100条
            'offset': offset,
            'fields': ','.join(fields)
        }
        
        return self._make_request('paper/search', params)
    
    def get_paper_details(self, paper_id: str, fields: List[str] = None) -> Optional[Dict]:
        """获取论文详情"""
        if fields is None:
            fields = [
                'paperId', 'title', 'abstract', 'authors', 'year',
                'citationCount', 'referenceCount', 'influentialCitationCount',
                'fieldsOfStudy', 'journal', 'venue', 'url', 'externalIds',
                'publicationDate', 'publicationTypes', 'publicationVenue'
            ]
        
        params = {'fields': ','.join(fields)}
        return self._make_request(f'paper/{paper_id}', params)
    
    def get_paper_citations(self, paper_id: str, limit: int = 100, 
                           offset: int = 0) -> Optional[Dict]:
        """获取论文引用"""
        params = {
            'limit': min(limit, 1000),
            'offset': offset,
            'fields': 'paperId,title,authors,year,citationCount,fieldsOfStudy'
        }
        
        return self._make_request(f'paper/{paper_id}/citations', params)
    
    def get_paper_references(self, paper_id: str, limit: int = 100,
                            offset: int = 0) -> Optional[Dict]:
        """获取论文参考文献"""
        params = {
            'limit': min(limit, 1000),
            'offset': offset,
            'fields': 'paperId,title,authors,year,citationCount,fieldsOfStudy'
        }
        
        return self._make_request(f'paper/{paper_id}/references', params)
    
    def get_author_details(self, author_id: str) -> Optional[Dict]:
        """获取作者详情"""
        fields = [
            'authorId', 'name', 'aliases', 'affiliations',
            'paperCount', 'citationCount', 'hIndex'
        ]
        
        params = {'fields': ','.join(fields)}
        return self._make_request(f'author/{author_id}', params)
    
    def get_author_papers(self, author_id: str, limit: int = 100,
                         offset: int = 0) -> Optional[Dict]:
        """获取作者论文"""
        params = {
            'limit': min(limit, 1000),
            'offset': offset,
            'fields': 'paperId,title,year,citationCount,fieldsOfStudy'
        }
        
        return self._make_request(f'author/{author_id}/papers', params)
```

### 3. 搜索策略实现

#### AI领域关键词搜索
```python
AI_SEARCH_QUERIES = {
    'core_ai': [
        'artificial intelligence',
        'machine learning',
        'deep learning',
        'neural networks'
    ],
    'nlp': [
        'natural language processing',
        'language models',
        'transformer',
        'BERT',
        'GPT'
    ],
    'cv': [
        'computer vision',
        'image recognition',
        'object detection',
        'convolutional neural networks'
    ],
    'ml_methods': [
        'reinforcement learning',
        'unsupervised learning',
        'transfer learning',
        'few-shot learning'
    ]
}

def search_ai_papers(api_client, max_papers_per_query=500):
    """搜索AI相关论文"""
    all_papers = []
    
    for category, queries in AI_SEARCH_QUERIES.items():
        for query in queries:
            logger.info(f"Searching for: {query}")
            
            offset = 0
            papers_collected = 0
            
            while papers_collected < max_papers_per_query:
                # 计算本次请求的数量
                limit = min(100, max_papers_per_query - papers_collected)
                
                result = api_client.search_papers(
                    query=query,
                    limit=limit,
                    offset=offset
                )
                
                if not result or 'data' not in result:
                    break
                
                papers = result['data']
                if not papers:
                    break
                
                # 过滤和处理论文
                for paper in papers:
                    if is_relevant_ai_paper(paper):
                        paper['search_category'] = category
                        paper['search_query'] = query
                        all_papers.append(paper)
                
                papers_collected += len(papers)
                offset += len(papers)
                
                # 如果返回的论文数少于请求数，说明没有更多结果
                if len(papers) < limit:
                    break
    
    return deduplicate_papers(all_papers)

def is_relevant_ai_paper(paper):
    """判断论文是否与AI相关"""
    # 检查发表年份
    year = paper.get('year')
    if not year or year < 2018:  # 只关注近期论文
        return False
    
    # 检查引用数
    citation_count = paper.get('citationCount', 0)
    if citation_count < 5:  # 过滤引用数过低的论文
        return False
    
    # 检查研究领域
    fields_of_study = paper.get('fieldsOfStudy', [])
    ai_fields = {
        'Computer Science', 'Mathematics', 'Engineering',
        'Physics', 'Medicine'  # AI应用领域
    }
    
    if not any(field in ai_fields for field in fields_of_study):
        return False
    
    return True
```

### 4. 数据增强和分析

#### 引用网络分析
```python
def build_citation_network(api_client, paper_ids, max_depth=2):
    """构建论文引用网络"""
    citation_network = {
        'nodes': {},  # paper_id -> paper_info
        'edges': []   # (citing_paper, cited_paper, weight)
    }
    
    processed_papers = set()
    papers_to_process = set(paper_ids)
    
    for depth in range(max_depth):
        current_batch = papers_to_process - processed_papers
        if not current_batch:
            break
        
        logger.info(f"Processing depth {depth + 1}, {len(current_batch)} papers")
        
        next_batch = set()
        
        for paper_id in current_batch:
            if paper_id in processed_papers:
                continue
            
            # 获取论文详情
            paper_details = api_client.get_paper_details(paper_id)
            if paper_details:
                citation_network['nodes'][paper_id] = paper_details
            
            # 获取引用关系
            citations = api_client.get_paper_citations(paper_id, limit=100)
            if citations and 'data' in citations:
                for citation in citations['data']:
                    citing_paper = citation.get('citingPaper', {})
                    citing_id = citing_paper.get('paperId')
                    
                    if citing_id:
                        # 添加边
                        citation_network['edges'].append({
                            'citing_paper': citing_id,
                            'cited_paper': paper_id,
                            'weight': 1
                        })
                        
                        # 添加到下一批处理
                        if depth < max_depth - 1:
                            next_batch.add(citing_id)
            
            # 获取参考文献
            references = api_client.get_paper_references(paper_id, limit=100)
            if references and 'data' in references:
                for reference in references['data']:
                    cited_paper = reference.get('citedPaper', {})
                    cited_id = cited_paper.get('paperId')
                    
                    if cited_id:
                        # 添加边
                        citation_network['edges'].append({
                            'citing_paper': paper_id,
                            'cited_paper': cited_id,
                            'weight': 1
                        })
                        
                        # 添加到下一批处理
                        if depth < max_depth - 1:
                            next_batch.add(cited_id)
            
            processed_papers.add(paper_id)
        
        papers_to_process.update(next_batch)
    
    return citation_network

def analyze_paper_influence(citation_network, paper_id):
    """分析论文影响力"""
    paper_info = citation_network['nodes'].get(paper_id, {})
    
    # 基础指标
    citation_count = paper_info.get('citationCount', 0)
    influential_citation_count = paper_info.get('influentialCitationCount', 0)
    reference_count = paper_info.get('referenceCount', 0)
    
    # 网络指标
    citing_papers = [edge['citing_paper'] for edge in citation_network['edges'] 
                    if edge['cited_paper'] == paper_id]
    cited_papers = [edge['cited_paper'] for edge in citation_network['edges'] 
                   if edge['citing_paper'] == paper_id]
    
    # 计算影响力分数
    influence_score = {
        'citation_count': citation_count,
        'influential_citation_count': influential_citation_count,
        'h_index_contribution': calculate_h_index_contribution(citation_network, paper_id),
        'network_centrality': calculate_network_centrality(citation_network, paper_id),
        'temporal_impact': calculate_temporal_impact(paper_info, citing_papers)
    }
    
    return influence_score
```

#### 作者影响力分析
```python
def analyze_author_influence(api_client, author_id):
    """分析作者学术影响力"""
    author_details = api_client.get_author_details(author_id)
    if not author_details:
        return None
    
    # 获取作者论文
    author_papers = api_client.get_author_papers(author_id, limit=1000)
    papers = author_papers.get('data', []) if author_papers else []
    
    # 计算影响力指标
    influence_metrics = {
        'basic_metrics': {
            'paper_count': author_details.get('paperCount', 0),
            'citation_count': author_details.get('citationCount', 0),
            'h_index': author_details.get('hIndex', 0)
        },
        'paper_analysis': analyze_author_papers(papers),
        'collaboration_network': analyze_collaboration_network(papers),
        'research_impact': calculate_research_impact(papers)
    }
    
    return influence_metrics

def analyze_author_papers(papers):
    """分析作者论文质量"""
    if not papers:
        return {}
    
    # 按年份分组
    papers_by_year = {}
    for paper in papers:
        year = paper.get('year')
        if year:
            if year not in papers_by_year:
                papers_by_year[year] = []
            papers_by_year[year].append(paper)
    
    # 计算指标
    total_citations = sum(paper.get('citationCount', 0) for paper in papers)
    avg_citations = total_citations / len(papers) if papers else 0
    
    # 高影响力论文（引用数前20%）
    sorted_papers = sorted(papers, key=lambda p: p.get('citationCount', 0), reverse=True)
    top_20_percent = int(len(sorted_papers) * 0.2)
    high_impact_papers = sorted_papers[:top_20_percent]
    
    return {
        'total_papers': len(papers),
        'total_citations': total_citations,
        'average_citations': avg_citations,
        'high_impact_papers': len(high_impact_papers),
        'papers_by_year': {year: len(papers) for year, papers in papers_by_year.items()},
        'recent_productivity': len([p for p in papers if p.get('year', 0) >= 2020])
    }
```

### 5. 数据质量评估

#### 论文质量评分
```python
def calculate_semantic_scholar_quality_score(paper_info):
    """计算基于Semantic Scholar数据的论文质量分数"""
    factors = {
        'citation_impact': assess_citation_impact(paper_info),
        'influential_citations': assess_influential_citations(paper_info),
        'venue_quality': assess_venue_quality(paper_info),
        'author_reputation': assess_author_reputation(paper_info),
        'recency': assess_paper_recency(paper_info),
        'field_relevance': assess_field_relevance(paper_info)
    }
    
    weights = {
        'citation_impact': 0.25,
        'influential_citations': 0.20,
        'venue_quality': 0.20,
        'author_reputation': 0.15,
        'recency': 0.10,
        'field_relevance': 0.10
    }
    
    score = sum(factors[key] * weights[key] for key in factors)
    return min(score, 10)

def assess_citation_impact(paper_info):
    """评估引用影响力"""
    citation_count = paper_info.get('citationCount', 0)
    year = paper_info.get('year')
    
    if not year:
        return 5
    
    # 计算年均引用数
    current_year = datetime.now().year
    years_since_publication = max(current_year - year, 1)
    citations_per_year = citation_count / years_since_publication
    
    # 分档评分
    if citations_per_year >= 50:
        return 10
    elif citations_per_year >= 20:
        return 8
    elif citations_per_year >= 10:
        return 7
    elif citations_per_year >= 5:
        return 6
    elif citations_per_year >= 2:
        return 5
    elif citations_per_year >= 1:
        return 4
    else:
        return 3

def assess_influential_citations(paper_info):
    """评估有影响力的引用"""
    influential_count = paper_info.get('influentialCitationCount', 0)
    total_citations = paper_info.get('citationCount', 0)
    
    if total_citations == 0:
        return 3
    
    # 计算有影响力引用的比例
    influential_ratio = influential_count / total_citations
    
    if influential_ratio >= 0.3:
        return 10
    elif influential_ratio >= 0.2:
        return 8
    elif influential_ratio >= 0.15:
        return 7
    elif influential_ratio >= 0.1:
        return 6
    elif influential_ratio >= 0.05:
        return 5
    else:
        return 4

def assess_venue_quality(paper_info):
    """评估发表场所质量"""
    venue = paper_info.get('venue', '')
    journal = paper_info.get('journal', {})
    
    # 顶级会议和期刊
    top_venues = {
        'NIPS', 'ICML', 'ICLR', 'AAAI', 'IJCAI', 'ACL', 'EMNLP',
        'CVPR', 'ICCV', 'ECCV', 'Nature', 'Science', 'Cell'
    }
    
    # 一流会议和期刊
    first_tier_venues = {
        'NAACL', 'EACL', 'COLING', 'SIGIR', 'WWW', 'KDD', 'WSDM',
        'ICDE', 'VLDB', 'SIGMOD', 'OSDI', 'SOSP'
    }
    
    venue_name = venue.upper()
    
    if any(top_venue in venue_name for top_venue in top_venues):
        return 10
    elif any(first_venue in venue_name for first_venue in first_tier_venues):
        return 8
    elif journal.get('name'):  # 有期刊信息
        return 6
    elif venue:  # 有会议信息
        return 5
    else:
        return 3
```

## 反爬虫应对策略

### 1. API优先策略
```python
# 优先使用官方API，减少网页爬取需求
API_FIRST_CONFIG = {
    'use_api_for_search': True,
    'use_api_for_details': True,
    'fallback_to_web': False,  # 仅在必要时使用网页爬取
    'cache_api_results': True,
    'cache_duration': 86400  # 24小时缓存
}
```

### 2. 智能缓存机制
```python
import pickle
import os
from datetime import datetime, timedelta

class SemanticScholarCache:
    def __init__(self, cache_dir='cache'):
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
    
    def _get_cache_path(self, key):
        return os.path.join(self.cache_dir, f"{key}.pkl")
    
    def get(self, key, max_age_hours=24):
        cache_path = self._get_cache_path(key)
        
        if not os.path.exists(cache_path):
            return None
        
        # 检查缓存是否过期
        file_time = datetime.fromtimestamp(os.path.getmtime(cache_path))
        if datetime.now() - file_time > timedelta(hours=max_age_hours):
            return None
        
        try:
            with open(cache_path, 'rb') as f:
                return pickle.load(f)
        except:
            return None
    
    def set(self, key, value):
        cache_path = self._get_cache_path(key)
        try:
            with open(cache_path, 'wb') as f:
                pickle.dump(value, f)
        except Exception as e:
            logger.warning(f"Failed to cache {key}: {e}")
```

### 3. 请求频率优化
```python
class OptimizedSemanticScholarAPI(SemanticScholarAPI):
    def __init__(self, api_key=None, cache_dir='cache'):
        super().__init__(api_key)
        self.cache = SemanticScholarCache(cache_dir)
        self.batch_size = 10  # 批量处理大小
    
    def search_papers_cached(self, query, **kwargs):
        cache_key = f"search_{hash(query)}_{hash(str(kwargs))}"
        
        # 尝试从缓存获取
        cached_result = self.cache.get(cache_key)
        if cached_result:
            return cached_result
        
        # API请求
        result = self.search_papers(query, **kwargs)
        
        # 缓存结果
        if result:
            self.cache.set(cache_key, result)
        
        return result
    
    def batch_get_paper_details(self, paper_ids):
        """批量获取论文详情"""
        results = {}
        
        for i in range(0, len(paper_ids), self.batch_size):
            batch = paper_ids[i:i + self.batch_size]
            
            for paper_id in batch:
                cache_key = f"paper_{paper_id}"
                cached_result = self.cache.get(cache_key)
                
                if cached_result:
                    results[paper_id] = cached_result
                else:
                    # API请求
                    result = self.get_paper_details(paper_id)
                    if result:
                        results[paper_id] = result
                        self.cache.set(cache_key, result)
        
        return results
```

## 配置参数

### API配置
```python
SEMANTIC_SCHOLAR_CONFIG = {
    'api_key': None,  # 从环境变量获取
    'base_url': 'https://api.semanticscholar.org/graph/v1',
    'rate_limit': {
        'requests_per_second': 10,
        'burst_limit': 100
    },
    'search_config': {
        'max_papers_per_query': 500,
        'min_citation_count': 5,
        'min_year': 2018,
        'fields_of_study_filter': ['Computer Science']
    },
    'cache_config': {
        'enabled': True,
        'cache_dir': 'cache/semantic_scholar',
        'max_age_hours': 24
    }
}
```

### 质量过滤配置
```python
QUALITY_FILTERS = {
    'min_citation_count': 10,
    'min_influential_citations': 2,
    'min_quality_score': 6.0,
    'required_fields': ['title', 'abstract', 'authors'],
    'exclude_publication_types': ['Review', 'Editorial'],
    'preferred_venues': [
        'NIPS', 'ICML', 'ICLR', 'AAAI', 'IJCAI',
        'ACL', 'EMNLP', 'CVPR', 'ICCV', 'ECCV'
    ]
}
```

## 数据输出格式

### JSON格式
```json
{
  "paper_id": "ss_001",
  "semantic_scholar_id": "1234567890abcdef",
  "title": "Attention Is All You Need",
  "abstract": "The dominant sequence transduction models...",
  "authors": [
    {
      "authorId": "author123",
      "name": "Ashish Vaswani",
      "affiliations": ["Google Brain"]
    }
  ],
  "year": 2017,
  "venue": "NIPS",
  "journal": {
    "name": "Advances in Neural Information Processing Systems",
    "volume": "30"
  },
  "citation_metrics": {
    "citationCount": 45678,
    "influentialCitationCount": 8901,
    "referenceCount": 42
  },
  "fields_of_study": [
    "Computer Science",
    "Mathematics"
  ],
  "external_ids": {
    "ArXiv": "1706.03762",
    "DBLP": "conf/nips/VaswaniSPUJGKP17",
    "DOI": "10.5555/3295222.3295349"
  },
  "urls": {
    "semantic_scholar": "https://www.semanticscholar.org/paper/1234567890abcdef",
    "arxiv": "https://arxiv.org/abs/1706.03762",
    "pdf": "https://arxiv.org/pdf/1706.03762.pdf"
  },
  "influence_analysis": {
    "citation_impact_score": 9.5,
    "influential_citation_ratio": 0.195,
    "venue_quality_score": 10,
    "temporal_impact": 8.7
  },
  "quality_score": 9.1,
  "search_metadata": {
    "search_category": "nlp",
    "search_query": "transformer",
    "crawl_timestamp": "2024-01-15T10:30:00Z"
  }
}
```

## 常见问题与解决方案

### 1. API限制问题
**问题**: 达到API请求限制
**解决**: 
- 申请API密钥提高限额
- 实现智能缓存减少重复请求
- 使用批量API减少请求次数

### 2. 数据不完整
**问题**: 部分论文缺少关键信息
**解决**: 
- 结合多个数据源补充信息
- 实现数据验证和清洗
- 标记数据完整性等级

### 3. 引用数据延迟
**问题**: 引用数据更新不及时
**解决**: 
- 定期更新引用数据
- 结合其他数据源验证
- 提供数据更新时间戳

### 4. 作者消歧问题
**问题**: 同名作者识别错误
**解决**: 
- 使用作者ID而非姓名
- 结合机构信息验证
- 实现作者消歧算法

## 维护建议

### 定期检查项目
1. **API变化**: 监控Semantic Scholar API更新
2. **数据质量**: 验证爬取数据准确性
3. **缓存管理**: 清理过期缓存数据
4. **性能优化**: 监控API请求效率

### 优化方向
1. **智能推荐**: 基于引用网络的论文推荐
2. **趋势预测**: 预测研究领域发展趋势
3. **影响力预测**: 预测论文未来影响力
4. **学者网络**: 构建学者合作网络图谱

## 相关资源

- [Semantic Scholar](https://www.semanticscholar.org/)
- [Semantic Scholar API文档](https://api.semanticscholar.org/)
- [学术搜索最佳实践](https://www.semanticscholar.org/faq)
- [引用网络分析方法](https://www.nature.com/articles/s41598-019-47116-w)