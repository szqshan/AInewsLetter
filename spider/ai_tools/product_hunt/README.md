# Product Hunt AI工具爬虫技术文档

## 目标网站信息

- **网站名称**: Product Hunt
- **网站地址**: https://www.producthunt.com/
- **网站类型**: 产品发现平台
- **内容类型**: 新产品发布、AI工具、创业产品
- **更新频率**: 每日更新
- **语言**: 英文为主
- **特点**: 社区驱动、产品投票、创新工具聚集地

## 爬虫方案概述

### 技术架构
- **爬虫类型**: Web爬虫 + API调用
- **主要技术**: Python + requests + BeautifulSoup + Selenium
- **数据格式**: JSON → 结构化数据
- **特色功能**: AI产品识别、热度追踪、产品分析

### 核心功能
1. **每日产品获取**: 获取每日发布的新产品
2. **AI产品筛选**: 自动识别AI相关产品
3. **产品详情提取**: 获取产品详细信息和统计数据
4. **热度分析**: 基于投票数和评论分析产品热度
5. **分类整理**: 按AI应用领域分类产品
6. **趋势追踪**: 追踪AI产品发展趋势

## 爬取方式详解

### 1. Product Hunt 网站结构分析

#### 网站特点和API端点
```python
PRODUCT_HUNT_CONFIG = {
    'base_url': 'https://www.producthunt.com',
    'api_base': 'https://www.producthunt.com/frontend/graphql',
    'endpoints': {
        'daily_posts': '/posts',
        'product_detail': '/posts/{slug}',
        'search': '/search',
        'topics': '/topics/{topic}',
        'collections': '/collections'
    },
    'selectors': {
        'product_list': '[data-test="post-item"], .styles_item__1EtQo',
        'product_title': '[data-test="post-name"], h3 a',
        'product_link': '[data-test="post-url"], .styles_postUrl__3QWms',
        'product_description': '[data-test="post-description"], .styles_tagline__2ZHNz',
        'vote_count': '[data-test="vote-count"], .styles_voteCount__3nVlj',
        'comment_count': '[data-test="comment-count"], .styles_commentCount__3jKgZ',
        'maker_info': '[data-test="post-maker"], .styles_makerInfo__2ZzBz',
        'product_image': '[data-test="post-media"] img, .styles_media__1lhPo img',
        'product_tags': '[data-test="post-topics"], .styles_topics__2ZzBz a'
    },
    'ai_keywords': [
        'ai', 'artificial intelligence', 'machine learning', 'ml',
        'deep learning', 'neural network', 'nlp', 'computer vision',
        'automation', 'chatbot', 'gpt', 'llm', 'generative',
        'predictive', 'recommendation', 'analytics', 'data science'
    ],
    'headers': {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Referer': 'https://www.producthunt.com/'
    }
}
```

### 2. Product Hunt 爬虫实现

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
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Set
import logging
from dataclasses import dataclass, asdict
from urllib.parse import urljoin, urlparse
import hashlib

@dataclass
class ProductHuntProduct:
    name: str
    description: str
    url: str
    product_hunt_url: str
    votes: int
    comments: int
    launch_date: str
    makers: List[str]
    topics: List[str]
    image_url: str = ''
    website_url: str = ''
    pricing: str = ''
    ai_category: str = ''
    ai_confidence: float = 0.0
    product_id: str = ''
    
    def __post_init__(self):
        if not self.product_id:
            self.product_id = self.generate_product_id()
    
    def generate_product_id(self) -> str:
        content = f"{self.name}{self.product_hunt_url}ph"
        return hashlib.md5(content.encode('utf-8')).hexdigest()[:16]

class ProductHuntSpider:
    def __init__(self, use_selenium: bool = True):
        self.base_url = 'https://www.producthunt.com'
        self.use_selenium = use_selenium
        
        # 设置请求会话
        self.session = requests.Session()
        self.session.headers.update(PRODUCT_HUNT_CONFIG['headers'])
        
        # Selenium配置
        if self.use_selenium:
            self.setup_selenium()
        
        self.logger = logging.getLogger("ProductHuntSpider")
        
        # AI分类器
        self.ai_classifier = AIProductClassifier()
    
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
    
    def get_page_content(self, url: str) -> Optional[BeautifulSoup]:
        """获取页面内容"""
        try:
            if self.use_selenium:
                return self.get_page_with_selenium(url)
            else:
                return self.get_page_with_requests(url)
        except Exception as e:
            self.logger.error(f"Failed to get page content {url}: {e}")
            return None
    
    def get_page_with_requests(self, url: str) -> Optional[BeautifulSoup]:
        """使用requests获取页面"""
        response = self.session.get(url, timeout=30)
        response.raise_for_status()
        
        return BeautifulSoup(response.text, 'html.parser')
    
    def get_page_with_selenium(self, url: str) -> Optional[BeautifulSoup]:
        """使用Selenium获取页面（处理JavaScript渲染）"""
        self.driver.get(url)
        
        # 等待页面加载
        try:
            self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '[data-test="post-item"], .styles_item__1EtQo')))
        except:
            # 如果找不到产品列表，等待一般内容加载
            time.sleep(5)
        
        # 滚动页面加载更多内容
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)
        
        return BeautifulSoup(self.driver.page_source, 'html.parser')
    
    def get_daily_products(self, date: str = None) -> List[ProductHuntProduct]:
        """获取指定日期的产品"""
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        # Product Hunt的日期URL格式
        date_url = f"{self.base_url}/posts/{date}"
        
        self.logger.info(f"Fetching products for date: {date}")
        
        soup = self.get_page_content(date_url)
        if not soup:
            return []
        
        products = self.parse_product_list(soup, date)
        
        # 获取产品详细信息
        detailed_products = []
        for product in products:
            try:
                detailed_product = self.get_product_details(product)
                if detailed_product:
                    detailed_products.append(detailed_product)
                
                time.sleep(1)  # 添加延迟
            except Exception as e:
                self.logger.warning(f"Error getting details for {product.name}: {e}")
                detailed_products.append(product)
        
        return detailed_products
    
    def parse_product_list(self, soup: BeautifulSoup, date: str) -> List[ProductHuntProduct]:
        """解析产品列表页面"""
        products = []
        
        # 尝试多种选择器
        product_selectors = [
            '[data-test="post-item"]',
            '.styles_item__1EtQo',
            'div[class*="post"]',
            'article'
        ]
        
        product_elements = []
        for selector in product_selectors:
            elements = soup.select(selector)
            if elements:
                product_elements = elements
                self.logger.info(f"Found {len(elements)} products using selector: {selector}")
                break
        
        for element in product_elements:
            try:
                product = self.extract_product_info(element, date)
                if product:
                    products.append(product)
            except Exception as e:
                self.logger.warning(f"Error parsing product element: {e}")
                continue
        
        return products
    
    def extract_product_info(self, element, date: str) -> Optional[ProductHuntProduct]:
        """从产品元素提取基本信息"""
        # 提取产品名称和链接
        name_selectors = [
            '[data-test="post-name"] a',
            'h3 a', 'h2 a',
            '.styles_postName__3QWms a',
            'a[href*="/posts/"]'
        ]
        
        name = ''
        product_url = ''
        
        for selector in name_selectors:
            name_elem = element.select_one(selector)
            if name_elem:
                name = name_elem.get_text(strip=True)
                product_url = name_elem.get('href', '')
                break
        
        if not name or not product_url:
            return None
        
        # 处理相对URL
        if product_url.startswith('/'):
            product_url = urljoin(self.base_url, product_url)
        
        # 提取描述
        description_selectors = [
            '[data-test="post-description"]',
            '.styles_tagline__2ZHNz',
            '.tagline', 'p'
        ]
        
        description = ''
        for selector in description_selectors:
            desc_elem = element.select_one(selector)
            if desc_elem:
                description = desc_elem.get_text(strip=True)
                if len(description) > 20:
                    break
        
        # 提取投票数
        vote_selectors = [
            '[data-test="vote-count"]',
            '.styles_voteCount__3nVlj',
            '.vote-count'
        ]
        
        votes = 0
        for selector in vote_selectors:
            vote_elem = element.select_one(selector)
            if vote_elem:
                vote_text = vote_elem.get_text(strip=True)
                vote_match = re.search(r'(\d+)', vote_text)
                if vote_match:
                    votes = int(vote_match.group(1))
                    break
        
        # 提取评论数
        comment_selectors = [
            '[data-test="comment-count"]',
            '.styles_commentCount__3jKgZ',
            '.comment-count'
        ]
        
        comments = 0
        for selector in comment_selectors:
            comment_elem = element.select_one(selector)
            if comment_elem:
                comment_text = comment_elem.get_text(strip=True)
                comment_match = re.search(r'(\d+)', comment_text)
                if comment_match:
                    comments = int(comment_match.group(1))
                    break
        
        # 提取制作者信息
        maker_selectors = [
            '[data-test="post-maker"] a',
            '.styles_makerInfo__2ZzBz a',
            '.maker a'
        ]
        
        makers = []
        for selector in maker_selectors:
            maker_elems = element.select(selector)
            for maker_elem in maker_elems:
                maker_name = maker_elem.get_text(strip=True)
                if maker_name and maker_name not in makers:
                    makers.append(maker_name)
        
        # 提取标签/主题
        topic_selectors = [
            '[data-test="post-topics"] a',
            '.styles_topics__2ZzBz a',
            '.topics a'
        ]
        
        topics = []
        for selector in topic_selectors:
            topic_elems = element.select(selector)
            for topic_elem in topic_elems:
                topic_name = topic_elem.get_text(strip=True)
                if topic_name and topic_name not in topics:
                    topics.append(topic_name)
        
        # 提取产品图片
        image_selectors = [
            '[data-test="post-media"] img',
            '.styles_media__1lhPo img',
            '.post-image img'
        ]
        
        image_url = ''
        for selector in image_selectors:
            img_elem = element.select_one(selector)
            if img_elem:
                image_url = img_elem.get('src', '') or img_elem.get('data-src', '')
                if image_url:
                    break
        
        # 创建产品对象
        product = ProductHuntProduct(
            name=name,
            description=description,
            url='',  # 将在详情页面获取
            product_hunt_url=product_url,
            votes=votes,
            comments=comments,
            launch_date=date,
            makers=makers,
            topics=topics,
            image_url=image_url
        )
        
        return product
    
    def get_product_details(self, product: ProductHuntProduct) -> Optional[ProductHuntProduct]:
        """获取产品详细信息"""
        if not product.product_hunt_url:
            return product
        
        try:
            self.logger.info(f"Fetching details for: {product.name}")
            
            soup = self.get_page_content(product.product_hunt_url)
            if not soup:
                return product
            
            # 提取产品网站URL
            website_selectors = [
                '[data-test="post-url"]',
                '.styles_postUrl__3QWms',
                'a[href*="http"][target="_blank"]'
            ]
            
            for selector in website_selectors:
                url_elem = soup.select_one(selector)
                if url_elem:
                    website_url = url_elem.get('href', '')
                    if website_url and not 'producthunt.com' in website_url:
                        product.url = website_url
                        break
            
            # 提取更详细的描述
            detail_desc_selectors = [
                '[data-test="post-description-full"]',
                '.styles_description__2ZzBz',
                '.post-description'
            ]
            
            for selector in detail_desc_selectors:
                desc_elem = soup.select_one(selector)
                if desc_elem:
                    detailed_desc = desc_elem.get_text(strip=True)
                    if len(detailed_desc) > len(product.description):
                        product.description = detailed_desc
                    break
            
            # 提取定价信息
            pricing_selectors = [
                '[data-test="pricing"]',
                '.pricing', '.price',
                'span:contains("Free"), span:contains("Paid"), span:contains("Freemium")'
            ]
            
            for selector in pricing_selectors:
                pricing_elem = soup.select_one(selector)
                if pricing_elem:
                    product.pricing = pricing_elem.get_text(strip=True)
                    break
            
            # AI分类和置信度
            ai_result = self.ai_classifier.classify_product(product)
            product.ai_category = ai_result['category']
            product.ai_confidence = ai_result['confidence']
            
        except Exception as e:
            self.logger.error(f"Error fetching details for {product.name}: {e}")
        
        return product
    
    def search_ai_products(self, query: str = "AI", max_pages: int = 5) -> List[ProductHuntProduct]:
        """搜索AI相关产品"""
        products = []
        
        for page in range(1, max_pages + 1):
            try:
                search_url = f"{self.base_url}/search?q={query}&page={page}"
                
                self.logger.info(f"Searching AI products - Page {page}: {search_url}")
                
                soup = self.get_page_content(search_url)
                if not soup:
                    continue
                
                page_products = self.parse_product_list(soup, datetime.now().strftime('%Y-%m-%d'))
                if not page_products:
                    break
                
                # 获取详细信息
                for product in page_products:
                    detailed_product = self.get_product_details(product)
                    if detailed_product:
                        products.append(detailed_product)
                    
                    time.sleep(1)
                
                time.sleep(2)  # 页面间延迟
                
            except Exception as e:
                self.logger.error(f"Error searching page {page}: {e}")
                continue
        
        return products
    
    def get_trending_ai_products(self, days: int = 7) -> List[ProductHuntProduct]:
        """获取最近几天的热门AI产品"""
        all_products = []
        
        # 获取最近几天的产品
        for i in range(days):
            date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
            daily_products = self.get_daily_products(date)
            all_products.extend(daily_products)
            
            time.sleep(2)  # 日期间延迟
        
        # 过滤AI产品
        ai_products = []
        for product in all_products:
            if self.ai_classifier.is_ai_product(product):
                ai_products.append(product)
        
        # 按热度排序
        ai_products.sort(key=lambda x: self.calculate_popularity_score(x), reverse=True)
        
        return ai_products
    
    def calculate_popularity_score(self, product: ProductHuntProduct) -> float:
        """计算产品热度分数"""
        score = 0.0
        
        # 投票数权重最高
        score += product.votes * 1.0
        
        # 评论数
        score += product.comments * 2.0
        
        # AI置信度加成
        score += product.ai_confidence * 10
        
        # 时间衰减（越新的产品权重越高）
        try:
            launch_date = datetime.strptime(product.launch_date, '%Y-%m-%d')
            days_ago = (datetime.now() - launch_date).days
            time_factor = max(0.1, 1 - (days_ago / 30))  # 30天内线性衰减
            score *= time_factor
        except:
            pass
        
        return score
    
    def get_products_by_topic(self, topic: str) -> List[ProductHuntProduct]:
        """按主题获取产品"""
        topic_url = f"{self.base_url}/topics/{topic}"
        
        try:
            self.logger.info(f"Fetching products for topic: {topic}")
            
            soup = self.get_page_content(topic_url)
            if not soup:
                return []
            
            products = self.parse_product_list(soup, datetime.now().strftime('%Y-%m-%d'))
            
            # 获取详细信息
            detailed_products = []
            for product in products:
                detailed_product = self.get_product_details(product)
                if detailed_product:
                    detailed_products.append(detailed_product)
                
                time.sleep(1)
            
            return detailed_products
            
        except Exception as e:
            self.logger.error(f"Error fetching products for topic {topic}: {e}")
            return []
    
    def __del__(self):
        """清理资源"""
        if hasattr(self, 'driver'):
            try:
                self.driver.quit()
            except:
                pass

class AIProductClassifier:
    """AI产品分类器"""
    
    def __init__(self):
        self.ai_keywords = {
            'general': ['ai', 'artificial intelligence', 'machine learning', 'ml', 'automation'],
            'nlp': ['nlp', 'natural language', 'text analysis', 'chatbot', 'gpt', 'llm', 'language model'],
            'computer_vision': ['computer vision', 'cv', 'image recognition', 'object detection', 'ocr'],
            'data_science': ['data science', 'analytics', 'predictive', 'statistics', 'big data'],
            'generative': ['generative', 'generate', 'creation', 'synthesis', 'gan'],
            'recommendation': ['recommendation', 'personalization', 'suggest', 'recommend'],
            'voice': ['voice', 'speech', 'audio', 'sound', 'tts', 'stt'],
            'robotics': ['robot', 'robotics', 'autonomous', 'drone'],
            'business': ['business intelligence', 'crm', 'sales', 'marketing automation'],
            'development': ['code', 'programming', 'development', 'api', 'sdk']
        }
        
        self.negative_keywords = [
            'manual', 'human-only', 'traditional', 'non-automated'
        ]
    
    def is_ai_product(self, product: ProductHuntProduct) -> bool:
        """判断是否为AI产品"""
        result = self.classify_product(product)
        return result['confidence'] >= 0.3
    
    def classify_product(self, product: ProductHuntProduct) -> Dict:
        """分类AI产品"""
        text = f"{product.name} {product.description} {' '.join(product.topics)}".lower()
        
        # 检查负面关键词
        for neg_keyword in self.negative_keywords:
            if neg_keyword in text:
                return {'category': 'Non-AI', 'confidence': 0.0}
        
        # 计算各类别得分
        category_scores = {}
        
        for category, keywords in self.ai_keywords.items():
            score = 0
            for keyword in keywords:
                if keyword in text:
                    # 根据关键词重要性给不同权重
                    if keyword in ['ai', 'artificial intelligence', 'machine learning']:
                        score += 3
                    elif len(keyword) > 10:  # 长关键词更具体
                        score += 2
                    else:
                        score += 1
            
            if score > 0:
                category_scores[category] = score
        
        if not category_scores:
            return {'category': 'Non-AI', 'confidence': 0.0}
        
        # 找到最高分类别
        best_category = max(category_scores.items(), key=lambda x: x[1])
        
        # 计算置信度
        max_score = best_category[1]
        confidence = min(max_score / 10.0, 1.0)  # 归一化到0-1
        
        return {
            'category': best_category[0].replace('_', ' ').title(),
            'confidence': confidence
        }
```

### 3. 产品分析器

```python
class ProductAnalyzer:
    """产品分析器"""
    
    def __init__(self):
        self.logger = logging.getLogger("ProductAnalyzer")
    
    def analyze_products(self, products: List[ProductHuntProduct]) -> Dict:
        """分析产品数据"""
        if not products:
            return {}
        
        analysis = {
            'summary': self.generate_summary(products),
            'categories': self.analyze_categories(products),
            'trends': self.analyze_trends(products),
            'top_products': self.get_top_products(products),
            'makers': self.analyze_makers(products)
        }
        
        return analysis
    
    def generate_summary(self, products: List[ProductHuntProduct]) -> Dict:
        """生成总结统计"""
        total_products = len(products)
        ai_products = [p for p in products if p.ai_confidence >= 0.3]
        
        total_votes = sum(p.votes for p in products)
        total_comments = sum(p.comments for p in products)
        
        return {
            'total_products': total_products,
            'ai_products': len(ai_products),
            'ai_percentage': len(ai_products) / total_products * 100 if total_products > 0 else 0,
            'total_votes': total_votes,
            'total_comments': total_comments,
            'avg_votes': total_votes / total_products if total_products > 0 else 0,
            'avg_comments': total_comments / total_products if total_products > 0 else 0
        }
    
    def analyze_categories(self, products: List[ProductHuntProduct]) -> Dict:
        """分析产品分类"""
        category_stats = {}
        
        for product in products:
            if product.ai_confidence >= 0.3:
                category = product.ai_category or 'General'
                
                if category not in category_stats:
                    category_stats[category] = {
                        'count': 0,
                        'total_votes': 0,
                        'total_comments': 0,
                        'products': []
                    }
                
                category_stats[category]['count'] += 1
                category_stats[category]['total_votes'] += product.votes
                category_stats[category]['total_comments'] += product.comments
                category_stats[category]['products'].append(product)
        
        # 计算平均值
        for category, stats in category_stats.items():
            count = stats['count']
            stats['avg_votes'] = stats['total_votes'] / count if count > 0 else 0
            stats['avg_comments'] = stats['total_comments'] / count if count > 0 else 0
            
            # 只保留前5个产品
            stats['products'] = sorted(stats['products'], key=lambda x: x.votes, reverse=True)[:5]
        
        return category_stats
    
    def analyze_trends(self, products: List[ProductHuntProduct]) -> Dict:
        """分析趋势"""
        # 按日期分组
        date_stats = {}
        
        for product in products:
            date = product.launch_date
            
            if date not in date_stats:
                date_stats[date] = {
                    'total_products': 0,
                    'ai_products': 0,
                    'total_votes': 0
                }
            
            date_stats[date]['total_products'] += 1
            date_stats[date]['total_votes'] += product.votes
            
            if product.ai_confidence >= 0.3:
                date_stats[date]['ai_products'] += 1
        
        # 计算AI产品比例趋势
        for date, stats in date_stats.items():
            total = stats['total_products']
            stats['ai_percentage'] = stats['ai_products'] / total * 100 if total > 0 else 0
        
        return date_stats
    
    def get_top_products(self, products: List[ProductHuntProduct], top_n: int = 10) -> List[ProductHuntProduct]:
        """获取热门产品"""
        ai_products = [p for p in products if p.ai_confidence >= 0.3]
        
        # 按投票数排序
        top_products = sorted(ai_products, key=lambda x: x.votes, reverse=True)[:top_n]
        
        return top_products
    
    def analyze_makers(self, products: List[ProductHuntProduct]) -> Dict:
        """分析制作者"""
        maker_stats = {}
        
        for product in products:
            if product.ai_confidence >= 0.3:
                for maker in product.makers:
                    if maker not in maker_stats:
                        maker_stats[maker] = {
                            'products': [],
                            'total_votes': 0,
                            'total_comments': 0
                        }
                    
                    maker_stats[maker]['products'].append(product)
                    maker_stats[maker]['total_votes'] += product.votes
                    maker_stats[maker]['total_comments'] += product.comments
        
        # 只保留有多个产品的制作者
        active_makers = {k: v for k, v in maker_stats.items() if len(v['products']) > 1}
        
        # 按总投票数排序
        sorted_makers = sorted(active_makers.items(), key=lambda x: x[1]['total_votes'], reverse=True)
        
        return dict(sorted_makers[:20])  # 返回前20名
```

## 反爬虫应对策略

### 1. 动态内容处理
```python
class ProductHuntAntiBot:
    def __init__(self):
        self.request_count = 0
        self.last_request_time = 0
    
    def smart_delay(self):
        """智能延迟"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        # 基于请求频率调整延迟
        if time_since_last < 2:
            delay = random.uniform(3, 6)
        else:
            delay = random.uniform(1, 3)
        
        time.sleep(delay)
        self.last_request_time = time.time()
        self.request_count += 1
    
    def rotate_user_agents(self):
        """轮换User-Agent"""
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
        ]
        return random.choice(user_agents)
```

### 2. 会话管理
```python
def maintain_session(session: requests.Session):
    """维护会话状态"""
    # 定期访问主页保持会话
    if random.random() < 0.1:  # 10%概率
        session.get('https://www.producthunt.com/')
        time.sleep(2)
```

## 配置参数

### 爬虫配置
```python
PRODUCT_HUNT_SPIDER_CONFIG = {
    'request_settings': {
        'timeout': 30,
        'max_retries': 3,
        'delay_range': [1, 5],
        'use_selenium': True
    },
    'ai_classification': {
        'confidence_threshold': 0.3,
        'enable_deep_analysis': True,
        'category_mapping': True
    },
    'data_collection': {
        'max_days_back': 30,
        'include_details': True,
        'extract_images': True,
        'follow_external_links': False
    },
    'quality_filters': {
        'min_votes': 5,
        'min_description_length': 20,
        'exclude_inactive': True
    }
}
```

## 数据输出格式

### JSON格式
```json
{
  "product_id": "ph_001",
  "name": "ChatGPT Assistant",
  "description": "AI-powered writing assistant that helps you create content",
  "url": "https://chatgpt-assistant.com",
  "product_hunt_url": "https://www.producthunt.com/posts/chatgpt-assistant",
  "votes": 1250,
  "comments": 89,
  "launch_date": "2024-01-15",
  "makers": ["John Smith", "Jane Doe"],
  "topics": ["AI", "Productivity", "Writing"],
  "image_url": "https://ph-files.imgix.net/example.png",
  "website_url": "https://chatgpt-assistant.com",
  "pricing": "Freemium",
  "ai_category": "NLP",
  "ai_confidence": 0.95,
  "analysis": {
    "popularity_score": 1428.5,
    "category_rank": 2,
    "trending_score": 8.7
  },
  "crawl_metadata": {
    "crawl_timestamp": "2024-01-15T12:00:00Z",
    "extraction_method": "selenium",
    "spider_version": "1.0"
  }
}
```

## 常见问题与解决方案

### 1. JavaScript渲染问题
**问题**: Product Hunt大量使用JavaScript
**解决**: 
- 使用Selenium作为主要方案
- 实现智能等待机制
- 备用API调用方案

### 2. 反爬虫检测
**问题**: 可能被识别为机器人
**解决**: 
- 模拟真实用户行为
- 随机延迟和User-Agent
- 维护会话状态

### 3. AI产品识别准确性
**问题**: 自动分类可能不准确
**解决**: 
- 多维度关键词匹配
- 置信度评分机制
- 人工审核补充

### 4. 数据更新频率
**问题**: 产品信息变化快
**解决**: 
- 增量更新机制
- 定期全量同步
- 变化监控告警

## 维护建议

### 定期维护任务
1. **选择器更新**: 监控网站结构变化
2. **AI分类优化**: 优化关键词和分类算法
3. **数据质量检查**: 验证提取数据的准确性
4. **性能监控**: 监控爬取速度和成功率

### 扩展方向
1. **深度分析**: 增加产品成功预测模型
2. **竞品分析**: 对比同类产品表现
3. **市场趋势**: 分析AI产品市场趋势
4. **用户画像**: 分析产品用户群体特征

## 相关资源

- [Product Hunt](https://www.producthunt.com/)
- [Product Hunt API](https://api.producthunt.com/v2/docs)
- [Product Hunt Developer Guidelines](https://www.producthunt.com/developers)
- [Selenium Documentation](https://selenium-python.readthedocs.io/)
- [BeautifulSoup Documentation](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)