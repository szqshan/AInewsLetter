#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强版arXiv论文爬虫主程序（简化版，无调度器）
支持每日爬取、分类爬取、关键词爬取功能
"""

import argparse
import json
import logging
import os
import sys
from pathlib import Path
import asyncio
from datetime import datetime

# 添加src目录到Python路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

from arxiv_system.crawler.enhanced_arxiv_crawler import EnhancedArxivCrawler
from arxiv_system.oss.wrapper import OSSUploader
from arxiv_system.utils.file_utils import setup_logging, load_config, save_json, ensure_directory


def setup_argument_parser():
    """设置命令行参数解析器"""
    parser = argparse.ArgumentParser(
        description="增强版arXiv论文爬虫系统",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  # 每日爬取
  python main_enhanced_simple.py daily --days 1
  python main_enhanced_simple.py daily --days 3 --categories cs.AI cs.LG
  
  # 分类爬取
  python main_enhanced_simple.py category --categories cs.AI cs.LG --max-per-category 100
  
  # 关键词爬取
  python main_enhanced_simple.py keyword --keywords "transformer" "LLM" --days 7
  
  # 信息查看
  python main_enhanced_simple.py info --categories
  python main_enhanced_simple.py info --keywords
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="可用命令")
    
    # 每日爬取命令
    daily_parser = subparsers.add_parser("daily", help="爬取每日新论文")
    daily_parser.add_argument("--days", type=int, default=1, help="回溯天数")
    daily_parser.add_argument("--categories", nargs="*", help="指定分类（如：cs.AI cs.LG）")
    daily_parser.add_argument("--config", default="config_enhanced.json", help="配置文件路径")
    
    # 分类爬取命令
    category_parser = subparsers.add_parser("category", help="按分类爬取论文")
    category_parser.add_argument("--categories", nargs="*", help="分类列表（空=所有AI分类）")
    category_parser.add_argument("--max-per-category", type=int, default=100, help="每个分类最大论文数")
    category_parser.add_argument("--folders", action="store_true", help="生成完整的文件夹结构")
    category_parser.add_argument("--config", default="config_enhanced.json", help="配置文件路径")
    
    # 关键词爬取命令
    keyword_parser = subparsers.add_parser("keyword", help="按关键词爬取论文")
    keyword_parser.add_argument("--keywords", nargs="*", help="关键词列表（空=使用默认热门关键词）")
    keyword_parser.add_argument("--days", type=int, default=7, help="回溯天数")
    keyword_parser.add_argument("--config", default="config_enhanced.json", help="配置文件路径")
    
    # 信息命令
    info_parser = subparsers.add_parser("info", help="显示配置和统计信息")
    info_parser.add_argument("--categories", action="store_true", help="显示所有分类")
    info_parser.add_argument("--keywords", action="store_true", help="显示默认关键词")
    info_parser.add_argument("--config", default="config_enhanced.json", help="配置文件路径")
    
    return parser


async def handle_daily_command(args):
    """处理每日爬取命令"""
    print(f"🌅 开始每日爬取任务（回溯 {args.days} 天）")
    
    config = load_config(args.config)
    crawler = EnhancedArxivCrawler(config)
    
    async with crawler:
        result = await crawler.crawl_and_save_daily(
            days_back=args.days,
            categories=args.categories
        )
        
        print(f"✅ 每日爬取完成: {result}")
        return result


async def handle_category_command(args):
    """处理分类爬取命令"""
    print(f"📊 开始分类爬取任务")
    
    config = load_config(args.config)
    crawler = EnhancedArxivCrawler(config)
    
    async with crawler:
        if args.folders:
            # 使用增强的文件夹生成功能
            result = await crawler.crawl_and_save_by_categories(
                categories=args.categories,
                max_per_category=args.max_per_category,
                generate_folders=True
            )
            print(f"✅ 分类爬取完成（含文件夹结构）: {result}")
        else:
            # 只生成JSON数据
            papers_by_category = await crawler.crawl_by_categories(
                categories=args.categories,
                max_per_category=args.max_per_category
            )
            
            # 保存结果
            output_dir = os.path.join(config.get("crawler", {}).get("output_directory", "crawled_data"), "category")
            await save_category_results(papers_by_category, output_dir)
            
            result = {
                "total_papers": sum(len(papers) for papers in papers_by_category.values()),
                "categories": list(papers_by_category.keys()),
                "output_dir": output_dir,
                "folder_structure_generated": False
            }
            print(f"✅ 分类爬取完成（仅JSON）: {result}")
        
        return result


async def handle_keyword_command(args):
    """处理关键词爬取命令"""
    print(f"🔍 开始关键词爬取任务（回溯 {args.days} 天）")
    
    config = load_config(args.config)
    crawler = EnhancedArxivCrawler(config)
    
    async with crawler:
        result = await crawler.crawl_and_save_weekly(
            keywords=args.keywords,
            days_back=args.days
        )
        
        print(f"✅ 关键词爬取完成: {result}")
        return result


def handle_info_command(args):
    """处理信息命令"""
    config = load_config(args.config)
    crawler = EnhancedArxivCrawler(config)
    
    print("ℹ️ 系统信息")
    
    if args.categories:
        print("\n📂 所有AI相关分类:")
        category_groups = crawler.get_category_groups()
        for group, categories in category_groups.items():
            print(f"\n{group}:")
            for cat in categories:
                print(f"   - {cat}")
        
        print(f"\n总计: {len(crawler.get_all_ai_categories())} 个分类")
    
    if args.keywords:
        print("\n🔥 默认热门关键词:")
        keywords = crawler.trending_keywords
        for i, keyword in enumerate(keywords, 1):
            print(f"   {i:2d}. {keyword}")
        
        print(f"\n总计: {len(keywords)} 个关键词")
    
    if not args.categories and not args.keywords:
        # 显示完整信息
        print("\n📋 系统配置摘要:")
        print(f"   配置文件: {args.config}")
        print(f"   AI分类组: {len(crawler.get_category_groups())} 组")
        print(f"   总分类数: {len(crawler.get_all_ai_categories())} 个")
        print(f"   热门关键词: {len(crawler.trending_keywords)} 个")
        
        oss_config = config.get('oss', {})
        print(f"\n☁️ OSS配置:")
        print(f"   API地址: {oss_config.get('base_url', 'N/A')}")
        print(f"   存储桶: {oss_config.get('bucket_name', 'N/A')}")


async def save_category_results(papers_by_category, output_dir):
    """保存分类爬取结果"""
    ensure_directory(output_dir)
    
    # 保存按分类组织的数据
    save_json(papers_by_category, os.path.join(output_dir, "papers_by_category.json"))
    
    # 合并所有论文
    all_papers = []
    for papers in papers_by_category.values():
        all_papers.extend(papers)
    
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


def main():
    """主函数"""
    # 设置日志
    setup_logging()
    logger = logging.getLogger(__name__)
    
    # 解析命令行参数
    parser = setup_argument_parser()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        if args.command == "daily":
            asyncio.run(handle_daily_command(args))
            
        elif args.command == "category":
            asyncio.run(handle_category_command(args))
            
        elif args.command == "keyword":
            asyncio.run(handle_keyword_command(args))
            
        elif args.command == "info":
            handle_info_command(args)
            
    except KeyboardInterrupt:
        print("\n🛑 用户中断，程序退出")
        sys.exit(0)
    except Exception as e:
        logger.error(f"执行失败: {e}")
        print(f"❌ 执行失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
