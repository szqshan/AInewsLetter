#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
结构化GitHub爬虫启动脚本
支持时间维度分类、去重、结构化存储
"""

import argparse
import asyncio
import sys
from pathlib import Path
from datetime import datetime

# 导入结构化爬虫
from structured_spider import StructuredGitHubSpider


def print_banner():
    """打印启动横幅"""
    print("""
🚀 GitHub Trending 结构化爬虫
================================
✨ 功能特点:
  📅 支持 daily/weekly/monthly 三种时间维度
  🔄 智能去重，避免重复爬取
  📁 为每个工具创建单独目录
  🏆 自动生成热度排行榜
  📊 参考arXiv架构的结构化存储
================================
    """)


async def run_full_crawl(output_dir: str = "crawled_data"):
    """运行完整的分时间维度爬取"""
    print_banner()
    
    start_time = datetime.now()
    
    try:
        # 创建爬虫实例
        spider = StructuredGitHubSpider(output_dir)
        
        print("🎯 开始完整的GitHub Trending爬取...")
        print("   📅 将爬取 daily、weekly、monthly 三个时间维度")
        print("   🔍 将爬取所有语言的AI工具（不按语言分类）")
        print("   ⏱️ 预计耗时: 10-20分钟")
        print("-" * 60)
        
        # 执行完整爬取
        results = await spider.crawl_all_time_ranges()
        
        # 统计结果
        total_tools = sum(len(repos) for repos in results.values())
        unique_tools = len(spider.processed_repos)
        
        end_time = datetime.now()
        duration = end_time - start_time
        
        print("\n" + "=" * 60)
        print("🎉 爬取任务完成!")
        print(f"   ⏱️ 总耗时: {duration}")
        print(f"   📊 爬取统计:")
        print(f"      📅 Daily: {len(results.get('daily', []))} 个AI工具")
        print(f"      📅 Weekly: {len(results.get('weekly', []))} 个AI工具") 
        print(f"      📅 Monthly: {len(results.get('monthly', []))} 个AI工具")
        print(f"   🔄 去重统计:")
        print(f"      📚 总爬取数: {total_tools}")
        print(f"      🎯 唯一工具: {unique_tools}")
        print(f"   📡 请求统计:")
        print(f"      🌐 网页请求: {spider.web_requests_count}")
        print(f"      🔧 API请求: {spider.api_requests_count}")
        
        print(f"\n📁 输出目录结构:")
        print(f"   📂 {output_dir}/")
        print(f"   ├── 📁 tools/           # 每个工具的单独目录")
        print(f"   │   ├── 📁 daily/")
        print(f"   │   ├── 📁 weekly/")
        print(f"   │   └── 📁 monthly/")
        print(f"   ├── 📁 data/            # 聚合数据JSON")
        print(f"   ├── 📁 rankings/        # 热度排行榜")
        print(f"   └── 📁 metadata/        # 去重记录")
        
        return results
        
    except KeyboardInterrupt:
        print("\n⚠️ 用户中断爬取")
        return None
    except Exception as e:
        print(f"\n❌ 爬取过程出现错误: {e}")
        import traceback
        traceback.print_exc()
        return None


async def run_single_time_range(time_range: str, output_dir: str = "crawled_data"):
    """运行单一时间维度爬取"""
    print_banner()
    
    if time_range not in ["daily", "weekly", "monthly"]:
        print(f"❌ 无效的时间范围: {time_range}")
        print("   支持的时间范围: daily, weekly, monthly")
        return None
    
    start_time = datetime.now()
    
    try:
        spider = StructuredGitHubSpider(output_dir)
        
        print(f"🎯 开始爬取 {time_range} GitHub Trending...")
        print("-" * 40)
        
        # 爬取单一时间维度（所有语言）
        print(f"\n🔍 爬取所有语言的AI工具...")
        
        repos = await spider.crawl_trending_repos(None, time_range)
        all_repos = await spider.process_and_filter_repos(repos, time_range)
        
        # 保存结果
        await spider.save_time_range_results(all_repos, time_range)
        spider.save_processed_repos()
        
        end_time = datetime.now()
        duration = end_time - start_time
        
        print(f"\n✅ {time_range} 爬取完成!")
        print(f"   ⏱️ 耗时: {duration}")
        print(f"   📊 AI工具数量: {len(all_repos)}")
        print(f"   🔄 去重后唯一工具: {len(spider.processed_repos)}")
        
        return all_repos
        
    except Exception as e:
        print(f"\n❌ 爬取失败: {e}")
        return None


def show_directory_structure(output_dir: str):
    """显示输出目录结构"""
    output_path = Path(output_dir)
    
    if not output_path.exists():
        print(f"❌ 目录不存在: {output_dir}")
        return
    
    print(f"📁 目录结构: {output_dir}")
    print("=" * 40)
    
    # 统计各类文件数量
    tools_dirs = list((output_path / "tools").rglob("*/")) if (output_path / "tools").exists() else []
    data_files = list((output_path / "data").rglob("*.json")) if (output_path / "data").exists() else []
    ranking_files = list((output_path / "rankings").rglob("*.md")) if (output_path / "rankings").exists() else []
    
    print(f"📂 工具目录: {len(tools_dirs)} 个")
    print(f"📄 数据文件: {len(data_files)} 个")
    print(f"🏆 排行榜文件: {len(ranking_files)} 个")
    
    # 显示最近的几个工具目录
    if tools_dirs:
        print("\n📝 最近的工具目录 (前5个):")
        for tool_dir in sorted(tools_dirs, key=lambda x: x.stat().st_mtime, reverse=True)[:5]:
            rel_path = tool_dir.relative_to(output_path)
            content_file = tool_dir / "content.md"
            metadata_file = tool_dir / "metadata.json"
            
            status = "✅" if content_file.exists() and metadata_file.exists() else "⚠️"
            print(f"   {status} {rel_path}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="GitHub Trending 结构化爬虫",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 完整爬取所有时间维度
  python run_structured_crawler.py

  # 只爬取每日trending
  python run_structured_crawler.py --time-range daily

  # 自定义输出目录
  python run_structured_crawler.py --output my_data

  # 显示目录结构
  python run_structured_crawler.py --show-structure

特性说明:
  📅 时间维度: daily, weekly, monthly
  🔍 编程语言: python, javascript, typescript, all
  🔄 自动去重: 避免重复爬取相同项目
  📁 结构化存储: 每个工具单独目录
  🏆 排行榜: 按质量分数排序
        """
    )
    
    parser.add_argument(
        '--time-range', '-t',
        type=str,
        choices=['daily', 'weekly', 'monthly', 'all'],
        default='all',
        help='时间范围 (默认: all - 爬取所有时间维度)'
    )
    
    parser.add_argument(
        '--output', '-o',
        type=str,
        default='crawled_data',
        help='输出目录 (默认: crawled_data)'
    )
    
    parser.add_argument(
        '--show-structure', '-s',
        action='store_true',
        help='显示输出目录结构'
    )
    
    args = parser.parse_args()
    
    # 显示目录结构
    if args.show_structure:
        show_directory_structure(args.output)
        return
    
    # 创建输出目录
    output_path = Path(args.output)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # 执行爬取任务
    try:
        if args.time_range == 'all':
            # 完整爬取
            results = asyncio.run(run_full_crawl(args.output))
        else:
            # 单一时间维度爬取
            results = asyncio.run(run_single_time_range(args.time_range, args.output))
        
        if results:
            print(f"\n🎊 任务完成! 数据已保存到: {output_path.absolute()}")
            print("\n💡 下一步操作:")
            print(f"   查看目录结构: python {sys.argv[0]} --show-structure")
            print(f"   查看排行榜: ls {args.output}/rankings/")
            print(f"   查看工具详情: ls {args.output}/tools/")
        
    except Exception as e:
        print(f"\n❌ 程序执行失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
