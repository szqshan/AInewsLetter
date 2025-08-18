#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hugging Face博客爬虫运行脚本
支持命令行参数和多种运行模式
"""

import argparse
import sys
import logging
import os
from pathlib import Path

# 设置编码
if sys.platform.startswith('win'):
    os.environ['PYTHONIOENCODING'] = 'utf-8'

from spider import HuggingFaceBlogSpider


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='Hugging Face博客爬虫',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python run_crawler.py                    # 混合模式，默认参数
  python run_crawler.py --api-only --max 20  # 仅API模式，最多20篇
  python run_crawler.py --html-only            # 仅HTML模式
  python run_crawler.py --force               # 强制重新爬取
  python run_crawler.py --config my_config.json  # 使用自定义配置
        """
    )
    
    # 运行模式参数
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument(
        '--api-only', 
        action='store_true', 
        help='仅使用API方式爬取（推荐，速度快）'
    )
    mode_group.add_argument(
        '--html-only', 
        action='store_true', 
        help='仅使用HTML解析方式爬取（备选，更全面）'
    )
    
    # 爬取参数
    parser.add_argument(
        '--max', 
        type=int, 
        default=None, 
        help='最大爬取文章数量（默认无限制）'
    )
    parser.add_argument(
        '--force', 
        action='store_true', 
        help='强制重新爬取已存在的文章'
    )
    
    # 配置参数
    parser.add_argument(
        '--config', 
        default='config.json', 
        help='配置文件路径（默认: config.json）'
    )
    
    # 日志参数
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='详细输出模式'
    )
    parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='静默模式，仅输出错误'
    )
    
    # 测试参数
    parser.add_argument(
        '--test',
        action='store_true',
        help='测试模式，仅爬取5篇文章'
    )
    
    args = parser.parse_args()
    
    # 设置日志级别
    if args.quiet:
        logging.getLogger().setLevel(logging.ERROR)
    elif args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # 检查配置文件
    if not Path(args.config).exists():
        print(f"Error: Config file {args.config} not found")
        sys.exit(1)
    
    try:
        # 初始化爬虫
        print(f"Initializing spider with config: {args.config}")
        spider = HuggingFaceBlogSpider(args.config)
        
        # 确定最大文章数
        max_articles = args.max
        if args.test:
            max_articles = 5
            print("Test mode: crawling only 5 articles")
        
        # 执行爬取
        if args.api_only:
            print("Running mode: API only")
            success_count = spider.run_api_only(max_articles=max_articles, force=args.force)
        elif args.html_only:
            print("Running mode: HTML only")
            success_count = spider.run_html_only(max_articles=max_articles, force=args.force)
        else:
            print("Running mode: Mixed (API + HTML)")
            success_count = spider.run(max_articles=max_articles, force=args.force)
        
        print(f"\nCrawling completed! Successfully crawled {success_count} articles")
        
        # 显示数据存储位置
        data_dir = Path(spider.config['storage']['data_dir'])
        articles_dir = data_dir / spider.config['storage']['data_type']
        print(f"Data storage location: {articles_dir.absolute()}")
        
    except KeyboardInterrupt:
        print("\nCrawling interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"Error occurred during crawling: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()