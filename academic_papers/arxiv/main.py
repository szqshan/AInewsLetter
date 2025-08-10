#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
arXiv论文爬虫主程序
参照nlpSp1der架构设计的统一入口程序
"""

import argparse
import json
import logging
import os
import sys
from pathlib import Path

# 添加src目录到Python路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

from arxiv_system.crawler.arxiv_crawler import ArxivCrawler
from arxiv_system.oss.wrapper import OSSUploader
from arxiv_system.utils.file_utils import setup_logging, load_config


def setup_argument_parser():
    """设置命令行参数解析器"""
    parser = argparse.ArgumentParser(
        description="arXiv论文爬虫系统",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  python main.py crawl --query "artificial intelligence" --max-results 50
  python main.py upload --source crawled_data
  python main.py status
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="可用命令")
    
    # 爬取命令
    crawl_parser = subparsers.add_parser("crawl", help="爬取arXiv论文")
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
    
    # 上传命令
    upload_parser = subparsers.add_parser("upload", help="上传数据到OSS")
    upload_parser.add_argument("--source", default="crawled_data", 
                              help="源数据目录")
    upload_parser.add_argument("--bucket", type=str, help="指定bucket名称")
    upload_parser.add_argument("--resume", action="store_true", help="断点续传")
    upload_parser.add_argument("--concurrent", type=int, default=5, 
                              help="并发上传数量")
    
    # 状态命令
    status_parser = subparsers.add_parser("status", help="查看系统状态")
    
    return parser


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
        # 加载配置
        config = load_config("config.json")
        
        if args.command == "crawl":
            logger.info(f"开始爬取arXiv论文: {args.query}")
            crawler = ArxivCrawler(config)
            crawler.crawl(
                query=args.query,
                max_results=args.max_results,
                output_dir=args.output,
                concurrent=args.concurrent,
                download_pdf=args.download_pdf
            )
            
        elif args.command == "upload":
            logger.info(f"开始上传数据到OSS: {args.source}")
            import asyncio
            
            async def upload_task():
                # 如果指定了bucket，更新配置
                if args.bucket:
                    config['oss']['bucket_name'] = args.bucket
                    
                async with OSSUploader(config['oss']) as uploader:
                    result = await uploader.upload_all(
                        base_dir=Path(args.source),
                        resume=args.resume
                    )
                    
                    if result['success']:
                        logger.info(f"✅ 上传成功！共上传 {result['uploaded_files']} 个文件")
                        if result.get('sample_urls'):
                            logger.info("📋 示例URL:")
                            for url in result['sample_urls'][:3]:
                                logger.info(f"  🔗 {url}")
                    else:
                        logger.error(f"❌ 上传失败: {result.get('error', '未知错误')}")
                        sys.exit(1)
            
            asyncio.run(upload_task())
            
        elif args.command == "status":
            logger.info("查看系统状态")
            # TODO: 实现状态查看功能
            print("系统状态功能待实现")
            
    except Exception as e:
        logger.error(f"执行失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()