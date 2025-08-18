#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Stability AI News & Research Spider
爬取 Stability AI 的新闻和研究文章
"""

import requests
from bs4 import BeautifulSoup
import json
import os
import time
import hashlib
from urllib.parse import urljoin, urlparse
from pathlib import Path
import re
from datetime import datetime

class StabilitySpider:
    def __init__(self, config_file="config.json"):
        """初始化爬虫"""
        self.base_url = "https://stability.ai"
        self.news_url = "https://stability.ai/news"
        self.research_url = "https://stability.ai/research"
        
        # 加载配置
        self.config = self.load_config(config_file)
        
        # 设置HTTP会话
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': self.config['crawler']['user_agent']
        })
        
        # 设置数据目录
        self.setup_directories()
        
        print(f"Stability AI Spider initialized")
        print(f"Data directory: {self.data_dir}")
    
    def load_config(self, config_file):
        """加载配置文件"""
        try:
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                # 返回默认配置
                return self.get_default_config()
        except Exception as e:
            print(f"Error loading config: {e}")
            return self.get_default_config()
    
    def get_default_config(self):
        """获取默认配置"""
        return {
            "crawler": {
                "delay": 3,
                "timeout": 30,
                "max_retries": 3,
                "max_articles": 50,
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            },
            "media": {
                "download_images": True,
                "image_timeout": 20,
                "max_file_size": 20971520,  # 20MB
                "allowed_extensions": [".jpg", ".png", ".gif", ".webp"]
            },
            "storage": {
                "data_dir": "crawled_data",
                "data_type": "stability_articles"
            },
            "filter": {
                "skip_duplicates": True,
                "min_content_length": 100
            }
        }
    
    def setup_directories(self):
        """创建必要的目录结构"""
        self.data_dir = Path(self.config['storage']['data_dir'])
        self.articles_dir = self.data_dir / self.config['storage']['data_type']
        
        # 创建目录
        self.articles_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"Created directory structure: {self.articles_dir}")
    
    def get_article_list(self):
        """获取文章列表 (新闻 + 研究)"""
        print("Getting article list from news and research pages...")
        
        all_articles = []
        
        # 获取新闻文章
        news_articles = self.get_articles_from_page(self.news_url, "news")
        all_articles.extend(news_articles)
        print(f"Found {len(news_articles)} news articles")
        
        # 获取研究文章
        research_articles = self.get_articles_from_page(self.research_url, "research")
        all_articles.extend(research_articles)
        print(f"Found {len(research_articles)} research articles")
        
        print(f"Total articles found: {len(all_articles)}")
        return all_articles
    
    def get_articles_from_page(self, url, page_type):
        """从指定页面获取文章列表"""
        try:
            response = self.safe_request(url)
            if not response:
                return []
            
            soup = BeautifulSoup(response.content, 'html.parser')
            articles = soup.find_all('article', class_='blog-item')
            
            article_list = []
            
            for i, article in enumerate(articles):
                article_data = self.extract_article_preview(article, page_type, i)
                if article_data:
                    article_list.append(article_data)
                    
                # 限制文章数量
                if len(article_list) >= self.config['crawler']['max_articles']:
                    break
            
            return article_list
            
        except Exception as e:
            print(f"Error getting articles from {url}: {e}")
            return []
    
    def extract_article_preview(self, article, page_type, index):
        """从文章预览元素提取数据"""
        try:
            # 获取文章链接
            link_elem = article.find('a', href=True)
            if not link_elem:
                return None
                
            article_url = urljoin(self.base_url, link_elem['href'])
            
            # 生成文章ID (基于URL)
            article_id = self.generate_article_id(article_url)
            
            # 检查是否已存在
            if self.config['filter']['skip_duplicates'] and self.is_article_exists(article_id):
                print(f"Article already exists: {article_id}")
                return None
            
            # 提取标题
            title_elem = article.find('h1', class_='blog-title')
            title = title_elem.get_text(strip=True) if title_elem else "Untitled"
            
            # 提取日期
            date_elem = article.find('time')
            date_text = date_elem.get_text(strip=True) if date_elem else ""
            
            # 提取摘要
            summary_paragraphs = article.find_all('p')
            summary = ""
            if summary_paragraphs:
                summary = ' '.join([p.get_text(strip=True) for p in summary_paragraphs])
                summary = summary[:300] + "..." if len(summary) > 300 else summary
            
            # 提取预览图片
            img_elem = article.find('img')
            preview_image = ""
            if img_elem and img_elem.get('src'):
                preview_image = urljoin(self.base_url, img_elem['src'])
            
            return {
                'id': article_id,
                'url': article_url,
                'title': title,
                'summary': summary,
                'date': date_text,
                'preview_image': preview_image,
                'page_type': page_type,
                'index': index
            }
            
        except Exception as e:
            print(f"Error extracting article preview {index}: {e}")
            return None
    
    def generate_article_id(self, url):
        """根据URL生成文章ID"""
        # 提取URL路径的最后部分作为ID
        path = urlparse(url).path
        article_slug = path.split('/')[-1]
        
        # 如果slug为空，使用URL的hash
        if not article_slug:
            article_slug = hashlib.md5(url.encode()).hexdigest()[:10]
        
        return article_slug
    
    def is_article_exists(self, article_id):
        """检查文章是否已存在"""
        article_dir = self.articles_dir / article_id
        return article_dir.exists() and (article_dir / "metadata.json").exists()
    
    def crawl_article(self, article_info):
        """爬取单篇文章详情"""
        print(f"Crawling article: {article_info['title'][:50]}...")
        
        try:
            response = self.safe_request(article_info['url'])
            if not response:
                return False
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 提取文章详情
            article_data = self.extract_article_data(soup, article_info)
            
            if article_data:
                # 保存文章
                success = self.save_article(article_data)
                if success:
                    print(f"Article saved: {article_data['id']}")
                    return True
                else:
                    print(f"Failed to save article: {article_data['id']}")
                    return False
            else:
                print(f"Failed to extract article data")
                return False
                
        except Exception as e:
            print(f"Error crawling article {article_info['url']}: {e}")
            return False
    
    def extract_article_data(self, soup, article_info):
        """提取文章详细数据"""
        try:
            # 提取标题 (详情页面的标题可能更完整)
            title_elem = soup.find('h1', class_='entry-title')
            title = title_elem.get_text(strip=True) if title_elem else article_info['title']
            
            # 提取正文内容
            content_elem = soup.find(class_='content')
            content_html = str(content_elem) if content_elem else ""
            content_text = content_elem.get_text(strip=True) if content_elem else ""
            
            # 检查内容长度
            if len(content_text) < self.config['filter']['min_content_length']:
                print(f"Content too short: {len(content_text)} chars")
                return None
            
            # 提取元数据
            metadata = self.extract_metadata(soup)
            
            # 提取图片
            images = self.extract_images(soup, article_info['id'])
            
            # 生成Markdown内容
            markdown_content = self.generate_markdown(title, metadata, content_text, images, article_info)
            
            return {
                'id': article_info['id'],
                'url': article_info['url'],
                'title': title,
                'content_html': content_html,
                'content_text': content_text,
                'markdown': markdown_content,
                'metadata': metadata,
                'images': images,
                'page_type': article_info['page_type'],
                'crawl_time': datetime.now().isoformat(),
                'word_count': len(content_text.split()),
                'content_hash': hashlib.md5(content_text.encode()).hexdigest()
            }
            
        except Exception as e:
            print(f"Error extracting article data: {e}")
            return None
    
    def extract_metadata(self, soup):
        """提取文章元数据"""
        metadata = {}
        
        # 提取日期
        date_elem = soup.find('time')
        if date_elem:
            metadata['date'] = date_elem.get_text(strip=True)
            metadata['datetime'] = date_elem.get('datetime', '')
        
        # 提取作者
        author_elem = soup.find(class_='author')
        if author_elem:
            metadata['author'] = author_elem.get_text(strip=True)
        
        # 提取标签/分类 (如果有)
        tags = []
        tag_elements = soup.find_all(class_='tag') or soup.find_all(class_='category')
        for tag_elem in tag_elements:
            tag_text = tag_elem.get_text(strip=True)
            if tag_text:
                tags.append(tag_text)
        
        if tags:
            metadata['tags'] = tags
        
        return metadata
    
    def extract_images(self, soup, article_id):
        """提取文章中的图片"""
        images = []
        
        # 查找正文中的图片
        content_elem = soup.find(class_='content')
        if not content_elem:
            return images
        
        img_elements = content_elem.find_all('img')
        
        for i, img in enumerate(img_elements):
            src = img.get('src', '')
            if not src:
                continue
                
            # 转换为绝对URL
            img_url = urljoin(self.base_url, src)
            
            # 生成本地文件名
            img_ext = self.get_image_extension(img_url)
            local_filename = f"image_{i+1}{img_ext}"
            
            image_info = {
                'url': img_url,
                'alt': img.get('alt', ''),
                'title': img.get('title', ''),
                'local_filename': local_filename,
                'local_path': f"media/{local_filename}",
                'downloaded': False
            }
            
            images.append(image_info)
        
        return images
    
    def get_image_extension(self, img_url):
        """获取图片扩展名"""
        path = urlparse(img_url).path
        ext = os.path.splitext(path)[1].lower()
        
        # 检查扩展名是否在允许列表中
        allowed = self.config['media']['allowed_extensions']
        if ext in allowed:
            return ext
        else:
            return '.jpg'  # 默认扩展名
    
    def generate_markdown(self, title, metadata, content, images, article_info):
        """生成Markdown格式的内容"""
        lines = []
        
        # 标题
        lines.append(f"# {title}")
        lines.append("")
        
        # 元数据
        lines.append(f"**分类**: {article_info['page_type']}")
        if metadata.get('date'):
            lines.append(f"**发布日期**: {metadata['date']}")
        if metadata.get('author'):
            lines.append(f"**作者**: {metadata['author']}")
        lines.append(f"**来源**: {article_info['url']}")
        lines.append(f"**爬取时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")
        lines.append("---")
        lines.append("")
        
        # 正文内容 (简化处理，保留段落结构)
        paragraphs = content.split('\n\n')
        for para in paragraphs:
            para = para.strip()
            if para:
                lines.append(para)
                lines.append("")
        
        # 图片
        if images:
            lines.append("## 相关媒体")
            lines.append("")
            for img in images:
                alt_text = img['alt'] or f"图片 {img['local_filename']}"
                lines.append(f"![{alt_text}]({img['local_path']})")
                lines.append("")
        
        return '\n'.join(lines)
    
    def save_article(self, article_data):
        """保存文章数据"""
        try:
            article_dir = self.articles_dir / article_data['id']
            article_dir.mkdir(exist_ok=True)
            
            # 创建媒体目录
            media_dir = article_dir / "media"
            media_dir.mkdir(exist_ok=True)
            
            # 保存Markdown内容
            with open(article_dir / "content.md", 'w', encoding='utf-8') as f:
                f.write(article_data['markdown'])
            
            # 保存元数据JSON
            metadata = {
                'url': article_data['url'],
                'title': article_data['title'],
                'content': article_data['content_text'],
                'metadata': article_data['metadata'],
                'images': article_data['images'],
                'page_type': article_data['page_type'],
                'crawl_time': article_data['crawl_time'],
                'word_count': article_data['word_count'],
                'content_hash': article_data['content_hash'],
                'slug': article_data['id']
            }
            
            with open(article_dir / "metadata.json", 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            
            # 下载图片
            if self.config['media']['download_images']:
                self.download_article_images(article_data, media_dir)
            
            return True
            
        except Exception as e:
            print(f"Error saving article {article_data['id']}: {e}")
            return False
    
    def download_article_images(self, article_data, media_dir):
        """下载文章图片"""
        for img in article_data['images']:
            try:
                img_url = img['url']
                local_path = media_dir / img['local_filename']
                
                # 跳过已下载的图片
                if local_path.exists():
                    img['downloaded'] = True
                    continue
                
                print(f"  Downloading image: {img['local_filename']}")
                
                response = self.safe_request(img_url, timeout=self.config['media']['image_timeout'])
                if response and len(response.content) <= self.config['media']['max_file_size']:
                    with open(local_path, 'wb') as f:
                        f.write(response.content)
                    img['downloaded'] = True
                    print(f"    Downloaded: {img['local_filename']}")
                else:
                    print(f"    Failed to download: {img['local_filename']}")
                
                # 下载间隔
                time.sleep(1)
                
            except Exception as e:
                print(f"    Error downloading {img['local_filename']}: {e}")
    
    def safe_request(self, url, timeout=None):
        """安全的HTTP请求"""
        timeout = timeout or self.config['crawler']['timeout']
        max_retries = self.config['crawler']['max_retries']
        
        for attempt in range(max_retries):
            try:
                response = self.session.get(url, timeout=timeout)
                response.raise_for_status()
                return response
                
            except requests.RequestException as e:
                print(f"Request failed (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # 指数退避
                else:
                    return None
        
        return None
    
    def run(self, max_articles=None):
        """执行爬虫"""
        print("Starting Stability AI Spider...")
        
        # 限制文章数量
        if max_articles:
            self.config['crawler']['max_articles'] = max_articles
        
        # 获取文章列表
        articles = self.get_article_list()
        
        if not articles:
            print("No articles found!")
            return
        
        print(f"Found {len(articles)} articles to crawl")
        
        # 爬取文章
        success_count = 0
        failed_count = 0
        
        for i, article in enumerate(articles, 1):
            print(f"\n[{i}/{len(articles)}] Processing: {article['title'][:50]}...")
            
            if self.crawl_article(article):
                success_count += 1
            else:
                failed_count += 1
            
            # 请求间隔
            if i < len(articles):
                delay = self.config['crawler']['delay']
                print(f"Waiting {delay} seconds...")
                time.sleep(delay)
        
        # 打印总结
        print(f"\n" + "="*60)
        print("CRAWLING SUMMARY")
        print("="*60)
        print(f"Total articles processed: {len(articles)}")
        print(f"Successfully crawled: {success_count}")
        print(f"Failed: {failed_count}")
        print(f"Data saved to: {self.articles_dir}")
        print("="*60)

if __name__ == "__main__":
    spider = StabilitySpider()
    spider.run(max_articles=10)  # 测试模式，只爬取10篇