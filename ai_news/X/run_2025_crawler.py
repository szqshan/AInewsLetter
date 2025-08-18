#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
X (Twitter) 2025年推文爬虫启动器
专门爬取2025年所有博主发过的推文，逐条保存

使用方法:
    python run_2025_crawler.py --max 500
    python run_2025_crawler.py --max 1000
"""

import argparse
import subprocess
import sys
import os
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(
        description='X (Twitter) 2025年推文爬虫 - 爬取Following页面所有2025年推文',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
    python run_2025_crawler.py --max 500     # 爬取最多500条2025年推文
    python run_2025_crawler.py --max 1000    # 爬取最多1000条2025年推文
    python run_2025_crawler.py               # 默认爬取最多1000条推文

功能特点:
    ✅ 自动过滤2025年推文
    ✅ 逐条结构化保存
    ✅ 生成详细统计报告
    ✅ 防重复爬取机制
    ✅ 支持大量历史推文爬取
        """
    )
    
    parser.add_argument(
        '--max', 
        type=int, 
        default=1000,
        help='最大爬取推文数量 (默认: 1000)'
    )
    
    parser.add_argument(
        '--year',
        type=int,
        default=2025,
        help='目标年份 (默认: 2025)'
    )
    
    args = parser.parse_args()
    
    # 验证参数
    if args.max <= 0:
        print("❌ 错误: 最大爬取数量必须大于0")
        sys.exit(1)
    
    if args.year < 2006 or args.year > 2030:  # Twitter创立于2006年
        print("❌ 错误: 年份必须在2006-2030之间")
        sys.exit(1)
    
    # 检查Node.js脚本是否存在
    script_path = Path(__file__).parent / 'src' / 'scrape_2025_tweets.js'
    if not script_path.exists():
        print(f"❌ 错误: 找不到爬虫脚本 {script_path}")
        sys.exit(1)
    
    # 检查cookies文件是否存在
    cookies_path = Path(__file__).parent / 'src' / 'x_cookies.json'
    if not cookies_path.exists():
        print("❌ 错误: 找不到cookies文件")
        print("请先运行以下命令导出cookies:")
        print("    npm run export-cookies")
        print("或者:")
        print("    node src/export_browser_cookies.js")
        sys.exit(1)
    
    print("============================================================")
    print("🕷️  X (Twitter) 2025年推文爬虫")
    print("============================================================")
    print(f"📊 最大爬取数量: {args.max}")
    print(f"🎯 目标年份: {args.year}")
    print(f"💾 存储方式: 逐条结构化保存")
    print(f"📁 脚本路径: {script_path}")
    print("============================================================")
    
    try:
        # 构建Node.js命令
        cmd = ['node', str(script_path), str(args.max)]
        
        print(f"🚀 执行命令: {' '.join(cmd)}")
        print("")
        
        # 执行Node.js脚本
        result = subprocess.run(
            cmd,
            cwd=Path(__file__).parent,
            check=True,
            text=True,
            encoding='utf-8'
        )
        
        print("")
        print("🎉 2025年推文爬取完成！")
        print("")
        print("📁 数据保存位置:")
        print(f"   - 结构化数据: crawled_data/structured/")
        print(f"   - 汇总数据: crawled_data/tweets_2025/")
        print("")
        print("💡 提示: 可以查看生成的报告文件了解详细统计信息")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ 爬虫执行失败: {e}")
        print("")
        print("🔧 可能的解决方案:")
        print("   1. 检查cookies是否有效 (重新导出cookies)")
        print("   2. 检查网络连接")
        print("   3. 检查X账号是否正常登录")
        print("   4. 尝试减少爬取数量")
        sys.exit(1)
        
    except KeyboardInterrupt:
        print("")
        print("⚠️ 用户中断爬虫")
        sys.exit(0)
        
    except Exception as e:
        print(f"💥 未知错误: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()