#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
arXiv论文爬虫模块
重构自原始spider.py，采用新的数据模型和存储架构
"""

import asyncio
import aiohttp
import json
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import List, Dict, Optional, Any
import os
from pathlib import Path
import hashlib

from ..utils.file_utils import (
    ensure_directory, safe_filename, calculate_file_hash, 
    save_json, get_file_size_mb, parse_size_string
)


class ArxivCrawler:
    """arXiv论文爬虫类 - 重构版本"""
    
    def __init__(self, config: Dict[str, Any]):
        """初始化爬虫
        
        Args:
            config: 配置字典
        """
        self.config = config
        self.crawler_config = config.get("crawler", {})
        self.file_config = config.get("file_settings", {})
        
        self.base_url = self.crawler_config.get("base_url", "http://export.arxiv.org/api/query")
        self.output_dir = self.crawler_config.get("output_directory", "crawled_data")
        self.request_delay = self.crawler_config.get("request_delay", 1)
        self.max_retries = self.crawler_config.get("max_retries", 3)
        self.timeout = self.crawler_config.get("timeout", 30)
        self.enable_pdf_download = self.crawler_config.get("enable_pdf_download", True)
        self.max_concurrent = self.crawler_config.get("max_concurrent_papers", 3)
        
        # 文件大小限制
        pdf_max_size_str = self.file_config.get("pdf_max_size", "50MB")
        self.pdf_max_size = parse_size_string(pdf_max_size_str)
        
        self.session = None
        self.results = []
        
    async def __aenter__(self):
        """异步上下文管理器入口"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.timeout),
            connector=aiohttp.TCPConnector(limit=10)
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        if self.session:
            await self.session.close()
    
    def crawl(self, query: str, max_results: int, output_dir: str = None, 
              concurrent: int = None, download_pdf: bool = None) -> None:
        """爬取论文的同步入口
        
        Args:
            query: 搜索查询
            max_results: 最大结果数
            output_dir: 输出目录
            concurrent: 并发数
            download_pdf: 是否下载PDF
        """
        asyncio.run(self._crawl_async(
            query=query,
            max_results=max_results,
            output_dir=output_dir or self.output_dir,
            concurrent=concurrent or self.max_concurrent,
            download_pdf=download_pdf if download_pdf is not None else self.enable_pdf_download
        ))
    
    async def _crawl_async(self, query: str, max_results: int, output_dir: str,
                          concurrent: int, download_pdf: bool) -> None:
        """异步爬取论文
        
        Args:
            query: 搜索查询
            max_results: 最大结果数
            output_dir: 输出目录
            concurrent: 并发数
            download_pdf: 是否下载PDF
        """
        async with self:
            print(f"🚀 开始爬取arXiv论文: {query}")
            print(f"📊 最大结果数: {max_results}, 并发数: {concurrent}")
            print(f"📁 输出目录: {output_dir}")
            
            # 搜索论文
            papers = await self.search_papers(query, max_results)
            
            if not papers:
                print("❌ 没有找到论文")
                return
            
            print(f"✅ 找到 {len(papers)} 篇论文")
            
            # 创建输出目录
            articles_dir = os.path.join(output_dir, "articles")
            data_dir = os.path.join(output_dir, "data")
            ensure_directory(articles_dir)
            ensure_directory(data_dir)
            
            # 并发处理论文
            semaphore = asyncio.Semaphore(concurrent)
            tasks = []
            
            for paper in papers:
                task = self._process_paper_with_semaphore(
                    semaphore, paper, articles_dir, download_pdf
                )
                tasks.append(task)
            
            # 等待所有任务完成
            processed_papers = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 过滤成功处理的论文
            successful_papers = []
            for result in processed_papers:
                if isinstance(result, dict):
                    successful_papers.append(result)
                elif isinstance(result, Exception):
                    print(f"❌ 处理论文时出错: {result}")
            
            # 保存聚合数据
            await self._save_aggregated_data(successful_papers, data_dir)
            
            print(f"🎉 爬取完成！成功处理 {len(successful_papers)} 篇论文")
    
    async def _process_paper_with_semaphore(self, semaphore: asyncio.Semaphore, 
                                           paper: Dict, articles_dir: str, 
                                           download_pdf: bool) -> Dict:
        """使用信号量控制并发处理论文"""
        async with semaphore:
            return await self._process_single_paper(paper, articles_dir, download_pdf)
    
    async def _process_single_paper(self, paper: Dict, articles_dir: str, 
                                   download_pdf: bool) -> Dict:
        """处理单篇论文
        
        Args:
            paper: 论文数据
            articles_dir: 文章目录
            download_pdf: 是否下载PDF
            
        Returns:
            处理后的论文数据
        """
        arxiv_id = paper.get('arxiv_id', 'unknown')
        title = paper.get('title', 'Unknown Title')
        
        print(f"📄 处理论文: {arxiv_id} - {title[:50]}...")
        
        # 创建论文目录
        safe_title = safe_filename(title, max_length=50)
        paper_dir_name = f"{arxiv_id}_{safe_title}"
        paper_dir = os.path.join(articles_dir, paper_dir_name)
        ensure_directory(paper_dir)
        
        # 创建图片目录
        images_dir = os.path.join(paper_dir, "images")
        ensure_directory(images_dir)
        
        # 构建新的数据模型
        processed_paper = {
            "id": arxiv_id,
            "title": title,
            "abstract": paper.get('abstract', ''),
            "authors": paper.get('authors', []),
            "published": paper.get('published', ''),
            "updated": paper.get('updated', ''),
            "categories": paper.get('categories', []),
            "primary_category": paper.get('primary_category', ''),
            "url": paper.get('url', ''),
            "pdf_url": paper.get('pdf_url', ''),

            "local_images": [],
            "oss_urls": {},
            "elasticsearch_indexed": False
        }
        
        # 下载PDF文件
        if download_pdf and paper.get('pdf_url'):
            pdf_path = await self._download_pdf_to_paper_dir(
                paper.get('pdf_url'), arxiv_id, paper_dir
            )
            if pdf_path:
                processed_paper["local_pdf_path"] = "paper.pdf"
                processed_paper["content_hash"] = calculate_file_hash(pdf_path)
        
        # 创建content.md文件
        content_md_path = os.path.join(paper_dir, "content.md")
        await self._create_content_md(processed_paper, content_md_path)
        
        # 保存metadata.json
        metadata_path = os.path.join(paper_dir, "metadata.json")
        save_json(processed_paper, metadata_path)
        
        print(f"✅ 完成处理: {arxiv_id}")
        return processed_paper
    
    async def _download_pdf_to_paper_dir(self, pdf_url: str, arxiv_id: str, 
                                        paper_dir: str) -> Optional[str]:
        """下载PDF到论文目录
        
        Args:
            pdf_url: PDF下载链接
            arxiv_id: arXiv ID
            paper_dir: 论文目录
            
        Returns:
            本地PDF文件路径
        """
        try:
            pdf_path = os.path.join(paper_dir, "paper.pdf")
            
            async with self.session.get(pdf_url) as response:
                if response.status == 200:
                    # 检查文件大小
                    content_length = response.headers.get('content-length')
                    if content_length and int(content_length) > self.pdf_max_size:
                        print(f"⚠️ PDF文件过大，跳过下载: {arxiv_id}")
                        return None
                    
                    pdf_content = await response.read()
                    
                    # 再次检查实际大小
                    if len(pdf_content) > self.pdf_max_size:
                        print(f"⚠️ PDF文件过大，跳过保存: {arxiv_id}")
                        return None
                    
                    with open(pdf_path, 'wb') as f:
                        f.write(pdf_content)
                    
                    print(f"📥 PDF下载成功: {arxiv_id} ({get_file_size_mb(pdf_path):.1f}MB)")
                    return pdf_path
                else:
                    print(f"❌ PDF下载失败: {arxiv_id}, 状态码: {response.status}")
                    return None
                    
        except Exception as e:
            print(f"❌ PDF下载异常: {arxiv_id}, 错误: {e}")
            return None
    
    async def _create_content_md(self, paper: Dict, content_path: str) -> None:
        """创建content.md文件
        
        Args:
            paper: 论文数据
            content_path: content.md文件路径
        """
        content = f"""# {paper['title']}

## 基本信息

- **arXiv ID**: {paper['id']}
- **发布日期**: {paper['published']}
- **更新日期**: {paper['updated']}
- **主要分类**: {paper['primary_category']}
- **所有分类**: {', '.join(paper['categories'])}
- **作者**: {', '.join(paper['authors'])}

## 链接

- **论文链接**: [{paper['url']}]({paper['url']})
- **PDF链接**: [{paper['pdf_url']}]({paper['pdf_url']})

## 摘要

{paper['abstract']}
"""
        
        with open(content_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    async def _save_aggregated_data(self, papers: List[Dict], data_dir: str) -> None:
        """保存聚合数据
        
        Args:
            papers: 论文列表
            data_dir: 数据目录
        """
        # 保存所有论文元数据
        metadata_path = os.path.join(data_dir, "papers_metadata.json")
        save_json(papers, metadata_path)
        
        # 保存处理后的完整数据
        processed_path = os.path.join(data_dir, "processed_papers.json")
        save_json(papers, processed_path)
        
        # 保存爬取统计
        stats = {
            "total_papers": len(papers),
            "crawl_date": datetime.now().isoformat(),
            "categories": list(set(cat for paper in papers for cat in paper.get('categories', []))),
            "date_range": {
                "earliest": min(paper.get('published', '') for paper in papers if paper.get('published')),
                "latest": max(paper.get('published', '') for paper in papers if paper.get('published'))
            }
        }
        stats_path = os.path.join(data_dir, "crawl_stats.json")
        save_json(stats, stats_path)
        
        print(f"📊 聚合数据已保存到: {data_dir}")
    
    async def search_papers(self, query: str = "cat:cs.AI", 
                           max_results: int = 10, start: int = 0) -> List[Dict]:
        """搜索arXiv论文
        
        Args:
            query: 搜索查询
            max_results: 最大结果数
            start: 起始位置
            
        Returns:
            论文信息列表
        """
        params = {
            'search_query': query,
            'start': start,
            'max_results': max_results,
            'sortBy': 'submittedDate',
            'sortOrder': 'descending'
        }
        
        print(f"🔍 搜索论文: {query}, 最大结果: {max_results}")
        
        for attempt in range(self.max_retries):
            try:
                async with self.session.get(self.base_url, params=params) as response:
                    if response.status == 200:
                        content = await response.text()
                        papers = self._parse_xml_response(content)
                        print(f"✅ 搜索成功，找到 {len(papers)} 篇论文")
                        return papers
                    else:
                        print(f"❌ 搜索失败，状态码: {response.status}")
                        
            except Exception as e:
                print(f"❌ 搜索异常 (尝试 {attempt + 1}/{self.max_retries}): {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.request_delay)
        
        return []
    
    def _parse_xml_response(self, xml_content: str) -> List[Dict]:
        """解析arXiv API返回的XML响应
        
        Args:
            xml_content: XML响应内容
            
        Returns:
            解析后的论文信息列表
        """
        papers = []
        
        try:
            root = ET.fromstring(xml_content)
            
            namespaces = {
                'atom': 'http://www.w3.org/2005/Atom',
                'arxiv': 'http://arxiv.org/schemas/atom'
            }
            
            entries = root.findall('atom:entry', namespaces)
            
            for entry in entries:
                paper = {}
                
                # 标题
                title_elem = entry.find('atom:title', namespaces)
                paper['title'] = title_elem.text.strip().replace('\n', ' ') if title_elem is not None else "未知标题"
                
                # arXiv ID
                id_elem = entry.find('atom:id', namespaces)
                if id_elem is not None:
                    arxiv_id = id_elem.text.split('/')[-1]
                    paper['arxiv_id'] = arxiv_id
                    paper['url'] = f"https://arxiv.org/abs/{arxiv_id}"
                    paper['pdf_url'] = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
                
                # 摘要
                summary_elem = entry.find('atom:summary', namespaces)
                paper['abstract'] = summary_elem.text.strip().replace('\n', ' ') if summary_elem is not None else "无摘要"
                
                # 作者
                authors = []
                author_elems = entry.findall('atom:author', namespaces)
                for author_elem in author_elems:
                    name_elem = author_elem.find('atom:name', namespaces)
                    if name_elem is not None:
                        authors.append(name_elem.text)
                paper['authors'] = authors
                
                # 发布时间
                published_elem = entry.find('atom:published', namespaces)
                if published_elem is not None:
                    paper['published'] = published_elem.text[:10]
                
                # 更新时间
                updated_elem = entry.find('atom:updated', namespaces)
                if updated_elem is not None:
                    paper['updated'] = updated_elem.text[:10]
                
                # 分类
                categories = []
                category_elems = entry.findall('atom:category', namespaces)
                for cat_elem in category_elems:
                    term = cat_elem.get('term')
                    if term:
                        categories.append(term)
                paper['categories'] = categories
                
                # 主要分类
                primary_cat_elem = entry.find('arxiv:primary_category', namespaces)
                if primary_cat_elem is not None:
                    paper['primary_category'] = primary_cat_elem.get('term')
                
                papers.append(paper)
                
        except ET.ParseError as e:
            print(f"❌ XML解析错误: {e}")
        except Exception as e:
            print(f"❌ 数据解析异常: {e}")
            
        return papers