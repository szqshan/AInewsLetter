#!/usr/bin/env python3
"""
Claude Newsroom Spider
简化版新闻爬虫，从Claude官方newsroom爬取新闻并本地存储
"""

import os
import re
import json
import time
import hashlib
import requests
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import argparse

class ClaudeNewsroomSpider:
    def __init__(self, config_file="config.json"):
        """初始化爬虫"""
        self.base_url = "https://www.anthropic.com"
        self.newsroom_url = f"{self.base_url}/news"
        self.session = requests.Session()
        self.config = self.load_config(config_file)
        self.setup_directories()
        
        # 设置请求头
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
    
    def load_config(self, config_file):
        """加载配置文件"""
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"配置文件 {config_file} 未找到，使用默认配置")
            return self.get_default_config()
    
    def get_default_config(self):
        """获取默认配置"""
        return {
            "crawler": {
                "delay": 2,
                "timeout": 30,
                "max_retries": 3,
                "max_articles": 50
            },
            "media": {
                "download_images": True,
                "image_timeout": 15,
                "max_image_size": 10485760
            },
            "storage": {
                "data_dir": "crawled_data",
                "articles_dir": "articles",
                "create_subdirs": True
            }
        }
    
    def setup_directories(self):
        """创建必要的目录"""
        self.data_dir = Path(self.config["storage"]["data_dir"])
        self.articles_dir = self.data_dir / self.config["storage"]["articles_dir"]
        
        self.data_dir.mkdir(exist_ok=True)
        self.articles_dir.mkdir(exist_ok=True)
    
    def get_news_links(self):
        """获取新闻页面的所有新闻链接"""
        print(f"正在获取新闻列表: {self.newsroom_url}")
        
        try:
            response = self.session.get(
                self.newsroom_url, 
                timeout=self.config["crawler"]["timeout"]
            )
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"获取新闻列表失败: {e}")
            return []
        
        soup = BeautifulSoup(response.text, 'html.parser')
        news_links = []
        
        # 查找所有新闻链接
        # 基于之前分析，新闻链接格式为 /news/{slug}
        link_elements = soup.find_all('a', href=True)
        
        for link in link_elements:
            href = link.get('href', '')
            if href.startswith('/news/') and len(href) > 6:  # 过滤掉 /news 本身
                full_url = urljoin(self.base_url, href)
                if full_url not in news_links:
                    news_links.append(full_url)
        
        print(f"找到 {len(news_links)} 篇新闻")
        return news_links[:self.config["crawler"]["max_articles"]]
    
    def extract_article_content(self, url):
        """提取单篇文章内容"""
        print(f"正在爬取: {url}")
        
        try:
            response = self.session.get(url, timeout=self.config["crawler"]["timeout"])
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"获取文章失败: {e}")
            return None
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 提取文章信息
        article_data = {
            'url': url,
            'title': self.extract_title(soup),
            'category': self.extract_category(soup),
            'date': self.extract_date(soup),
            'content': self.extract_content(soup),
            'images': self.extract_images(soup),
            'crawl_time': datetime.now().isoformat(),
            'slug': self.extract_slug_from_url(url)
        }
        
        return article_data
    
    def extract_title(self, soup):
        """提取文章标题"""
        # 尝试多种选择器
        selectors = ['h1', 'h1[class*="title"]', '[data-testid="title"]', '.article-title']
        
        for selector in selectors:
            title_elem = soup.select_one(selector)
            if title_elem:
                return title_elem.get_text(strip=True)
        
        # 备用方案：从页面标题提取
        title_tag = soup.find('title')
        if title_tag:
            title = title_tag.get_text(strip=True)
            # 移除常见的网站后缀
            title = re.sub(r'\s*[\|\-]\s*Anthropic.*$', '', title)
            return title
        
        return "未知标题"
    
    def extract_category(self, soup):
        """提取文章分类"""
        # 根据页面分析，寻找可能的分类标签
        selectors = [
            '[class*="category"]',
            '[class*="tag"]',
            'span:contains("Announcements")',
            'span:contains("Product")',
            'span:contains("Policy")',
            'span:contains("Research")'
        ]
        
        for selector in selectors:
            try:
                category_elem = soup.select_one(selector)
                if category_elem:
                    category = category_elem.get_text(strip=True)
                    if category and len(category) < 50:  # 合理的分类长度
                        return category
            except:
                continue
        
        return "未分类"
    
    def extract_date(self, soup):
        """提取发布日期"""
        # 尝试多种日期格式和选择器
        selectors = [
            'time[datetime]',
            '[class*="date"]',
            '[class*="publish"]',
            'meta[property="article:published_time"]'
        ]
        
        for selector in selectors:
            date_elem = soup.select_one(selector)
            if date_elem:
                # 尝试从datetime属性获取
                datetime_attr = date_elem.get('datetime') or date_elem.get('content')
                if datetime_attr:
                    return datetime_attr
                
                # 从文本内容获取
                date_text = date_elem.get_text(strip=True)
                if date_text:
                    return self.parse_date_string(date_text)
        
        # 备用方案：在页面中搜索日期模式
        date_patterns = [
            r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},?\s+20\d{2}',
            r'\d{4}-\d{2}-\d{2}',
            r'\d{1,2}/\d{1,2}/20\d{2}'
        ]
        
        page_text = soup.get_text()
        for pattern in date_patterns:
            match = re.search(pattern, page_text)
            if match:
                return match.group(0)
        
        return datetime.now().strftime('%Y-%m-%d')
    
    def parse_date_string(self, date_str):
        """解析日期字符串"""
        # 清理日期字符串
        date_str = re.sub(r'[^\w\s,/-]', '', date_str).strip()
        
        # 尝试多种日期格式
        formats = [
            '%b %d, %Y',    # Jan 01, 2024
            '%B %d, %Y',    # January 01, 2024
            '%Y-%m-%d',     # 2024-01-01
            '%m/%d/%Y',     # 01/01/2024
            '%d/%m/%Y',     # 01/01/2024
        ]
        
        for fmt in formats:
            try:
                parsed_date = datetime.strptime(date_str, fmt)
                return parsed_date.strftime('%Y-%m-%d')
            except ValueError:
                continue
        
        return date_str
    
    def extract_content(self, soup):
        """提取文章正文内容"""
        # 移除不需要的元素
        for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside']):
            element.decompose()
        
        # 尝试多种内容选择器
        content_selectors = [
            'article',
            '[class*="content"]',
            '[class*="article"]',
            'main',
            '.post-content',
            '#content'
        ]
        
        for selector in content_selectors:
            content_elem = soup.select_one(selector)
            if content_elem:
                # 清理和格式化内容
                content = self.clean_content(content_elem)
                if len(content) > 100:  # 确保内容有足够长度
                    return content
        
        # 备用方案：提取主要段落
        paragraphs = soup.find_all('p')
        if paragraphs:
            content = '\n\n'.join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])
            return content
        
        return "无法提取内容"
    
    def clean_content(self, content_elem):
        """清理文章内容"""
        # 转换为markdown格式
        content_lines = []
        
        for element in content_elem.descendants:
            if element.name == 'h1':
                content_lines.append(f"\n# {element.get_text(strip=True)}\n")
            elif element.name == 'h2':
                content_lines.append(f"\n## {element.get_text(strip=True)}\n")
            elif element.name == 'h3':
                content_lines.append(f"\n### {element.get_text(strip=True)}\n")
            elif element.name == 'p':
                text = element.get_text(strip=True)
                if text:
                    content_lines.append(f"{text}\n")
            elif element.name == 'a' and element.get('href'):
                text = element.get_text(strip=True)
                href = element.get('href')
                if text and href:
                    content_lines.append(f"[{text}]({href})")
        
        return '\n'.join(content_lines).strip()
    
    def extract_images(self, soup):
        """提取文章中的图片信息"""
        images = []
        img_elements = soup.find_all('img', src=True)
        
        for img in img_elements:
            src = img.get('src')
            if not src:
                continue
            
            # 转换为完整URL
            full_url = urljoin(self.base_url, src)
            
            # 过滤掉小图标和装饰性图片
            if any(x in src.lower() for x in ['icon', 'logo', 'avatar']) and 'x' in src and '32' in src:
                continue
            
            # 获取更丰富的图片信息
            alt_text = img.get('alt', '').strip()
            title_text = img.get('title', '').strip()
            
            # 尝试从周围文本获取描述
            if not alt_text and not title_text:
                # 查找图片的父元素或兄弟元素中的文本
                parent = img.parent
                if parent:
                    # 查找图片说明文字
                    caption = parent.find(['figcaption', 'caption'])
                    if caption:
                        alt_text = caption.get_text().strip()
                    else:
                        # 查找附近的文本（限制长度避免获取正文）
                        siblings = parent.find_all(text=True, recursive=False)
                        for sibling in siblings:
                            text = sibling.strip()
                            if text and len(text) < 50 and not text.startswith('#'):
                                alt_text = text
                                break
            
            image_info = {
                'url': full_url,
                'alt': alt_text,
                'title': title_text,
                'filename': self.generate_image_filename(full_url)
            }
            images.append(image_info)
        
        return images
    
    def generate_image_filename(self, url):
        """生成图片文件名"""
        parsed = urlparse(url)
        original_name = os.path.basename(parsed.path)
        
        if not original_name or '.' not in original_name:
            # 如果没有扩展名，尝试从URL生成
            url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
            return f"image_{url_hash}.jpg"
        
        return original_name
    
    def download_images(self, images, article_dir):
        """下载文章图片"""
        if not self.config["media"]["download_images"]:
            return
        
        media_dir = article_dir / 'media'
        media_dir.mkdir(exist_ok=True)
        
        for img_info in images:
            try:
                response = self.session.get(
                    img_info['url'], 
                    timeout=self.config["media"]["image_timeout"],
                    stream=True
                )
                response.raise_for_status()
                
                # 检查文件大小
                content_length = response.headers.get('content-length')
                if content_length and int(content_length) > self.config["media"]["max_image_size"]:
                    print(f"图片太大，跳过: {img_info['url']}")
                    continue
                
                # 保存图片
                image_path = media_dir / img_info['filename']
                with open(image_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                img_info['local_path'] = str(image_path)
                print(f"下载图片: {img_info['filename']}")
                
            except Exception as e:
                print(f"下载图片失败 {img_info['url']}: {e}")
                img_info['download_error'] = str(e)
    
    def extract_slug_from_url(self, url):
        """从URL提取文章slug"""
        parsed = urlparse(url)
        parts = parsed.path.split('/')
        return parts[-1] if parts else hashlib.md5(url.encode()).hexdigest()[:8]
    
    def save_article(self, article_data):
        """保存文章到本地"""
        slug = article_data['slug']
        article_dir = self.articles_dir / slug
        article_dir.mkdir(exist_ok=True)
        
        # 下载图片
        if article_data.get('images'):
            self.download_images(article_data['images'], article_dir)
        
        # 保存元数据
        metadata_file = article_dir / 'metadata.json'
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(article_data, f, ensure_ascii=False, indent=2)
        
        # 保存Markdown内容
        content_file = article_dir / 'content.md'
        markdown_content = self.generate_markdown(article_data)
        with open(content_file, 'w', encoding='utf-8', newline='\n') as f:
            f.write(markdown_content)
        
        print(f"保存文章: {article_data['title']}")
        return article_dir
    
    def generate_markdown(self, article_data):
        """生成Markdown格式的文章"""
        markdown_lines = [
            f"# {article_data['title']}\n",
            f"**分类**: {article_data['category']}  ",
            f"**发布日期**: {article_data['date']}  ",
            f"**来源**: {article_data['url']}  ",
            f"**爬取时间**: {article_data['crawl_time']}\n",
            "---\n"
        ]
        
        # 处理正文内容，在合适位置插入图片
        content = article_data['content']
        images = article_data.get('images', [])
        
        if images:
            # 将内容按段落分割
            paragraphs = content.split('\n\n')
            enhanced_content = []
            image_index = 0
            total_paragraphs = len(paragraphs)
            
            # 计算图片插入位置
            insertion_points = []
            if total_paragraphs > 3:
                # 第一张图片在第2段后（避免紧跟标题）
                insertion_points.append(2)
                # 如果有多张图片，在中间位置插入
                if len(images) > 1 and total_paragraphs > 6:
                    insertion_points.append(total_paragraphs // 2)
                # 如果有很多图片，在3/4位置插入
                if len(images) > 2 and total_paragraphs > 10:
                    insertion_points.append(int(total_paragraphs * 0.75))
            
            for i, paragraph in enumerate(paragraphs):
                enhanced_content.append(paragraph)
                
                # 在指定位置插入图片
                if i in insertion_points and image_index < len(images):
                    img = images[image_index]
                    # 使用相对路径
                    relative_path = f"media/{img['filename']}"
                    alt_text = img.get('alt', '') or img.get('title', '') or f"{article_data['title']} - 图片 {image_index + 1}"
                    enhanced_content.append(f"\n![{alt_text}]({relative_path})\n")
                    image_index += 1
            
            content = '\n\n'.join(enhanced_content)
            
            # 在文章末尾添加剩余图片
            if image_index < len(images):
                content += "\n\n## 相关图片\n"
                for img in images[image_index:]:
                    relative_path = f"media/{img['filename']}"
                    alt_text = img.get('alt', '') or img.get('title', '') or f"{article_data['title']} - 图片"
                    content += f"\n![{alt_text}]({relative_path})\n"
        
        markdown_lines.append(content)
        return '\n'.join(markdown_lines)
    
    def is_article_exists(self, url):
        """检查文章是否已存在"""
        slug = self.extract_slug_from_url(url)
        article_dir = self.articles_dir / slug
        return article_dir.exists() and (article_dir / 'content.md').exists()
    
    def crawl(self, force_update=False, max_articles=None):
        """执行爬取任务"""
        print("🤖 Claude Newsroom 爬虫启动")
        print(f"目标: {self.newsroom_url}")
        
        # 获取新闻链接
        news_links = self.get_news_links()
        if not news_links:
            print("未找到新闻链接")
            return
        
        if max_articles:
            news_links = news_links[:max_articles]
        
        success_count = 0
        error_count = 0
        
        for i, url in enumerate(news_links, 1):
            print(f"\n[{i}/{len(news_links)}] 处理文章...")
            
            # 检查是否已存在（除非强制更新）
            if not force_update and self.is_article_exists(url):
                print(f"文章已存在，跳过: {url}")
                continue
            
            try:
                # 提取文章内容
                article_data = self.extract_article_content(url)
                if not article_data:
                    error_count += 1
                    continue
                
                # 保存文章
                self.save_article(article_data)
                success_count += 1
                
                # 延迟以避免请求过快
                time.sleep(self.config["crawler"]["delay"])
                
            except Exception as e:
                print(f"处理文章出错 {url}: {e}")
                error_count += 1
        
        print(f"\n✅ 爬取完成!")
        print(f"成功: {success_count} 篇")
        print(f"失败: {error_count} 篇")
        print(f"数据保存位置: {self.articles_dir}")

def main():
    parser = argparse.ArgumentParser(description='Claude Newsroom 爬虫')
    parser.add_argument('--config', default='config.json', help='配置文件路径')
    parser.add_argument('--force', action='store_true', help='强制更新已存在的文章')
    parser.add_argument('--max', type=int, help='最大爬取文章数量')
    
    args = parser.parse_args()
    
    spider = ClaudeNewsroomSpider(args.config)
    spider.crawl(force_update=args.force, max_articles=args.max)

if __name__ == "__main__":
    main()
