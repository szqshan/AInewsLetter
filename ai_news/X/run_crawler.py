#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
X (Twitter) 爬虫一键运行脚本
"""

import argparse
import sys
from pathlib import Path
from spider import XSpider

def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='X (Twitter) 爬虫一键运行工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python run_crawler.py                           # 默认爬取Following页面
  python run_crawler.py --max 10                 # 最多爬取10条
  python run_crawler.py --target following --max 5  # 爬取Following 5条推文
        """
    )
    
    parser.add_argument(
        '--target', 
        default='following',
        choices=['following'],
        help='爬取目标 (默认: following)'
    )
    
    parser.add_argument(
        '--max', 
        type=int, 
        default=20,
        help='最大爬取数量 (默认: 20)'
    )
    
    parser.add_argument(
        '--force', 
        action='store_true',
        help='强制重新爬取已存在的推文'
    )
    
    parser.add_argument(
        '--verbose', 
        action='store_true',
        help='显示详细日志'
    )
    
    args = parser.parse_args()
    
    # 显示启动信息
    print("="*60)
    print("🕷️  X (Twitter) 爬虫启动")
    print("="*60)
    print(f"📋 爬取目标: {args.target}")
    print(f"📊 最大数量: {args.max}")
    print(f"🔄 强制模式: {'是' if args.force else '否'}")
    print("="*60)
    
    try:
        # 初始化爬虫
        spider = XSpider()
        
        # 执行爬取
        print(f"🚀 开始爬取 {args.target}...")
        result = spider.run(target=args.target, max_tweets=args.max)
        
        if result is not None:
            print("\n✅ 爬取完成！")
            print(f"📁 数据保存在: crawled_data/")
        else:
            print("\n❌ 爬取失败！")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⚠️ 用户中断爬虫")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ 爬虫运行出错: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)
    
    print("\n🎉 任务完成！")
    print("="*60)

if __name__ == "__main__":
    main()