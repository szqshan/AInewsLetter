# Towards Data Science 爬虫技术文档

## 目标网站信息

- **网站名称**: Towards Data Science
- **网站地址**: https://towardsdatascience.com/
- **网站类型**: Medium平台上的技术出版物
- **内容类型**: 数据科学、机器学习、AI技术文章
- **更新频率**: 每日10-20篇新文章
- **语言**: 英文为主
- **特点**: 高质量技术内容、实战案例、教程指南

## 爬虫方案概述

### 技术架构
- **爬虫类型**: Medium平台爬虫
- **主要技术**: Python + requests + BeautifulSoup + Selenium (可选)
- **数据格式**: HTML → JSON → Markdown
- **特色功能**: 高质量技术文章、实战教程、代码示例

### 核心功能
1. **文章列表获取**: 从主页和分类页面获取文章列表
2. **内容深度解析**: 提取完整文章内容和代码块
3. **作者信息提取**: 获取作者背景和专业领域
4. **技术分类**: 按数据科学技术栈自动分类
5. **代码提取**: 专门提取和处理代码示例
6. **质量评估**: 基于阅读量、点赞数等指标评分

## 爬取方式详解

### 1. Towards Data Science 网站结构分析

#### 网站特点
```python
TDS_CONFIG = {
    'base_url': 'https://towardsdatascience.com',
    'medium_base': 'https://medium.com',
    'api_endpoints': {
        'latest': 'https://towardsdatascience.com/latest',
        'archive': 'https://towardsdatascience.com/archive',
        'tagged': 'https://towardsdatascience.com/tagged/{tag}',
        'feed': 'https://towardsdatascience.com/feed'
    },
    'selectors': {
        'article_list': 'div[data-testid="post-preview"], article',
        'article_title': 'h1, h2[data-testid="post-title"], .graf--title',
        'article_link': 'a[data-testid="post-preview-title"], h2 a',
        'article_subtitle': '.graf--subtitle, [data-testid="post-subtitle"]',
        'article_content': 'article section, .postArticle-content',
        'article_author': '[data-testid="authorName"], .postMetaInline-authorLockup a',
        'article_date': '[data-testid="storyPublishDate"], .postMetaInline time',
        'article_stats': '[data-testid="post-stats"], .postActions',
        'code_blocks': 'pre, .gist, [class*="code"]'
    },
    'categories': [
        'machine-learning', 'deep-learning', 'data-science',
        'artificial-intelligence', 'python', 'statistics',
        'data-visualization', 'nlp', 'computer-vision'
    ]
}
```

### 2. TDS 文章爬虫实现

#### 主爬虫类
```python
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import re
import json
import logging
from typing import List, Dict, Optional
from urllib.parse import urljoin, urlparse, parse_qs
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import feedparser

class TowardsDataScienceSpider:
    def __init__(self, use_selenium: bool = False):
        self.base_url = 'https://towardsdatascience.com'
        self.medium_base = 'https://medium.com'
        self.use_selenium = use_selenium
        
        # 设置请求会话
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Referer': 'https://towardsdatascience.com/'
        })
        
        # Selenium配置（如果需要）
        if self.use_selenium:
            self.setup_selenium()
        
        self.logger = logging.getLogger("TowardsDataScienceSpider")
    
    def setup_selenium(self):
        """设置Selenium WebDriver"""
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.wait = WebDriverWait(self.driver, 10)
        except Exception as e:
            self.logger.warning(f"Failed to setup Selenium: {e}")
            self.use_selenium = False
    
    def get_rss_feed(self) -> Optional[feedparser.FeedParserDict]:
        """获取RSS订阅内容"""
        try:
            feed_url = f"{self.base_url}/feed"
            self.logger.info(f"Fetching RSS feed: {feed_url}")
            
            feed = feedparser.parse(feed_url)
            
            if feed.bozo:
                self.logger.warning(f"RSS feed parsing warning: {feed.bozo_exception}")
            
            self.logger.info(f"Found {len(feed.entries)} entries in RSS feed")
            return feed
            
        except Exception as e:
            self.logger.error(f"Failed to fetch RSS feed: {e}")
            return None
    
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
        self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "article")))
        
        # 滚动页面确保所有内容加载
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)
        
        return BeautifulSoup(self.driver.page_source, 'html.parser')
    
    def get_latest_articles(self, max_pages: int = 5) -> List[Dict]:
        """获取最新文章列表"""
        articles = []
        
        # 首先尝试RSS
        feed = self.get_rss_feed()
        if feed:
            rss_articles = self.parse_rss_entries(feed)
            articles.extend(rss_articles)
        
        # 然后爬取网页内容作为补充
        for page in range(1, max_pages + 1):
            try:
                if page == 1:
                    page_url = f"{self.base_url}/latest"
                else:
                    page_url = f"{self.base_url}/latest?page={page}"
                
                self.logger.info(f"Fetching articles from page {page}: {page_url}")
                
                soup = self.get_page_content(page_url)
                if not soup:
                    continue
                
                page_articles = self.parse_article_list(soup)
                if not page_articles:
                    self.logger.info(f"No articles found on page {page}, stopping")
                    break
                
                articles.extend(page_articles)
                
                # 添加延迟
                time.sleep(2)
                
            except Exception as e:
                self.logger.error(f"Error fetching page {page}: {e}")
                continue
        
        # 去重
        unique_articles = self.deduplicate_articles(articles)
        
        self.logger.info(f"Total unique articles found: {len(unique_articles)}")
        return unique_articles
    
    def parse_rss_entries(self, feed: feedparser.FeedParserDict) -> List[Dict]:
        """解析RSS条目"""
        articles = []
        
        for entry in feed.entries:
            try:
                article_info = {
                    'title': entry.title,
                    'url': entry.link,
                    'summary': entry.get('summary', ''),
                    'publish_date': self.parse_publish_date(entry),
                    'author': self.extract_author_from_entry(entry),
                    'source': 'Towards Data Science',
                    'source_type': 'tech_blog',
                    'extraction_method': 'rss'
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
                return 'TDS Author'
        except:
            return 'TDS Author'
    
    def parse_article_list(self, soup: BeautifulSoup) -> List[Dict]:
        """解析文章列表页面"""
        articles = []
        
        # 尝试多种选择器
        article_selectors = [
            'div[data-testid="post-preview"]',
            'article',
            'div.postArticle',
            'div[class*="streamItem"]',
            'div[class*="post"]'
        ]
        
        article_elements = []
        for selector in article_selectors:
            elements = soup.select(selector)
            if elements:
                article_elements = elements
                self.logger.info(f"Found {len(elements)} articles using selector: {selector}")
                break
        
        for element in article_elements:
            try:
                article_info = self.extract_article_preview(element)
                if article_info:
                    articles.append(article_info)
            except Exception as e:
                self.logger.warning(f"Error parsing article element: {e}")
                continue
        
        return articles
    
    def extract_article_preview(self, element) -> Optional[Dict]:
        """从文章预览元素提取信息"""
        # 提取标题和链接
        title_selectors = [
            'h2[data-testid="post-preview-title"] a',
            'h2 a', 'h3 a', '.graf--title a',
            'a[data-testid="post-preview-title"]',
            '.postArticle-readMore a'
        ]
        
        title = ''
        url = ''
        
        for selector in title_selectors:
            title_elem = element.select_one(selector)
            if title_elem:
                title = title_elem.get_text(strip=True)
                url = title_elem.get('href', '')
                break
        
        # 如果没找到链接，尝试其他方法
        if not url:
            link_selectors = [
                'a[href*="towardsdatascience.com"]',
                'a[href*="medium.com"]',
                'a[href*="/@"]'
            ]
            
            for selector in link_selectors:
                link_elem = element.select_one(selector)
                if link_elem:
                    url = link_elem.get('href', '')
                    if not title:
                        title = link_elem.get_text(strip=True)
                    break
        
        if not title or not url:
            return None
        
        # 处理相对URL
        if url.startswith('/'):
            url = urljoin(self.base_url, url)
        elif url.startswith('https://medium.com'):
            # Medium链接处理
            pass
        
        # 提取摘要
        summary_selectors = [
            '[data-testid="post-preview-description"]',
            '.graf--subtitle', '.postArticle-readMore',
            'p', '.excerpt'
        ]
        
        summary = ''
        for selector in summary_selectors:
            summary_elem = element.select_one(selector)
            if summary_elem:
                summary_text = summary_elem.get_text(strip=True)
                if len(summary_text) > 50:
                    summary = summary_text[:300] + '...' if len(summary_text) > 300 else summary_text
                    break
        
        # 提取作者
        author_selectors = [
            '[data-testid="authorName"]',
            '.postMetaInline-authorLockup a',
            '.author-name', '.by-author'
        ]
        
        author = ''
        for selector in author_selectors:
            author_elem = element.select_one(selector)
            if author_elem:
                author = author_elem.get_text(strip=True)
                break
        
        # 提取发布日期
        date_selectors = [
            '[data-testid="storyPublishDate"]',
            '.postMetaInline time',
            'time', '.date'
        ]
        
        publish_date = ''
        for selector in date_selectors:
            date_elem = element.select_one(selector)
            if date_elem:
                datetime_attr = date_elem.get('datetime') or date_elem.get('title')
                if datetime_attr:
                    publish_date = datetime_attr
                else:
                    publish_date = date_elem.get_text(strip=True)
                break
        
        # 提取统计信息
        stats = self.extract_article_stats(element)
        
        article_info = {
            'title': title,
            'url': url,
            'summary': summary,
            'author': author or 'TDS Author',
            'publish_date': publish_date,
            'source': 'Towards Data Science',
            'source_type': 'tech_blog',
            'extraction_method': 'web_scraping',
            'stats': stats
        }
        
        # 生成唯一ID
        article_info['article_id'] = self.generate_article_id(article_info)
        
        return article_info
    
    def extract_article_stats(self, element) -> Dict:
        """提取文章统计信息"""
        stats = {
            'claps': 0,
            'responses': 0,
            'reading_time': 0
        }
        
        # 提取拍手数
        clap_selectors = [
            '[data-testid="post-stats"] button[aria-label*="clap"]',
            '.clapCount', '[class*="clap"]'
        ]
        
        for selector in clap_selectors:
            clap_elem = element.select_one(selector)
            if clap_elem:
                clap_text = clap_elem.get_text(strip=True)
                clap_match = re.search(r'(\d+)', clap_text)
                if clap_match:
                    stats['claps'] = int(clap_match.group(1))
                    break
        
        # 提取回复数
        response_selectors = [
            '[data-testid="post-stats"] button[aria-label*="response"]',
            '.responseCount', '[class*="response"]'
        ]
        
        for selector in response_selectors:
            response_elem = element.select_one(selector)
            if response_elem:
                response_text = response_elem.get_text(strip=True)
                response_match = re.search(r'(\d+)', response_text)
                if response_match:
                    stats['responses'] = int(response_match.group(1))
                    break
        
        # 提取阅读时间
        reading_time_selectors = [
            '[data-testid="storyReadTime"]',
            '.readingTime', '[class*="reading"]'
        ]
        
        for selector in reading_time_selectors:
            time_elem = element.select_one(selector)
            if time_elem:
                time_text = time_elem.get_text(strip=True)
                time_match = re.search(r'(\d+)', time_text)
                if time_match:
                    stats['reading_time'] = int(time_match.group(1))
                    break
        
        return stats
    
    def get_article_details(self, article_info: Dict) -> Dict:
        """获取文章详细内容"""
        url = article_info.get('url')
        if not url:
            return article_info
        
        try:
            self.logger.info(f"Fetching article details: {url}")
            
            soup = self.get_page_content(url)
            if not soup:
                return article_info
            
            # 提取文章内容
            content = self.extract_article_content(soup)
            if content:
                article_info['content'] = content
                article_info['word_count'] = len(content.split())
            
            # 提取代码块
            code_blocks = self.extract_code_blocks(soup)
            if code_blocks:
                article_info['code_blocks'] = code_blocks
            
            # 提取更详细的元数据
            detailed_metadata = self.extract_detailed_metadata(soup)
            article_info.update(detailed_metadata)
            
            # 提取图片信息
            images = self.extract_images(soup)
            if images:
                article_info['images'] = images
            
            # 技术内容分析
            tech_analysis = self.analyze_technical_content(content, article_info.get('title', ''))
            article_info['technical_analysis'] = tech_analysis
            
            # 计算质量分数
            article_info['quality_score'] = self.calculate_quality_score(article_info)
            
        except Exception as e:
            self.logger.error(f"Error fetching article details for {url}: {e}")
        
        return article_info
    
    def extract_article_content(self, soup: BeautifulSoup) -> str:
        """提取文章正文内容"""
        # Medium/TDS的内容结构
        content_selectors = [
            'article section',
            '.postArticle-content',
            'div[data-testid="storyContent"]',
            '.story-content',
            'article div[class*="content"]'
        ]
        
        for selector in content_selectors:
            content_elem = soup.select_one(selector)
            if content_elem:
                content = self.clean_article_content(content_elem)
                if len(content) > 300:
                    return content
        
        # 备用方案：查找所有段落
        paragraphs = soup.find_all('p')
        if paragraphs:
            content_parts = []
            for p in paragraphs:
                text = p.get_text(strip=True)
                if len(text) > 30:
                    content_parts.append(text)
            
            if content_parts:
                return '\n\n'.join(content_parts)
        
        return ''
    
    def clean_article_content(self, content_elem) -> str:
        """清理文章内容"""
        # 移除不需要的元素
        for tag in content_elem.find_all(['script', 'style', 'nav', 'aside', 'footer']):
            tag.decompose()
        
        # 移除广告和分享按钮
        for tag in content_elem.find_all(class_=re.compile(r'ad|share|social|related')):
            tag.decompose()
        
        # 处理代码块（保留原格式）
        for code_block in content_elem.find_all(['pre', 'code']):
            if code_block.name == 'pre':
                code_text = code_block.get_text()
                code_block.string = f"\n```\n{code_text}\n```\n"
            else:
                code_text = code_block.get_text()
                code_block.string = f"`{code_text}`"
        
        # 处理链接
        for link in content_elem.find_all('a', href=True):
            href = link.get('href')
            text = link.get_text(strip=True)
            if href and text and href != text:
                link.string = f"[{text}]({href})"
        
        # 处理图片
        for img in content_elem.find_all('img'):
            alt = img.get('alt', '')
            src = img.get('src', '')
            if alt and src:
                img.string = f"![{alt}]({src})"
            elif src:
                img.string = f"![Image]({src})"
        
        # 获取文本内容
        text = content_elem.get_text(separator='\n', strip=True)
        
        # 清理多余的空行
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        return '\n\n'.join(lines)
    
    def extract_code_blocks(self, soup: BeautifulSoup) -> List[Dict]:
        """提取代码块"""
        code_blocks = []
        
        # 查找代码块
        code_selectors = [
            'pre', '.gist', 'div[class*="code"]',
            'div[class*="highlight"]', 'code'
        ]
        
        for selector in code_selectors:
            code_elements = soup.select(selector)
            
            for elem in code_elements:
                code_text = elem.get_text(strip=True)
                
                # 过滤短代码片段
                if len(code_text) < 20:
                    continue
                
                # 检测编程语言
                language = self.detect_programming_language(code_text)
                
                code_info = {
                    'code': code_text,
                    'language': language,
                    'line_count': len(code_text.split('\n')),
                    'char_count': len(code_text)
                }
                
                code_blocks.append(code_info)
        
        return code_blocks
    
    def detect_programming_language(self, code: str) -> str:
        """检测编程语言"""
        code_lower = code.lower()
        
        # Python关键词
        python_keywords = ['import ', 'def ', 'class ', 'if __name__', 'print(', 'pandas', 'numpy']
        if any(keyword in code_lower for keyword in python_keywords):
            return 'python'
        
        # R关键词
        r_keywords = ['library(', '<-', 'data.frame', 'ggplot']
        if any(keyword in code_lower for keyword in r_keywords):
            return 'r'
        
        # SQL关键词
        sql_keywords = ['select ', 'from ', 'where ', 'join ', 'group by']
        if any(keyword in code_lower for keyword in sql_keywords):
            return 'sql'
        
        # JavaScript关键词
        js_keywords = ['function(', 'var ', 'let ', 'const ', 'console.log']
        if any(keyword in code_lower for keyword in js_keywords):
            return 'javascript'
        
        return 'unknown'
    
    def extract_detailed_metadata(self, soup: BeautifulSoup) -> Dict:
        """提取详细元数据"""
        metadata = {}
        
        # 提取标签
        tag_selectors = [
            'a[href*="/tagged/"]',
            '.tags a', '.post-tags a'
        ]
        
        for selector in tag_selectors:
            tag_elems = soup.select(selector)
            if tag_elems:
                tags = []
                for elem in tag_elems:
                    tag_text = elem.get_text(strip=True)
                    if tag_text and len(tag_text) < 50:
                        tags.append(tag_text)
                metadata['tags'] = tags[:10]  # 限制标签数量
                break
        
        # 提取作者详细信息
        author_bio_selectors = [
            '.author-bio', '.author-description',
            '[data-testid="authorBio"]'
        ]
        
        for selector in author_bio_selectors:
            bio_elem = soup.select_one(selector)
            if bio_elem:
                bio_text = bio_elem.get_text(strip=True)
                if len(bio_text) > 20:
                    metadata['author_bio'] = bio_text
                    break
        
        # 提取发布统计
        stats_selectors = [
            '[data-testid="post-stats"]',
            '.postActions', '.story-stats'
        ]
        
        for selector in stats_selectors:
            stats_elem = soup.select_one(selector)
            if stats_elem:
                # 提取详细统计信息
                detailed_stats = self.extract_detailed_stats(stats_elem)
                metadata['detailed_stats'] = detailed_stats
                break
        
        return metadata
    
    def extract_detailed_stats(self, stats_elem) -> Dict:
        """提取详细统计信息"""
        stats = {
            'claps': 0,
            'responses': 0,
            'reading_time': 0,
            'followers': 0
        }
        
        stats_text = stats_elem.get_text()
        
        # 提取各种统计数字
        clap_match = re.search(r'(\d+)\s*clap', stats_text, re.IGNORECASE)
        if clap_match:
            stats['claps'] = int(clap_match.group(1))
        
        response_match = re.search(r'(\d+)\s*response', stats_text, re.IGNORECASE)
        if response_match:
            stats['responses'] = int(response_match.group(1))
        
        time_match = re.search(r'(\d+)\s*min', stats_text, re.IGNORECASE)
        if time_match:
            stats['reading_time'] = int(time_match.group(1))
        
        return stats
    
    def extract_images(self, soup: BeautifulSoup) -> List[Dict]:
        """提取文章图片"""
        images = []
        
        # 查找文章中的图片
        img_tags = soup.select('article img, .story-content img, section img')
        
        for img in img_tags:
            src = img.get('src')
            if src:
                # 处理相对URL
                if src.startswith('//'):
                    src = 'https:' + src
                elif src.startswith('/'):
                    src = urljoin(self.base_url, src)
                
                # 过滤小图标
                width = img.get('width')
                height = img.get('height')
                if width and height:
                    try:
                        if int(width) < 100 or int(height) < 100:
                            continue
                    except:
                        pass
                
                image_info = {
                    'url': src,
                    'alt': img.get('alt', ''),
                    'title': img.get('title', ''),
                    'width': width,
                    'height': height
                }
                
                images.append(image_info)
        
        return images
    
    def analyze_technical_content(self, content: str, title: str) -> Dict:
        """分析技术内容"""
        analysis = {}
        
        # 数据科学技术栈关键词
        tech_keywords = {
            'python': ['python', 'pandas', 'numpy', 'scikit-learn', 'matplotlib', 'seaborn'],
            'machine_learning': ['machine learning', 'ml', 'algorithm', 'model', 'training'],
            'deep_learning': ['deep learning', 'neural network', 'tensorflow', 'pytorch', 'keras'],
            'data_analysis': ['data analysis', 'statistics', 'correlation', 'regression'],
            'data_visualization': ['visualization', 'plot', 'chart', 'graph', 'dashboard'],
            'nlp': ['nlp', 'natural language', 'text mining', 'sentiment analysis'],
            'computer_vision': ['computer vision', 'image processing', 'opencv', 'cnn'],
            'big_data': ['big data', 'spark', 'hadoop', 'distributed computing'],
            'cloud': ['aws', 'azure', 'gcp', 'cloud computing', 'docker']
        }
        
        # 内容类型关键词
        content_type_keywords = {
            'tutorial': ['tutorial', 'guide', 'how to', 'step by step', 'walkthrough'],
            'case_study': ['case study', 'project', 'real world', 'implementation'],
            'theory': ['theory', 'concept', 'principle', 'mathematical', 'algorithm'],
            'comparison': ['comparison', 'vs', 'versus', 'compare', 'difference'],
            'review': ['review', 'overview', 'survey', 'comprehensive']
        }
        
        combined_text = (title + ' ' + content).lower()
        
        # 分析技术栈
        for tech, keywords in tech_keywords.items():
            mentions = sum(combined_text.count(keyword.lower()) for keyword in keywords)
            analysis[f'{tech}_mentions'] = mentions
        
        # 确定主要技术栈
        tech_scores = {k.replace('_mentions', ''): v for k, v in analysis.items() if k.endswith('_mentions')}
        if tech_scores:
            analysis['primary_tech_stack'] = max(tech_scores.items(), key=lambda x: x[1])[0]
        
        # 分析内容类型
        for content_type, keywords in content_type_keywords.items():
            score = sum(combined_text.count(keyword.lower()) for keyword in keywords)
            analysis[f'{content_type}_score'] = score
        
        # 确定主要内容类型
        type_scores = {k.replace('_score', ''): v for k, v in analysis.items() if k.endswith('_score')}
        if type_scores:
            analysis['primary_content_type'] = max(type_scores.items(), key=lambda x: x[1])[0]
        
        # 技术深度评估
        technical_terms = [
            'algorithm', 'implementation', 'optimization', 'performance',
            'accuracy', 'precision', 'recall', 'f1-score', 'cross-validation'
        ]
        tech_depth = sum(combined_text.count(term) for term in technical_terms)
        analysis['technical_depth_score'] = min(tech_depth / 3, 10)  # 归一化到0-10
        
        # 实用性评估
        practical_indicators = [
            'code', 'example', 'implementation', 'practical', 'hands-on',
            'tutorial', 'step by step', 'github', 'notebook'
        ]
        practical_score = sum(combined_text.count(indicator) for indicator in practical_indicators)
        analysis['practical_score'] = min(practical_score / 2, 10)
        
        return analysis
    
    def get_articles_by_tag(self, tag: str, max_articles: int = 50) -> List[Dict]:
        """按标签获取文章"""
        tag_url = f"{self.base_url}/tagged/{tag}"
        
        try:
            self.logger.info(f"Fetching articles for tag: {tag}")
            
            soup = self.get_page_content(tag_url)
            if not soup:
                return []
            
            articles = self.parse_article_list(soup)
            
            # 获取详细内容
            detailed_articles = []
            for article in articles[:max_articles]:
                detailed_article = self.get_article_details(article)
                detailed_articles.append(detailed_article)
                
                time.sleep(1)  # 添加延迟
            
            return detailed_articles
            
        except Exception as e:
            self.logger.error(f"Error fetching articles for tag {tag}: {e}")
            return []
    
    def get_trending_articles(self, days: int = 7) -> List[Dict]:
        """获取热门文章"""
        articles = self.get_latest_articles(max_pages=3)
        
        # 过滤最近几天的文章
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_articles = []
        
        for article in articles:
            try:
                pub_date_str = article.get('publish_date', '')
                if pub_date_str:
                    pub_date = self.parse_date(pub_date_str)
                    if pub_date and pub_date >= cutoff_date:
                        recent_articles.append(article)
                else:
                    recent_articles.append(article)
            except:
                recent_articles.append(article)
        
        # 获取详细内容并计算热度
        trending_articles = []
        for article in recent_articles:
            detailed_article = self.get_article_details(article)
            
            # 计算热度分数
            popularity_score = self.calculate_popularity_score(detailed_article)
            detailed_article['popularity_score'] = popularity_score
            
            trending_articles.append(detailed_article)
            time.sleep(1)
        
        # 按热度排序
        trending_articles.sort(key=lambda x: x.get('popularity_score', 0), reverse=True)
        
        return trending_articles
    
    def parse_date(self, date_str: str) -> Optional[datetime]:
        """解析日期字符串"""
        date_formats = [
            '%Y-%m-%dT%H:%M:%S%z',
            '%Y-%m-%dT%H:%M:%SZ',
            '%Y-%m-%d',
            '%B %d, %Y',
            '%b %d, %Y',
            '%d %B %Y',
            '%d %b %Y'
        ]
        
        for fmt in date_formats:
            try:
                return datetime.strptime(date_str, fmt)
            except:
                continue
        
        return None
    
    def calculate_popularity_score(self, article: Dict) -> float:
        """计算热度分数"""
        score = 0.0
        
        # 基于统计数据
        stats = article.get('stats', {})
        detailed_stats = article.get('detailed_stats', {})
        
        claps = stats.get('claps', 0) or detailed_stats.get('claps', 0)
        responses = stats.get('responses', 0) or detailed_stats.get('responses', 0)
        reading_time = stats.get('reading_time', 0) or detailed_stats.get('reading_time', 0)
        
        # 拍手数权重最高
        score += claps * 0.1
        
        # 回复数
        score += responses * 2
        
        # 阅读时间（适中的阅读时间更受欢迎）
        if 5 <= reading_time <= 15:
            score += 10
        elif reading_time > 0:
            score += 5
        
        # 质量分数
        quality_score = article.get('quality_score', 0)
        score += quality_score * 5
        
        # 时间衰减
        try:
            pub_date_str = article.get('publish_date', '')
            if pub_date_str:
                pub_date = self.parse_date(pub_date_str)
                if pub_date:
                    age_days = (datetime.now() - pub_date).days
                    time_factor = max(0.1, 1 - (age_days / 30))  # 30天内线性衰减
                    score *= time_factor
        except:
            pass
        
        return round(score, 2)
    
    def calculate_quality_score(self, article: Dict) -> float:
        """计算文章质量分数"""
        score = 6.0  # TDS基础高分
        
        # 内容长度
        word_count = article.get('word_count', 0)
        if word_count > 2000:
            score += 1.5
        elif word_count > 1000:
            score += 1.0
        elif word_count > 500:
            score += 0.5
        
        # 技术分析
        tech_analysis = article.get('technical_analysis', {})
        tech_depth = tech_analysis.get('technical_depth_score', 0)
        practical_score = tech_analysis.get('practical_score', 0)
        
        score += min(tech_depth * 0.2, 1.5)
        score += min(practical_score * 0.15, 1.0)
        
        # 代码块
        code_blocks = article.get('code_blocks', [])
        if len(code_blocks) > 3:
            score += 1.0
        elif len(code_blocks) > 0:
            score += 0.5
        
        # 图片
        images = article.get('images', [])
        if len(images) > 2:
            score += 0.5
        
        # 统计数据
        stats = article.get('stats', {})
        claps = stats.get('claps', 0)
        if claps > 100:
            score += 1.0
        elif claps > 50:
            score += 0.5
        
        return min(score, 10.0)
    
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
        content = f"{article.get('title', '')}{article.get('url', '')}tds"
        return hashlib.md5(content.encode('utf-8')).hexdigest()[:16]
    
    def __del__(self):
        """清理资源"""
        if hasattr(self, 'driver'):
            try:
                self.driver.quit()
            except:
                pass
```

## 反爬虫应对策略

### 1. Medium平台限制处理
```python
class MediumRateLimiter:
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

### 2. 动态内容处理
```python
def handle_dynamic_content(url: str, use_selenium: bool = False):
    """处理动态加载的内容"""
    if use_selenium:
        # 使用Selenium处理JavaScript渲染
        driver = webdriver.Chrome()
        driver.get(url)
        
        # 等待内容加载
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "article"))
        )
        
        # 滚动加载更多内容
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)
        
        content = driver.page_source
        driver.quit()
        
        return BeautifulSoup(content, 'html.parser')
    else:
        # 使用requests处理静态内容
        response = requests.get(url)
        return BeautifulSoup(response.text, 'html.parser')
```

## 配置参数

### 爬虫配置
```python
TDS_SPIDER_CONFIG = {
    'request_settings': {
        'timeout': 30,
        'max_retries': 3,
        'delay_range': [1, 3],
        'use_selenium': False
    },
    'content_processing': {
        'max_content_length': 50000,
        'extract_code_blocks': True,
        'extract_images': True,
        'clean_html': True
    },
    'quality_filters': {
        'min_word_count': 300,
        'min_reading_time': 2,
        'require_code': False
    },
    'categories': [
        'machine-learning', 'deep-learning', 'data-science',
        'python', 'statistics', 'data-visualization'
    ]
}
```

## 数据输出格式

### JSON格式
```json
{
  "article_id": "tds_001",
  "title": "Complete Guide to Machine Learning with Python",
  "url": "https://towardsdatascience.com/complete-guide-ml-python-abc123",
  "summary": "A comprehensive tutorial on machine learning...",
  "content": "Full article content with code examples...",
  "author": "John Data Scientist",
  "author_bio": "Senior ML Engineer at Tech Company...",
  "publish_date": "2024-01-15T10:00:00Z",
  "source": "Towards Data Science",
  "source_type": "tech_blog",
  "word_count": 2500,
  "tags": ["machine-learning", "python", "tutorial"],
  "stats": {
    "claps": 156,
    "responses": 23,
    "reading_time": 12
  },
  "code_blocks": [
    {
      "code": "import pandas as pd\nimport numpy as np...",
      "language": "python",
      "line_count": 15,
      "char_count": 450
    }
  ],
  "images": [
    {
      "url": "https://miro.medium.com/max/1400/1*example.png",
      "alt": "ML Algorithm Comparison",
      "title": "Performance Comparison"
    }
  ],
  "technical_analysis": {
    "primary_tech_stack": "python",
    "primary_content_type": "tutorial",
    "technical_depth_score": 8.5,
    "practical_score": 9.0,
    "python_mentions": 25,
    "machine_learning_mentions": 18
  },
  "quality_score": 8.7,
  "popularity_score": 145.3,
  "crawl_metadata": {
    "crawl_timestamp": "2024-01-15T12:00:00Z",
    "extraction_method": "web_scraping",
    "spider_version": "1.0",
    "processing_time_ms": 2800
  }
}
```

## 常见问题与解决方案

### 1. Medium付费墙问题
**问题**: 部分文章需要Medium会员
**解决**: 
- 优先爬取免费文章
- 使用RSS获取摘要
- 实现会员状态检测

### 2. 动态加载内容
**问题**: 部分内容通过JavaScript加载
**解决**: 
- 使用Selenium作为备用方案
- 分析网络请求，直接调用API
- 实现智能检测机制

### 3. 代码块格式化
**问题**: 代码块可能格式混乱
**解决**: 
- 使用专门的代码提取器
- 保留原始格式
- 实现语言检测

### 4. 图片处理
**问题**: Medium图片可能有防盗链
**解决**: 
- 使用正确的Referer头
- 实现图片代理
- 提供备用图片源

## 维护建议

### 定期维护任务
1. **网站结构监控**: 检查TDS网站结构变化
2. **内容质量评估**: 评估提取内容的完整性
3. **代码提取优化**: 优化代码块提取效果
4. **性能监控**: 监控爬取速度和成功率

### 扩展方向
1. **作者分析**: 增加作者影响力分析
2. **趋势预测**: 基于文章数据预测技术趋势
3. **个性化推荐**: 基于用户兴趣推荐文章
4. **多平台整合**: 整合其他技术博客平台

## 相关资源

- [Towards Data Science](https://towardsdatascience.com/)
- [Medium Partner Program](https://help.medium.com/hc/en-us/articles/115011694187)
- [Medium API Documentation](https://github.com/Medium/medium-api-docs)
- [Medium RSS Feeds](https://help.medium.com/hc/en-us/articles/214874118)
- [Medium Content Guidelines](https://help.medium.com/hc/en-us/articles/360006362473)