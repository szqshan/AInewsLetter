"""
OpenAI Newsroom 爬虫核心模块
负责抓取OpenAI新闻动态页面的文章信息
"""

import asyncio
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Union, Any
from urllib.parse import urljoin, urlparse
import os

import aiohttp
import requests
from bs4 import BeautifulSoup
from loguru import logger
from pydantic import BaseModel, Field, validator

from playwright.async_api import async_playwright
import asyncio_throttle


class ArticleInfo(BaseModel):
    """文章基本信息模型"""
    title: str = Field(..., description="文章标题")
    url: str = Field(..., description="文章URL")
    summary: Optional[str] = Field(None, description="文章摘要")
    publish_date: Optional[str] = Field(None, description="发布日期")
    author: Optional[str] = Field(None, description="作者")
    category: Optional[str] = Field(None, description="文章分类")
    source: str = Field(default="OpenAI Newsroom", description="来源")


class ArticleDetail(BaseModel):
    """文章详情数据模型"""
    title: str
    url: str
    content: str
    author: Optional[str] = None
    publish_date: Optional[str] = None
    tags: List[str] = []
    images: List[str] = []
    word_count: int = 0
    metadata: Dict[str, Any] = {}
    source: str = "OpenAI Newsroom"
    
    @validator('word_count', pre=True, always=True)
    def calculate_word_count(cls, v, values):
        """自动计算字数"""
        content = values.get('content', '')
        return len(content.split()) if content else 0


class OpenAINewsroomSpider:
    """OpenAI Newsroom 爬虫类"""
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.base_url = self.config.get('base_url', 'https://openai.com')
        self.newsroom_url = self.config.get('newsroom_url', 'https://openai.com/zh-Hans-CN/news/')
        self.session = None
        self.throttler = asyncio_throttle.Throttler(rate_limit=1, period=2)  # 每2秒1个请求
        
        # 设置日志
        log_dir = Path("./logs")
        log_dir.mkdir(exist_ok=True)
        logger.add(log_dir / "spider.log", rotation="10 MB", retention="10 days", level="INFO")
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        self.session = aiohttp.ClientSession(
            headers={
                'User-Agent': self.config.get('user_agent', 
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
            },
            timeout=aiohttp.ClientTimeout(total=self.config.get('timeout', 30))
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        if self.session:
            await self.session.close()
    
    def html_to_markdown(self, html_content: str) -> str:
        """将HTML转换为Markdown格式"""
        soup = BeautifulSoup(html_content, 'lxml')
        
        # 处理标题
        for h1 in soup.find_all('h1'):
            h1.replace_with(f"# {h1.get_text().strip()}\n\n")
        for h2 in soup.find_all('h2'):
            h2.replace_with(f"## {h2.get_text().strip()}\n\n")
        for h3 in soup.find_all('h3'):
            h3.replace_with(f"### {h3.get_text().strip()}\n\n")
        for h4 in soup.find_all('h4'):
            h4.replace_with(f"#### {h4.get_text().strip()}\n\n")
        
        # 处理段落
        for p in soup.find_all('p'):
            p.replace_with(f"{p.get_text().strip()}\n\n")
        
        # 处理列表
        for ul in soup.find_all('ul'):
            items = []
            for li in ul.find_all('li'):
                items.append(f"- {li.get_text().strip()}")
            ul.replace_with('\n'.join(items) + '\n\n')
        
        for ol in soup.find_all('ol'):
            items = []
            for i, li in enumerate(ol.find_all('li'), 1):
                items.append(f"{i}. {li.get_text().strip()}")
            ol.replace_with('\n'.join(items) + '\n\n')
        
        # 处理代码块
        for pre in soup.find_all('pre'):
            code = pre.find('code')
            if code:
                language = code.get('class', [''])[0].replace('language-', '') if code.get('class') else ''
                pre.replace_with(f"```{language}\n{code.get_text()}\n```\n\n")
            else:
                pre.replace_with(f"```\n{pre.get_text()}\n```\n\n")
        
        # 处理行内代码
        for code in soup.find_all('code'):
            if code.parent.name != 'pre':
                code.replace_with(f"`{code.get_text().strip()}`")
        
        # 处理链接
        for a in soup.find_all('a', href=True):
            text = a.get_text().strip()
            href = a['href']
            if text and href:
                a.replace_with(f"[{text}]({href})")
        
        # 处理图片
        for img in soup.find_all('img', src=True):
            alt = img.get('alt', '').strip() or 'image'
            src = img['src']
            img.replace_with(f"![{alt}]({src})\n\n")
        
        # 处理加粗和斜体
        for strong in soup.find_all(['strong', 'b']):
            strong.replace_with(f"**{strong.get_text().strip()}**")
        
        for em in soup.find_all(['em', 'i']):
            em.replace_with(f"*{em.get_text().strip()}*")
        
        # 清理多余的空行
        text = soup.get_text()
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        return '\n\n'.join(lines)

    async def fetch_page(self, url: str) -> str:
        """获取页面内容"""
        async with self.throttler:
            # 确保session已创建
            if not hasattr(self, 'session') or self.session is None or self.session.closed:
                connector = aiohttp.TCPConnector(ssl=False)
                timeout = aiohttp.ClientTimeout(total=30)
                self.session = aiohttp.ClientSession(
                    connector=connector,
                    timeout=timeout,
                    headers={
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                        'Accept-Language': 'en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7',
                        'Accept-Encoding': 'gzip, deflate, br',
                        'Connection': 'keep-alive',
                        'Upgrade-Insecure-Requests': '1',
                        'Sec-Fetch-Dest': 'document',
                        'Sec-Fetch-Mode': 'navigate',
                        'Sec-Fetch-Site': 'none',
                        'Cache-Control': 'no-cache',
                        'Pragma': 'no-cache',
                    }
                )
            
            try:
                async with self.session.get(url) as response:
                    response.raise_for_status()
                    return await response.text()
            except aiohttp.ClientResponseError as e:
                if e.status == 403:
                    logger.warning(f"403错误，尝试使用Playwright: {url}")
                    return await self.fetch_page_with_playwright(url)
                else:
                    logger.error(f"获取页面失败: {url}, 错误: {str(e)}")
                    raise
            except Exception as e:
                logger.error(f"获取页面失败: {url}, 错误: {str(e)}")
                raise

    async def fetch_page_with_playwright(self, url: str) -> str:
        """使用Playwright获取页面内容"""
        try:
            from playwright.async_api import async_playwright
            async with async_playwright() as p:
                browser = await p.chromium.launch(
                    headless=True,
                    args=[
                        '--no-sandbox',
                        '--disable-setuid-sandbox',
                        '--disable-blink-features=AutomationControlled',
                        '--disable-web-security',
                        '--disable-features=VizDisplayCompositor',
                        '--disable-extensions',
                        '--disable-plugins',
                        '--disable-images',
                        '--disable-javascript'
                    ]
                )
                context = await browser.new_context(
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    viewport={'width': 1920, 'height': 1080},
                    ignore_https_errors=True
                )
                page = await context.new_page()
                
                try:
                    # 先尝试无JavaScript的快速模式
                    await page.goto(url, wait_until='domcontentloaded', timeout=15000)
                    content = await page.content()
                    
                    # 如果内容太少，再启用JavaScript
                    if len(content) < 1000:
                        logger.info("内容太少，重新启用JavaScript加载")
                        await context.close()
                        
                        # 重新创建启用了JavaScript的context
                        context = await browser.new_context(
                            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                            viewport={'width': 1920, 'height': 1080},
                            ignore_https_errors=True,
                            java_script_enabled=True
                        )
                        page = await context.new_page()
                        
                        await page.goto(url, wait_until='domcontentloaded', timeout=30000)
                        await page.wait_for_timeout(3000)
                        content = await page.content()
                    
                    await browser.close()
                    return content
                    
                except Exception as e:
                    # 如果还是失败，尝试最简模式
                    logger.warning(f"第一次尝试失败，尝试最简模式: {str(e)}")
                    await page.goto(url, wait_until='commit', timeout=10000)
                    content = await page.content()
                    await browser.close()
                    return content
                
        except ImportError:
            logger.error("Playwright未安装，请先安装: pip install playwright")
            raise
        except Exception as e:
            logger.error(f"Playwright获取页面失败 {url}: {str(e)}")
            raise
    
    def parse_article_list(self, html: str, base_url: str) -> List[ArticleInfo]:
        """解析中文新闻列表页面"""
        soup = BeautifulSoup(html, 'lxml')
        articles = []
        seen_urls = set()
        
        # 根据中文新闻页面的实际HTML结构解析
        # 查找新闻条目容器 - 每个新闻都在一个包含日期、类别、标题和链接的div中
        news_items = soup.find_all('div', class_=lambda x: x and ('news' in x.lower() or 'article' in x.lower() or 'post' in x.lower()))
        
        # 如果没找到特定class，尝试查找包含新闻链接的容器
        if not news_items:
            # 查找所有包含/index/链接的容器
            all_links = soup.find_all('a', href=True)
            for link in all_links:
                href = link.get('href', '').strip()
                if '/index/' in href:
                    # 找到父容器
                    parent = link.find_parent(['div', 'article', 'section'])
                    if parent and parent not in news_items:
                        news_items.append(parent)
        
        # 如果还是没找到，直接查找所有/index/链接
        if not news_items:
            index_links = soup.find_all('a', href=lambda x: x and '/index/' in x)
            for link in index_links:
                try:
                    href = link.get('href', '').strip()
                    
                    # 处理相对路径
                    if not href.startswith('http'):
                        href = urljoin(base_url, href)
                    
                    # 过滤重复URL
                    if href in seen_urls:
                        continue
                    seen_urls.add(href)
                    
                    # 确保是OpenAI的链接
                    if 'openai.com' not in href:
                        continue
                    
                    # 获取标题 - 从链接文本或父容器中提取
                    title = ''
                    
                    # 尝试从链接本身获取标题
                    link_text = link.get_text(strip=True)
                    if link_text and len(link_text) > 5:
                        title = link_text
                    
                    # 如果链接文本不够，从父容器查找标题
                    if not title or len(title) < 10:
                        parent = link.find_parent(['div', 'article', 'section'])
                        if parent:
                            # 查找标题元素
                            title_elem = parent.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
                            if title_elem:
                                title = title_elem.get_text(strip=True)
                            else:
                                # 如果没有标题标签，取第一个有意义的文本
                                texts = [t.strip() for t in parent.stripped_strings if len(t.strip()) > 10]
                                if texts:
                                    title = texts[0]
                    
                    if not title or len(title) < 5:
                        continue
                    
                    # 提取日期和分类 - 从父容器中查找
                    publish_date = ''
                    category = ''
                    
                    parent = link.find_parent(['div', 'article', 'section'])
                    if parent:
                        # 查找日期模式
                        date_patterns = [
                            r'\d{4}年\d{1,2}月\d{1,2}日',
                            r'\d{1,2}/\d{1,2}/\d{4}',
                            r'\d{4}-\d{1,2}-\d{1,2}',
                            r'\d{1,2} \w+ \d{4}'
                        ]
                        
                        parent_text = parent.get_text()
                        for pattern in date_patterns:
                            match = re.search(pattern, parent_text)
                            if match:
                                publish_date = match.group()
                                break
                        
                        # 查找分类 - 通常在特定的span或div中
                        category_elem = parent.find(['span', 'div'], class_=lambda x: x and ('category' in x.lower() or 'tag' in x.lower() or 'type' in x.lower()))
                        if category_elem:
                            category = category_elem.get_text(strip=True)
                    
                    articles.append(ArticleInfo(
                        title=title,
                        url=href,
                        summary='',  # 将在详情页获取
                        publish_date=publish_date,
                        author='OpenAI',
                        category=category
                    ))
                    
                except Exception as e:
                    logger.warning(f"解析新闻链接失败: {str(e)}")
                    continue
        
        # 处理找到的新闻容器
        for item in news_items:
            try:
                # 查找链接
                link = item.find('a', href=True)
                if not link:
                    continue
                
                href = link.get('href', '').strip()
                
                # 处理相对路径
                if not href.startswith('http'):
                    href = urljoin(base_url, href)
                
                # 过滤重复URL
                if href in seen_urls:
                    continue
                seen_urls.add(href)
                
                # 确保是OpenAI的链接且包含/index/
                if 'openai.com' not in href or '/index/' not in href:
                    continue
                
                # 获取标题
                title = ''
                title_elem = item.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
                if title_elem:
                    title = title_elem.get_text(strip=True)
                else:
                    # 从链接文本获取
                    title = link.get_text(strip=True)
                
                if not title or len(title) < 5:
                    continue
                
                # 获取日期和分类
                publish_date = ''
                category = ''
                
                # 查找日期
                date_elem = item.find(['time', 'span'], class_=lambda x: x and 'date' in x.lower())
                if date_elem:
                    publish_date = date_elem.get_text(strip=True)
                
                # 查找分类
                category_elem = item.find(['span', 'div'], class_=lambda x: x and ('category' in x.lower() or 'tag' in x.lower()))
                if category_elem:
                    category = category_elem.get_text(strip=True)
                
                articles.append(ArticleInfo(
                    title=title,
                    url=href,
                    summary='',
                    publish_date=publish_date,
                    author='OpenAI',
                    category=category
                ))
                
            except Exception as e:
                logger.warning(f"解析新闻容器失败: {str(e)}")
                continue

        
        logger.info(f"成功解析到 {len(articles)} 篇新闻文章")
        return articles
    
    def parse_article_detail(self, html: str, url: str) -> ArticleDetail:
        """解析文章详情页面"""
        soup = BeautifulSoup(html, 'lxml')
        
        # 提取标题
        title = ''
        title_selectors = [
            'h1[data-testid="title"]',
            'h1[class*="title"]',
            'h1',
            '[class*="post-title"]',
            '[class*="article-title"]'
        ]
        for selector in title_selectors:
            title_elem = soup.select_one(selector)
            if title_elem:
                title = title_elem.get_text(strip=True)
                break
        
        # 提取内容 - 更精确的选择器
        content = ''
        content_selectors = [
            'article',
            '[class*="post-content"]',
            '[class*="article-content"]',
            '[class*="entry-content"]',
            'main [class*="content"]',
            '.content',
            '[data-testid="content"]'
        ]
        
        content_elem = None
        for selector in content_selectors:
            content_elem = soup.select_one(selector)
            if content_elem:
                break
        
        if content_elem:
            # 移除脚本和样式，但保留其他格式
            for script in content_elem(["script", "style", "nav", "header", "footer", "aside"]):
                script.decompose()
            
            # 转换为markdown格式
            content = self.html_to_markdown(str(content_elem))
            
            # 如果内容太短，尝试其他选择器
            if len(content.strip()) < 100:
                # 尝试更通用的内容区域
                possible_content = soup.find('main') or soup.find('body')
                if possible_content:
                    content = self.html_to_markdown(str(possible_content))
        
        # 提取日期
        date = ''
        date_elem = soup.find(['time', 'span'], class_=re.compile(r'.*date.*|.*publish.*', re.I))
        if date_elem:
            date = date_elem.get('datetime') or date_elem.get_text(strip=True)
        
        # 提取作者
        author = ''
        author_elem = soup.find(['span', 'div'], class_=re.compile(r'.*author.*|.*byline.*', re.I))
        if author_elem:
            author = author_elem.get_text(strip=True)
        
        # 提取标签
        tags = []
        tag_elems = soup.find_all(['a', 'span'], class_=re.compile(r'.*tag.*', re.I))
        for tag in tag_elems:
            tags.append(tag.get_text(strip=True))
        
        # 提取图片
        images = []
        img_elems = soup.find_all('img')
        for img in img_elems:
            src = img.get('src') or img.get('data-src')
            if src:
                images.append(urljoin(url, src))
        
        return ArticleDetail(
            title=title,
            url=url,
            content=content,
            publish_date=date,
            author=author,
            tags=tags,
            images=images,
            word_count=len(content.split()),
            metadata={
                'scraped_at': datetime.now().isoformat(),
                'source_url': url
            }
        )
    
    async def download_images(self, images: List[str], output_dir: str) -> Dict[str, str]:
        """下载图片并返回URL到本地文件名的映射"""
        if not images:
            return {}
            
        # 创建media目录
        media_dir = Path(output_dir) / "media"
        media_dir.mkdir(parents=True, exist_ok=True)
        
        url_to_filename = {}
        
        for i, img_url in enumerate(images, 1):
            try:
                # 生成本地文件名
                filename = f"image_{i}.png"
                file_path = media_dir / filename
                
                # 下载图片
                async with aiohttp.ClientSession() as session:
                    async with session.get(img_url) as response:
                        if response.status == 200:
                            content = await response.read()
                            with open(file_path, 'wb') as f:
                                f.write(content)
                            url_to_filename[img_url] = filename
                            logger.info(f"图片已下载: {filename}")
                        else:
                            logger.warning(f"图片下载失败: {img_url}, 状态码: {response.status}")
            except Exception as e:
                logger.error(f"下载图片失败: {img_url}, 错误: {str(e)}")
                
        return url_to_filename
    
    def replace_images_in_content(self, content: str, url_to_filename: Dict[str, str]) -> str:
        """替换内容中的图片URL为本地路径"""
        if not url_to_filename:
            return content
            
        modified_content = content
        for original_url, filename in url_to_filename.items():
            # 替换markdown格式的图片链接
            local_path = f"./media/{filename}"
            modified_content = modified_content.replace(original_url, local_path)
            
        return modified_content
    
    def sanitize_filename(self, title: str) -> str:
        """统一的文件名清理逻辑，与uploader.py保持一致"""
        import re
        # 清理特殊字符，保留中文、英文、数字、空格和连字符
        clean_title = re.sub(r'[^\w\u4e00-\u9fff\s-]', '', title)
        # 将多个空格替换为单个连字符
        clean_title = re.sub(r'\s+', '-', clean_title.strip())
        # 限制长度，防止目录名过长
        if len(clean_title) > 50:
            clean_title = clean_title[:50]
        return clean_title
    
    async def get_article_list(self, url: str = None) -> List[ArticleInfo]:
        """获取文章列表"""
        url = url or self.newsroom_url
        logger.info(f"开始获取文章列表: {url}")
        
        try:
            html = await self.fetch_page(url)
            articles = self.parse_article_list(html, self.base_url)
            logger.info(f"成功获取 {len(articles)} 篇文章")
            return articles
        except Exception as e:
            logger.error(f"获取文章列表失败: {str(e)}")
            return []
    
    async def get_article_detail(self, article_info: ArticleInfo, output_dir: str = "./crawled_data") -> ArticleDetail:
        """获取文章详情"""
        logger.info(f"开始获取文章详情: {article_info.title}")
        
        try:
            html = await self.fetch_page(article_info.url)
            detail = self.parse_article_detail(html, article_info.url)
            
            # 补充基本信息
            if not detail.publish_date and article_info.publish_date:
                detail.publish_date = article_info.publish_date
            if not detail.author and article_info.author:
                detail.author = article_info.author
            
            # 生成文章目录 - 使用统一的文件名清理逻辑
            safe_title = self.sanitize_filename(detail.title)
            article_dir = Path(output_dir) / safe_title
            
            # 下载图片并替换内容中的图片链接
            if detail.images:
                logger.info(f"开始下载 {len(detail.images)} 张图片")
                url_to_filename = await self.download_images(detail.images, str(article_dir))
                
                # 替换内容中的图片链接
                detail.content = self.replace_images_in_content(detail.content, url_to_filename)
                
                # 更新images字段为本地文件名
                detail.images = list(url_to_filename.values())
                
                # 在metadata中保存原始图片URL
                detail.metadata['original_images'] = list(url_to_filename.keys())
            
            return detail
        except Exception as e:
            logger.error(f"获取文章详情失败: {article_info.title}, 错误: {str(e)}")
            # 返回基本信息
            return ArticleDetail(
                title=article_info.title,
                url=article_info.url,
                content="",
                publish_date=article_info.publish_date,
                author=article_info.author,
                metadata={'error': str(e), 'scraped_at': datetime.now().isoformat()}
            )
    
    async def crawl_all_articles(self, max_articles: int = None, output_dir: str = "./crawled_data") -> List[ArticleDetail]:
        """爬取所有文章"""
        articles_info = await self.get_article_list()
        
        if max_articles:
            articles_info = articles_info[:max_articles]
        
        logger.info(f"开始爬取 {len(articles_info)} 篇文章的详情")
        
        # 并发获取详情
        semaphore = asyncio.Semaphore(self.config.get('max_concurrent', 5))
        
        async def fetch_with_semaphore(article_info):
            async with semaphore:
                return await self.get_article_detail(article_info, output_dir)
        
        tasks = [fetch_with_semaphore(article) for article in articles_info]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 过滤成功的结果
        articles = [r for r in results if isinstance(r, ArticleDetail)]
        errors = [r for r in results if isinstance(r, Exception)]
        
        logger.info(f"成功爬取 {len(articles)} 篇文章, 失败 {len(errors)} 篇")
        return articles