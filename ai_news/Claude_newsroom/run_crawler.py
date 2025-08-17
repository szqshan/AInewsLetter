#!/usr/bin/env python3
"""
Claude Newsroom 爬虫运行脚本
简化的一键运行脚本，包含爬取和上传功能
"""

import os
import sys
import time
import argparse
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(description='Claude Newsroom 一键爬虫')
    parser.add_argument('--crawl-only', action='store_true', help='仅执行爬取，不上传')
    parser.add_argument('--upload-only', action='store_true', help='仅执行上传，不爬取')
    parser.add_argument('--max', type=int, default=20, help='最大爬取文章数量')
    parser.add_argument('--force', action='store_true', help='强制更新已存在的文章')
    parser.add_argument('--config', default='config.json', help='配置文件路径')
    
    args = parser.parse_args()
    
    print("🤖 Claude Newsroom 一键爬虫启动")
    print("=" * 50)
    
    # 检查依赖
    try:
        import requests
        import bs4
        print("✅ 依赖检查通过")
    except ImportError as e:
        print(f"❌ 缺少依赖: {e}")
        print("请运行: pip install -r requirements.txt")
        return 1
    
    success = True
    
    # 1. 执行爬取
    if not args.upload_only:
        print("\n📥 开始爬取新闻...")
        try:
            from spider import ClaudeNewsroomSpider
            
            spider = ClaudeNewsroomSpider(args.config)
            spider.crawl(force_update=args.force, max_articles=args.max)
            print("✅ 爬取完成")
        except Exception as e:
            print(f"❌ 爬取失败: {e}")
            success = False
            if args.crawl_only:
                return 1
    
    # 2. 执行上传
    if not args.crawl_only and success:
        print("\n📤 开始上传数据...")
        try:
            from uploader import ClaudeNewsUploader
            
            uploader = ClaudeNewsUploader(args.config)
            uploader.upload_all(force_update=args.force)
            print("✅ 上传完成")
        except Exception as e:
            print(f"❌ 上传失败: {e}")
            print("如果MinIO服务不可用，数据已保存在本地")
            success = False
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 所有任务完成!")
    else:
        print("⚠️  部分任务失败，请检查日志")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
