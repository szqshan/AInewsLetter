#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
arXiv分类爬虫专用脚本
专门用于按分类批量爬取论文
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

# 添加src目录到Python路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

from arxiv_system.crawler.arxiv_crawler import ArxivCrawler
from arxiv_system.utils.file_utils import setup_logging, load_config, ensure_directory, save_json


class CategoryCrawler:
    """按分类爬取arXiv论文的专用爬虫"""
    
    def __init__(self, config_path: str = "config.json"):
        """初始化分类爬虫
        
        Args:
            config_path: 配置文件路径
        """
        self.config = load_config(config_path)
        self.logger = logging.getLogger(__name__)
        
    async def crawl_by_categories(self, categories: List[str], 
                                 max_per_category: int = 200,
                                 concurrent: int = 3,
                                 download_pdf: bool = True,
                                 output_base_dir: str = "crawled_data") -> Dict[str, Any]:
        """按分类爬取论文
        
        Args:
            categories: 分类列表，如 ["cs.AI", "cs.LG"]
            max_per_category: 每个分类最大爬取数量
            concurrent: 并发数量
            download_pdf: 是否下载PDF
            output_base_dir: 输出基础目录
            
        Returns:
            爬取结果统计
        """
        self.logger.info(f"🚀 开始按分类爬取arXiv论文")
        self.logger.info(f"📂 分类列表: {categories}")
        self.logger.info(f"📊 每分类最大数量: {max_per_category}")
        
        # 创建时间戳目录
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = os.path.join(output_base_dir, "by_category", timestamp)
        ensure_directory(output_dir)
        
        results = {
            "crawl_info": {
                "start_time": datetime.now().isoformat(),
                "categories": categories,
                "max_per_category": max_per_category,
                "concurrent": concurrent,
                "download_pdf": download_pdf
            },
            "category_results": {},
            "summary": {
                "total_papers": 0,
                "successful_categories": 0,
                "failed_categories": 0
            }
        }
        
        # 逐个分类爬取
        for i, category in enumerate(categories, 1):
            self.logger.info(f"📑 [{i}/{len(categories)}] 开始爬取分类: {category}")
            
            try:
                # 构建查询条件
                query = f"cat:{category}"
                
                # 创建分类专用目录
                category_dir = os.path.join(output_dir, category.replace(".", "_"))
                ensure_directory(category_dir)
                
                # 执行爬取
                async with ArxivCrawler(self.config) as crawler:
                    papers = await crawler.search_papers(
                        query=query, 
                        max_results=max_per_category
                    )
                    
                    if papers:
                        self.logger.info(f"✅ {category}: 找到 {len(papers)} 篇论文，开始处理...")
                        
                        # 处理论文数据
                        processed_papers = []
                        articles_dir = os.path.join(category_dir, "articles")
                        ensure_directory(articles_dir)
                        
                        for paper in papers:
                            try:
                                processed_paper = await crawler._process_single_paper(
                                    paper, articles_dir, download_pdf
                                )
                                processed_papers.append(processed_paper)
                            except Exception as e:
                                self.logger.error(f"❌ 处理论文失败: {paper.get('arxiv_id', 'unknown')} - {e}")
                        
                        # 保存分类数据
                        await self._save_category_data(processed_papers, category_dir, category)
                        
                        # 记录结果
                        results["category_results"][category] = {
                            "total_found": len(papers),
                            "successfully_processed": len(processed_papers),
                            "output_dir": category_dir,
                            "status": "success"
                        }
                        results["summary"]["total_papers"] += len(processed_papers)
                        results["summary"]["successful_categories"] += 1
                        
                        self.logger.info(f"🎉 {category}: 成功处理 {len(processed_papers)} 篇论文")
                    else:
                        self.logger.warning(f"⚠️ {category}: 未找到论文")
                        results["category_results"][category] = {
                            "total_found": 0,
                            "successfully_processed": 0,
                            "output_dir": category_dir,
                            "status": "no_papers"
                        }
                        
            except Exception as e:
                self.logger.error(f"❌ 分类 {category} 爬取失败: {e}")
                results["category_results"][category] = {
                    "error": str(e),
                    "status": "failed"
                }
                results["summary"]["failed_categories"] += 1
            
            # 分类间延迟，避免请求过频
            if i < len(categories):
                await asyncio.sleep(2)
        
        # 保存总体结果
        results["crawl_info"]["end_time"] = datetime.now().isoformat()
        results_file = os.path.join(output_dir, "crawl_results.json")
        save_json(results, results_file)
        
        # 生成简要报告
        self._generate_summary_report(results, output_dir)
        
        self.logger.info(f"🎊 分类爬取完成！")
        self.logger.info(f"📊 总计爬取: {results['summary']['total_papers']} 篇论文")
        self.logger.info(f"✅ 成功分类: {results['summary']['successful_categories']}/{len(categories)}")
        self.logger.info(f"📁 输出目录: {output_dir}")
        
        return results
    
    async def _save_category_data(self, papers: List[Dict], category_dir: str, category: str):
        """保存分类数据
        
        Args:
            papers: 论文数据列表
            category_dir: 分类目录
            category: 分类名称
        """
        # 保存论文列表
        papers_file = os.path.join(category_dir, f"{category.replace('.', '_')}_papers.json")
        save_json(papers, papers_file)
        
        # 生成分类统计
        stats = {
            "category": category,
            "total_papers": len(papers),
            "crawl_date": datetime.now().isoformat(),
            "authors": list(set(author for paper in papers for author in paper.get('authors', []))),
            "date_range": {
                "earliest": min(paper.get('published', '') for paper in papers if paper.get('published')),
                "latest": max(paper.get('published', '') for paper in papers if paper.get('published'))
            } if papers else {}
        }
        
        stats_file = os.path.join(category_dir, f"{category.replace('.', '_')}_stats.json")
        save_json(stats, stats_file)
    
    def _generate_summary_report(self, results: Dict, output_dir: str):
        """生成简要报告
        
        Args:
            results: 爬取结果
            output_dir: 输出目录
        """
        report_lines = [
            "# arXiv分类爬取报告",
            "",
            f"**爬取时间**: {results['crawl_info']['start_time']} - {results['crawl_info']['end_time']}",
            f"**总计论文**: {results['summary']['total_papers']} 篇",
            f"**成功分类**: {results['summary']['successful_categories']}/{len(results['crawl_info']['categories'])}",
            "",
            "## 分类详情",
            ""
        ]
        
        for category, result in results["category_results"].items():
            if result["status"] == "success":
                report_lines.append(f"- **{category}**: {result['successfully_processed']} 篇论文 ✅")
            elif result["status"] == "no_papers":
                report_lines.append(f"- **{category}**: 未找到论文 ⚠️")
            else:
                report_lines.append(f"- **{category}**: 爬取失败 ❌")
        
        report_content = "\n".join(report_lines)
        report_file = os.path.join(output_dir, "README.md")
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report_content)


async def main():
    """主函数"""
    # 设置日志
    setup_logging()
    
    # 定义要爬取的分类
    TARGET_CATEGORIES = [
        "cs.AI",   # 人工智能
        "cs.LG",   # 机器学习
        "cs.CL",   # 计算与语言
        "cs.CV",   # 计算机视觉
        "cs.NE"    # 神经和进化计算
    ]
    
    # 创建爬虫实例
    crawler = CategoryCrawler()
    
    # 执行分类爬取
    results = await crawler.crawl_by_categories(
        categories=TARGET_CATEGORIES,
        max_per_category=300,  # 每个分类最多300篇
        concurrent=3,          # 并发数
        download_pdf=True,     # 下载PDF
        output_base_dir="crawled_data"
    )
    
    print(f"\n🎉 爬取完成！共获取 {results['summary']['total_papers']} 篇论文")
    print(f"📁 数据保存在: crawled_data/by_category/")


if __name__ == "__main__":
    asyncio.run(main())
