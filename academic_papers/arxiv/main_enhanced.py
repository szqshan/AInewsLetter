#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强版arXiv论文爬虫主程序
支持每日爬取、分类爬取、关键词爬取和定时任务
"""

import argparse
import json
import logging
import os
import sys
from pathlib import Path
import asyncio

# 添加src目录到Python路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

from arxiv_system.crawler.enhanced_arxiv_crawler import EnhancedArxivCrawler
from arxiv_system.scheduler.arxiv_scheduler import ArxivScheduler
from arxiv_system.oss.wrapper import OSSUploader
from arxiv_system.utils.file_utils import setup_logging, load_config


def setup_argument_parser():
    """设置命令行参数解析器"""
    parser = argparse.ArgumentParser(
        description="增强版arXiv论文爬虫系统",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  # 每日爬取
  python main_enhanced.py daily --days 1
  python main_enhanced.py daily --days 3 --categories cs.AI cs.LG
  
  # 分类爬取
  python main_enhanced.py category --categories cs.AI cs.LG --max-per-category 1000
  
  # 关键词爬取
  python main_enhanced.py keyword --keywords "transformer" "diffusion" --days 7
  
  # 定时任务
  python main_enhanced.py schedule --daily-time "09:00" --immediate
  
  # 传统爬取
  python main_enhanced.py crawl --query "artificial intelligence" --max-results 50
  
  # 上传和状态
  python main_enhanced.py upload --source crawled_data
  python main_enhanced.py status --detail
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="可用命令")
    
    # 每日爬取命令
    daily_parser = subparsers.add_parser("daily", help="爬取每日新论文")
    daily_parser.add_argument("--days", type=int, default=1, help="回溯天数")
    daily_parser.add_argument("--categories", nargs="*", help="指定分类（如：cs.AI cs.LG）")
    daily_parser.add_argument("--config", default="config_enhanced.json", help="配置文件路径")
    daily_parser.add_argument("--upload", action="store_true", help="完成后自动上传到OSS")
    
    # 分类爬取命令
    category_parser = subparsers.add_parser("category", help="按分类爬取论文")
    category_parser.add_argument("--categories", nargs="*", help="分类列表（空=所有AI分类）")
    category_parser.add_argument("--max-per-category", type=int, default=1000, help="每个分类最大论文数")
    category_parser.add_argument("--config", default="config_enhanced.json", help="配置文件路径")
    category_parser.add_argument("--upload", action="store_true", help="完成后自动上传到OSS")
    
    # 关键词爬取命令
    keyword_parser = subparsers.add_parser("keyword", help="按关键词爬取论文")
    keyword_parser.add_argument("--keywords", nargs="*", help="关键词列表（空=使用默认热门关键词）")
    keyword_parser.add_argument("--days", type=int, default=7, help="回溯天数")
    keyword_parser.add_argument("--config", default="config_enhanced.json", help="配置文件路径")
    keyword_parser.add_argument("--upload", action="store_true", help="完成后自动上传到OSS")
    
    # 定时任务命令
    schedule_parser = subparsers.add_parser("schedule", help="启动定时任务")
    schedule_parser.add_argument("--config", default="config_enhanced.json", help="配置文件路径")
    schedule_parser.add_argument("--daily-time", default="09:00", help="每日执行时间")
    schedule_parser.add_argument("--weekly-time", default="02:00", help="每周执行时间")
    schedule_parser.add_argument("--immediate", action="store_true", help="立即执行一次")
    schedule_parser.add_argument("--once-daily", action="store_true", help="仅执行一次每日任务")
    schedule_parser.add_argument("--once-weekly", action="store_true", help="仅执行一次每周任务")
    
    # 传统爬取命令（兼容性）
    crawl_parser = subparsers.add_parser("crawl", help="传统爬取模式")
    crawl_parser.add_argument("--query", default="cat:cs.AI OR cat:cs.LG OR cat:cs.CL", 
                             help="搜索查询条件")
    crawl_parser.add_argument("--max-results", type=int, default=100, 
                             help="最大结果数量")
    crawl_parser.add_argument("--output", default="crawled_data", 
                             help="输出目录")
    crawl_parser.add_argument("--concurrent", type=int, default=3, 
                             help="并发数量")
    crawl_parser.add_argument("--download-pdf", action="store_true", 
                             help="下载PDF文件")
    crawl_parser.add_argument("--config", default="config_enhanced.json", help="配置文件路径")
    
    # 上传命令
    upload_parser = subparsers.add_parser("upload", help="上传数据到OSS")
    upload_parser.add_argument("--source", default="crawled_data", 
                              help="源数据目录")
    upload_parser.add_argument("--bucket", type=str, help="指定bucket名称")
    upload_parser.add_argument("--resume", action="store_true", help="断点续传")
    upload_parser.add_argument("--concurrent", type=int, default=5, 
                              help="并发上传数量")
    upload_parser.add_argument("--config", default="config_enhanced.json", help="配置文件路径")
    
    # 状态命令
    status_parser = subparsers.add_parser("status", help="查看系统状态")
    status_parser.add_argument("--detail", action="store_true", help="显示详细信息")
    status_parser.add_argument("--schedule", action="store_true", help="显示定时任务状态")
    status_parser.add_argument("--config", default="config_enhanced.json", help="配置文件路径")
    
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
        
        if args.upload:
            await upload_to_oss(result["output_dir"], config)
        
        return result


async def handle_category_command(args):
    """处理分类爬取命令"""
    print(f"📊 开始分类爬取任务")
    
    config = load_config(args.config)
    crawler = EnhancedArxivCrawler(config)
    
    async with crawler:
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
            "output_dir": output_dir
        }
        
        print(f"✅ 分类爬取完成: {result}")
        
        if args.upload:
            await upload_to_oss(output_dir, config)
        
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
        
        if args.upload:
            await upload_to_oss(result["output_dir"], config)
        
        return result


def handle_schedule_command(args):
    """处理定时任务命令"""
    print("⏰ 启动定时任务系统")
    
    scheduler = ArxivScheduler(args.config)
    
    if args.once_daily:
        return scheduler.run_once_daily()
    elif args.once_weekly:
        return scheduler.run_once_weekly()
    else:
        scheduler.start_custom_schedule(
            daily_time=args.daily_time,
            weekly_time=args.weekly_time,
            immediate_run=args.immediate
        )


async def handle_crawl_command(args):
    """处理传统爬取命令（兼容性）"""
    print("🕷️ 使用传统爬取模式")
    
    config = load_config(args.config)
    crawler = EnhancedArxivCrawler(config)
    
    await crawler._crawl_async(
        query=args.query,
        max_results=args.max_results,
        output_dir=args.output,
        concurrent=args.concurrent,
        download_pdf=args.download_pdf
    )


async def handle_upload_command(args):
    """处理上传命令"""
    print(f"☁️ 开始上传到OSS: {args.source}")
    
    config = load_config(args.config)
    
    # 如果指定了bucket，更新配置
    if args.bucket:
        config['oss']['bucket_name'] = args.bucket
    
    await upload_to_oss(args.source, config)


def handle_status_command(args):
    """处理状态命令"""
    print("📊 系统状态信息")
    
    config = load_config(args.config)
    
    # 显示配置信息
    print("\n🔧 配置信息:")
    print(f"   配置文件: {args.config}")
    print(f"   输出目录: {config.get('crawler', {}).get('output_directory', 'crawled_data')}")
    print(f"   每日爬取: {'启用' if config.get('crawler', {}).get('enable_daily_crawl', False) else '禁用'}")
    
    # 显示AI分类
    ai_categories = config.get('crawler', {}).get('ai_categories', {})
    print(f"\n📂 AI分类配置:")
    for group, categories in ai_categories.items():
        print(f"   {group}: {', '.join(categories)}")
    
    # 显示定时任务状态
    if args.schedule:
        scheduler = ArxivScheduler(args.config)
        status = scheduler.get_schedule_status()
        print(f"\n⏰ 定时任务状态:")
        print(f"   运行状态: {'运行中' if status['running'] else '未运行'}")
        print(f"   任务数量: {status['total_jobs']}")
        for job in status['jobs']:
            print(f"   - {job['function']}: {job['interval']} {job['unit']}")
    
    # 显示存储信息
    output_dir = Path(config.get('crawler', {}).get('output_directory', 'crawled_data'))
    if output_dir.exists():
        print(f"\n💾 存储信息:")
        
        daily_dir = output_dir / "daily"
        if daily_dir.exists():
            daily_count = len(list(daily_dir.iterdir()))
            print(f"   每日数据: {daily_count} 个目录")
        
        weekly_dir = output_dir / "weekly"
        if weekly_dir.exists():
            weekly_count = len(list(weekly_dir.iterdir()))
            print(f"   每周数据: {weekly_count} 个目录")


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
        print(f"   自动上传: {'启用' if oss_config.get('enable_auto_upload', False) else '禁用'}")


async def save_category_results(papers_by_category, output_dir):
    """保存分类爬取结果"""
    from arxiv_system.utils.file_utils import ensure_directory, save_json
    
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


async def upload_to_oss(source_dir, config):
    """上传到OSS"""
    oss_config = config.get('oss', {})
    
    async with OSSUploader(oss_config) as uploader:
        result = await uploader.upload_all(
            base_dir=Path(source_dir),
            resume=True
        )
        
        if result.get('success'):
            print(f"✅ OSS上传成功！共上传 {result.get('uploaded_files', 0)} 个文件")
            if result.get('sample_urls'):
                print("📋 示例URL:")
                for url in result['sample_urls'][:3]:
                    print(f"  🔗 {url}")
        else:
            print(f"❌ OSS上传失败: {result.get('error', '未知错误')}")


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
            
        elif args.command == "schedule":
            handle_schedule_command(args)
            
        elif args.command == "crawl":
            asyncio.run(handle_crawl_command(args))
            
        elif args.command == "upload":
            asyncio.run(handle_upload_command(args))
            
        elif args.command == "status":
            handle_status_command(args)
            
        elif args.command == "info":
            handle_info_command(args)
            
    except KeyboardInterrupt:
        print("\n🛑 用户中断，程序退出")
        sys.exit(0)
    except Exception as e:
        logger.error(f"执行失败: {e}")
        print(f"❌ 执行失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
