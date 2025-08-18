#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Google Research Blog RSS Spider
主爬虫脚本 - 按照新的项目结构组织
"""

import feedparser
import requests
from bs4 import BeautifulSoup
import json
import os
import re
import hashlib
import time
import logging
from datetime import datetime
from urllib.parse import urljoin, urlparse
from pathlib import Path

class GoogleResearchSpider:
    def __init__(self, config_file='config.json'):
        """初始化爬虫"""
        self.load_config(config_file)
        self.setup_logging()
        self.setup_session()
        self.setup_directories()
        
    def load_config(self, config_file):
        """加载配置文件"""
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
        except FileNotFoundError:
            self.config = self.get_default_config()
            self.save_config(config_file)
        
        # 设置基本参数
        self.rss_url = self.config['rss']['url']
        self.base_url = self.config['rss']['base_url']
        self.data_dir = Path(self.config['storage']['data_directory'])
        self.max_articles = self.config['crawler']['max_articles_per_run']
        self.download_media = self.config['media']['download_enabled']
        
    def get_default_config(self):
        """获取默认配置"""
        return {
            "rss": {
                "url": "https://research.google/blog/rss/",
                "base_url": "https://research.google/blog/"
            },
            "crawler": {
                "max_articles_per_run": 20,
                "request_delay": 2,
                "timeout": 30,
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            },
            "storage": {
                "data_directory": "crawled_data",
                "save_markdown": True,
                "save_metadata": True
            },
            "media": {
                "download_enabled": True,
                "max_file_size": 10485760,
                "allowed_extensions": ["jpg", "jpeg", "png", "gif", "pdf", "mp4", "avi"]
            },
            "content": {
                "min_word_count": 100,
                "extract_images": True,
                "extract_links": True
            }
        }
    
    def save_config(self, config_file):
        """保存配置文件"""
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)
    
    def setup_logging(self):
        """设置日志"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('spider.log', encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def setup_session(self):
        """设置请求会话"""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': self.config['crawler']['user_agent']
        })
    
    def setup_directories(self):
        """创建目录结构"""
        self.data_dir.mkdir(exist_ok=True)
        self.logger.info(f"数据目录: {self.data_dir}")
    
    def get_rss_feed(self):
        """获取RSS订阅"""
        try:
            self.logger.info(f"获取RSS订阅: {self.rss_url}")
            feed = feedparser.parse(self.rss_url)
            
            if feed.bozo:
                self.logger.warning(f"RSS解析警告: {feed.bozo_exception}")
            
            self.logger.info(f"发现 {len(feed.entries)} 篇文章")
            return feed
            
        except Exception as e:
            self.logger.error(f"获取RSS失败: {e}")
            return None
    
    def generate_article_id(self, entry):
        """生成文章唯一ID"""
        # 使用标题和URL生成唯一ID
        content = f"{entry.title}{entry.link}"
        hash_id = hashlib.md5(content.encode('utf-8')).hexdigest()[:8]
        
        # 尝试从发布日期获取日期
        try:
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                pub_date = datetime(*entry.published_parsed[:6])
                date_str = pub_date.strftime('%Y%m%d')
            else:
                date_str = datetime.now().strftime('%Y%m%d')
        except:
            date_str = datetime.now().strftime('%Y%m%d')
        
        return f"article_{date_str}_{hash_id}"
    
    def article_exists(self, article_id):
        """检查文章是否已存在"""
        article_dir = self.data_dir / article_id
        return article_dir.exists()
    
    def extract_article_content(self, url):
        """提取文章内容"""
        try:
            self.logger.info(f"提取文章内容: {url}")
            
            response = self.session.get(url, timeout=self.config['crawler']['timeout'])
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 尝试多种选择器提取文章内容
            content_selectors = [
                'article',
                '[role="main"]',
                '.post-content',
                '.entry-content',
                '.article-content',
                'main'
            ]
            
            article_content = None
            for selector in content_selectors:
                element = soup.select_one(selector)
                if element and len(element.get_text(strip=True)) > 200:
                    article_content = element
                    break
            
            if not article_content:
                self.logger.warning(f"无法找到文章主要内容: {url}")
                return None, [], []
            
            # 提取图片和链接
            images = self.extract_images(article_content, url)
            links = self.extract_links(article_content, url)
            
            # 清理内容并转换为Markdown
            markdown_content = self.convert_to_markdown(article_content)
            
            return markdown_content, images, links
            
        except Exception as e:
            self.logger.error(f"提取文章内容失败 {url}: {e}")
            return None, [], []
    
    def extract_images(self, content_element, base_url):
        """提取图片信息"""
        images = []
        img_tags = content_element.find_all('img')
        
        for img in img_tags:
            src = img.get('src')
            if not src:
                continue
            
            # 处理相对URL
            if src.startswith('//'):
                src = 'https:' + src
            elif src.startswith('/'):
                src = urljoin(base_url, src)
            elif not src.startswith(('http://', 'https://')):
                src = urljoin(base_url, src)
            
            # 过滤小图片（可能是图标）
            width = img.get('width')
            height = img.get('height')
            if width and height:
                try:
                    if int(width) < 50 or int(height) < 50:
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
    
    def extract_links(self, content_element, base_url):
        """提取外部链接"""
        links = []
        link_tags = content_element.find_all('a', href=True)
        
        for link in link_tags:
            href = link.get('href')
            text = link.get_text(strip=True)
            
            if not href or not text:
                continue
            
            # 处理相对URL
            if href.startswith('/'):
                href = urljoin(base_url, href)
            
            # 跳过内部链接和锚点
            if href.startswith('#') or 'research.google' in href:
                continue
            
            # 分类链接类型
            link_type = 'other'
            if 'arxiv.org' in href or 'paper' in href.lower():
                link_type = 'paper'
            elif 'github.com' in href or 'code' in href.lower():
                link_type = 'code'
            elif any(ext in href.lower() for ext in ['.pdf', '.doc', '.docx']):
                link_type = 'document'
            elif 'colab' in href.lower() or 'demo' in href.lower():
                link_type = 'demo'
            
            link_info = {
                'url': href,
                'text': text,
                'type': link_type
            }
            
            links.append(link_info)
        
        return links
    
    def convert_to_markdown(self, content_element):
        """将HTML内容转换为Markdown"""
        # 移除不需要的元素
        for tag in content_element.find_all(['script', 'style', 'nav', 'aside', 'footer']):
            tag.decompose()
        
        # 处理标题
        for i in range(1, 7):
            for h in content_element.find_all(f'h{i}'):
                h.string = f"{'#' * i} {h.get_text(strip=True)}"
        
        # 处理代码块
        for pre in content_element.find_all('pre'):
            code_text = pre.get_text()
            pre.string = f"\\n```\\n{code_text}\\n```\\n"
        
        # 处理行内代码
        for code in content_element.find_all('code'):
            if code.parent.name != 'pre':
                code_text = code.get_text()
                code.string = f"`{code_text}`"
        
        # 处理链接
        for a in content_element.find_all('a', href=True):
            href = a.get('href')
            text = a.get_text(strip=True)
            if href and text:
                a.string = f"[{text}]({href})"
        
        # 处理图片
        for img in content_element.find_all('img'):
            alt = img.get('alt', '')
            src = img.get('src', '')
            img.string = f"![{alt}]({src})"
        
        # 处理粗体和斜体
        for strong in content_element.find_all(['strong', 'b']):
            text = strong.get_text(strip=True)
            strong.string = f"**{text}**"
        
        for em in content_element.find_all(['em', 'i']):
            text = em.get_text(strip=True)
            em.string = f"*{text}*"
        
        # 获取文本并清理
        text = content_element.get_text(separator='\\n', strip=True)
        lines = [line.strip() for line in text.split('\\n') if line.strip()]
        
        return '\\n\\n'.join(lines)
    
    def download_media_file(self, url, save_path):
        """下载媒体文件"""
        try:
            response = self.session.get(url, timeout=30, stream=True)
            response.raise_for_status()
            
            # 检查文件大小
            content_length = response.headers.get('content-length')
            if content_length:
                file_size = int(content_length)
                max_size = self.config['media']['max_file_size']
                if file_size > max_size:
                    self.logger.warning(f"文件过大，跳过下载: {url} ({file_size} bytes)")
                    return False
            
            # 创建目录
            save_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 下载文件
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            self.logger.info(f"媒体文件已下载: {save_path.name}")
            return True
            
        except Exception as e:
            self.logger.error(f"下载媒体文件失败 {url}: {e}")
            return False
    
    def get_file_extension(self, url):
        """从URL获取文件扩展名"""
        parsed = urlparse(url)
        path = parsed.path
        if '.' in path:
            return path.split('.')[-1].lower()
        return 'unknown'
    
    def process_article(self, entry):
        """处理单篇文章"""
        article_id = self.generate_article_id(entry)
        
        # 检查文章是否已存在
        if self.article_exists(article_id):
            self.logger.info(f"文章已存在，跳过: {article_id}")
            return None
        
        # 创建文章目录
        article_dir = self.data_dir / article_id
        article_dir.mkdir(exist_ok=True)
        
        # 提取文章内容
        markdown_content, images, links = self.extract_article_content(entry.link)
        
        if not markdown_content:
            self.logger.warning(f"无法提取文章内容，跳过: {entry.title}")
            return None
        
        # 准备元数据
        metadata = {
            'title': entry.title,
            'url': entry.link,
            'summary': entry.get('summary', ''),
            'author': entry.get('author', 'Google Research Team'),
            'published_date': entry.get('published', ''),
            'crawled_date': datetime.now().isoformat(),
            'word_count': len(markdown_content.split()),
            'images': [],
            'links': links,
            'article_id': article_id
        }
        
        # 下载媒体文件
        if self.download_media and images:
            media_dir = article_dir / 'media'
            media_dir.mkdir(exist_ok=True)
            
            for i, image in enumerate(images):
                url = image['url']
                extension = self.get_file_extension(url)
                
                # 检查扩展名是否允许
                allowed_extensions = self.config['media']['allowed_extensions']
                if extension not in allowed_extensions:
                    continue
                
                filename = f"image_{i+1}.{extension}"
                save_path = media_dir / filename
                
                if self.download_media_file(url, save_path):
                    image['local_path'] = f"media/{filename}"
                    metadata['images'].append(image)
        else:
            metadata['images'] = images
        
        # 保存Markdown内容
        if self.config['storage']['save_markdown']:
            content_file = article_dir / 'content.md'
            with open(content_file, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
        
        # 保存元数据
        if self.config['storage']['save_metadata']:
            metadata_file = article_dir / 'metadata.json'
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"文章已保存: {article_id} - {entry.title}")
        return metadata
    
    def crawl(self):
        """执行爬取任务"""
        self.logger.info("开始爬取Google Research Blog")
        
        # 获取RSS订阅
        feed = self.get_rss_feed()
        if not feed:
            return []
        
        # 处理文章
        processed_articles = []
        entries = feed.entries[:self.max_articles]
        
        for i, entry in enumerate(entries, 1):
            self.logger.info(f"处理文章 {i}/{len(entries)}: {entry.title}")
            
            try:
                metadata = self.process_article(entry)
                if metadata:
                    processed_articles.append(metadata)
                
                # 添加延迟
                if i < len(entries):
                    time.sleep(self.config['crawler']['request_delay'])
                    
            except Exception as e:
                self.logger.error(f"处理文章失败: {e}")
                continue
        
        self.logger.info(f"爬取完成，共处理 {len(processed_articles)} 篇新文章")
        return processed_articles

def main():
    """主函数"""
    spider = GoogleResearchSpider()
    articles = spider.crawl()
    
    print(f"\\n爬取完成！")
    print(f"新增文章: {len(articles)} 篇")
    
    if articles:
        print("\\n文章列表:")
        for article in articles:
            print(f"- {article['title']}")
    
    print(f"\\n文章保存在: {spider.data_dir}")

if __name__ == "__main__":
    main()