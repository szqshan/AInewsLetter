#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Stability AI 一键爬虫脚本
"""

import argparse
import sys
import os
from pathlib import Path

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from spider import StabilitySpider

def main():
    parser = argparse.ArgumentParser(description='Stability AI 一键爬虫')
    
    # 基础参数
    parser.add_argument('--max', type=int, default=20, 
                       help='最大爬取文章数量 (默认: 20)')
    parser.add_argument('--config', type=str, default='config.json',
                       help='配置文件路径 (默认: config.json)')
    
    # 功能开关
    parser.add_argument('--crawl-only', action='store_true',
                       help='只爬取数据，不上传到MinIO')
    parser.add_argument('--upload-only', action='store_true', 
                       help='只上传已有数据到MinIO，不爬取')
    parser.add_argument('--no-images', action='store_true',
                       help='不下载图片')
    parser.add_argument('--force', action='store_true',
                       help='强制重新爬取已存在的文章')
    
    # 调试参数
    parser.add_argument('--test', action='store_true',
                       help='测试模式，只爬取3篇文章')
    parser.add_argument('--verbose', action='store_true',
                       help='详细输出')
    
    args = parser.parse_args()
    
    # 测试模式
    if args.test:
        args.max = 3
        print("Test mode: crawling only 3 articles")
    
    try:
        # 初始化爬虫
        spider = StabilitySpider(config_file=args.config)
        
        # 修改配置
        if args.no_images:
            spider.config['media']['download_images'] = False
            print("Image download disabled")
        
        if args.force:
            spider.config['filter']['skip_duplicates'] = False
            print("Force mode: will re-crawl existing articles")
        
        # 只上传模式
        if args.upload_only:
            print("Upload-only mode")
            upload_to_minio(spider)
            return
        
        # 执行爬取
        if not args.upload_only:
            print(f"Starting crawler with max {args.max} articles...")
            spider.run(max_articles=args.max)
        
        # 上传到MinIO (如果不是只爬取模式)
        if not args.crawl_only:
            print("Uploading to MinIO...")
            upload_to_minio(spider)
        
    except KeyboardInterrupt:
        print("\nCrawler interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

def upload_to_minio(spider):
    """上传数据到MinIO"""
    try:
        # 这里可以集成MinIO上传功能
        # 暂时只是打印信息
        data_dir = spider.articles_dir
        
        if not data_dir.exists():
            print("No data directory found")
            return
        
        articles = list(data_dir.iterdir())
        print(f"Found {len(articles)} articles to upload")
        
        for article_dir in articles:
            if article_dir.is_dir():
                print(f"  {article_dir.name}")
        
        print("Upload completed (placeholder - implement MinIO integration)")
        
    except Exception as e:
        print(f"Upload failed: {e}")

def show_stats():
    """显示爬取统计信息"""
    data_dir = Path("crawled_data/stability_articles")
    
    if not data_dir.exists():
        print("No data found")
        return
    
    articles = list(data_dir.iterdir())
    print(f"\nSTATISTICS")
    print(f"Data directory: {data_dir}")
    print(f"Total articles: {len(articles)}")
    
    # 统计图片数量
    total_images = 0
    for article_dir in articles:
        if article_dir.is_dir():
            media_dir = article_dir / "media"
            if media_dir.exists():
                images = list(media_dir.glob("*"))
                total_images += len(images)
    
    print(f"Total images: {total_images}")

if __name__ == "__main__":
    main()