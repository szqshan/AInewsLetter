#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强版 arXiv 爬虫 - 支持每日更新和分类爬取
基于原始 ArxivCrawler 扩展，增加多种爬取策略
"""

import asyncio
import aiohttp
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Union
import os
from pathlib import Path
import logging

from .arxiv_crawler import ArxivCrawler
from ..utils.file_utils import ensure_directory, save_json


class EnhancedArxivCrawler(ArxivCrawler):
    """增强版 arXiv 爬虫"""
    
    def __init__(self, config: Dict[str, Any]):
        """初始化增强版爬虫
        
        Args:
            config: 配置字典
        """
        super().__init__(config)
        
        self.crawl_strategies = config.get("crawl_strategies", {})
        self.logger = logging.getLogger(__name__)
        
        # AI相关分类配置
        self.ai_categories = self.crawler_config.get("ai_categories", {
            "core_ai": ["cs.AI", "cs.LG", "cs.CL", "cs.CV", "cs.NE"],
            "related_ai": ["cs.IR", "cs.RO", "cs.MA", "cs.CR", "cs.HC"],
            "interdisciplinary": ["stat.ML", "q-bio.QM", "physics.comp-ph", "eess.AS", "eess.IV"]
        })
        
        # 热门关键词
        self.trending_keywords = self.crawler_config.get("trending_keywords", [
            "transformer", "diffusion", "LLM", "large language model",
            "multimodal", "RLHF", "in-context learning", "few-shot"
        ])
    
    async def crawl_daily_new_papers(self, days_back: int = 1, 
                                   categories: List[str] = None) -> Dict[str, List]:
        """爬取最近几天的新论文
        
        Args:
            days_back: 回溯天数
            categories: 指定分类列表，为空则使用所有AI分类
            
        Returns:
            按分类组织的论文字典
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        self.logger.info(f"开始爬取 {start_date.strftime('%Y-%m-%d')} 到 {end_date.strftime('%Y-%m-%d')} 的新论文")
        print(f"🚀 开始爬取 {start_date.strftime('%Y-%m-%d')} 到 {end_date.strftime('%Y-%m-%d')} 的新论文")
        
        # 确定要爬取的分类
        if categories:
            target_categories = {"specified": categories}
        else:
            target_categories = self.ai_categories
        
        all_papers = {}
        total_papers = 0
        
        # 遍历所有目标分类
        for category_group, categories_list in target_categories.items():
            print(f"\n📂 处理分类组: {category_group}")
            all_papers[category_group] = []
            
            for category in categories_list:
                papers = await self._crawl_category_by_date(
                    category, start_date, end_date
                )
                all_papers[category_group].extend(papers)
                total_papers += len(papers)
                print(f"   ✅ {category}: {len(papers)} 篇论文")
                
                # 避免请求过于频繁
                await asyncio.sleep(self.request_delay)
        
        print(f"🎉 每日爬取完成！总计获取 {total_papers} 篇论文")
        self.logger.info(f"每日爬取完成，总计: {total_papers} 篇论文")
        
        return all_papers
    
    async def _crawl_category_by_date(self, category: str, start_date: datetime, 
                                     end_date: datetime) -> List[Dict]:
        """按分类和日期范围爬取论文
        
        Args:
            category: arXiv分类代码
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            论文信息列表
        """
        # 构建日期范围查询
        start_str = start_date.strftime("%Y%m%d")
        end_str = end_date.strftime("%Y%m%d")
        
        query = f"cat:{category} AND submittedDate:[{start_str}* TO {end_str}*]"
        
        # 分页获取所有结果
        all_papers = []
        start = 0
        max_results = 200  # 每次最多200篇
        
        strategy_config = self.crawl_strategies.get("daily_new", {})
        max_total = strategy_config.get("max_results", 500)
        
        while len(all_papers) < max_total:
            current_batch_size = min(max_results, max_total - len(all_papers))
            
            papers = await self.search_papers(
                query=query,
                max_results=current_batch_size,
                start=start
            )
            
            if not papers:
                break
                
            all_papers.extend(papers)
            
            # 如果返回的结果少于请求数量，说明已经到底了
            if len(papers) < current_batch_size:
                break
                
            start += current_batch_size
            await asyncio.sleep(1)  # 避免请求过快
        
        return all_papers[:max_total]  # 确保不超过限制
    
    async def crawl_by_categories(self, categories: List[str] = None, 
                                 max_per_category: int = 1000) -> Dict[str, List]:
        """按分类爬取论文
        
        Args:
            categories: 要爬取的分类列表
            max_per_category: 每个分类最大论文数
            
        Returns:
            按分类组织的论文字典
        """
        if not categories:
            # 默认爬取所有AI相关分类
            categories = []
            for cat_list in self.ai_categories.values():
                categories.extend(cat_list)
        
        print(f"🎯 开始按分类爬取论文，共 {len(categories)} 个分类")
        self.logger.info(f"开始按分类爬取，目标分类: {categories}")
        
        results = {}
        total_papers = 0
        
        for category in categories:
            print(f"\n📊 爬取分类: {category}")
            
            papers = await self._crawl_category_full(category, max_per_category)
            results[category] = papers
            total_papers += len(papers)
            
            print(f"   ✅ 完成: {len(papers)} 篇论文")
            await asyncio.sleep(self.request_delay)  # 分类间延迟
        
        print(f"🎉 分类爬取完成！总计获取 {total_papers} 篇论文")
        self.logger.info(f"分类爬取完成，总计: {total_papers} 篇论文")
        
        return results
    
    async def crawl_and_save_by_categories(self, categories: List[str] = None, 
                                          max_per_category: int = 1000,
                                          output_base_dir: str = None,
                                          generate_folders: bool = True) -> Dict[str, Any]:
        """按分类爬取论文并保存（支持生成文件夹结构）
        
        Args:
            categories: 要爬取的分类列表
            max_per_category: 每个分类最大论文数
            output_base_dir: 输出基础目录
            generate_folders: 是否生成完整的文件夹结构
            
        Returns:
            爬取结果统计
        """
        if not output_base_dir:
            output_base_dir = self.output_dir
        
        # 创建分类输出目录
        category_dir = os.path.join(output_base_dir, "category")
        ensure_directory(category_dir)
        
        if generate_folders:
            articles_dir = os.path.join(output_base_dir, "articles")
            ensure_directory(articles_dir)
        
        # 爬取论文
        papers_by_category = await self.crawl_by_categories(
            categories=categories, 
            max_per_category=max_per_category
        )
        
        # 合并所有论文
        all_papers = []
        for papers in papers_by_category.values():
            all_papers.extend(papers)
        
        # 生成文件夹结构（如果启用）
        if generate_folders and all_papers:
            print(f"\n📁 开始生成 {len(all_papers)} 篇论文的文件夹结构...")
            await self._generate_paper_folders(all_papers, articles_dir)
        
        # 保存JSON数据
        await self._save_category_results(papers_by_category, all_papers, category_dir)
        
        # 统计结果
        total_papers = len(all_papers)
        
        result = {
            "success": True,
            "total_papers": total_papers,
            "categories": list(papers_by_category.keys()),
            "output_dir": category_dir,
            "articles_dir": articles_dir if generate_folders else None,
            "folder_structure_generated": generate_folders
        }
        
        self.logger.info(f"分类爬取保存完成: {result}")
        return result
    
    async def _generate_paper_folders(self, papers: List[Dict], articles_dir: str) -> None:
        """为论文列表生成完整的文件夹结构
        
        Args:
            papers: 论文列表
            articles_dir: 文章目录
        """
        semaphore = asyncio.Semaphore(5)  # 限制并发数
        tasks = []
        
        for paper in papers:
            task = self._generate_single_paper_folder(semaphore, paper, articles_dir)
            tasks.append(task)
        
        # 等待所有任务完成
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        successful = sum(1 for r in results if not isinstance(r, Exception))
        failed = len(results) - successful
        
        print(f"📁 文件夹生成完成: 成功 {successful}, 失败 {failed}")
    
    async def _generate_single_paper_folder(self, semaphore: asyncio.Semaphore,
                                           paper: Dict, articles_dir: str) -> Dict:
        """为单篇论文生成文件夹结构"""
        async with semaphore:
            return await self._create_enhanced_paper_folder(paper, articles_dir)
    
    async def _create_enhanced_paper_folder(self, paper: Dict, articles_dir: str) -> Dict:
        """创建增强的论文文件夹结构
        
        Args:
            paper: 论文数据
            articles_dir: 文章目录
            
        Returns:
            处理后的论文数据
        """
        from ..utils.file_utils import safe_filename, save_json
        
        arxiv_id = paper.get('arxiv_id', 'unknown')
        title = paper.get('title', 'Unknown Title')
        
        # 创建论文目录
        safe_title = safe_filename(title, max_length=50)
        paper_dir_name = f"{arxiv_id}_{safe_title}"
        paper_dir = os.path.join(articles_dir, paper_dir_name)
        ensure_directory(paper_dir)
        
        # 创建子目录
        images_dir = os.path.join(paper_dir, "images")
        ensure_directory(images_dir)
        
        # 构建增强的数据模型
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
            "local_pdf_path": "",
            "content_hash": "",
            "processed_date": datetime.now().isoformat(),
            "wordcount": len(paper.get('abstract', '').split()),
            "local_images": [],
            "oss_urls": {},
            "elasticsearch_indexed": False
        }
        
        # 创建增强的文件结构
        await self._create_enhanced_files(processed_paper, paper_dir)
        
        print(f"✅ 文件夹创建完成: {arxiv_id}")
        return processed_paper
    
    async def _create_enhanced_files(self, paper: Dict, paper_dir: str) -> None:
        """创建增强的文件结构
        
        Args:
            paper: 论文数据
            paper_dir: 论文目录
        """
        from ..utils.file_utils import save_json
        
        # 1. 创建主content.md文件
        content_md_path = os.path.join(paper_dir, "content.md")
        await self._create_enhanced_content_md(paper, content_md_path)
        
        # 2. 创建详细metadata.json
        metadata_path = os.path.join(paper_dir, "metadata.json")
        save_json(paper, metadata_path)
        
        # 3. 创建单独的摘要文件
        abstract_path = os.path.join(paper_dir, "abstract.txt")
        with open(abstract_path, 'w', encoding='utf-8') as f:
            f.write(paper.get('abstract', ''))
        
        # 4. 创建作者信息文件
        authors_data = {
            "authors": paper.get('authors', []),
            "author_count": len(paper.get('authors', [])),
            "first_author": paper.get('authors', [''])[0] if paper.get('authors') else '',
            "last_author": paper.get('authors', [''])[-1] if paper.get('authors') else ''
        }
        authors_path = os.path.join(paper_dir, "authors.json")
        save_json(authors_data, authors_path)
        
        # 5. 创建分类标签文件
        categories_data = {
            "categories": paper.get('categories', []),
            "primary_category": paper.get('primary_category', ''),
            "category_count": len(paper.get('categories', [])),
            "is_ai_related": any(cat.startswith(('cs.AI', 'cs.LG', 'cs.CL', 'cs.CV', 'cs.NE')) 
                               for cat in paper.get('categories', []))
        }
        categories_path = os.path.join(paper_dir, "categories.json")
        save_json(categories_data, categories_path)
        
        # 6. 创建链接文件
        links_data = {
            "arxiv_url": paper.get('url', ''),
            "pdf_url": paper.get('pdf_url', ''),
            "arxiv_id": paper.get('id', ''),
            "doi": "",  # 可以后续扩展
            "external_links": []  # 可以后续扩展
        }
        links_path = os.path.join(paper_dir, "links.json")
        save_json(links_data, links_path)
    
    async def _create_enhanced_content_md(self, paper: Dict, content_path: str) -> None:
        """创建增强的content.md文件
        
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

- **arXiv页面**: [{paper['url']}]({paper['url']})
- **PDF下载**: [{paper['pdf_url']}]({paper['pdf_url']})

## 摘要

{paper['abstract']}

## 处理信息

- **处理时间**: {paper['processed_date']}
- **字数统计**: {paper['wordcount']}
- **本地PDF**: {paper['local_pdf_path'] or '未下载'}
- **内容哈希**: {paper['content_hash'] or '无'}
"""
        
        with open(content_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    async def _save_category_results(self, papers_by_category: Dict[str, List], 
                                    all_papers: List[Dict], output_dir: str) -> None:
        """保存分类爬取结果
        
        Args:
            papers_by_category: 按分类组织的论文数据
            all_papers: 所有论文列表
            output_dir: 输出目录
        """
        # 保存按分类组织的数据
        save_json(papers_by_category, os.path.join(output_dir, "papers_by_category.json"))
        
        # 保存所有论文的合并数据
        save_json(all_papers, os.path.join(output_dir, "all_papers.json"))
        
        # 保存统计信息
        stats = {
            "crawl_date": datetime.now().isoformat(),
            "total_papers": len(all_papers),
            "categories_stats": {
                category: len(papers) 
                for category, papers in papers_by_category.items()
            }
        }
        save_json(stats, os.path.join(output_dir, "category_stats.json"))
        
        print(f"📊 分类结果已保存到: {output_dir}")
    
    async def _crawl_category_full(self, category: str, max_results: int) -> List[Dict]:
        """全量爬取某个分类的论文
        
        Args:
            category: arXiv分类代码
            max_results: 最大结果数
            
        Returns:
            论文信息列表
        """
        query = f"cat:{category}"
        
        all_papers = []
        start = 0
        batch_size = 200
        
        while len(all_papers) < max_results:
            current_batch_size = min(batch_size, max_results - len(all_papers))
            
            papers = await self.search_papers(
                query=query,
                max_results=current_batch_size,
                start=start
            )
            
            if not papers:
                break
                
            all_papers.extend(papers)
            
            if len(papers) < current_batch_size:
                break
                
            start += current_batch_size
            await asyncio.sleep(1)
        
        return all_papers[:max_results]  # 确保不超过限制
    
    async def crawl_trending_keywords(self, keywords: List[str] = None, 
                                    days_back: int = 7) -> Dict[str, List]:
        """爬取热门关键词相关论文
        
        Args:
            keywords: 关键词列表，为空则使用默认热门关键词
            days_back: 回溯天数
            
        Returns:
            按关键词组织的论文字典
        """
        if not keywords:
            keywords = self.trending_keywords
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        start_str = start_date.strftime("%Y%m%d")
        end_str = end_date.strftime("%Y%m%d")
        
        print(f"🔥 爬取热门关键词论文，时间范围: {start_str} - {end_str}")
        print(f"🎯 目标关键词: {', '.join(keywords)}")
        self.logger.info(f"开始关键词爬取，关键词: {keywords}, 时间范围: {start_str}-{end_str}")
        
        results = {}
        total_papers = 0
        
        # 构建核心AI分类查询条件
        core_categories = " OR ".join([f"cat:{cat}" for cat in self.ai_categories["core_ai"]])
        
        for keyword in keywords:
            print(f"\n🔍 搜索关键词: {keyword}")
            
            # 在AI相关分类中搜索关键词
            query = f"({core_categories}) AND all:{keyword} AND submittedDate:[{start_str}* TO {end_str}*]"
            
            strategy_config = self.crawl_strategies.get("trending_weekly", {})
            max_results = strategy_config.get("max_results", 500)
            
            papers = await self.search_papers(
                query=query,
                max_results=max_results
            )
            
            results[keyword] = papers
            total_papers += len(papers)
            print(f"   ✅ 找到 {len(papers)} 篇相关论文")
            await asyncio.sleep(self.request_delay)
        
        print(f"🎉 关键词爬取完成！总计获取 {total_papers} 篇论文")
        self.logger.info(f"关键词爬取完成，总计: {total_papers} 篇论文")
        
        return results
    
    async def crawl_and_save_daily(self, days_back: int = 1, 
                                  categories: List[str] = None,
                                  output_base_dir: str = None) -> Dict[str, Any]:
        """爬取每日新论文并保存到指定目录
        
        Args:
            days_back: 回溯天数
            categories: 指定分类列表
            output_base_dir: 输出基础目录
            
        Returns:
            爬取结果统计
        """
        if not output_base_dir:
            output_base_dir = self.output_dir
        
        # 创建每日输出目录
        date_str = datetime.now().strftime("%Y-%m-%d")
        daily_dir = os.path.join(output_base_dir, "daily", date_str)
        ensure_directory(daily_dir)
        
        # 爬取论文
        papers_by_category = await self.crawl_daily_new_papers(
            days_back=days_back, 
            categories=categories
        )
        
        # 保存结果
        await self._save_daily_results(papers_by_category, daily_dir)
        
        # 统计结果
        total_papers = sum(len(papers) for papers in papers_by_category.values())
        
        result = {
            "success": True,
            "date": date_str,
            "total_papers": total_papers,
            "categories": list(papers_by_category.keys()),
            "output_dir": daily_dir
        }
        
        self.logger.info(f"每日爬取保存完成: {result}")
        return result
    
    async def crawl_and_save_weekly(self, keywords: List[str] = None,
                                   days_back: int = 7,
                                   output_base_dir: str = None) -> Dict[str, Any]:
        """爬取每周热门关键词论文并保存
        
        Args:
            keywords: 关键词列表
            days_back: 回溯天数
            output_base_dir: 输出基础目录
            
        Returns:
            爬取结果统计
        """
        if not output_base_dir:
            output_base_dir = self.output_dir
        
        # 创建每周输出目录
        week_str = datetime.now().strftime("%Y-W%U")
        weekly_dir = os.path.join(output_base_dir, "weekly", week_str)
        ensure_directory(weekly_dir)
        
        # 爬取论文
        papers_by_keyword = await self.crawl_trending_keywords(
            keywords=keywords,
            days_back=days_back
        )
        
        # 保存结果
        await self._save_weekly_results(papers_by_keyword, weekly_dir)
        
        # 统计结果
        total_papers = sum(len(papers) for papers in papers_by_keyword.values())
        
        result = {
            "success": True,
            "week": week_str,
            "total_papers": total_papers,
            "keywords": list(papers_by_keyword.keys()),
            "output_dir": weekly_dir
        }
        
        self.logger.info(f"每周爬取保存完成: {result}")
        return result
    
    async def _save_daily_results(self, papers_by_category: Dict[str, List], 
                                 output_dir: str) -> None:
        """保存每日爬取结果
        
        Args:
            papers_by_category: 按分类组织的论文数据
            output_dir: 输出目录
        """
        # 保存原始数据
        save_json(papers_by_category, os.path.join(output_dir, "daily_papers_by_category.json"))
        
        # 合并所有论文
        all_papers = []
        for papers in papers_by_category.values():
            all_papers.extend(papers)
        
        # 保存合并后的数据
        save_json(all_papers, os.path.join(output_dir, "daily_papers_all.json"))
        
        # 保存统计信息
        stats = {
            "crawl_date": datetime.now().isoformat(),
            "total_papers": len(all_papers),
            "categories_stats": {
                category: len(papers) 
                for category, papers in papers_by_category.items()
            },
            "date_range": self._get_date_range(all_papers) if all_papers else {}
        }
        save_json(stats, os.path.join(output_dir, "daily_stats.json"))
        
        print(f"📊 每日结果已保存到: {output_dir}")
    
    async def _save_weekly_results(self, papers_by_keyword: Dict[str, List], 
                                  output_dir: str) -> None:
        """保存每周爬取结果
        
        Args:
            papers_by_keyword: 按关键词组织的论文数据
            output_dir: 输出目录
        """
        # 保存原始数据
        save_json(papers_by_keyword, os.path.join(output_dir, "weekly_papers_by_keyword.json"))
        
        # 合并所有论文并去重
        all_papers = []
        seen_ids = set()
        
        for papers in papers_by_keyword.values():
            for paper in papers:
                arxiv_id = paper.get('arxiv_id')
                if arxiv_id and arxiv_id not in seen_ids:
                    all_papers.append(paper)
                    seen_ids.add(arxiv_id)
        
        # 保存去重后的数据
        save_json(all_papers, os.path.join(output_dir, "weekly_papers_deduplicated.json"))
        
        # 保存统计信息
        stats = {
            "crawl_date": datetime.now().isoformat(),
            "total_papers": len(all_papers),
            "total_papers_with_duplicates": sum(len(papers) for papers in papers_by_keyword.values()),
            "keywords_stats": {
                keyword: len(papers) 
                for keyword, papers in papers_by_keyword.items()
            },
            "date_range": self._get_date_range(all_papers) if all_papers else {}
        }
        save_json(stats, os.path.join(output_dir, "weekly_stats.json"))
        
        print(f"📊 每周结果已保存到: {output_dir}")
    
    def _get_date_range(self, papers: List[Dict]) -> Dict[str, str]:
        """获取论文的日期范围
        
        Args:
            papers: 论文列表
            
        Returns:
            包含最早和最晚日期的字典
        """
        if not papers:
            return {}
        
        dates = [
            paper.get('published', '') 
            for paper in papers 
            if paper.get('published')
        ]
        
        if not dates:
            return {}
        
        return {
            "earliest": min(dates),
            "latest": max(dates)
        }
    
    def get_all_ai_categories(self) -> List[str]:
        """获取所有AI相关分类
        
        Returns:
            所有AI分类的列表
        """
        all_categories = []
        for cat_list in self.ai_categories.values():
            all_categories.extend(cat_list)
        return list(set(all_categories))  # 去重
    
    def get_category_groups(self) -> Dict[str, List[str]]:
        """获取分类组配置
        
        Returns:
            分类组字典
        """
        return self.ai_categories.copy()
