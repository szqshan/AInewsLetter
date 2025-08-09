# AI工具目录聚合爬虫技术文档

## 目标网站信息

- **网站类型**: AI工具目录聚合
- **主要目标网站**: 
  - AI Tool Directory (https://aitool.directory/)
  - There's An AI For That (https://theresanaiforthat.com/)
  - AI Tools Directory (https://ai-tools.directory/)
  - Futurepedia (https://www.futurepedia.io/)
  - ToolScout (https://toolscout.ai/)
  - AI Valley (https://aivalley.ai/)
- **内容类型**: AI工具分类目录、工具评测、使用指南
- **更新频率**: 每日更新
- **语言**: 英文为主
- **特点**: 分类详细、评分系统、用户评价

## 爬虫方案概述

### 技术架构
- **爬虫类型**: 多站点聚合爬虫
- **主要技术**: Python + requests + BeautifulSoup + Selenium
- **数据格式**: JSON → 统一结构化数据
- **特色功能**: 多源数据融合、去重合并、质量评估

### 核心功能
1. **多站点爬取**: 同时爬取多个AI工具目录网站
2. **数据标准化**: 统一不同网站的数据格式
3. **智能去重**: 识别和合并重复工具
4. **质量评估**: 基于多源数据评估工具质量
5. **分类整合**: 统一分类体系
6. **趋势分析**: 分析AI工具发展趋势

## 爬取方式详解

### 1. 支持的工具目录网站

#### 网站配置
```python
TOOL_DIRECTORIES_CONFIG = {
    'aitool_directory': {
        'base_url': 'https://aitool.directory',
        'name': 'AI Tool Directory',
        'selectors': {
            'tool_list': '.tool-card, .tool-item',
            'tool_name': '.tool-name, h3 a',
            'tool_description': '.tool-description, .description',
            'tool_url': '.tool-link, .visit-tool',
            'tool_category': '.category, .tag',
            'tool_rating': '.rating, .score',
            'tool_image': '.tool-image img, .thumbnail img'
        },
        'pagination': {
            'type': 'page_number',
            'param': 'page',
            'max_pages': 50
        }
    },
    'theresanaiforthat': {
        'base_url': 'https://theresanaiforthat.com',
        'name': "There's An AI For That",
        'selectors': {
            'tool_list': '.tool-card, .ai-tool',
            'tool_name': '.tool-title, h2 a',
            'tool_description': '.tool-desc, .description',
            'tool_url': '.tool-website, .website-link',
            'tool_category': '.category-tag, .tags a',
            'tool_rating': '.rating-score, .votes',
            'tool_image': '.tool-logo img, .ai-tool img'
        },
        'pagination': {
            'type': 'infinite_scroll',
            'load_more': '.load-more, .show-more'
        }
    },
    'futurepedia': {
        'base_url': 'https://www.futurepedia.io',
        'name': 'Futurepedia',
        'selectors': {
            'tool_list': '.tool-item, .ai-tool-card',
            'tool_name': '.tool-name, .title a',
            'tool_description': '.tool-summary, .excerpt',
            'tool_url': '.visit-tool, .external-link',
            'tool_category': '.category, .tag-list a',
            'tool_rating': '.rating, .score-value',
            'tool_image': '.tool-thumbnail img, .featured-image img'
        },
        'pagination': {
            'type': 'page_number',
            'param': 'page',
            'max_pages': 100
        }
    },
    'toolscout': {
        'base_url': 'https://toolscout.ai',
        'name': 'ToolScout',
        'selectors': {
            'tool_list': '.tool-card, .product-card',
            'tool_name': '.product-name, h3',
            'tool_description': '.product-description, .summary',
            'tool_url': '.product-link, .visit-site',
            'tool_category': '.category-badge, .tags span',
            'tool_rating': '.rating-stars, .score',
            'tool_image': '.product-image img, .logo img'
        },
        'pagination': {
            'type': 'page_number',
            'param': 'p',
            'max_pages': 30
        }
    },
    'aivalley': {
        'base_url': 'https://aivalley.ai',
        'name': 'AI Valley',
        'selectors': {
            'tool_list': '.ai-tool, .tool-listing',
            'tool_name': '.tool-title, .name',
            'tool_description': '.tool-desc, .description',
            'tool_url': '.tool-website, .official-link',
            'tool_category': '.category, .type',
            'tool_rating': '.rating, .popularity',
            'tool_image': '.tool-icon img, .avatar img'
        },
        'pagination': {
            'type': 'page_number',
            'param': 'page',
            'max_pages': 25
        }
    }
}

COMMON_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1'
}
```

### 2. 多站点聚合爬虫实现

#### 主爬虫类
```python
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import json
import re
import time
from datetime import datetime
from typing import List, Dict, Optional, Set
import logging
from dataclasses import dataclass, asdict
from urllib.parse import urljoin, urlparse
import hashlib
from concurrent.futures import ThreadPoolExecutor, as_completed
import difflib

@dataclass
class AITool:
    name: str
    description: str
    url: str
    category: str
    rating: float = 0.0
    pricing: str = ''
    image_url: str = ''
    tags: List[str] = None
    source_site: str = ''
    source_url: str = ''
    tool_id: str = ''
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if not self.tool_id:
            self.tool_id = self.generate_tool_id()
    
    def generate_tool_id(self) -> str:
        content = f"{self.name.lower()}{self.url}td"
        return hashlib.md5(content.encode('utf-8')).hexdigest()[:16]

class ToolDirectorySpider:
    def __init__(self, use_selenium: bool = True):
        self.use_selenium = use_selenium
        self.session = requests.Session()
        self.session.headers.update(COMMON_HEADERS)
        
        if self.use_selenium:
            self.setup_selenium()
        
        self.logger = logging.getLogger("ToolDirectorySpider")
        self.deduplicator = ToolDeduplicator()
        self.quality_assessor = ToolQualityAssessor()
        
        # 爬取统计
        self.crawl_stats = {
            'total_tools': 0,
            'unique_tools': 0,
            'duplicates_removed': 0,
            'sites_crawled': 0,
            'errors': 0
        }
    
    def setup_selenium(self):
        """设置Selenium WebDriver"""
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.wait = WebDriverWait(self.driver, 15)
        except Exception as e:
            self.logger.warning(f"Failed to setup Selenium: {e}")
            self.use_selenium = False
    
    def crawl_all_directories(self) -> List[AITool]:
        """爬取所有工具目录"""
        all_tools = []
        
        # 使用线程池并发爬取
        with ThreadPoolExecutor(max_workers=3) as executor:
            future_to_site = {
                executor.submit(self.crawl_directory, site_key, config): site_key 
                for site_key, config in TOOL_DIRECTORIES_CONFIG.items()
            }
            
            for future in as_completed(future_to_site):
                site_key = future_to_site[future]
                try:
                    tools = future.result()
                    all_tools.extend(tools)
                    self.crawl_stats['sites_crawled'] += 1
                    self.logger.info(f"Crawled {len(tools)} tools from {site_key}")
                except Exception as e:
                    self.logger.error(f"Error crawling {site_key}: {e}")
                    self.crawl_stats['errors'] += 1
        
        self.crawl_stats['total_tools'] = len(all_tools)
        
        # 去重和质量评估
        unique_tools = self.deduplicator.deduplicate_tools(all_tools)
        self.crawl_stats['unique_tools'] = len(unique_tools)
        self.crawl_stats['duplicates_removed'] = len(all_tools) - len(unique_tools)
        
        # 质量评估
        assessed_tools = []
        for tool in unique_tools:
            quality_score = self.quality_assessor.assess_tool(tool)
            if quality_score >= 0.3:  # 质量阈值
                assessed_tools.append(tool)
        
        return assessed_tools
    
    def crawl_directory(self, site_key: str, config: Dict) -> List[AITool]:
        """爬取单个工具目录"""
        tools = []
        base_url = config['base_url']
        site_name = config['name']
        
        self.logger.info(f"Starting to crawl {site_name}")
        
        try:
            if config['pagination']['type'] == 'page_number':
                tools = self.crawl_paginated_site(site_key, config)
            elif config['pagination']['type'] == 'infinite_scroll':
                tools = self.crawl_infinite_scroll_site(site_key, config)
            else:
                tools = self.crawl_single_page_site(site_key, config)
        
        except Exception as e:
            self.logger.error(f"Error crawling {site_name}: {e}")
        
        return tools
    
    def crawl_paginated_site(self, site_key: str, config: Dict) -> List[AITool]:
        """爬取分页网站"""
        tools = []
        base_url = config['base_url']
        max_pages = config['pagination'].get('max_pages', 10)
        param_name = config['pagination'].get('param', 'page')
        
        for page in range(1, max_pages + 1):
            try:
                # 构建分页URL
                if '?' in base_url:
                    page_url = f"{base_url}&{param_name}={page}"
                else:
                    page_url = f"{base_url}?{param_name}={page}"
                
                self.logger.info(f"Crawling {config['name']} page {page}: {page_url}")
                
                soup = self.get_page_content(page_url)
                if not soup:
                    continue
                
                page_tools = self.extract_tools_from_page(soup, config, site_key)
                if not page_tools:
                    self.logger.info(f"No tools found on page {page}, stopping")
                    break
                
                tools.extend(page_tools)
                
                # 添加延迟
                time.sleep(2)
                
            except Exception as e:
                self.logger.error(f"Error crawling page {page}: {e}")
                continue
        
        return tools
    
    def crawl_infinite_scroll_site(self, site_key: str, config: Dict) -> List[AITool]:
        """爬取无限滚动网站"""
        if not self.use_selenium:
            self.logger.warning(f"Selenium required for infinite scroll site {config['name']}")
            return []
        
        tools = []
        base_url = config['base_url']
        
        try:
            self.driver.get(base_url)
            
            # 等待页面加载
            time.sleep(5)
            
            last_height = self.driver.execute_script("return document.body.scrollHeight")
            
            while True:
                # 滚动到页面底部
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                
                # 等待新内容加载
                time.sleep(3)
                
                # 检查是否有"加载更多"按钮
                load_more_selector = config['pagination'].get('load_more')
                if load_more_selector:
                    try:
                        load_more_btn = self.driver.find_element(By.CSS_SELECTOR, load_more_selector)
                        if load_more_btn.is_displayed():
                            load_more_btn.click()
                            time.sleep(3)
                    except:
                        pass
                
                # 检查页面高度是否变化
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height
            
            # 解析页面内容
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            tools = self.extract_tools_from_page(soup, config, site_key)
            
        except Exception as e:
            self.logger.error(f"Error crawling infinite scroll site {config['name']}: {e}")
        
        return tools
    
    def crawl_single_page_site(self, site_key: str, config: Dict) -> List[AITool]:
        """爬取单页网站"""
        tools = []
        base_url = config['base_url']
        
        try:
            soup = self.get_page_content(base_url)
            if soup:
                tools = self.extract_tools_from_page(soup, config, site_key)
        except Exception as e:
            self.logger.error(f"Error crawling single page site {config['name']}: {e}")
        
        return tools
    
    def get_page_content(self, url: str) -> Optional[BeautifulSoup]:
        """获取页面内容"""
        try:
            if self.use_selenium:
                self.driver.get(url)
                time.sleep(3)
                return BeautifulSoup(self.driver.page_source, 'html.parser')
            else:
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                return BeautifulSoup(response.text, 'html.parser')
        except Exception as e:
            self.logger.error(f"Failed to get page content {url}: {e}")
            return None
    
    def extract_tools_from_page(self, soup: BeautifulSoup, config: Dict, site_key: str) -> List[AITool]:
        """从页面提取工具信息"""
        tools = []
        selectors = config['selectors']
        
        # 查找工具列表
        tool_elements = soup.select(selectors['tool_list'])
        
        self.logger.info(f"Found {len(tool_elements)} tool elements on page")
        
        for element in tool_elements:
            try:
                tool = self.extract_tool_info(element, selectors, config, site_key)
                if tool:
                    tools.append(tool)
            except Exception as e:
                self.logger.warning(f"Error extracting tool info: {e}")
                continue
        
        return tools
    
    def extract_tool_info(self, element, selectors: Dict, config: Dict, site_key: str) -> Optional[AITool]:
        """从元素提取工具信息"""
        # 提取工具名称
        name_elem = element.select_one(selectors['tool_name'])
        if not name_elem:
            return None
        
        name = name_elem.get_text(strip=True)
        if not name:
            return None
        
        # 提取描述
        desc_elem = element.select_one(selectors['tool_description'])
        description = desc_elem.get_text(strip=True) if desc_elem else ''
        
        # 提取URL
        url_elem = element.select_one(selectors['tool_url'])
        tool_url = ''
        if url_elem:
            tool_url = url_elem.get('href', '') or url_elem.get('data-url', '')
            if tool_url and not tool_url.startswith('http'):
                tool_url = urljoin(config['base_url'], tool_url)
        
        # 提取分类
        category_elem = element.select_one(selectors['tool_category'])
        category = category_elem.get_text(strip=True) if category_elem else 'General'
        
        # 提取评分
        rating = 0.0
        rating_elem = element.select_one(selectors['tool_rating'])
        if rating_elem:
            rating_text = rating_elem.get_text(strip=True)
            rating_match = re.search(r'([0-9.]+)', rating_text)
            if rating_match:
                try:
                    rating = float(rating_match.group(1))
                except ValueError:
                    rating = 0.0
        
        # 提取图片
        image_url = ''
        image_elem = element.select_one(selectors['tool_image'])
        if image_elem:
            image_url = image_elem.get('src', '') or image_elem.get('data-src', '')
            if image_url and not image_url.startswith('http'):
                image_url = urljoin(config['base_url'], image_url)
        
        # 提取标签
        tags = []
        tag_elements = element.select(selectors.get('tool_tags', ''))
        for tag_elem in tag_elements:
            tag = tag_elem.get_text(strip=True)
            if tag and tag not in tags:
                tags.append(tag)
        
        # 创建工具对象
        tool = AITool(
            name=name,
            description=description,
            url=tool_url,
            category=category,
            rating=rating,
            image_url=image_url,
            tags=tags,
            source_site=config['name'],
            source_url=config['base_url']
        )
        
        return tool
    
    def get_crawl_statistics(self) -> Dict:
        """获取爬取统计信息"""
        return self.crawl_stats.copy()
    
    def __del__(self):
        """清理资源"""
        if hasattr(self, 'driver'):
            try:
                self.driver.quit()
            except:
                pass
```

### 3. 工具去重器

```python
class ToolDeduplicator:
    """工具去重器"""
    
    def __init__(self, similarity_threshold: float = 0.8):
        self.similarity_threshold = similarity_threshold
        self.logger = logging.getLogger("ToolDeduplicator")
    
    def deduplicate_tools(self, tools: List[AITool]) -> List[AITool]:
        """去重工具列表"""
        if not tools:
            return []
        
        self.logger.info(f"Deduplicating {len(tools)} tools")
        
        unique_tools = []
        processed_urls = set()
        
        for tool in tools:
            # 首先基于URL去重
            if tool.url and tool.url in processed_urls:
                continue
            
            # 检查是否与已有工具相似
            is_duplicate = False
            for existing_tool in unique_tools:
                if self.are_tools_similar(tool, existing_tool):
                    # 合并工具信息
                    merged_tool = self.merge_tools(existing_tool, tool)
                    # 替换原工具
                    index = unique_tools.index(existing_tool)
                    unique_tools[index] = merged_tool
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique_tools.append(tool)
                if tool.url:
                    processed_urls.add(tool.url)
        
        self.logger.info(f"After deduplication: {len(unique_tools)} unique tools")
        return unique_tools
    
    def are_tools_similar(self, tool1: AITool, tool2: AITool) -> bool:
        """判断两个工具是否相似"""
        # 名称相似度
        name_similarity = difflib.SequenceMatcher(None, tool1.name.lower(), tool2.name.lower()).ratio()
        
        # URL相似度（如果都有URL）
        url_similarity = 0.0
        if tool1.url and tool2.url:
            # 提取域名比较
            domain1 = urlparse(tool1.url).netloc.lower()
            domain2 = urlparse(tool2.url).netloc.lower()
            if domain1 == domain2:
                url_similarity = 1.0
            else:
                url_similarity = difflib.SequenceMatcher(None, domain1, domain2).ratio()
        
        # 描述相似度
        desc_similarity = 0.0
        if tool1.description and tool2.description:
            desc_similarity = difflib.SequenceMatcher(None, tool1.description.lower(), tool2.description.lower()).ratio()
        
        # 综合相似度
        if url_similarity > 0.9:  # URL几乎相同
            return True
        
        if name_similarity > self.similarity_threshold:
            if desc_similarity > 0.6 or url_similarity > 0.7:
                return True
        
        return False
    
    def merge_tools(self, tool1: AITool, tool2: AITool) -> AITool:
        """合并两个相似工具的信息"""
        # 选择更完整的信息
        merged = AITool(
            name=tool1.name if len(tool1.name) >= len(tool2.name) else tool2.name,
            description=tool1.description if len(tool1.description) >= len(tool2.description) else tool2.description,
            url=tool1.url or tool2.url,
            category=tool1.category if tool1.category != 'General' else tool2.category,
            rating=max(tool1.rating, tool2.rating),
            pricing=tool1.pricing or tool2.pricing,
            image_url=tool1.image_url or tool2.image_url,
            tags=list(set(tool1.tags + tool2.tags)),
            source_site=f"{tool1.source_site}, {tool2.source_site}",
            source_url=tool1.source_url
        )
        
        return merged
```

### 4. 工具质量评估器

```python
class ToolQualityAssessor:
    """工具质量评估器"""
    
    def __init__(self):
        self.logger = logging.getLogger("ToolQualityAssessor")
    
    def assess_tool(self, tool: AITool) -> float:
        """评估工具质量"""
        score = 0.0
        
        # 基础信息完整性 (40%)
        completeness_score = self.assess_completeness(tool)
        score += completeness_score * 0.4
        
        # 描述质量 (30%)
        description_score = self.assess_description_quality(tool)
        score += description_score * 0.3
        
        # 评分和来源可信度 (20%)
        credibility_score = self.assess_credibility(tool)
        score += credibility_score * 0.2
        
        # 分类准确性 (10%)
        category_score = self.assess_category_accuracy(tool)
        score += category_score * 0.1
        
        return min(score, 1.0)
    
    def assess_completeness(self, tool: AITool) -> float:
        """评估信息完整性"""
        score = 0.0
        
        # 必要字段
        if tool.name and len(tool.name.strip()) > 2:
            score += 0.3
        
        if tool.description and len(tool.description.strip()) > 10:
            score += 0.3
        
        if tool.url and tool.url.startswith('http'):
            score += 0.2
        
        # 可选字段
        if tool.category and tool.category != 'General':
            score += 0.1
        
        if tool.image_url:
            score += 0.05
        
        if tool.tags:
            score += 0.05
        
        return score
    
    def assess_description_quality(self, tool: AITool) -> float:
        """评估描述质量"""
        if not tool.description:
            return 0.0
        
        desc = tool.description.strip()
        score = 0.0
        
        # 长度评分
        if len(desc) >= 50:
            score += 0.4
        elif len(desc) >= 20:
            score += 0.2
        
        # 关键词评分
        ai_keywords = ['ai', 'artificial intelligence', 'machine learning', 'automation', 'intelligent']
        for keyword in ai_keywords:
            if keyword in desc.lower():
                score += 0.1
                break
        
        # 语言质量评分
        if not re.search(r'[^a-zA-Z0-9\s.,!?-]', desc):  # 基本英文字符
            score += 0.2
        
        # 避免垃圾描述
        spam_indicators = ['click here', 'buy now', 'limited time', '!!!']
        for indicator in spam_indicators:
            if indicator in desc.lower():
                score -= 0.3
                break
        
        return max(score, 0.0)
    
    def assess_credibility(self, tool: AITool) -> float:
        """评估可信度"""
        score = 0.0
        
        # 评分
        if tool.rating > 0:
            score += min(tool.rating / 5.0, 0.5)  # 最高0.5分
        
        # 来源网站可信度
        trusted_sources = ['futurepedia', 'theresanaiforthat', 'aitool.directory']
        if any(source in tool.source_site.lower() for source in trusted_sources):
            score += 0.3
        else:
            score += 0.1
        
        # URL有效性
        if tool.url and self.is_valid_url(tool.url):
            score += 0.2
        
        return score
    
    def assess_category_accuracy(self, tool: AITool) -> float:
        """评估分类准确性"""
        if not tool.category or tool.category == 'General':
            return 0.5
        
        # 检查分类是否与描述匹配
        category_keywords = {
            'nlp': ['text', 'language', 'chat', 'writing', 'translation'],
            'image': ['image', 'photo', 'visual', 'picture', 'graphic'],
            'video': ['video', 'movie', 'film', 'animation'],
            'audio': ['audio', 'music', 'sound', 'voice', 'speech'],
            'data': ['data', 'analytics', 'analysis', 'statistics'],
            'business': ['business', 'marketing', 'sales', 'crm'],
            'development': ['code', 'programming', 'developer', 'api']
        }
        
        desc_lower = tool.description.lower() if tool.description else ''
        category_lower = tool.category.lower()
        
        for cat, keywords in category_keywords.items():
            if cat in category_lower:
                if any(keyword in desc_lower for keyword in keywords):
                    return 1.0
                else:
                    return 0.3
        
        return 0.7  # 默认分数
    
    def is_valid_url(self, url: str) -> bool:
        """检查URL有效性"""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except:
            return False
```

## 反爬虫应对策略

### 1. 智能请求管理
```python
class AntiDetectionManager:
    def __init__(self):
        self.request_count = 0
        self.last_request_time = 0
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
        ]
    
    def smart_delay(self):
        """智能延迟"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < 3:
            delay = random.uniform(4, 8)
        else:
            delay = random.uniform(2, 5)
        
        time.sleep(delay)
        self.last_request_time = time.time()
        self.request_count += 1
    
    def get_random_headers(self):
        """获取随机请求头"""
        headers = COMMON_HEADERS.copy()
        headers['User-Agent'] = random.choice(self.user_agents)
        return headers
```

### 2. 错误重试机制
```python
def retry_request(func, max_retries=3, delay=5):
    """请求重试装饰器"""
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            if attempt == max_retries - 1:
                raise e
            time.sleep(delay * (attempt + 1))
    return None
```

## 配置参数

### 爬虫配置
```python
TOOL_DIRECTORY_SPIDER_CONFIG = {
    'request_settings': {
        'timeout': 30,
        'max_retries': 3,
        'delay_range': [2, 8],
        'use_selenium': True,
        'concurrent_sites': 3
    },
    'deduplication': {
        'similarity_threshold': 0.8,
        'merge_similar_tools': True,
        'url_based_dedup': True
    },
    'quality_assessment': {
        'min_quality_score': 0.3,
        'enable_quality_filter': True,
        'assess_all_tools': True
    },
    'data_collection': {
        'max_pages_per_site': 50,
        'include_images': True,
        'extract_tags': True,
        'follow_tool_links': False
    }
}
```

## 数据输出格式

### JSON格式
```json
{
  "tool_id": "td_001",
  "name": "ChatGPT",
  "description": "Advanced AI chatbot for conversations and content creation",
  "url": "https://chat.openai.com",
  "category": "NLP",
  "rating": 4.8,
  "pricing": "Freemium",
  "image_url": "https://example.com/chatgpt-logo.png",
  "tags": ["AI", "Chatbot", "Writing", "Productivity"],
  "source_site": "Futurepedia, There's An AI For That",
  "source_url": "https://www.futurepedia.io",
  "quality_metrics": {
    "completeness_score": 0.9,
    "description_quality": 0.85,
    "credibility_score": 0.95,
    "category_accuracy": 1.0,
    "overall_quality": 0.92
  },
  "aggregation_info": {
    "sources_count": 2,
    "first_seen": "2024-01-15T10:00:00Z",
    "last_updated": "2024-01-15T15:30:00Z",
    "duplicate_count": 3
  },
  "crawl_metadata": {
    "crawl_timestamp": "2024-01-15T12:00:00Z",
    "spider_version": "1.0",
    "extraction_method": "multi_source"
  }
}
```

## 常见问题与解决方案

### 1. 网站结构差异
**问题**: 不同网站结构差异很大
**解决**: 
- 为每个网站配置独立选择器
- 实现通用提取逻辑
- 定期更新选择器配置

### 2. 数据去重准确性
**问题**: 相同工具在不同网站上信息不一致
**解决**: 
- 多维度相似度计算
- 智能信息合并策略
- 人工审核机制

### 3. 质量评估准确性
**问题**: 自动质量评估可能不准确
**解决**: 
- 多指标综合评估
- 机器学习模型优化
- 用户反馈集成

### 4. 爬取效率
**问题**: 多站点爬取耗时长
**解决**: 
- 并发爬取优化
- 增量更新机制
- 缓存策略

## 维护建议

### 定期维护任务
1. **选择器更新**: 监控各网站结构变化
2. **去重算法优化**: 提升去重准确性
3. **质量评估调优**: 优化质量评估算法
4. **新站点集成**: 添加新的工具目录网站

### 扩展方向
1. **智能分类**: 使用机器学习改进分类
2. **趋势分析**: 分析AI工具发展趋势
3. **用户评价**: 集成用户评价和反馈
4. **API服务**: 提供工具查询API服务

## 相关资源

- [AI Tool Directory](https://aitool.directory/)
- [There's An AI For That](https://theresanaiforthat.com/)
- [Futurepedia](https://www.futurepedia.io/)
- [ToolScout](https://toolscout.ai/)
- [AI Valley](https://aivalley.ai/)
- [Selenium Documentation](https://selenium-python.readthedocs.io/)
- [BeautifulSoup Documentation](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)