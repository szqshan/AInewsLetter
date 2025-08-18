# Google Research Blog RSS 爬虫

🤖 一个专门用于爬取 Google Research Blog 的 RSS 订阅爬虫，自动获取最新的 AI 研究文章并按照规范的目录结构存储。

## ✨ 特性

- 🔄 **RSS 自动订阅**: 实时获取 Google Research Blog 最新文章
- 📂 **规范存储结构**: 每篇文章独立文件夹，包含内容、元数据和媒体文件
- 🖼️ **媒体文件下载**: 自动下载文章中的图片、视频等媒体资源
- 📝 **Markdown 转换**: 将 HTML 内容转换为易读的 Markdown 格式
- 🔧 **高度可配置**: 支持自定义爬取参数、过滤条件等
- 🚀 **一键运行**: 提供简单易用的命令行界面

## 爬取方式详解

### 1. Google AI Blog 网站结构分析

#### 网站特点
```python
GOOGLE_AI_BLOG_CONFIG = {
    'base_url': 'https://ai.googleblog.com',
    'rss_url': 'https://ai.googleblog.com/feeds/posts/default',
    'archive_url': 'https://ai.googleblog.com/search',
    'api_endpoints': {
        'posts': 'https://www.blogger.com/feeds/8474926331452026626/posts/default',
        'search': 'https://ai.googleblog.com/search/label/{label}'
    },
    'selectors': {
        'title': 'h3.post-title',
        'content': 'div.post-body',
        'author': 'span.post-author',
        'publish_date': 'h2.date-header',
        'labels': 'span.post-labels a',
        'images': 'div.post-body img'
    },
    'categories': [
        'Machine Learning', 'Deep Learning', 'Natural Language Processing',
        'Computer Vision', 'Robotics', 'Healthcare', 'Research', 'TensorFlow'
    ]
}
```

### 2. RSS订阅爬虫实现

#### RSS解析器
```python
import feedparser
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import re
import json
import logging
from typing import List, Dict, Optional
from urllib.parse import urljoin, urlparse
import time

class GoogleAIBlogSpider:
    def __init__(self):
        self.base_url = 'https://ai.googleblog.com'
        self.rss_url = 'https://ai.googleblog.com/feeds/posts/default'
        
        # 设置请求会话
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive'
        })
        
        self.logger = logging.getLogger("GoogleAIBlogSpider")
    
    def get_rss_feed(self) -> Optional[feedparser.FeedParserDict]:
        """获取RSS订阅内容"""
        try:
            self.logger.info(f"Fetching RSS feed: {self.rss_url}")
            
            # 使用feedparser解析RSS
            feed = feedparser.parse(self.rss_url)
            
            if feed.bozo:
                self.logger.warning(f"RSS feed parsing warning: {feed.bozo_exception}")
            
            self.logger.info(f"Found {len(feed.entries)} entries in RSS feed")
            return feed
            
        except Exception as e:
            self.logger.error(f"Failed to fetch RSS feed: {e}")
            return None
    
    def parse_rss_entries(self, feed: feedparser.FeedParserDict, 
                         max_entries: int = 50) -> List[Dict]:
        """解析RSS条目"""
        articles = []
        
        for entry in feed.entries[:max_entries]:
            try:
                # 基础信息
                article_info = {
                    'title': entry.title,
                    'url': entry.link,
                    'summary': entry.get('summary', ''),
                    'publish_date': self.parse_publish_date(entry),
                    'author': self.extract_author_from_entry(entry),
                    'categories': self.extract_categories_from_entry(entry),
                    'source': 'Google AI Blog',
                    'source_type': 'official_blog'
                }
                
                # 生成唯一ID
                article_info['article_id'] = self.generate_article_id(article_info)
                
                articles.append(article_info)
                
            except Exception as e:
                self.logger.warning(f"Error parsing RSS entry: {e}")
                continue
        
        return articles
    
    def parse_publish_date(self, entry) -> str:
        """解析发布日期"""
        try:
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                return datetime(*entry.published_parsed[:6]).isoformat()
            elif hasattr(entry, 'published'):
                return entry.published
            elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                return datetime(*entry.updated_parsed[:6]).isoformat()
            else:
                return datetime.now().isoformat()
        except:
            return datetime.now().isoformat()
    
    def extract_author_from_entry(self, entry) -> str:
        """从RSS条目提取作者信息"""
        try:
            if hasattr(entry, 'author'):
                return entry.author
            elif hasattr(entry, 'authors') and entry.authors:
                return ', '.join([author.name for author in entry.authors if hasattr(author, 'name')])
            else:
                return 'Google AI Team'
        except:
            return 'Google AI Team'
    
    def extract_categories_from_entry(self, entry) -> List[str]:
        """从RSS条目提取分类信息"""
        categories = []
        
        try:
            if hasattr(entry, 'tags') and entry.tags:
                categories = [tag.term for tag in entry.tags if hasattr(tag, 'term')]
            elif hasattr(entry, 'category'):
                categories = [entry.category]
        except:
            pass
        
        return categories
    
    def get_article_details(self, article_info: Dict) -> Dict:
        """获取文章详细内容"""
        url = article_info.get('url')
        if not url:
            return article_info
        
        try:
            self.logger.info(f"Fetching article details: {url}")
            
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 提取文章内容
            content = self.extract_article_content(soup)
            if content:
                article_info['content'] = content
                article_info['word_count'] = len(content.split())
            
            # 提取更详细的元数据
            detailed_metadata = self.extract_detailed_metadata(soup)
            article_info.update(detailed_metadata)
            
            # 提取图片信息
            images = self.extract_images(soup)
            if images:
                article_info['images'] = images
            
            # 技术分析
            tech_analysis = self.analyze_technical_content(content)
            article_info['technical_analysis'] = tech_analysis
            
        except Exception as e:
            self.logger.error(f"Error fetching article details for {url}: {e}")
        
        return article_info
    
    def extract_article_content(self, soup: BeautifulSoup) -> str:
        """提取文章正文内容"""
        # Google AI Blog的内容结构
        content_selectors = [
            'div.post-body',
            'div.entry-content',
            'article .post-content',
            'div.blog-post-content'
        ]
        
        for selector in content_selectors:
            content_elem = soup.select_one(selector)
            if content_elem:
                # 清理内容
                content = self.clean_article_content(content_elem)
                if len(content) > 100:
                    return content
        
        return ''
    
    def clean_article_content(self, content_elem) -> str:
        """清理文章内容"""
        # 移除不需要的元素
        for tag in content_elem.find_all(['script', 'style', 'nav', 'aside', 'footer']):
            tag.decompose()
        
        # 移除广告和分享按钮
        for tag in content_elem.find_all(class_=re.compile(r'ad|share|social|related')):
            tag.decompose()
        
        # 处理代码块
        for code_block in content_elem.find_all(['pre', 'code']):
            code_block.string = f"\n```\n{code_block.get_text()}\n```\n"
        
        # 处理链接
        for link in content_elem.find_all('a', href=True):
            href = link.get('href')
            text = link.get_text(strip=True)
            if href and text:
                link.string = f"[{text}]({href})"
        
        # 获取文本内容
        text = content_elem.get_text(separator='\n', strip=True)
        
        # 清理多余的空行
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        return '\n'.join(lines)
    
    def extract_detailed_metadata(self, soup: BeautifulSoup) -> Dict:
        """提取详细元数据"""
        metadata = {}
        
        # 提取作者信息（如果RSS中没有）
        author_selectors = [
            'span.post-author',
            'div.author-info',
            'span.by-author',
            'div.post-meta .author'
        ]
        
        for selector in author_selectors:
            author_elem = soup.select_one(selector)
            if author_elem:
                metadata['detailed_author'] = author_elem.get_text(strip=True)
                break
        
        # 提取发布日期（更精确）
        date_selectors = [
            'h2.date-header',
            'time.published',
            'span.post-timestamp',
            'div.post-meta .date'
        ]
        
        for selector in date_selectors:
            date_elem = soup.select_one(selector)
            if date_elem:
                metadata['detailed_publish_date'] = date_elem.get_text(strip=True)
                break
        
        # 提取标签/分类
        label_selectors = [
            'span.post-labels a',
            'div.post-tags a',
            'div.categories a'
        ]
        
        for selector in label_selectors:
            label_elems = soup.select(selector)
            if label_elems:
                metadata['detailed_labels'] = [elem.get_text(strip=True) for elem in label_elems]
                break
        
        # 提取相关链接
        external_links = []
        for link in soup.find_all('a', href=True):
            href = link.get('href')
            if href and not href.startswith('#') and 'googleblog.com' not in href:
                external_links.append({
                    'url': href,
                    'text': link.get_text(strip=True)
                })
        
        metadata['external_links'] = external_links[:10]  # 限制数量
        
        return metadata
    
    def extract_images(self, soup: BeautifulSoup) -> List[Dict]:
        """提取文章图片"""
        images = []
        
        # 查找文章中的图片
        img_tags = soup.select('div.post-body img, div.entry-content img')
        
        for img in img_tags:
            src = img.get('src')
            if src:
                # 处理相对URL
                if src.startswith('//'):
                    src = 'https:' + src
                elif src.startswith('/'):
                    src = urljoin(self.base_url, src)
                
                image_info = {
                    'url': src,
                    'alt': img.get('alt', ''),
                    'title': img.get('title', ''),
                    'width': img.get('width'),
                    'height': img.get('height')
                }
                
                images.append(image_info)
        
        return images
    
    def analyze_technical_content(self, content: str) -> Dict:
        """分析技术内容"""
        analysis = {}
        
        # 技术关键词检测
        tech_keywords = {
            'machine_learning': ['machine learning', 'ML', 'supervised learning', 'unsupervised learning'],
            'deep_learning': ['deep learning', 'neural network', 'CNN', 'RNN', 'LSTM', 'transformer'],
            'nlp': ['natural language processing', 'NLP', 'language model', 'BERT', 'GPT'],
            'computer_vision': ['computer vision', 'image recognition', 'object detection', 'segmentation'],
            'tensorflow': ['TensorFlow', 'TF', 'Keras', 'TensorBoard'],
            'research': ['research', 'paper', 'study', 'experiment', 'dataset'],
            'product': ['product', 'release', 'feature', 'update', 'announcement']
        }
        
        content_lower = content.lower()
        
        for category, keywords in tech_keywords.items():
            count = sum(content_lower.count(keyword.lower()) for keyword in keywords)
            analysis[f'{category}_mentions'] = count
        
        # 确定主要技术领域
        max_category = max(analysis.items(), key=lambda x: x[1])
        analysis['primary_tech_area'] = max_category[0].replace('_mentions', '')
        
        # 计算技术深度分数
        technical_indicators = [
            'algorithm', 'model', 'training', 'accuracy', 'performance',
            'dataset', 'benchmark', 'evaluation', 'architecture', 'optimization'
        ]
        
        tech_depth_score = sum(content_lower.count(indicator) for indicator in technical_indicators)
        analysis['technical_depth_score'] = min(tech_depth_score / 10, 10)  # 归一化到0-10
        
        # 检测是否包含代码
        code_indicators = ['```', 'import ', 'def ', 'class ', 'function', 'code']
        analysis['contains_code'] = any(indicator in content for indicator in code_indicators)
        
        # 检测是否包含数学公式
        math_indicators = ['equation', 'formula', '∑', '∫', '∂', 'matrix']
        analysis['contains_math'] = any(indicator in content for indicator in math_indicators)
        
        return analysis
    
    def search_articles_by_category(self, category: str, max_results: int = 20) -> List[Dict]:
        """按分类搜索文章"""
        search_url = f"https://ai.googleblog.com/search/label/{category}"
        
        try:
            response = self.session.get(search_url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            articles = []
            
            # 查找文章列表
            post_items = soup.find_all('div', class_='post')
            
            for post in post_items[:max_results]:
                try:
                    # 提取标题和链接
                    title_elem = post.find('h3', class_='post-title')
                    if not title_elem:
                        continue
                    
                    title_link = title_elem.find('a')
                    if not title_link:
                        continue
                    
                    title = title_link.get_text(strip=True)
                    url = title_link.get('href')
                    
                    # 提取摘要
                    summary_elem = post.find('div', class_='post-body')
                    summary = ''
                    if summary_elem:
                        summary_text = summary_elem.get_text(strip=True)
                        summary = summary_text[:300] + '...' if len(summary_text) > 300 else summary_text
                    
                    # 提取日期
                    date_elem = post.find('h2', class_='date-header')
                    publish_date = date_elem.get_text(strip=True) if date_elem else ''
                    
                    article_info = {
                        'title': title,
                        'url': url,
                        'summary': summary,
                        'publish_date': publish_date,
                        'category': category,
                        'source': 'Google AI Blog',
                        'article_id': self.generate_article_id({'title': title, 'url': url})
                    }
                    
                    articles.append(article_info)
                    
                except Exception as e:
                    self.logger.warning(f"Error parsing search result: {e}")
                    continue
            
            self.logger.info(f"Found {len(articles)} articles for category: {category}")
            return articles
            
        except Exception as e:
            self.logger.error(f"Error searching articles by category {category}: {e}")
            return []
    
    def get_recent_articles(self, days: int = 30, max_articles: int = 50) -> List[Dict]:
        """获取最近的文章"""
        # 首先尝试RSS
        feed = self.get_rss_feed()
        if feed:
            articles = self.parse_rss_entries(feed, max_articles)
            
            # 过滤最近的文章
            cutoff_date = datetime.now() - timedelta(days=days)
            recent_articles = []
            
            for article in articles:
                try:
                    pub_date = datetime.fromisoformat(article['publish_date'].replace('Z', '+00:00'))
                    if pub_date.replace(tzinfo=None) >= cutoff_date:
                        recent_articles.append(article)
                except:
                    # 如果日期解析失败，仍然包含文章
                    recent_articles.append(article)
            
            # 获取详细内容
            detailed_articles = []
            for article in recent_articles:
                detailed_article = self.get_article_details(article)
                detailed_articles.append(detailed_article)
                
                # 添加延迟避免过于频繁的请求
                time.sleep(1)
            
            return detailed_articles
        
        return []
    
    def crawl_all_categories(self, max_articles_per_category: int = 10) -> List[Dict]:
        """爬取所有分类的文章"""
        categories = [
            'Machine Learning', 'Deep Learning', 'Natural Language Processing',
            'Computer Vision', 'Robotics', 'Healthcare', 'Research', 'TensorFlow'
        ]
        
        all_articles = []
        
        for category in categories:
            self.logger.info(f"Crawling category: {category}")
            
            try:
                articles = self.search_articles_by_category(category, max_articles_per_category)
                
                # 获取详细内容
                for article in articles:
                    detailed_article = self.get_article_details(article)
                    all_articles.append(detailed_article)
                    
                    time.sleep(1)  # 添加延迟
                
            except Exception as e:
                self.logger.error(f"Error crawling category {category}: {e}")
                continue
        
        # 去重
        unique_articles = self.deduplicate_articles(all_articles)
        
        self.logger.info(f"Total unique articles crawled: {len(unique_articles)}")
        return unique_articles
    
    def deduplicate_articles(self, articles: List[Dict]) -> List[Dict]:
        """文章去重"""
        seen_urls = set()
        unique_articles = []
        
        for article in articles:
            url = article.get('url', '')
            if url not in seen_urls:
                seen_urls.add(url)
                unique_articles.append(article)
        
        return unique_articles
    
    def generate_article_id(self, article: Dict) -> str:
        """生成文章唯一ID"""
        import hashlib
        content = f"{article.get('title', '')}{article.get('url', '')}google_ai_blog"
        return hashlib.md5(content.encode('utf-8')).hexdigest()[:16]
    
    def calculate_quality_score(self, article: Dict) -> float:
        """计算文章质量分数"""
        score = 8.0  # Google AI Blog基础高分
        
        # 技术深度加分
        tech_analysis = article.get('technical_analysis', {})
        tech_depth = tech_analysis.get('technical_depth_score', 0)
        score += min(tech_depth * 0.2, 2.0)
        
        # 内容长度加分
        word_count = article.get('word_count', 0)
        if word_count > 1000:
            score += 1.0
        elif word_count > 500:
            score += 0.5
        
        # 包含代码或数学公式加分
        if tech_analysis.get('contains_code'):
            score += 0.5
        if tech_analysis.get('contains_math'):
            score += 0.5
        
        # 图片丰富度
        images = article.get('images', [])
        if len(images) > 3:
            score += 0.5
        
        return min(score, 10.0)
```

### 3. 数据处理和分析

#### 内容分析器
```python
class GoogleAIContentAnalyzer:
    def __init__(self):
        self.tech_categories = {
            'machine_learning': {
                'keywords': ['machine learning', 'ML', 'supervised', 'unsupervised', 'reinforcement'],
                'weight': 1.0
            },
            'deep_learning': {
                'keywords': ['deep learning', 'neural network', 'CNN', 'RNN', 'transformer'],
                'weight': 1.2
            },
            'nlp': {
                'keywords': ['NLP', 'language model', 'BERT', 'GPT', 'text processing'],
                'weight': 1.1
            },
            'computer_vision': {
                'keywords': ['computer vision', 'image', 'object detection', 'segmentation'],
                'weight': 1.1
            },
            'research': {
                'keywords': ['research', 'paper', 'study', 'experiment', 'novel'],
                'weight': 0.9
            },
            'product': {
                'keywords': ['product', 'release', 'feature', 'tool', 'platform'],
                'weight': 0.8
            }
        }
    
    def analyze_article_trends(self, articles: List[Dict]) -> Dict:
        """分析文章趋势"""
        # 按月份统计
        monthly_stats = {}
        category_stats = {}
        
        for article in articles:
            # 提取月份
            try:
                pub_date = datetime.fromisoformat(article['publish_date'].replace('Z', '+00:00'))
                month_key = pub_date.strftime('%Y-%m')
                
                if month_key not in monthly_stats:
                    monthly_stats[month_key] = 0
                monthly_stats[month_key] += 1
            except:
                pass
            
            # 统计技术分类
            tech_analysis = article.get('technical_analysis', {})
            primary_area = tech_analysis.get('primary_tech_area', 'unknown')
            
            if primary_area not in category_stats:
                category_stats[primary_area] = 0
            category_stats[primary_area] += 1
        
        return {
            'monthly_publication_stats': monthly_stats,
            'technology_category_stats': category_stats,
            'total_articles': len(articles),
            'analysis_timestamp': datetime.now().isoformat()
        }
    
    def extract_research_insights(self, articles: List[Dict]) -> Dict:
        """提取研究洞察"""
        insights = {
            'trending_technologies': [],
            'research_directions': [],
            'product_announcements': [],
            'collaboration_mentions': []
        }
        
        # 分析技术趋势
        tech_mentions = {}
        for article in articles:
            content = article.get('content', '')
            tech_analysis = article.get('technical_analysis', {})
            
            for category, info in self.tech_categories.items():
                mentions = sum(content.lower().count(keyword.lower()) for keyword in info['keywords'])
                if mentions > 0:
                    if category not in tech_mentions:
                        tech_mentions[category] = 0
                    tech_mentions[category] += mentions * info['weight']
        
        # 排序得到趋势技术
        insights['trending_technologies'] = sorted(
            tech_mentions.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:10]
        
        # 提取产品发布
        product_keywords = ['announce', 'release', 'launch', 'introduce', 'available']
        for article in articles:
            content = article.get('content', '').lower()
            if any(keyword in content for keyword in product_keywords):
                insights['product_announcements'].append({
                    'title': article.get('title'),
                    'url': article.get('url'),
                    'date': article.get('publish_date')
                })
        
        return insights
```

## 反爬虫应对策略

### 1. 尊重robots.txt
```python
import urllib.robotparser

def check_robots_txt(url: str) -> bool:
    """检查robots.txt规则"""
    try:
        rp = urllib.robotparser.RobotFileParser()
        rp.set_url(f"{url}/robots.txt")
        rp.read()
        return rp.can_fetch('*', url)
    except:
        return True  # 如果无法获取robots.txt，默认允许
```

### 2. 请求频率控制
```python
class RateLimiter:
    def __init__(self, requests_per_minute: int = 30):
        self.requests_per_minute = requests_per_minute
        self.request_times = []
    
    def wait_if_needed(self):
        now = time.time()
        
        # 清理超过1分钟的记录
        self.request_times = [t for t in self.request_times if now - t < 60]
        
        # 如果请求过于频繁，等待
        if len(self.request_times) >= self.requests_per_minute:
            sleep_time = 60 - (now - self.request_times[0])
            if sleep_time > 0:
                time.sleep(sleep_time)
        
        self.request_times.append(now)
```

## 配置参数

### 爬虫配置
```python
GOOGLE_AI_BLOG_CONFIG = {
    'rate_limiting': {
        'requests_per_minute': 30,
        'delay_between_requests': 2,
        'retry_delay': 60
    },
    'content_processing': {
        'max_content_length': 50000,
        'extract_images': True,
        'extract_code_blocks': True,
        'clean_html': True
    },
    'quality_filters': {
        'min_word_count': 200,
        'min_technical_depth': 3.0,
        'require_author': False
    },
    'output_config': {
        'include_full_content': True,
        'include_images': True,
        'include_technical_analysis': True
    }
}
```

## 数据输出格式

### JSON格式
```json
{
  "article_id": "google_ai_001",
  "title": "Introducing PaLM 2: Google's Next Generation Large Language Model",
  "url": "https://ai.googleblog.com/2023/05/introducing-palm-2.html",
  "summary": "Today we're announcing PaLM 2, our next generation large language model...",
  "content": "Full article content...",
  "author": "Google AI Team",
  "publish_date": "2023-05-10T10:00:00Z",
  "source": "Google AI Blog",
  "source_type": "official_blog",
  "categories": ["Natural Language Processing", "Large Language Models"],
  "word_count": 1500,
  "images": [
    {
      "url": "https://blogger.googleusercontent.com/img/palm2-architecture.png",
      "alt": "PaLM 2 Architecture Diagram",
      "title": "PaLM 2 Model Architecture"
    }
  ],
  "external_links": [
    {
      "url": "https://arxiv.org/abs/2305.10403",
      "text": "PaLM 2 Technical Report"
    }
  ],
  "technical_analysis": {
    "primary_tech_area": "nlp",
    "technical_depth_score": 8.5,
    "contains_code": true,
    "contains_math": false,
    "machine_learning_mentions": 15,
    "deep_learning_mentions": 8,
    "nlp_mentions": 25
  },
  "quality_score": 9.2,
  "crawl_metadata": {
    "crawl_timestamp": "2024-01-15T12:00:00Z",
    "spider_version": "1.0",
    "processing_time_ms": 2500
  }
}
```

## 常见问题与解决方案

### 1. RSS更新延迟
**问题**: RSS订阅可能不是最新的
**解决**: 
- 结合网站直接爬取
- 设置合理的缓存时间
- 实现增量更新机制

### 2. 内容格式变化
**问题**: Google可能更新博客模板
**解决**: 
- 使用多种选择器策略
- 实现自适应解析
- 定期检查解析效果

### 3. 图片资源处理
**问题**: 图片链接可能失效或需要特殊处理
**解决**: 
- 验证图片链接有效性
- 实现图片本地缓存
- 提供备用图片源

### 4. 技术内容理解
**问题**: 自动分类可能不准确
**解决**: 
- 使用更丰富的关键词库
- 结合机器学习分类
- 人工验证重要文章

## 维护建议

### 定期维护任务
1. **RSS监控**: 检查RSS订阅是否正常
2. **内容验证**: 验证文章内容提取完整性
3. **分类更新**: 更新技术分类和关键词
4. **质量评估**: 评估爬取内容质量

### 扩展方向
1. **多语言支持**: 支持其他语言的Google AI博客
2. **深度分析**: 增加更深入的技术内容分析
3. **趋势预测**: 基于历史数据预测技术趋势
4. **关联分析**: 分析文章间的技术关联性

## 相关资源

- [Google AI Blog](https://ai.googleblog.com/)
- [Google AI Blog RSS](https://ai.googleblog.com/feeds/posts/default)
- [Google Research](https://research.google/)
- [TensorFlow Blog](https://blog.tensorflow.org/)
- [Google Developers Blog](https://developers.googleblog.com/)