#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Semantic Scholar爬虫启动脚本
简化版启动接口
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path

# 导入爬虫
from spider import SemanticScholarPublicCrawler


def load_config(config_path: str = "config.json") -> dict:
    """加载配置文件"""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"❌ 配置文件未找到: {config_path}")
        return {}
    except json.JSONDecodeError:
        print(f"❌ 配置文件格式错误: {config_path}")
        return {}


async def run_crawler(max_papers: int = 200, output_dir: str = None):
    """运行爬虫"""
    print("🔬 Semantic Scholar 无API密钥爬虫")
    print("=" * 50)
    print(f"📊 计划爬取: {max_papers} 篇论文")
    print(f"⏱️  预计耗时: {max_papers * 2 / 60:.1f} 分钟")
    print("🐌 慢速爬取中，请耐心等待...")
    print("-" * 50)
    
    if output_dir is None:
        output_dir = "crawled_data"
    
    async with SemanticScholarPublicCrawler(output_dir) as crawler:
        try:
            # 开始爬取
            papers = await crawler.crawl_ai_papers(max_papers=max_papers)
            
            print(f"\n🎉 爬取完成!")
            print(f"   📚 成功爬取: {len(papers)} 篇论文")
            print(f"   🌐 API请求: {crawler.request_count} 次")
            
            # 保存结果
            await crawler.save_results()
            print("💾 结果已保存到本地")
            
            return papers
            
        except KeyboardInterrupt:
            print("\n⚠️ 用户中断爬取")
            if crawler.papers_data:
                await crawler.save_results()
                print("💾 已保存部分结果")
            return crawler.papers_data
        except Exception as e:
            print(f"\n❌ 爬取过程中出现错误: {e}")
            if crawler.papers_data:
                await crawler.save_results()
                print("💾 已保存部分结果")
            return crawler.papers_data


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="Semantic Scholar无API密钥爬虫",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python run_crawler.py                    # 默认爬取200篇论文
  python run_crawler.py --papers 100      # 爬取100篇论文
  python run_crawler.py --papers 500 --output results  # 自定义输出目录

注意事项:
  - 无需API密钥，但请求频率受限
  - 每2秒发送1次请求，请耐心等待
  - 可随时Ctrl+C中断，会保存已爬取的数据
        """
    )
    
    parser.add_argument(
        '--papers', '-p',
        type=int,
        default=200,
        help='要爬取的论文数量 (默认: 200)'
    )
    
    parser.add_argument(
        '--output', '-o',
        type=str,
        default='crawled_data',
        help='输出目录 (默认: crawled_data)'
    )
    
    parser.add_argument(
        '--config', '-c',
        type=str,
        default='config.json',
        help='配置文件路径 (默认: config.json)'
    )
    
    args = parser.parse_args()
    
    # 验证参数
    if args.papers <= 0:
        print("❌ 论文数量必须大于0")
        sys.exit(1)
    
    if args.papers > 1000:
        print("⚠️ 论文数量过大，建议不超过1000篇")
        choice = input("是否继续? (y/N): ")
        if choice.lower() != 'y':
            sys.exit(0)
    
    # 创建输出目录
    output_path = Path(args.output)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # 运行爬虫
    try:
        papers = asyncio.run(run_crawler(args.papers, args.output))
        
        print(f"\n✅ 任务完成!")
        print(f"   📁 输出目录: {output_path.absolute()}")
        print(f"   📊 论文数量: {len(papers) if papers else 0}")
        
        if papers:
            # 显示一些统计信息
            years = [p.get('year') for p in papers if p.get('year')]
            if years:
                print(f"   📅 年份范围: {min(years)} - {max(years)}")
            
            citations = [p.get('citationCount', 0) for p in papers]
            if citations:
                avg_citations = sum(citations) / len(citations)
                print(f"   📈 平均引用: {avg_citations:.1f}")
        
    except Exception as e:
        print(f"\n❌ 程序出现错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
