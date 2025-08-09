# Google Scholar 学术搜索爬虫技术文档

## 目标网站信息

- **网站名称**: Google Scholar
- **网站地址**: https://scholar.google.com/
- **网站类型**: 学术搜索引擎
- **数据更新频率**: 实时更新
- **访问限制**: 严格的反爬虫机制，需要谨慎处理

## 爬虫方案概述

### 技术架构
- **爬虫类型**: 网页爬虫
- **主要技术**: Python + requests + BeautifulSoup4
- **数据格式**: HTML → JSON/Markdown
- **代理支持**: 支持代理池轮换

### 核心功能
1. **学术搜索**: 基于关键词搜索学术论文
2. **引用分析**: 获取论文引用数据
3. **作者信息**: 提取作者姓名和机构信息
4. **期刊信息**: 获取发表期刊和会议信息
5. **时间过滤**: 支持按发表时间筛选

## 爬取方式详解

### 1. 搜索URL构造

#### 基础搜索URL
```
https://scholar.google.com/scholar?q={query}&hl=en&as_sdt=0,5
```

#### 主要参数
- `q`: 搜索关键词
- `hl`: 界面语言（en=英文）
- `as_sdt`: 搜索类型（0,5=包含专利）
- `as_ylo`: 起始年份
- `as_yhi`: 结束年份
- `start`: 分页起始位置
- `num`: 每页结果数（最大20）

#### 高级搜索参数
```python
# 按时间范围搜索
url = f"https://scholar.google.com/scholar?q={query}&as_ylo=2020&as_yhi=2024"

# 按作者搜索
url = f"https://scholar.google.com/scholar?q=author:{author_name}"

# 按期刊搜索
url = f"https://scholar.google.com/scholar?q=source:{journal_name}"
```

### 2. HTML解析策略

#### 搜索结果页面结构
```html
<div class="gs_r gs_or gs_scl">
  <div class="gs_ri">
    <h3 class="gs_rt">
      <a href="/url?q=..." data-clk="hl=en&amp;sa=T&amp;ct=res&amp;cd=0">
        论文标题
      </a>
    </h3>
    <div class="gs_a">
      作者信息 - 期刊信息, 年份 - 出版商
    </div>
    <div class="gs_rs">
      论文摘要或描述...
    </div>
    <div class="gs_fl">
      <a href="/scholar?cites=...">
        被引用 123 次
      </a>
      <a href="/scholar?cluster=...">
        相关文章
      </a>
    </div>
  </div>
</div>
```

#### 关键CSS选择器
```python
SELECTORS = {
    'result_item': 'div.gs_r.gs_or.gs_scl',
    'title': 'h3.gs_rt a',
    'authors_info': 'div.gs_a',
    'abstract': 'div.gs_rs',
    'citation_link': 'a[href*="cites="]',
    'pdf_link': 'div.gs_or_ggsm a[href$=".pdf"]',
    'next_page': 'a[aria-label="Next"]'
}
```

### 3. 数据提取算法

#### 标题提取
```python
def extract_title(result_div):
    title_element = result_div.select_one('h3.gs_rt a')
    if title_element:
        # 移除HTML标签，保留纯文本
        return title_element.get_text(strip=True)
    return None
```

#### 作者和期刊信息解析
```python
def parse_authors_info(authors_text):
    # 格式: "作者1, 作者2 - 期刊名, 年份 - 出版商"
    parts = authors_text.split(' - ')
    
    authors = []
    journal = None
    year = None
    publisher = None
    
    if len(parts) >= 1:
        authors = [author.strip() for author in parts[0].split(',')]
    
    if len(parts) >= 2:
        # 解析期刊和年份
        journal_year = parts[1]
        year_match = re.search(r'\b(19|20)\d{2}\b', journal_year)
        if year_match:
            year = int(year_match.group())
            journal = journal_year.replace(year_match.group(), '').strip(', ')
        else:
            journal = journal_year
    
    if len(parts) >= 3:
        publisher = parts[2].strip()
    
    return {
        'authors': authors,
        'journal': journal,
        'year': year,
        'publisher': publisher
    }
```

#### 引用数提取
```python
def extract_citation_count(result_div):
    citation_link = result_div.select_one('a[href*="cites="]')
    if citation_link:
        citation_text = citation_link.get_text()
        # 提取数字: "被引用 123 次" -> 123
        match = re.search(r'\d+', citation_text)
        if match:
            return int(match.group())
    return 0
```

## 反爬虫应对策略

### 1. 请求头伪装
```python
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate, br',
    'DNT': '1',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none'
}
```

### 2. 代理池管理
```python
class ProxyManager:
    def __init__(self):
        self.proxies = self.load_proxy_list()
        self.current_index = 0
        self.failed_proxies = set()
    
    def get_next_proxy(self):
        # 轮换代理
        while self.current_index < len(self.proxies):
            proxy = self.proxies[self.current_index]
            self.current_index += 1
            
            if proxy not in self.failed_proxies:
                return proxy
        
        # 重置索引，重新开始
        self.current_index = 0
        return None
    
    def mark_proxy_failed(self, proxy):
        self.failed_proxies.add(proxy)
```

### 3. 访问频率控制
```python
RATE_LIMIT_CONFIG = {
    'requests_per_minute': 10,  # 每分钟最多10个请求
    'delay_between_requests': 6,  # 请求间隔6秒
    'random_delay_range': (3, 10),  # 随机延迟3-10秒
    'max_retries': 3,  # 最大重试次数
    'backoff_factor': 2  # 重试延迟倍数
}
```

### 4. CAPTCHA检测与处理
```python
def detect_captcha(response):
    # 检测是否遇到验证码
    captcha_indicators = [
        'captcha',
        'robot',
        'unusual traffic',
        'verify you are human'
    ]
    
    response_text = response.text.lower()
    for indicator in captcha_indicators:
        if indicator in response_text:
            return True
    
    return False

def handle_captcha_response(response):
    if detect_captcha(response):
        logger.warning("Detected CAPTCHA, switching proxy and adding delay")
        time.sleep(random.randint(300, 600))  # 等待5-10分钟
        return True
    return False
```

## 数据质量评估

### 评估维度
1. **引用影响力**: 基于引用数量评估
2. **期刊权威性**: 基于期刊影响因子
3. **作者声誉**: 基于作者h-index
4. **时效性**: 论文发表时间
5. **相关性**: 与搜索关键词的匹配度

### 评分算法
```python
def calculate_scholar_score(paper):
    scores = {
        'citation_impact': min(paper.get('citations', 0) / 100, 10),
        'journal_authority': get_journal_score(paper.get('journal')),
        'author_reputation': get_author_score(paper.get('authors')),
        'recency': calculate_recency_score(paper.get('year')),
        'relevance': calculate_keyword_relevance(paper)
    }
    
    # 加权平均
    weights = {
        'citation_impact': 0.3,
        'journal_authority': 0.25,
        'author_reputation': 0.2,
        'recency': 0.15,
        'relevance': 0.1
    }
    
    total_score = sum(scores[key] * weights[key] for key in scores)
    return min(total_score, 10)  # 限制最高分为10
```

## 配置参数

### 搜索配置
```python
GOOGLE_SCHOLAR_CONFIG = {
    'base_url': 'https://scholar.google.com/scholar',
    'default_params': {
        'hl': 'en',
        'as_sdt': '0,5',
        'num': 20
    },
    'search_queries': [
        'artificial intelligence',
        'machine learning',
        'deep learning',
        'neural networks',
        'computer vision',
        'natural language processing'
    ]
}
```

### 反爬虫配置
```python
ANTI_CRAWLER_CONFIG = {
    'use_proxy': True,
    'proxy_rotation': True,
    'min_delay': 5,
    'max_delay': 15,
    'max_pages_per_session': 5,
    'session_cooldown': 1800,  # 30分钟
    'user_agent_rotation': True
}
```

## 常见问题与解决方案

### 1. IP被封禁
**问题**: 请求过于频繁导致IP被暂时封禁
**解决**: 
- 使用代理池轮换IP
- 增加请求间隔
- 实现会话管理

### 2. 验证码拦截
**问题**: 遇到人机验证
**解决**: 
- 检测验证码页面
- 自动切换代理
- 增加冷却时间

### 3. 页面结构变化
**问题**: Google Scholar更新页面结构
**解决**: 
- 定期检查CSS选择器
- 实现多套解析规则
- 添加容错机制

### 4. 数据不完整
**问题**: 部分论文信息缺失
**解决**: 
- 实现多源数据补充
- 添加数据验证
- 记录缺失字段统计

## 维护建议

### 定期检查项目
1. **页面结构**: 监控Google Scholar页面变化
2. **反爬虫策略**: 关注新的反爬虫措施
3. **代理质量**: 定期更新代理池
4. **成功率监控**: 跟踪爬取成功率

### 优化方向
1. **智能重试**: 基于错误类型的智能重试
2. **分布式爬取**: 多机器协同爬取
3. **缓存机制**: 避免重复爬取相同内容
4. **数据去重**: 基于DOI或标题的去重算法

## 法律与道德考虑

### 使用限制
1. **遵守robots.txt**: 尊重网站爬虫协议
2. **合理使用**: 不过度占用服务器资源
3. **数据用途**: 仅用于学术研究和个人学习
4. **版权尊重**: 不侵犯论文版权

### 最佳实践
1. **请求频率**: 保持合理的请求频率
2. **错误处理**: 优雅处理各种异常情况
3. **日志记录**: 详细记录爬取过程
4. **数据清理**: 及时清理过期和无效数据

## 相关资源

- [Google Scholar搜索技巧](https://scholar.google.com/intl/en/scholar/help.html)
- [学术搜索最佳实践](https://libguides.mit.edu/google-scholar)
- [BeautifulSoup文档](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)
- [Requests库文档](https://docs.python-requests.org/)