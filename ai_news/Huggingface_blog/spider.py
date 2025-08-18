#!/usr/bin/env python3
"""
Hugging Face博客爬虫
基于API优先策略和HTML补充的混合爬取方案
"""

import json
import time
import re
import hashlib
import logging
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin, urlparse
from typing import List, Dict, Optional, Set

import requests
from bs4 import BeautifulSoup


class HuggingFaceBlogSpider:
    """Hugging Face博客爬虫主类"""
    
    def __init__(self, config_file: str = "config.json"):
        """初始化爬虫"""
        self.config = self.load_config(config_file)
        self.session = self.setup_session()
        self.setup_directories()
        self.setup_logging()
        self.crawled_urls: Set[str] = set()
        
    def load_config(self, config_file: str) -> Dict:
        """加载配置文件"""
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            logging.error(f"配置文件 {config_file} 不存在")
            raise
        except json.JSONDecodeError:
            logging.error(f"配置文件 {config_file} 格式错误")
            raise
    
    def setup_session(self) -> requests.Session:
        """设置请求会话"""
        session = requests.Session()
        session.headers.update({
            'User-Agent': self.config['crawler']['user_agent'],
            'Accept': 'application/json, text/html, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        })
        return session
    
    def setup_directories(self):
        """创建必要的目录结构"""
        data_dir = Path(self.config['storage']['data_dir'])
        articles_dir = data_dir / self.config['storage']['data_type']
        articles_dir.mkdir(parents=True, exist_ok=True)
        
    def setup_logging(self):
        """设置日志系统"""
        logging.basicConfig(
            level=getattr(logging, self.config['logging']['level']),
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.config['logging']['log_file'], encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def get_blog_posts_from_api(self) -> List[str]:
        """从Posts API获取博客链接"""
        self.logger.info("开始从API获取博客动态...")
        
        try:
            url = self.config['api']['posts_endpoint']
            params = self.config['api']['default_params'].copy()
            
            # 添加时间范围参数
            if self.config['api']['time_range']['since']:
                params['since'] = self.config['api']['time_range']['since']
            if self.config['api']['time_range']['until']:
                params['until'] = self.config['api']['time_range']['until']
            
            response = self.session.get(url, params=params, timeout=self.config['crawler']['timeout'])
            response.raise_for_status()
            
            data = response.json()
            
            # 提取博客链接
            blog_links = []
            posts = data.get('socialPosts', [])
            
            for post in posts:
                # 从文本内容中提取博客链接
                content = post.get('rawContent', '')
                links = re.findall(r'https://huggingface\.co/blog/[^\s\)]+', content)
                
                # 从发布内容中提取博客链接
                if post.get('text'):
                    text_links = re.findall(r'https://huggingface\.co/blog/[^\s\)]+', post['text'])
                    links.extend(text_links)
                
                blog_links.extend(links)
            
            # 去重并过滤
            unique_links = list(set(blog_links))
            filtered_links = [link for link in unique_links if self.is_valid_blog_url(link)]
            
            self.logger.info(f"从API获取到 {len(filtered_links)} 个有效博客链接")
            return filtered_links
            
        except Exception as e:
            self.logger.error(f"API请求失败: {e}")
            return []
    
    def get_articles_from_html_page(self, page_num: int = 0) -> List[str]:
        """从HTML页面获取文章列表"""
        self.logger.info(f"开始解析HTML页面 (第{page_num+1}页)...")
        
        try:
            url = f"https://huggingface.co/blog/zh?p={page_num}"
            response = self.session.get(url, timeout=self.config['crawler']['timeout'])
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 提取文章链接
            article_links = []
            for link in soup.find_all('a', href=True):
                href = link['href']
                if '/blog/' in href and href not in article_links:
                    full_url = urljoin('https://huggingface.co', href)
                    if self.is_valid_blog_url(full_url):
                        article_links.append(full_url)
            
            self.logger.info(f"从HTML页面获取到 {len(article_links)} 个文章链接")
            return article_links
            
        except Exception as e:
            self.logger.error(f"HTML页面解析失败: {e}")
            return []
    
    def get_all_html_pages(self) -> List[str]:
        """获取所有分页的文章"""
        self.logger.info("开始获取所有HTML分页...")
        
        all_articles = []
        page = 0
        consecutive_empty = 0
        max_empty_pages = 3
        
        while consecutive_empty < max_empty_pages:
            articles = self.get_articles_from_html_page(page)
            
            if not articles:
                consecutive_empty += 1
                self.logger.warning(f"第{page+1}页没有获取到文章，连续空页数: {consecutive_empty}")
            else:
                consecutive_empty = 0
                all_articles.extend(articles)
                self.logger.info(f"第{page+1}页获取到 {len(articles)} 篇文章")
            
            page += 1
            time.sleep(self.config['crawler']['delay'])
            
            # 避免无限循环
            if page > 50:
                self.logger.warning("已达到最大页数限制")
                break
        
        # 去重
        unique_articles = list(set(all_articles))
        self.logger.info(f"HTML分页总共获取到 {len(unique_articles)} 个唯一文章链接")
        return unique_articles
    
    def is_valid_blog_url(self, url: str) -> bool:
        """验证是否为有效的博客URL"""
        if not url or not url.startswith('https://huggingface.co/blog/'):
            return False
        
        # 排除某些模式
        exclude_patterns = self.config['filter']['exclude_patterns']
        for pattern in exclude_patterns:
            if re.search(pattern, url):
                return False
        
        return True
    
    def extract_slug_from_url(self, url: str) -> str:
        """从URL提取文章slug"""
        parsed = urlparse(url)
        path_parts = parsed.path.strip('/').split('/')
        
        if len(path_parts) >= 2 and path_parts[0] == 'blog':
            return path_parts[-1]  # 取最后一部分作为slug
        
        return hashlib.md5(url.encode()).hexdigest()[:8]
    
    def crawl_article_detail(self, article_url: str) -> Optional[Dict]:
        """爬取单篇文章的详细内容"""
        self.logger.info(f"开始爬取文章: {article_url}")
        
        try:
            response = self.session.get(article_url, timeout=self.config['crawler']['timeout'])
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 提取标题
            title_selectors = ['h1', 'title', '.title', '[data-testid="title"]']
            title = ""
            for selector in title_selectors:
                title_elem = soup.select_one(selector)
                if title_elem:
                    title = title_elem.get_text().strip()
                    break
            
            # 提取内容
            content_selectors = [
                'article', 
                '.prose', 
                '.content', 
                'main',
                '[data-testid="article-content"]',
                '.blog-content'
            ]
            content_div = None
            for selector in content_selectors:
                content_div = soup.select_one(selector)
                if content_div:
                    break
            
            if not content_div:
                # 如果没有找到特定容器，尝试获取主要内容区域
                content_div = soup.find('body')
            
            # 提取纯文本内容
            content_text = ""
            html_content = ""
            if content_div:
                content_text = content_div.get_text().strip()
                html_content = str(content_div)
            
            # 检查内容长度
            if len(content_text) < self.config['filter']['min_content_length']:
                self.logger.warning(f"文章内容过短，跳过: {article_url}")
                return None
            
            # 提取图片
            images = self.extract_images(soup, article_url)
            
            # 生成文章数据
            article_data = {
                'url': article_url,
                'title': title,
                'content': content_text,
                'html_content': html_content,
                'images': images,
                'slug': self.extract_slug_from_url(article_url),
                'crawl_time': datetime.now().isoformat(),
                'word_count': len(content_text.split()),
                'content_hash': hashlib.md5(content_text.encode()).hexdigest()
            }
            
            self.logger.info(f"成功爬取文章: {title[:50]}...")
            return article_data
            
        except Exception as e:
            self.logger.error(f"爬取文章失败 {article_url}: {e}")
            return None
    
    def extract_images(self, soup: BeautifulSoup, base_url: str) -> List[Dict]:
        """提取文章中的图片"""
        images = []
        for img in soup.find_all('img'):
            src = img.get('src')
            if src:
                # 处理相对URL
                full_url = urljoin(base_url, src)
                
                # 检查文件扩展名
                parsed_url = urlparse(full_url)
                path = parsed_url.path.lower()
                
                # 检查是否为允许的图片格式
                allowed_exts = self.config['media']['allowed_extensions']
                if any(path.endswith(ext) for ext in allowed_exts):
                    images.append({
                        'url': full_url,
                        'alt': img.get('alt', ''),
                        'title': img.get('title', ''),
                        'filename': Path(parsed_url.path).name
                    })
        
        return images
    
    def download_media_files(self, images: List[Dict], media_dir: Path):
        """下载媒体文件"""
        if not self.config['media']['download_images'] or not images:
            return
        
        media_dir.mkdir(parents=True, exist_ok=True)
        
        for i, img in enumerate(images):
            try:
                self.logger.info(f"下载图片: {img['url']}")
                
                response = self.session.get(
                    img['url'], 
                    timeout=self.config['media']['image_timeout'],
                    stream=True
                )
                response.raise_for_status()
                
                # 检查文件大小
                content_length = response.headers.get('content-length')
                if content_length and int(content_length) > self.config['media']['max_file_size']:
                    self.logger.warning(f"图片文件过大，跳过: {img['url']}")
                    continue
                
                # 生成文件名
                filename = img.get('filename') or f"image_{i+1:03d}.jpg"
                file_path = media_dir / filename
                
                # 保存文件
                with open(file_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                # 更新图片信息
                img['local_path'] = str(file_path.relative_to(media_dir.parent))
                
                self.logger.info(f"图片下载完成: {filename}")
                time.sleep(0.5)  # 避免请求过快
                
            except Exception as e:
                self.logger.error(f"下载图片失败 {img['url']}: {e}")
    
    def generate_markdown_content(self, article_data: Dict) -> str:
        """生成标准Markdown格式"""
        images_md = ""
        if article_data['images']:
            images_md = "\n## 相关媒体\n\n"
            for i, img in enumerate(article_data['images']):
                local_path = img.get('local_path', img['url'])
                alt_text = img.get('alt', f'Image {i+1}')
                images_md += f"![{alt_text}]({local_path})\n\n"
        
        return f"""# {article_data['title']}

**来源**: {article_data['url']}  
**爬取时间**: {article_data['crawl_time']}  
**字数**: {article_data['word_count']}

---

{article_data['content']}
{images_md}
"""
    
    def generate_metadata(self, article_data: Dict) -> Dict:
        """生成标准元数据JSON"""
        return {
            'url': article_data['url'],
            'title': article_data['title'],
            'slug': article_data['slug'],
            'content': article_data['content'],
            'images': article_data['images'],
            'crawl_time': article_data['crawl_time'],
            'word_count': article_data['word_count'],
            'content_hash': article_data['content_hash']
        }
    
    def save_article(self, article_data: Dict) -> bool:
        """保存文章到本地标准格式"""
        try:
            article_slug = article_data['slug']
            
            # 创建文章目录
            data_dir = Path(self.config['storage']['data_dir'])
            articles_dir = data_dir / self.config['storage']['data_type']
            article_dir = articles_dir / article_slug
            article_dir.mkdir(parents=True, exist_ok=True)
            
            # 检查是否已存在且启用去重
            if self.config['filter']['skip_duplicates']:
                existing_metadata_path = article_dir / "metadata.json"
                if existing_metadata_path.exists():
                    with open(existing_metadata_path, 'r', encoding='utf-8') as f:
                        existing_metadata = json.load(f)
                        if existing_metadata.get('content_hash') == article_data['content_hash']:
                            self.logger.info(f"文章已存在且内容相同，跳过: {article_slug}")
                            return True
            
            # 下载媒体文件
            if article_data['images']:
                media_dir = article_dir / "media"
                self.download_media_files(article_data['images'], media_dir)
            
            # 保存Markdown内容
            markdown_content = self.generate_markdown_content(article_data)
            with open(article_dir / "content.md", 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            
            # 保存JSON元数据
            metadata = self.generate_metadata(article_data)
            with open(article_dir / "metadata.json", 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"文章保存完成: {article_slug}")
            return True
            
        except Exception as e:
            self.logger.error(f"保存文章失败: {e}")
            return False
    
    def run_api_only(self, max_articles: int = None, force: bool = False) -> int:
        """仅使用API方式爬取"""
        self.logger.info("=== 开始API模式爬取 ===")
        
        blog_links = self.get_blog_posts_from_api()
        
        if max_articles:
            blog_links = blog_links[:max_articles]
        
        return self.crawl_articles(blog_links, force)
    
    def run_html_only(self, max_articles: int = None, force: bool = False) -> int:
        """仅使用HTML解析方式爬取"""
        self.logger.info("=== 开始HTML模式爬取 ===")
        
        blog_links = self.get_all_html_pages()
        
        if max_articles:
            blog_links = blog_links[:max_articles]
        
        return self.crawl_articles(blog_links, force)
    
    def run(self, max_articles: int = None, force: bool = False) -> int:
        """执行完整爬取流程（混合模式）"""
        self.logger.info("=== 开始混合模式爬取 ===")
        
        # 1. 优先使用API获取最新文章
        api_links = self.get_blog_posts_from_api()
        
        # 2. 使用HTML解析补充历史文章
        html_links = self.get_all_html_pages()
        
        # 3. 合并去重
        all_links = list(set(api_links + html_links))
        self.logger.info(f"总共发现 {len(all_links)} 个唯一文章链接")
        
        if max_articles:
            all_links = all_links[:max_articles]
        
        return self.crawl_articles(all_links, force)
    
    def crawl_articles(self, article_urls: List[str], force: bool = False) -> int:
        """批量爬取文章"""
        success_count = 0
        total_count = len(article_urls)
        
        self.logger.info(f"开始爬取 {total_count} 篇文章...")
        
        for i, url in enumerate(article_urls):
            self.logger.info(f"进度: {i+1}/{total_count}")
            
            # 检查是否已爬取过
            if not force and url in self.crawled_urls:
                self.logger.info(f"文章已爬取过，跳过: {url}")
                continue
            
            # 爬取文章
            article_data = self.crawl_article_detail(url)
            
            if article_data:
                # 保存文章
                if self.save_article(article_data):
                    success_count += 1
                    self.crawled_urls.add(url)
            
            # 请求间隔
            time.sleep(self.config['crawler']['delay'])
        
        self.logger.info(f"爬取完成: 成功 {success_count}/{total_count}")
        return success_count


if __name__ == "__main__":
    # 简单测试
    spider = HuggingFaceBlogSpider()
    spider.run(max_articles=5)