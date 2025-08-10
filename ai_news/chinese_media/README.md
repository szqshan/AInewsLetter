# 中文AI媒体爬虫技术文档

## 目标网站信息

- **爬取范围**: 主要中文AI媒体和技术博客
- **主要网站**: 机器之心、AI科技大本营、雷锋网、36氪AI、钛媒体AI等
- **内容类型**: AI新闻、技术文章、行业分析、产品评测
- **更新频率**: 每日更新
- **语言特点**: 中文内容，需要处理中文分词和编码

## 爬虫方案概述

### 技术架构
- **爬虫类型**: 多站点新闻聚合爬虫
- **主要技术**: Python + requests + BeautifulSoup + jieba
- **数据格式**: HTML → JSON → Markdown
- **特色功能**: 中文内容处理、热度分析、情感分析

### 核心功能
1. **多媒体聚合**: 聚合主流中文AI媒体内容
2. **智能去重**: 基于内容相似度的去重算法
3. **热度评估**: 综合阅读量、评论数等指标
4. **内容分类**: 按AI子领域自动分类
5. **情感分析**: 分析文章情感倾向和观点

## 爬取方式详解

### 1. 中文媒体网站配置

#### 支持的媒体列表
```python
CHINESE_MEDIA_CONFIGS = {
    'jiqizhixin': {
        'name': '机器之心',
        'base_url': 'https://www.jiqizhixin.com',
        'rss_url': 'https://www.jiqizhixin.com/rss',
        'article_list_url': 'https://www.jiqizhixin.com/articles',
        'category_urls': {
            'industry': 'https://www.jiqizhixin.com/categories/industry',
            'academic': 'https://www.jiqizhixin.com/categories/academic',
            'technology': 'https://www.jiqizhixin.com/categories/technology'
        },
        'selectors': {
            'title': 'h1.article-title',
            'content': 'div.article-content',
            'author': 'span.author-name',
            'publish_time': 'time.publish-time',
            'tags': 'div.article-tags a',
            'view_count': 'span.view-count'
        },
        'encoding': 'utf-8',
        'language': 'zh-CN'
    },
    'ai_tech_base': {
        'name': 'AI科技大本营',
        'base_url': 'https://blog.csdn.net/dQCFKyQDXYm3F8rB0',
        'article_list_url': 'https://blog.csdn.net/dQCFKyQDXYm3F8rB0/article/list',
        'selectors': {
            'title': 'h1.title-article',
            'content': 'div#content_views',
            'author': 'a.follow-nickName',
            'publish_time': 'span.time',
            'view_count': 'span.read-count',
            'comment_count': 'span.comment-count'
        },
        'encoding': 'utf-8',
        'language': 'zh-CN'
    },
    'leiphone': {
        'name': '雷锋网',
        'base_url': 'https://www.leiphone.com',
        'rss_url': 'https://www.leiphone.com/feed',
        'category_urls': {
            'ai': 'https://www.leiphone.com/category/ai',
            'robotics': 'https://www.leiphone.com/category/robotics',
            'autonomous_driving': 'https://www.leiphone.com/category/intelligent-driving'
        },
        'selectors': {
            'title': 'h1.article-title',
            'content': 'div.article-content',
            'author': 'span.author',
            'publish_time': 'time.publish-time',
            'tags': 'div.tags a',
            'view_count': 'span.view-num'
        },
        'encoding': 'utf-8',
        'language': 'zh-CN'
    },
    '36kr_ai': {
        'name': '36氪AI',
        'base_url': 'https://36kr.com',
        'category_urls': {
            'ai': 'https://36kr.com/search/articles/人工智能',
            'machine_learning': 'https://36kr.com/search/articles/机器学习',
            'deep_learning': 'https://36kr.com/search/articles/深度学习'
        },
        'selectors': {
            'title': 'h1.article-title',
            'content': 'div.article-content',
            'author': 'span.author-name',
            'publish_time': 'time.time',
            'view_count': 'span.view-count',
            'like_count': 'span.like-count'
        },
        'encoding': 'utf-8',
        'language': 'zh-CN'
    },
    'tmtpost_ai': {
        'name': '钛媒体AI',
        'base_url': 'https://www.tmtpost.com',
        'search_url': 'https://www.tmtpost.com/search?q=人工智能',
        'selectors': {
            'title': 'h1.article-title',
            'content': 'div.article-content',
            'author': 'span.author',
            'publish_time': 'time.publish-time',
            'view_count': 'span.view-count'
        },
        'encoding': 'utf-8',
        'language': 'zh-CN'
    },
    'infoq_ai': {
        'name': 'InfoQ AI',
        'base_url': 'https://www.infoq.cn',
        'category_urls': {
            'ai': 'https://www.infoq.cn/topic/ai',
            'machine_learning': 'https://www.infoq.cn/topic/machine-learning'
        },
        'selectors': {
            'title': 'h1.article-title',
            'content': 'div.article-content',
            'author': 'span.author',
            'publish_time': 'time.publish-time'
        },
        'encoding': 'utf-8',
        'language': 'zh-CN'
    }
}
```

### 2. 中文内容爬虫实现

#### 基础中文媒体爬虫
```python
import requests
from bs4 import BeautifulSoup
import jieba
import jieba.analyse
from datetime import datetime, timedelta
import re
import json
import logging
from typing import List, Dict, Optional
from urllib.parse import urljoin, urlparse
import time
import hashlib

class ChineseMediaSpider:
    def __init__(self, media_config: Dict):
        self.config = media_config
        self.base_url = media_config['base_url']
        self.media_name = media_config['name']
        self.encoding = media_config.get('encoding', 'utf-8')
        
        # 设置请求会话
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive'
        })
        
        # 初始化jieba分词
        self.setup_jieba()
        
        self.logger = logging.getLogger(f"ChineseMediaSpider_{self.media_name}")
    
    def setup_jieba(self):
        """设置jieba分词器"""
        # 添加AI领域专业词汇
        ai_terms = [
            '人工智能', '机器学习', '深度学习', '神经网络', '自然语言处理',
            '计算机视觉', '强化学习', '迁移学习', '生成对抗网络', '卷积神经网络',
            '循环神经网络', '注意力机制', '预训练模型', '大语言模型', '多模态',
            '自动驾驶', '智能机器人', '语音识别', '图像识别', '推荐系统',
            'ChatGPT', 'GPT', 'BERT', 'Transformer', 'LSTM', 'CNN', 'RNN',
            '百度', '阿里巴巴', '腾讯', '字节跳动', '华为', '商汤', '旷视', '依图'
        ]
        
        for term in ai_terms:
            jieba.add_word(term)
        
        # 设置关键词提取参数
        jieba.analyse.set_stop_words('stopwords.txt')  # 如果有停用词文件
    
    def get_page_content(self, url: str) -> Optional[str]:
        """获取页面内容"""
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            # 处理编码
            if response.encoding != self.encoding:
                response.encoding = self.encoding
            
            return response.text
        except Exception as e:
            self.logger.error(f"Failed to get page content from {url}: {e}")
            return None
    
    def parse_article_list(self, list_url: str, max_pages: int = 5) -> List[Dict]:
        """解析文章列表"""
        articles = []
        
        for page in range(1, max_pages + 1):
            page_url = f"{list_url}?page={page}" if '?' not in list_url else f"{list_url}&page={page}"
            
            self.logger.info(f"Fetching article list page {page}: {page_url}")
            
            content = self.get_page_content(page_url)
            if not content:
                continue
            
            soup = BeautifulSoup(content, 'html.parser')
            page_articles = self.extract_articles_from_list(soup)
            
            if not page_articles:
                break  # 没有更多文章
            
            articles.extend(page_articles)
            
            # 添加延迟
            time.sleep(2)
        
        self.logger.info(f"Found {len(articles)} articles from {self.media_name}")
        return articles
    
    def extract_articles_from_list(self, soup: BeautifulSoup) -> List[Dict]:
        """从列表页面提取文章信息"""
        articles = []
        
        # 根据媒体类型使用不同的解析策略
        if '机器之心' in self.media_name:
            articles = self.extract_jiqizhixin_articles(soup)
        elif 'AI科技大本营' in self.media_name:
            articles = self.extract_csdn_articles(soup)
        elif '雷锋网' in self.media_name:
            articles = self.extract_leiphone_articles(soup)
        elif '36氪' in self.media_name:
            articles = self.extract_36kr_articles(soup)
        elif '钛媒体' in self.media_name:
            articles = self.extract_tmtpost_articles(soup)
        elif 'InfoQ' in self.media_name:
            articles = self.extract_infoq_articles(soup)
        else:
            articles = self.extract_generic_articles(soup)
        
        return articles
    
    def extract_jiqizhixin_articles(self, soup: BeautifulSoup) -> List[Dict]:
        """提取机器之心文章"""
        articles = []
        
        # 机器之心文章列表结构
        article_items = soup.find_all('div', class_='article-item')
        
        for item in article_items:
            try:
                # 提取标题和链接
                title_elem = item.find('h3', class_='article-title') or item.find('a')
                if not title_elem:
                    continue
                
                title_link = title_elem.find('a') if title_elem.name != 'a' else title_elem
                if not title_link:
                    continue
                
                title = title_link.get_text(strip=True)
                url = title_link.get('href', '')
                
                if url.startswith('/'):
                    url = urljoin(self.base_url, url)
                
                # 提取摘要
                summary_elem = item.find('p', class_='article-summary')
                summary = summary_elem.get_text(strip=True) if summary_elem else ''
                
                # 提取发布时间
                time_elem = item.find('time') or item.find('span', class_='time')
                publish_time = time_elem.get_text(strip=True) if time_elem else ''
                
                # 提取作者
                author_elem = item.find('span', class_='author')
                author = author_elem.get_text(strip=True) if author_elem else ''
                
                # 提取标签
                tag_elems = item.find_all('span', class_='tag')
                tags = [tag.get_text(strip=True) for tag in tag_elems]
                
                article_info = {
                    'title': title,
                    'url': url,
                    'summary': summary,
                    'author': author,
                    'publish_time': publish_time,
                    'tags': tags,
                    'media_name': self.media_name,
                    'language': 'zh-CN'
                }
                
                articles.append(article_info)
                
            except Exception as e:
                self.logger.warning(f"Error extracting article from {self.media_name}: {e}")
                continue
        
        return articles
    
    def extract_csdn_articles(self, soup: BeautifulSoup) -> List[Dict]:
        """提取CSDN文章"""
        articles = []
        
        # CSDN文章列表结构
        article_items = soup.find_all('div', class_='article-item-box')
        
        for item in article_items:
            try:
                # 提取标题和链接
                title_elem = item.find('h4') or item.find('a', class_='article-title')
                if not title_elem:
                    continue
                
                title_link = title_elem.find('a') if title_elem.name != 'a' else title_elem
                if not title_link:
                    continue
                
                title = title_link.get_text(strip=True)
                url = title_link.get('href', '')
                
                # 提取摘要
                summary_elem = item.find('p', class_='content')
                summary = summary_elem.get_text(strip=True) if summary_elem else ''
                
                # 提取发布时间
                time_elem = item.find('span', class_='date')
                publish_time = time_elem.get_text(strip=True) if time_elem else ''
                
                # 提取阅读数和评论数
                read_elem = item.find('span', class_='read-num')
                read_count = read_elem.get_text(strip=True) if read_elem else '0'
                
                comment_elem = item.find('span', class_='comment-num')
                comment_count = comment_elem.get_text(strip=True) if comment_elem else '0'
                
                article_info = {
                    'title': title,
                    'url': url,
                    'summary': summary,
                    'publish_time': publish_time,
                    'read_count': read_count,
                    'comment_count': comment_count,
                    'media_name': self.media_name,
                    'language': 'zh-CN'
                }
                
                articles.append(article_info)
                
            except Exception as e:
                self.logger.warning(f"Error extracting article from {self.media_name}: {e}")
                continue
        
        return articles
    
    def extract_leiphone_articles(self, soup: BeautifulSoup) -> List[Dict]:
        """提取雷锋网文章"""
        articles = []
        
        # 雷锋网文章列表结构
        article_items = soup.find_all('div', class_='news-item')
        
        for item in article_items:
            try:
                # 提取标题和链接
                title_elem = item.find('h3') or item.find('a', class_='title')
                if not title_elem:
                    continue
                
                title_link = title_elem.find('a') if title_elem.name != 'a' else title_elem
                if not title_link:
                    continue
                
                title = title_link.get_text(strip=True)
                url = title_link.get('href', '')
                
                if url.startswith('/'):
                    url = urljoin(self.base_url, url)
                
                # 提取摘要
                summary_elem = item.find('p', class_='summary')
                summary = summary_elem.get_text(strip=True) if summary_elem else ''
                
                # 提取作者和时间
                meta_elem = item.find('div', class_='meta')
                author = ''
                publish_time = ''
                
                if meta_elem:
                    author_elem = meta_elem.find('span', class_='author')
                    author = author_elem.get_text(strip=True) if author_elem else ''
                    
                    time_elem = meta_elem.find('span', class_='time')
                    publish_time = time_elem.get_text(strip=True) if time_elem else ''
                
                # 提取标签
                tag_elems = item.find_all('span', class_='tag')
                tags = [tag.get_text(strip=True) for tag in tag_elems]
                
                article_info = {
                    'title': title,
                    'url': url,
                    'summary': summary,
                    'author': author,
                    'publish_time': publish_time,
                    'tags': tags,
                    'media_name': self.media_name,
                    'language': 'zh-CN'
                }
                
                articles.append(article_info)
                
            except Exception as e:
                self.logger.warning(f"Error extracting article from {self.media_name}: {e}")
                continue
        
        return articles
    
    def extract_generic_articles(self, soup: BeautifulSoup) -> List[Dict]:
        """通用文章提取方法"""
        articles = []
        
        # 尝试多种常见的文章列表结构
        selectors = [
            'article',
            'div.article',
            'div.post',
            'div.news-item',
            'div.content-item',
            'li.article-item'
        ]
        
        for selector in selectors:
            items = soup.select(selector)
            if items:
                break
        
        for item in items:
            try:
                # 查找标题链接
                title_link = None
                for tag in ['h1', 'h2', 'h3', 'h4', 'h5']:
                    title_elem = item.find(tag)
                    if title_elem:
                        title_link = title_elem.find('a')
                        if title_link:
                            break
                
                if not title_link:
                    # 直接查找链接
                    title_link = item.find('a')
                
                if not title_link:
                    continue
                
                title = title_link.get_text(strip=True)
                url = title_link.get('href', '')
                
                if url.startswith('/'):
                    url = urljoin(self.base_url, url)
                
                # 查找摘要
                summary = ''
                summary_selectors = ['p.summary', 'div.summary', 'p.excerpt', 'div.excerpt']
                for sel in summary_selectors:
                    summary_elem = item.select_one(sel)
                    if summary_elem:
                        summary = summary_elem.get_text(strip=True)
                        break
                
                article_info = {
                    'title': title,
                    'url': url,
                    'summary': summary,
                    'media_name': self.media_name,
                    'language': 'zh-CN'
                }
                
                articles.append(article_info)
                
            except Exception as e:
                self.logger.warning(f"Error extracting article: {e}")
                continue
        
        return articles
    
    def get_article_details(self, article_info: Dict) -> Dict:
        """获取文章详细内容"""
        url = article_info.get('url')
        if not url:
            return article_info
        
        content = self.get_page_content(url)
        if not content:
            return article_info
        
        soup = BeautifulSoup(content, 'html.parser')
        
        # 提取正文内容
        article_content = self.extract_article_content(soup)
        if article_content:
            article_info['content'] = article_content
            
            # 进行中文文本分析
            analysis_result = self.analyze_chinese_text(article_content)
            article_info.update(analysis_result)
        
        # 提取其他详细信息
        selectors = self.config.get('selectors', {})
        
        # 提取作者（如果还没有）
        if not article_info.get('author') and selectors.get('author'):
            author_elem = soup.select_one(selectors['author'])
            if author_elem:
                article_info['author'] = author_elem.get_text(strip=True)
        
        # 提取发布时间（如果还没有）
        if not article_info.get('publish_time') and selectors.get('publish_time'):
            time_elem = soup.select_one(selectors['publish_time'])
            if time_elem:
                article_info['publish_time'] = time_elem.get_text(strip=True)
        
        # 提取阅读数
        if selectors.get('view_count'):
            view_elem = soup.select_one(selectors['view_count'])
            if view_elem:
                view_text = view_elem.get_text(strip=True)
                article_info['view_count'] = self.extract_number_from_text(view_text)
        
        # 提取评论数
        if selectors.get('comment_count'):
            comment_elem = soup.select_one(selectors['comment_count'])
            if comment_elem:
                comment_text = comment_elem.get_text(strip=True)
                article_info['comment_count'] = self.extract_number_from_text(comment_text)
        
        # 提取标签（如果还没有）
        if not article_info.get('tags') and selectors.get('tags'):
            tag_elems = soup.select(selectors['tags'])
            if tag_elems:
                article_info['tags'] = [tag.get_text(strip=True) for tag in tag_elems]
        
        return article_info
    
    def extract_article_content(self, soup: BeautifulSoup) -> str:
        """提取文章正文内容"""
        # 尝试多种内容选择器
        content_selectors = [
            'div.article-content',
            'div.post-content',
            'div.content',
            'article',
            'div.entry-content',
            'div#content',
            'main'
        ]
        
        # 使用配置中的选择器
        selectors = self.config.get('selectors', {})
        if selectors.get('content'):
            content_selectors.insert(0, selectors['content'])
        
        for selector in content_selectors:
            content_elem = soup.select_one(selector)
            if content_elem:
                # 清理内容
                content = self.clean_article_content(content_elem)
                if len(content) > 100:  # 确保内容足够长
                    return content
        
        return ''
    
    def clean_article_content(self, content_elem) -> str:
        """清理文章内容"""
        # 移除不需要的元素
        for tag in content_elem.find_all(['script', 'style', 'nav', 'aside', 'footer']):
            tag.decompose()
        
        # 移除广告和无关内容
        for tag in content_elem.find_all(class_=re.compile(r'ad|advertisement|sidebar|related')):
            tag.decompose()
        
        # 获取文本内容
        text = content_elem.get_text(separator='\n', strip=True)
        
        # 清理多余的空行
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        return '\n'.join(lines)
    
    def analyze_chinese_text(self, text: str) -> Dict:
        """分析中文文本"""
        analysis = {}
        
        # 基础统计
        analysis['word_count'] = len(text)
        analysis['char_count'] = len(text.replace(' ', '').replace('\n', ''))
        
        # 关键词提取
        keywords = jieba.analyse.extract_tags(text, topK=10, withWeight=True)
        analysis['keywords'] = [{'word': word, 'weight': weight} for word, weight in keywords]
        
        # TF-IDF关键词
        tfidf_keywords = jieba.analyse.textrank(text, topK=10, withWeight=True)
        analysis['tfidf_keywords'] = [{'word': word, 'weight': weight} for word, weight in tfidf_keywords]
        
        # 分词结果
        words = list(jieba.cut(text))
        analysis['word_segmentation'] = words[:50]  # 只保存前50个词
        
        # AI相关度评分
        analysis['ai_relevance_score'] = self.calculate_ai_relevance(text)
        
        return analysis
    
    def calculate_ai_relevance(self, text: str) -> float:
        """计算AI相关度"""
        ai_keywords = {
            '人工智能': 3, '机器学习': 3, '深度学习': 3, '神经网络': 2,
            '自然语言处理': 2, '计算机视觉': 2, '强化学习': 2, '大数据': 1,
            '算法': 1, '模型': 1, '训练': 1, '预测': 1, '智能': 1,
            'AI': 3, 'ML': 2, 'DL': 2, 'NLP': 2, 'CV': 2,
            'ChatGPT': 3, 'GPT': 2, 'BERT': 2, 'Transformer': 2
        }
        
        score = 0
        text_lower = text.lower()
        
        for keyword, weight in ai_keywords.items():
            count = text.count(keyword) + text_lower.count(keyword.lower())
            score += count * weight
        
        # 归一化到0-10分
        max_score = len(text) / 100  # 假设每100字符最多1分
        normalized_score = min(score / max_score * 10, 10) if max_score > 0 else 0
        
        return round(normalized_score, 2)
    
    def extract_number_from_text(self, text: str) -> int:
        """从文本中提取数字"""
        # 处理中文数字单位
        text = text.replace('万', '0000').replace('千', '000').replace('百', '00')
        
        # 提取数字
        numbers = re.findall(r'\d+', text)
        if numbers:
            return int(numbers[0])
        
        return 0
    
    def crawl_media_articles(self, max_articles: int = 100) -> List[Dict]:
        """爬取媒体文章"""
        all_articles = []
        
        # 获取文章列表URL
        list_urls = []
        
        if self.config.get('article_list_url'):
            list_urls.append(self.config['article_list_url'])
        
        if self.config.get('category_urls'):
            list_urls.extend(self.config['category_urls'].values())
        
        for list_url in list_urls:
            self.logger.info(f"Crawling articles from: {list_url}")
            
            try:
                articles = self.parse_article_list(list_url, max_pages=3)
                
                # 获取详细内容
                for i, article in enumerate(articles[:max_articles]):
                    if i % 5 == 0:
                        self.logger.info(f"Processing article {i+1}/{len(articles)}")
                    
                    detailed_article = self.get_article_details(article)
                    
                    # 添加唯一ID
                    detailed_article['article_id'] = self.generate_article_id(detailed_article)
                    detailed_article['crawl_timestamp'] = datetime.now().isoformat()
                    
                    all_articles.append(detailed_article)
                    
                    # 添加延迟
                    time.sleep(2)
                    
                    if len(all_articles) >= max_articles:
                        break
                
            except Exception as e:
                self.logger.error(f"Error crawling {list_url}: {e}")
                continue
        
        self.logger.info(f"Total articles crawled from {self.media_name}: {len(all_articles)}")
        return all_articles
    
    def generate_article_id(self, article: Dict) -> str:
        """生成文章唯一ID"""
        content = f"{article.get('title', '')}{article.get('url', '')}{self.media_name}"
        return hashlib.md5(content.encode('utf-8')).hexdigest()[:16]
```

### 3. 多媒体聚合器

#### 中文媒体聚合管理器
```python
class ChineseMediaAggregator:
    def __init__(self):
        self.media_configs = CHINESE_MEDIA_CONFIGS
        self.spiders = {}
        self.articles = []
        
        # 初始化各媒体爬虫
        for media_key, media_config in self.media_configs.items():
            try:
                self.spiders[media_key] = ChineseMediaSpider(media_config)
            except Exception as e:
                logging.error(f"Failed to initialize spider for {media_key}: {e}")
    
    def crawl_all_media(self, max_articles_per_media: int = 50) -> List[Dict]:
        """爬取所有媒体文章"""
        all_articles = []
        
        for media_key, spider in self.spiders.items():
            logging.info(f"Starting crawl for {media_key}")
            
            try:
                articles = spider.crawl_media_articles(max_articles_per_media)
                all_articles.extend(articles)
                
                logging.info(f"Completed {media_key}: {len(articles)} articles")
                
            except Exception as e:
                logging.error(f"Error crawling {media_key}: {e}")
                continue
        
        # 去重和排序
        deduplicated_articles = self.deduplicate_articles(all_articles)
        sorted_articles = self.sort_articles_by_relevance(deduplicated_articles)
        
        self.articles = sorted_articles
        return sorted_articles
    
    def deduplicate_articles(self, articles: List[Dict]) -> List[Dict]:
        """文章去重"""
        seen_titles = set()
        unique_articles = []
        
        for article in articles:
            title = article.get('title', '')
            
            # 简单的标题相似度检查
            is_duplicate = False
            for seen_title in seen_titles:
                if self.calculate_title_similarity(title, seen_title) > 0.8:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                seen_titles.add(title)
                unique_articles.append(article)
        
        logging.info(f"Deduplicated: {len(articles)} -> {len(unique_articles)} articles")
        return unique_articles
    
    def calculate_title_similarity(self, title1: str, title2: str) -> float:
        """计算标题相似度"""
        # 简单的Jaccard相似度
        words1 = set(jieba.cut(title1))
        words2 = set(jieba.cut(title2))
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        if len(union) == 0:
            return 0
        
        return len(intersection) / len(union)
    
    def sort_articles_by_relevance(self, articles: List[Dict]) -> List[Dict]:
        """按相关度排序文章"""
        def relevance_score(article):
            score = 0
            
            # AI相关度
            score += article.get('ai_relevance_score', 0) * 0.4
            
            # 阅读数
            view_count = article.get('view_count', 0)
            if view_count > 0:
                score += min(view_count / 10000, 5) * 0.3  # 最多5分
            
            # 评论数
            comment_count = article.get('comment_count', 0)
            if comment_count > 0:
                score += min(comment_count / 100, 3) * 0.2  # 最多3分
            
            # 时间新鲜度
            publish_time = article.get('publish_time', '')
            if publish_time:
                score += self.calculate_freshness_score(publish_time) * 0.1
            
            return score
        
        return sorted(articles, key=relevance_score, reverse=True)
    
    def calculate_freshness_score(self, publish_time: str) -> float:
        """计算时间新鲜度分数"""
        try:
            # 尝试解析时间
            now = datetime.now()
            
            # 处理常见的中文时间格式
            if '小时前' in publish_time:
                hours = int(re.findall(r'(\d+)', publish_time)[0])
                pub_time = now - timedelta(hours=hours)
            elif '天前' in publish_time:
                days = int(re.findall(r'(\d+)', publish_time)[0])
                pub_time = now - timedelta(days=days)
            elif '分钟前' in publish_time:
                minutes = int(re.findall(r'(\d+)', publish_time)[0])
                pub_time = now - timedelta(minutes=minutes)
            else:
                # 尝试解析具体日期
                pub_time = datetime.strptime(publish_time, '%Y-%m-%d')
            
            # 计算天数差
            days_diff = (now - pub_time).days
            
            if days_diff <= 1:
                return 10
            elif days_diff <= 3:
                return 8
            elif days_diff <= 7:
                return 6
            elif days_diff <= 30:
                return 4
            else:
                return 2
                
        except:
            return 5  # 默认分数
    
    def generate_summary_report(self) -> Dict:
        """生成汇总报告"""
        if not self.articles:
            return {}
        
        # 按媒体统计
        media_stats = {}
        for article in self.articles:
            media = article.get('media_name', 'Unknown')
            if media not in media_stats:
                media_stats[media] = 0
            media_stats[media] += 1
        
        # 热门关键词统计
        all_keywords = []
        for article in self.articles:
            keywords = article.get('keywords', [])
            for kw in keywords:
                if isinstance(kw, dict):
                    all_keywords.append(kw['word'])
                else:
                    all_keywords.append(str(kw))
        
        keyword_counts = {}
        for keyword in all_keywords:
            keyword_counts[keyword] = keyword_counts.get(keyword, 0) + 1
        
        top_keywords = sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)[:20]
        
        # AI相关度分布
        ai_scores = [article.get('ai_relevance_score', 0) for article in self.articles]
        avg_ai_score = sum(ai_scores) / len(ai_scores) if ai_scores else 0
        
        return {
            'total_articles': len(self.articles),
            'media_statistics': media_stats,
            'top_keywords': top_keywords,
            'average_ai_relevance': round(avg_ai_score, 2),
            'crawl_timestamp': datetime.now().isoformat()
        }
```

## 反爬虫应对策略

### 1. 中文网站特殊处理
```python
# 处理中文编码
def handle_chinese_encoding(response):
    if response.encoding in ['ISO-8859-1', 'ascii']:
        response.encoding = 'utf-8'
    return response.text

# 处理中文URL
def encode_chinese_url(url):
    from urllib.parse import quote
    return quote(url, safe=':/?#[]@!$&\'()*+,;=')
```

### 2. 请求头优化
```python
CHINESE_HEADERS = {
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br',
    'Cache-Control': 'no-cache',
    'Pragma': 'no-cache'
}
```

## 配置参数

### 爬虫配置
```python
CHINESE_MEDIA_CONFIG = {
    'rate_limiting': {
        'requests_per_second': 0.5,  # 更保守的频率
        'burst_limit': 3,
        'retry_delay': 120
    },
    'text_processing': {
        'enable_jieba': True,
        'extract_keywords': True,
        'keyword_count': 10,
        'min_content_length': 100
    },
    'quality_filters': {
        'min_ai_relevance': 3.0,
        'min_word_count': 200,
        'exclude_keywords': ['广告', '推广', '营销']
    },
    'deduplication': {
        'title_similarity_threshold': 0.8,
        'content_similarity_threshold': 0.9
    }
}
```

## 数据输出格式

### JSON格式
```json
{
  "article_id": "zh_media_001",
  "title": "ChatGPT引发的AI革命：机器学习的新纪元",
  "url": "https://www.jiqizhixin.com/articles/2024-01-15-chatgpt-revolution",
  "summary": "ChatGPT的出现标志着人工智能进入了一个全新的发展阶段...",
  "content": "完整文章内容...",
  "author": "张三",
  "media_name": "机器之心",
  "publish_time": "2024-01-15 10:30:00",
  "language": "zh-CN",
  "tags": ["人工智能", "ChatGPT", "机器学习"],
  "keywords": [
    {"word": "人工智能", "weight": 0.8},
    {"word": "机器学习", "weight": 0.6},
    {"word": "深度学习", "weight": 0.4}
  ],
  "metrics": {
    "view_count": 15000,
    "comment_count": 120,
    "word_count": 2500,
    "char_count": 3800
  },
  "analysis": {
    "ai_relevance_score": 8.5,
    "sentiment": "positive",
    "readability_score": 7.2
  },
  "crawl_metadata": {
    "crawl_timestamp": "2024-01-15T12:00:00Z",
    "spider_version": "1.0",
    "encoding": "utf-8"
  }
}
```

## 常见问题与解决方案

### 1. 中文编码问题
**问题**: 中文字符显示乱码
**解决**: 
- 正确设置请求编码
- 使用chardet自动检测编码
- 统一使用UTF-8处理

### 2. 分词准确性
**问题**: jieba分词对专业术语识别不准
**解决**: 
- 添加AI领域专业词典
- 使用自定义词典
- 结合多种分词方法

### 3. 反爬虫机制
**问题**: 中文网站反爬虫较严格
**解决**: 
- 降低请求频率
- 使用更真实的请求头
- 实现会话保持

### 4. 内容质量参差不齐
**问题**: 不同媒体内容质量差异大
**解决**: 
- 实现内容质量评分
- 按媒体权威性加权
- 过滤低质量内容

## 维护建议

### 定期维护任务
1. **词典更新**: 定期更新AI专业词典
2. **网站监控**: 检查各媒体网站结构变化
3. **质量评估**: 评估爬取内容质量
4. **性能优化**: 优化中文文本处理性能

### 扩展方向
1. **情感分析**: 增加中文情感分析功能
2. **热点追踪**: 实现AI热点话题追踪
3. **观点挖掘**: 提取不同媒体观点差异
4. **影响力分析**: 分析文章传播影响力

## 相关资源

- [jieba中文分词](https://github.com/fxsjy/jieba)
- [中文停用词表](https://github.com/goto456/stopwords)
- [中文文本分析工具](https://github.com/fighting41love/funNLP)
- [机器之心](https://www.jiqizhixin.com/)
- [雷锋网AI频道](https://www.leiphone.com/category/ai)