#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
主控制脚本
统一管理所有爬虫的执行
"""

import os
import sys
import argparse
import asyncio
import subprocess
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from shared.config import PLATFORM_CONFIGS, ensure_directories
from shared.utils import save_json, generate_filename
from shared.quality_scorer import QualityScorer

class SpiderManager:
    """
    爬虫管理器
    统一管理所有平台的爬虫
    """
    
    def __init__(self):
        self.quality_scorer = QualityScorer()
        self.results = {
            "academic_papers": [],
            "ai_news": [],
            "ai_tools": []
        }
        
        # 确保目录结构存在
        ensure_directories()
    
    async def run_all_spiders(self, categories: List[str] = None):
        """
        运行所有爬虫
        
        Args:
            categories: 要运行的分类列表，None表示运行所有
        """
        print("Starting AI Content Aggregation Spider System!")
        print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        if not categories:
            categories = ["academic_papers", "ai_news", "ai_tools"]
        
        tasks = []
        
        if "academic_papers" in categories:
            tasks.append(self._run_academic_spiders())
        
        if "ai_news" in categories:
            tasks.append(self._run_news_spiders())
        
        if "ai_tools" in categories:
            tasks.append(self._run_tools_spiders())
        
        # 并发执行所有爬虫
        await asyncio.gather(*tasks)
        
        # 处理和保存结果
        await self._process_results()
        
        print("\nAll spider tasks completed!")
        print(f"End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    async def _run_academic_spiders(self):
        """
        运行学术论文爬虫
        """
        print("\nStarting academic papers crawling...")
        
        # arXiv爬虫
        try:
            sys.path.append(os.path.join(project_root, 'academic_papers', 'arxiv'))
            import subprocess
            result = subprocess.run([sys.executable, os.path.join(project_root, 'academic_papers', 'arxiv', 'spider.py')], 
                                  capture_output=True, text=True, cwd=project_root)
            if result.returncode == 0:
                print("Success: arXiv crawler completed")
            else:
                print(f"Error: arXiv crawler failed: {result.stderr}")
        except Exception as e:
            print(f"Error: arXiv crawler failed: {e}")
        
        # Google Scholar爬虫
        try:
            result = subprocess.run([sys.executable, os.path.join(project_root, 'academic_papers', 'google_scholar', 'spider.py')], 
                                  capture_output=True, text=True, cwd=project_root)
            if result.returncode == 0:
                print("Success: Google Scholar crawler completed")
            else:
                print(f"Error: Google Scholar crawler failed: {result.stderr}")
        except Exception as e:
            print(f"Error: Google Scholar crawler failed: {e}")
        
        # Papers with Code爬虫
        try:
            from academic_papers.papers_with_code.spider import PapersWithCodeSpider
            pwc_spider = PapersWithCodeSpider()
            pwc_results = await pwc_spider.crawl()
            self.results["academic_papers"].extend(pwc_results)
            print(f"Success: Papers with Code: Got {len(pwc_results)} papers")
        except ImportError:
            print("Warning: Papers with Code crawler module not found, skipping")
        except Exception as e:
            print(f"Error: Papers with Code crawler failed: {e}")
        
        # 可以继续添加其他学术平台爬虫...
    
    async def _run_news_spiders(self):
        """
        运行AI新闻爬虫
        """
        print("\nStarting AI news crawling...")
        
        # Hugging Face Daily Papers
        try:
            result = subprocess.run([sys.executable, os.path.join(project_root, 'ai_news', 'huggingface_daily', 'spider.py')], 
                                  capture_output=True, text=True, cwd=project_root)
            if result.returncode == 0:
                print("Success: Hugging Face crawler completed")
            else:
                print(f"Error: Hugging Face crawler failed: {result.stderr}")
        except Exception as e:
            print(f"Error: Hugging Face crawler failed: {e}")
        
        # 可以继续添加其他新闻平台爬虫...
    
    async def _run_tools_spiders(self):
        """
        运行AI工具爬虫
        """
        print("\nStarting AI tools crawling...")
        
        # GitHub Trending
        try:
            result = subprocess.run([sys.executable, os.path.join(project_root, 'ai_tools', 'github_trending', 'spider.py')], 
                                  capture_output=True, text=True, cwd=project_root)
            if result.returncode == 0:
                print("Success: GitHub Trending crawler completed")
            else:
                print(f"Error: GitHub Trending crawler failed: {result.stderr}")
        except Exception as e:
            print(f"Error: GitHub Trending crawler failed: {e}")
        
        # 可以继续添加其他工具平台爬虫...
    
    async def _process_results(self):
        """
        处理和保存爬取结果
        """
        print("\nStarting to process crawling results...")
        
        # 质量评估和排序
        for category, items in self.results.items():
            if not items:
                continue
            
            print(f"\nEvaluating quality for {category}...")
            
            for item in items:
                if category == "academic_papers":
                    scores = self.quality_scorer.score_paper(item)
                elif category == "ai_news":
                    scores = self.quality_scorer.score_news(item)
                elif category == "ai_tools":
                    scores = self.quality_scorer.score_tool(item)
                
                item["quality_scores"] = scores
            
            # 按质量分数排序
            items.sort(key=lambda x: x["quality_scores"]["total_score"], reverse=True)
            
            print(f"Success: {category}: Evaluated {len(items)} items")
        
        # 保存结果
        await self._save_results()
    
    async def _save_results(self):
        """
        保存爬取结果到文件
        """
        print("\nSaving results to files...")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        for category, items in self.results.items():
            if not items:
                continue
            
            # 保存JSON格式
            json_filename = f"{category}_{timestamp}.json"
            json_filepath = project_root / "data" / "processed" / json_filename
            save_json(items, str(json_filepath))
            
            # 保存Markdown格式
            md_content = self._generate_markdown_report(category, items)
            md_filename = f"{category}_{timestamp}.md"
            md_filepath = project_root / "data" / "exports" / md_filename
            
            with open(md_filepath, 'w', encoding='utf-8') as f:
                f.write(md_content)
            
            print(f"Success: {category}: JSON and Markdown files saved")
        
        # 生成汇总报告
        summary_report = self._generate_summary_report()
        summary_filepath = project_root / "data" / "exports" / f"summary_report_{timestamp}.md"
        
        with open(summary_filepath, 'w', encoding='utf-8') as f:
            f.write(summary_report)
        
        print(f"Success: Summary report saved: {summary_filepath}")
    
    def _generate_markdown_report(self, category: str, items: List[Dict]) -> str:
        """
        生成Markdown格式的报告
        
        Args:
            category: 分类名称
            items: 项目列表
        
        Returns:
            Markdown内容
        """
        title_map = {
            "academic_papers": "Academic Papers Report",
            "ai_news": "AI News Report",
            "ai_tools": "AI Tools Report"
        }
        
        md_content = f"# {title_map.get(category, category)}\n\n"
        md_content += f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        md_content += f"总计: {len(items)} 个项目\n\n"
        
        # 按质量等级分组
        quality_groups = {}
        for item in items:
            level = item["quality_scores"]["quality_level"]
            if level not in quality_groups:
                quality_groups[level] = []
            quality_groups[level].append(item)
        
        for level in ["优秀", "良好", "一般", "较差", "很差"]:
            if level not in quality_groups:
                continue
            
            md_content += f"## {level} ({len(quality_groups[level])} 个)\n\n"
            
            for i, item in enumerate(quality_groups[level], 1):
                md_content += f"### {i}. {item.get('title', '未知标题')}\n\n"
                md_content += f"**质量分数**: {item['quality_scores']['total_score']}/10\n\n"
                
                if category == "academic_papers":
                    md_content += f"**作者**: {', '.join(item.get('authors', []))}\n\n"
                    md_content += f"**发布日期**: {item.get('published', '未知')}\n\n"
                    md_content += f"**链接**: [{item.get('id', '')}]({item.get('link', '')})\n\n"
                    md_content += f"**摘要**: {item.get('summary', '')[:200]}...\n\n"
                
                elif category == "ai_news":
                    md_content += f"**来源**: {item.get('source', '未知')}\n\n"
                    md_content += f"**发布日期**: {item.get('published', '未知')}\n\n"
                    md_content += f"**链接**: [查看原文]({item.get('link', '')})\n\n"
                
                elif category == "ai_tools":
                    md_content += f"**描述**: {item.get('description', '')}\n\n"
                    md_content += f"**GitHub**: [查看项目]({item.get('github_url', '')})\n\n"
                    popularity = item.get('popularity', {})
                    md_content += f"**Stars**: {popularity.get('github_stars', 0)}\n\n"
                
                md_content += "---\n\n"
        
        return md_content
    
    def _generate_summary_report(self) -> str:
        """
        生成汇总报告
        
        Returns:
            汇总报告内容
        """
        md_content = "# 🤖 AI内容聚合报告\n\n"
        md_content += f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        # 统计信息
        total_papers = len(self.results["academic_papers"])
        total_news = len(self.results["ai_news"])
        total_tools = len(self.results["ai_tools"])
        
        md_content += "## Statistical Overview\n\n"
        md_content += f"- Academic Papers: {total_papers} items\n"
        md_content += f"- AI News: {total_news} items\n"
        md_content += f"- AI Tools: {total_tools} items\n\n"
        
        # 质量分布
        md_content += "## 🏆 质量分布\n\n"
        
        for category, items in self.results.items():
            if not items:
                continue
            
            quality_dist = {}
            for item in items:
                level = item["quality_scores"]["quality_level"]
                quality_dist[level] = quality_dist.get(level, 0) + 1
            
            category_name = {
                "academic_papers": "学术论文",
                "ai_news": "AI新闻",
                "ai_tools": "AI工具"
            }[category]
            
            md_content += f"### {category_name}\n\n"
            for level in ["优秀", "良好", "一般", "较差", "很差"]:
                count = quality_dist.get(level, 0)
                if count > 0:
                    md_content += f"- {level}: {count} 个\n"
            md_content += "\n"
        
        # 推荐内容
        md_content += "## ⭐ 今日推荐\n\n"
        
        all_items = []
        for category, items in self.results.items():
            for item in items:
                item["category"] = category
                all_items.append(item)
        
        # 按质量分数排序，取前10
        top_items = sorted(all_items, key=lambda x: x["quality_scores"]["total_score"], reverse=True)[:10]
        
        for i, item in enumerate(top_items, 1):
            category_emoji = {
                "academic_papers": "[PAPER]",
                "ai_news": "[NEWS]",
                "ai_tools": "[TOOL]"
            }
            
            emoji = category_emoji.get(item["category"], "[ITEM]")
            md_content += f"### {i}. {emoji} {item.get('title', '未知标题')}\n\n"
            md_content += f"**质量分数**: {item['quality_scores']['total_score']}/10\n\n"
            md_content += f"**分类**: {item['category']}\n\n"
            
            if item.get('link'):
                md_content += f"**链接**: [查看详情]({item['link']})\n\n"
            
            md_content += "---\n\n"
        
        return md_content

def main():
    """
    主函数
    """
    parser = argparse.ArgumentParser(description="AI内容聚合爬虫系统")
    parser.add_argument(
        "--categories",
        nargs="*",
        choices=["academic_papers", "ai_news", "ai_tools"],
        help="要运行的爬虫分类"
    )
    parser.add_argument(
        "--config",
        type=str,
        help="配置文件路径"
    )
    
    args = parser.parse_args()
    
    # 创建爬虫管理器
    manager = SpiderManager()
    
    # 运行爬虫
    asyncio.run(manager.run_all_spiders(args.categories))

if __name__ == "__main__":
    main()
