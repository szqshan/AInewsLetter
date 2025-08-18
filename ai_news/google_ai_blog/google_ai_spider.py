#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Google AI Blog RSS Spider
爬取Google AI Blog的RSS订阅内容并按照指定存储结构保存
"""

import feedparser
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import re
import json
import logging
import os
import hashlib
import time
from typing import List, Dict, Optional
from urllib.parse import urljoin, urlparse
import urllib.robotparser

class GoogleAIBlogSpider:
    def __init__(self, base_path: str = None):
        """
        初始化爬虫
        Args:
            base_path: 数据存储基础路径，默认为当前目录
        """
        self.base_path = base_path or os.getcwd()
        self.data_path = os.path.join(self.base_path, 'data')
        
        # 注意：Google Research博客的RSS地址
        self.base_url = 'https://research.google/blog/'
        self.rss_url = 'https://research.google/blog/rss/'
        
        # 设置请求会话
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive'
        })
        
        # 设置日志
        self.setup_logging()
        
        # 创建目录结构
        self.create_directory_structure()
        
        # 加载已有索引
        self.load_article_index()
    
    def setup_logging(self):
        """设置日志"""
        log_dir = os.path.join(self.base_path, 'logs')
        os.makedirs(log_dir, exist_ok=True)
        
        log_file = os.path.join(log_dir, f'google_ai_spider_{datetime.now().strftime("%Y%m%d")}.log')
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        
        self.logger = logging.getLogger("GoogleAIBlogSpider")
    
    def create_directory_structure(self):
        """创建目录结构"""
        directories = [
            os.path.join(self.data_path, 'articles'),
            os.path.join(self.data_path, 'images'),
            os.path.join(self.data_path, 'metadata'),
            os.path.join(self.data_path, 'exports', 'daily'),
            os.path.join(self.data_path, 'exports', 'weekly'),
            os.path.join(self.data_path, 'exports', 'monthly'),
            os.path.join(self.base_path, 'logs'),
            os.path.join(self.base_path, 'config')
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
        
        self.logger.info("目录结构创建完成")
    
    def load_article_index(self):
        """加载文章索引"""
        self.index_file = os.path.join(self.data_path, 'metadata', 'article_index.json')
        
        if os.path.exists(self.index_file):
            try:
                with open(self.index_file, 'r', encoding='utf-8') as f:
                    self.article_index = json.load(f)
                self.logger.info(f"加载已有索引，共{self.article_index.get('total_articles', 0)}篇文章")
            except Exception as e:
                self.logger.error(f"加载索引文件失败: {e}")
                self.article_index = self.create_empty_index()
        else:
            self.article_index = self.create_empty_index()
    
    def create_empty_index(self) -> Dict:
        """创建空索引"""
        return {
            "total_articles": 0,
            "last_update": datetime.now().isoformat(),
            "articles": [],
            "categories": {},
            "monthly_stats": {}
        }
    
    def save_article_index(self):
        """保存文章索引"""
        self.article_index['last_update'] = datetime.now().isoformat()
        
        try:
            with open(self.index_file, 'w', encoding='utf-8') as f:
                json.dump(self.article_index, f, indent=2, ensure_ascii=False)
            self.logger.info("文章索引已保存")
        except Exception as e:
            self.logger.error(f"保存索引文件失败: {e}")
    
    def check_robots_txt(self) -> bool:
        """检查robots.txt规则"""
        try:
            rp = urllib.robotparser.RobotFileParser()
            rp.set_url(f"{self.base_url}/robots.txt")
            rp.read()
            return rp.can_fetch('*', self.rss_url)
        except:
            return True  # 如果无法获取robots.txt，默认允许
    
    def get_rss_feed(self) -> Optional[feedparser.FeedParserDict]:
        """获取RSS订阅内容"""
        try:
            self.logger.info(f"获取RSS订阅: {self.rss_url}")
            
            # 检查robots.txt
            if not self.check_robots_txt():
                self.logger.warning("robots.txt不允许访问RSS")
                return None
            
            # 使用feedparser解析RSS
            feed = feedparser.parse(self.rss_url)
            
            if feed.bozo:
                self.logger.warning(f"RSS解析警告: {feed.bozo_exception}")
            
            self.logger.info(f"RSS订阅中发现{len(feed.entries)}篇文章")
            return feed
            
        except Exception as e:
            self.logger.error(f"获取RSS订阅失败: {e}")
            return None
    
    def parse_rss_entries(self, feed: feedparser.FeedParserDict, max_entries: int = 50) -> List[Dict]:
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
                    'source': 'Google Research Blog',
                    'source_type': 'official_blog',
                    'language': 'en'
                }
                
                # 生成唯一ID
                article_info['article_id'] = self.generate_article_id(article_info)
                
                # 检查是否已存在
                if not self.is_article_exists(article_info['article_id']):
                    articles.append(article_info)
                else:
                    self.logger.info(f"文章已存在，跳过: {article_info['title']}")
                
            except Exception as e:
                self.logger.warning(f"解析RSS条目失败: {e}")
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
                return 'Google Research Team'
        except:
            return 'Google Research Team'
    
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
            self.logger.info(f"获取文章详情: {article_info['title']}")
            
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 提取文章内容
            content = self.extract_article_content(soup)
            if content:
                article_info['content'] = content
                article_info['word_count'] = len(content.split())
                article_info['reading_time_minutes'] = max(1, article_info['word_count'] // 200)
            
            # 提取更详细的元数据
            detailed_metadata = self.extract_detailed_metadata(soup)
            article_info.update(detailed_metadata)
            
            # 提取图片信息
            images = self.extract_images(soup, article_info['article_id'])
            if images:
                article_info['images'] = images
            
            # 技术分析
            tech_analysis = self.analyze_technical_content(content)
            article_info['technical_analysis'] = tech_analysis
            
            # 计算质量分数
            article_info['quality_score'] = self.calculate_quality_score(article_info)
            
            # 添加爬取时间
            article_info['crawl_date'] = datetime.now().isoformat()
            
        except Exception as e:
            self.logger.error(f"获取文章详情失败 {url}: {e}")
        
        return article_info
    
    def extract_article_content(self, soup: BeautifulSoup) -> str:
        """提取文章正文内容"""
        # Google Research Blog的内容结构
        content_selectors = [
            'div.post-body',
            'div.entry-content',
            'article .post-content',
            'div.blog-post-content',
            'main article',
            '[role="main"] article'
        ]
        
        for selector in content_selectors:
            content_elem = soup.select_one(selector)
            if content_elem:
                # 清理内容
                content = self.clean_article_content(content_elem)
                if len(content) > 100:
                    return content
        
        # 如果找不到特定选择器，尝试通用方法
        article_elem = soup.find('article')
        if article_elem:
            content = self.clean_article_content(article_elem)
            if len(content) > 100:
                return content
        
        return ''
    
    def clean_article_content(self, content_elem) -> str:
        """清理文章内容"""
        # 移除不需要的元素
        for tag in content_elem.find_all(['script', 'style', 'nav', 'aside', 'footer', 'header']):
            tag.decompose()
        
        # 移除广告和分享按钮
        for tag in content_elem.find_all(class_=re.compile(r'ad|share|social|related|sidebar')):
            tag.decompose()
        
        # 处理代码块
        for code_block in content_elem.find_all(['pre', 'code']):
            if code_block.parent.name != 'pre':  # 避免重复处理
                code_text = code_block.get_text()
                code_block.string = f"`{code_text}`"
        
        # 处理预格式化文本
        for pre_block in content_elem.find_all('pre'):
            pre_text = pre_block.get_text()
            pre_block.string = f"\\n```\\n{pre_text}\\n```\\n"
        
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
            if alt or src:
                img.string = f"![{alt}]({src})"
        
        # 获取文本内容
        text = content_elem.get_text(separator='\\n', strip=True)
        
        # 清理多余的空行
        lines = [line.strip() for line in text.split('\\n') if line.strip()]
        
        return '\\n\\n'.join(lines)
    
    def extract_detailed_metadata(self, soup: BeautifulSoup) -> Dict:
        """提取详细元数据"""
        metadata = {}
        
        # 提取外部链接
        external_links = []
        for link in soup.find_all('a', href=True):
            href = link.get('href')
            if href and not href.startswith('#') and 'research.google' not in href:
                link_type = 'other'
                if 'arxiv.org' in href or 'paper' in href.lower():
                    link_type = 'paper'
                elif 'github.com' in href or 'code' in href.lower():
                    link_type = 'code'
                elif 'demo' in href.lower() or 'colab' in href.lower():
                    link_type = 'demo'
                
                external_links.append({
                    'url': href,
                    'text': link.get_text(strip=True),
                    'type': link_type
                })
        
        metadata['external_links'] = external_links[:20]  # 限制数量
        
        return metadata
    
    def extract_images(self, soup: BeautifulSoup, article_id: str) -> List[Dict]:
        """提取文章图片"""
        images = []
        
        # 查找文章中的图片
        img_tags = soup.find_all('img')
        
        for i, img in enumerate(img_tags):
            src = img.get('src')
            if src:
                # 处理相对URL
                if src.startswith('//'):
                    src = 'https:' + src
                elif src.startswith('/'):
                    src = urljoin(self.base_url, src)
                
                # 跳过很小的图片（可能是图标）
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
                    'height': height,
                    'local_path': ''  # 暂时为空，后续可实现图片下载
                }
                
                images.append(image_info)
        
        return images
    
    def analyze_technical_content(self, content: str) -> Dict:
        """分析技术内容"""
        if not content:
            return {}
        
        analysis = {}
        
        # 技术关键词检测
        tech_keywords = {
            'machine_learning': ['machine learning', 'ML', 'supervised learning', 'unsupervised learning'],
            'deep_learning': ['deep learning', 'neural network', 'CNN', 'RNN', 'LSTM', 'transformer'],
            'nlp': ['natural language processing', 'NLP', 'language model', 'BERT', 'GPT'],
            'computer_vision': ['computer vision', 'image recognition', 'object detection', 'segmentation'],
            'ai_research': ['artificial intelligence', 'AI', 'research', 'algorithm'],
            'tensorflow': ['TensorFlow', 'TF', 'Keras', 'TensorBoard'],
            'research': ['research', 'paper', 'study', 'experiment', 'dataset'],
            'product': ['product', 'release', 'feature', 'update', 'announcement']
        }
        
        content_lower = content.lower()
        
        for category, keywords in tech_keywords.items():
            count = sum(content_lower.count(keyword.lower()) for keyword in keywords)
            analysis[f'{category}_mentions'] = count
        
        # 确定主要技术领域
        if analysis:
            max_category = max(analysis.items(), key=lambda x: x[1])
            analysis['primary_tech_area'] = max_category[0].replace('_mentions', '')
        else:
            analysis['primary_tech_area'] = 'research'
        
        # 计算技术深度分数
        technical_indicators = [
            'algorithm', 'model', 'training', 'accuracy', 'performance',
            'dataset', 'benchmark', 'evaluation', 'architecture', 'optimization'
        ]
        
        tech_depth_score = sum(content_lower.count(indicator) for indicator in technical_indicators)
        analysis['technical_depth_score'] = min(tech_depth_score / 5, 10)  # 归一化到0-10
        
        # 检测是否包含代码
        code_indicators = ['```', 'import ', 'def ', 'class ', 'function', 'code', '`']
        analysis['contains_code'] = any(indicator in content for indicator in code_indicators)
        
        # 检测是否包含数学公式
        math_indicators = ['equation', 'formula', '∑', '∫', '∂', 'matrix', '$']
        analysis['contains_math'] = any(indicator in content for indicator in math_indicators)
        
        # 提取关键词
        keywords = []
        for category, kws in tech_keywords.items():
            for kw in kws:
                if kw.lower() in content_lower:
                    keywords.append(kw)
        
        analysis['keywords'] = list(set(keywords))[:10]  # 去重并限制数量
        
        return analysis
    
    def calculate_quality_score(self, article: Dict) -> float:
        """计算文章质量分数"""
        score = 7.0  # Google Research基础分数
        
        # 技术深度加分
        tech_analysis = article.get('technical_analysis', {})
        tech_depth = tech_analysis.get('technical_depth_score', 0)
        score += min(tech_depth * 0.3, 2.0)
        
        # 内容长度加分
        word_count = article.get('word_count', 0)
        if word_count > 2000:
            score += 1.5
        elif word_count > 1000:
            score += 1.0
        elif word_count > 500:
            score += 0.5
        
        # 包含代码或数学公式加分
        if tech_analysis.get('contains_code'):
            score += 0.5
        if tech_analysis.get('contains_math'):
            score += 0.3
        
        # 图片丰富度
        images = article.get('images', [])
        if len(images) > 5:
            score += 0.7
        elif len(images) > 2:
            score += 0.3
        
        # 外部链接丰富度
        external_links = article.get('external_links', [])
        paper_links = [link for link in external_links if link.get('type') == 'paper']
        code_links = [link for link in external_links if link.get('type') == 'code']
        
        if paper_links:
            score += 0.5
        if code_links:
            score += 0.3
        
        return min(score, 10.0)
    
    def generate_article_id(self, article: Dict) -> str:
        """生成文章唯一ID"""
        # 从发布日期获取日期部分
        try:
            pub_date = datetime.fromisoformat(article['publish_date'].replace('Z', '+00:00'))
            date_str = pub_date.strftime('%Y%m%d')
        except:
            date_str = datetime.now().strftime('%Y%m%d')
        
        # 使用标题和URL生成哈希
        content = f"{article.get('title', '')}{article.get('url', '')}"
        hash_part = hashlib.md5(content.encode('utf-8')).hexdigest()[:8]
        
        return f"google_ai_{date_str}_{hash_part}"
    
    def is_article_exists(self, article_id: str) -> bool:
        """检查文章是否已存在"""
        for article in self.article_index.get('articles', []):
            if article.get('article_id') == article_id:
                return True
        return False
    
    def save_article(self, article: Dict) -> bool:
        """保存文章到本地"""
        try:
            # 获取日期信息
            pub_date = datetime.fromisoformat(article['publish_date'].replace('Z', '+00:00'))
            year = pub_date.strftime('%Y')
            month = pub_date.strftime('%m')
            
            # 创建年月目录
            article_dir = os.path.join(self.data_path, 'articles', year, month)
            os.makedirs(article_dir, exist_ok=True)
            
            article_id = article['article_id']
            
            # 保存JSON文件
            json_file = os.path.join(article_dir, f"{article_id}.json")
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(article, f, indent=2, ensure_ascii=False)
            
            # 保存Markdown文件
            md_file = os.path.join(article_dir, f"{article_id}.md")
            self.save_article_as_markdown(article, md_file)
            
            # 更新索引
            self.update_article_index(article, f"data/articles/{year}/{month}/{article_id}.json")
            
            self.logger.info(f"文章已保存: {article['title']}")
            return True
            
        except Exception as e:
            self.logger.error(f"保存文章失败: {e}")
            return False
    
    def save_article_as_markdown(self, article: Dict, file_path: str):
        """将文章保存为Markdown格式"""
        md_content = f"""---
title: "{article.get('title', '')}"
author: "{article.get('author', '')}"
date: "{article.get('publish_date', '').split('T')[0]}"
source: "{article.get('source', '')}"
url: "{article.get('url', '')}"
categories: {json.dumps(article.get('categories', []))}
tags: {json.dumps(article.get('technical_analysis', {}).get('keywords', []))}
quality_score: {article.get('quality_score', 0)}
---

# {article.get('title', '')}

**作者**: {article.get('author', '')}  
**发布时间**: {article.get('publish_date', '').split('T')[0]}  
**来源**: [{article.get('source', '')}]({article.get('url', '')})  
**分类**: {', '.join(article.get('categories', []))}  

## 摘要
{article.get('summary', '')}

## 正文
{article.get('content', '')}

## 相关链接
"""
        
        # 添加外部链接
        external_links = article.get('external_links', [])
        if external_links:
            for link in external_links:
                link_type = link.get('type', 'other')
                emoji = {'paper': '📄', 'code': '💻', 'demo': '🎮'}.get(link_type, '🔗')
                md_content += f"- {emoji} [{link.get('text', 'Link')}]({link.get('url', '')})\n"
        else:
            md_content += "暂无相关链接\n"
        
        # 添加技术分析
        tech_analysis = article.get('technical_analysis', {})
        md_content += f"""
## 技术分析
- **主要技术领域**: {tech_analysis.get('primary_tech_area', 'N/A')}
- **技术深度**: {tech_analysis.get('technical_depth_score', 0):.1f}/10
- **包含代码**: {'是' if tech_analysis.get('contains_code') else '否'}
- **包含数学公式**: {'是' if tech_analysis.get('contains_math') else '否'}
- **关键词**: {', '.join(tech_analysis.get('keywords', []))}
"""
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(md_content)
    
    def update_article_index(self, article: Dict, file_path: str):
        """更新文章索引"""
        # 添加到文章列表
        article_summary = {
            'article_id': article['article_id'],
            'title': article['title'],
            'date': article['publish_date'].split('T')[0],
            'categories': article.get('categories', []),
            'quality_score': article.get('quality_score', 0),
            'file_path': file_path
        }
        
        self.article_index['articles'].append(article_summary)
        self.article_index['total_articles'] = len(self.article_index['articles'])
        
        # 更新分类统计
        for category in article.get('categories', []):
            if category in self.article_index['categories']:
                self.article_index['categories'][category] += 1
            else:
                self.article_index['categories'][category] = 1
        
        # 更新月度统计
        month_key = article['publish_date'][:7]  # YYYY-MM
        if month_key in self.article_index['monthly_stats']:
            self.article_index['monthly_stats'][month_key] += 1
        else:
            self.article_index['monthly_stats'][month_key] = 1
    
    def crawl_latest_articles(self, max_articles: int = 20) -> List[Dict]:
        """爬取最新文章"""
        self.logger.info("开始爬取最新文章")
        
        # 获取RSS订阅
        feed = self.get_rss_feed()
        if not feed:
            self.logger.error("无法获取RSS订阅")
            return []
        
        # 解析RSS条目
        articles = self.parse_rss_entries(feed, max_articles)
        self.logger.info(f"发现{len(articles)}篇新文章")
        
        # 获取详细内容并保存
        saved_articles = []
        for article in articles:
            try:
                # 获取详细内容
                detailed_article = self.get_article_details(article)
                
                # 保存文章
                if self.save_article(detailed_article):
                    saved_articles.append(detailed_article)
                
                # 添加延迟避免过于频繁的请求
                time.sleep(2)
                
            except Exception as e:
                self.logger.error(f"处理文章失败: {e}")
                continue
        
        # 保存更新的索引
        self.save_article_index()
        
        self.logger.info(f"成功保存{len(saved_articles)}篇文章")
        return saved_articles

def main():
    """主函数"""
    spider = GoogleAIBlogSpider()
    
    # 爬取最新文章
    articles = spider.crawl_latest_articles(max_articles=10)
    
    print(f"成功爬取并保存了 {len(articles)} 篇文章")
    
    # 打印文章列表
    for article in articles:
        print(f"- {article['title']} (质量分数: {article.get('quality_score', 0):.1f})")

if __name__ == "__main__":
    main()