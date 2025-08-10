#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强版 arXiv 爬虫功能测试脚本
验证新增的每日爬取、分类爬取和关键词爬取功能
"""

import asyncio
import sys
import json
from pathlib import Path

# 添加src目录到Python路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

from arxiv_system.crawler.enhanced_arxiv_crawler import EnhancedArxivCrawler
from arxiv_system.utils.file_utils import load_config


async def test_config_loading():
    """测试配置文件加载"""
    print("🔧 测试配置文件加载...")
    
    try:
        config = load_config("config_enhanced.json")
        print("✅ 增强版配置文件加载成功")
        
        # 检查关键配置项
        ai_categories = config.get("crawler", {}).get("ai_categories", {})
        print(f"   - AI分类组: {len(ai_categories)} 组")
        
        crawl_strategies = config.get("crawl_strategies", {})
        print(f"   - 爬取策略: {len(crawl_strategies)} 种")
        
        trending_keywords = config.get("crawler", {}).get("trending_keywords", [])
        print(f"   - 热门关键词: {len(trending_keywords)} 个")
        
        return config
        
    except Exception as e:
        print(f"❌ 配置文件加载失败: {e}")
        return None


async def test_enhanced_crawler_initialization():
    """测试增强版爬虫初始化"""
    print("\n🕷️ 测试增强版爬虫初始化...")
    
    try:
        config = load_config("config_enhanced.json")
        crawler = EnhancedArxivCrawler(config)
        
        print("✅ 增强版爬虫初始化成功")
        
        # 检查分类配置
        all_categories = crawler.get_all_ai_categories()
        print(f"   - 所有AI分类: {len(all_categories)} 个")
        print(f"   - 分类列表: {', '.join(all_categories[:5])}...")
        
        # 检查关键词配置
        keywords = crawler.trending_keywords
        print(f"   - 热门关键词: {len(keywords)} 个")
        print(f"   - 关键词列表: {', '.join(keywords[:3])}...")
        
        return crawler
        
    except Exception as e:
        print(f"❌ 增强版爬虫初始化失败: {e}")
        return None


async def test_daily_crawl_small():
    """测试小规模每日爬取"""
    print("\n🌅 测试小规模每日爬取...")
    
    try:
        config = load_config("config_enhanced.json")
        crawler = EnhancedArxivCrawler(config)
        
        async with crawler:
            # 仅测试cs.AI分类，最近1天，小量数据
            papers = await crawler.crawl_daily_new_papers(
                days_back=1,
                categories=["cs.AI"]
            )
            
            total_papers = sum(len(papers_list) for papers_list in papers.values())
            print(f"✅ 每日爬取测试完成，获取 {total_papers} 篇论文")
            
            # 显示详细统计
            for group, papers_list in papers.items():
                print(f"   - {group}: {len(papers_list)} 篇")
            
            return papers
            
    except Exception as e:
        print(f"❌ 每日爬取测试失败: {e}")
        return None


async def test_category_crawl_small():
    """测试小规模分类爬取"""
    print("\n📊 测试小规模分类爬取...")
    
    try:
        config = load_config("config_enhanced.json")
        crawler = EnhancedArxivCrawler(config)
        
        async with crawler:
            # 仅测试2个分类，每个最多10篇
            papers = await crawler.crawl_by_categories(
                categories=["cs.AI", "cs.LG"],
                max_per_category=10
            )
            
            total_papers = sum(len(papers_list) for papers_list in papers.values())
            print(f"✅ 分类爬取测试完成，获取 {total_papers} 篇论文")
            
            # 显示详细统计
            for category, papers_list in papers.items():
                print(f"   - {category}: {len(papers_list)} 篇")
            
            return papers
            
    except Exception as e:
        print(f"❌ 分类爬取测试失败: {e}")
        return None


async def test_keyword_crawl_small():
    """测试小规模关键词爬取"""
    print("\n🔍 测试小规模关键词爬取...")
    
    try:
        config = load_config("config_enhanced.json")
        crawler = EnhancedArxivCrawler(config)
        
        async with crawler:
            # 仅测试2个关键词，最近3天
            papers = await crawler.crawl_trending_keywords(
                keywords=["transformer", "LLM"],
                days_back=3
            )
            
            total_papers = sum(len(papers_list) for papers_list in papers.values())
            print(f"✅ 关键词爬取测试完成，获取 {total_papers} 篇论文")
            
            # 显示详细统计
            for keyword, papers_list in papers.items():
                print(f"   - {keyword}: {len(papers_list)} 篇")
            
            return papers
            
    except Exception as e:
        print(f"❌ 关键词爬取测试失败: {e}")
        return None


async def test_save_functionality():
    """测试保存功能"""
    print("\n💾 测试保存功能...")
    
    try:
        config = load_config("config_enhanced.json")
        crawler = EnhancedArxivCrawler(config)
        
        async with crawler:
            # 测试每日爬取并保存
            result = await crawler.crawl_and_save_daily(
                days_back=1,
                categories=["cs.AI"],
                output_base_dir="test_output"
            )
            
            print(f"✅ 保存功能测试完成: {result}")
            
            # 检查输出目录
            output_path = Path(result["output_dir"])
            if output_path.exists():
                files = list(output_path.glob("*.json"))
                print(f"   - 生成文件: {len(files)} 个")
                for file in files:
                    print(f"     • {file.name}")
            
            return result
            
    except Exception as e:
        print(f"❌ 保存功能测试失败: {e}")
        return None


def test_cli_help():
    """测试CLI帮助信息"""
    print("\n📋 测试CLI帮助信息...")
    
    try:
        # 导入CLI模块
        import subprocess
        import sys
        
        # 测试主程序帮助
        result = subprocess.run([
            sys.executable, "main_enhanced.py", "--help"
        ], capture_output=True, text=True, cwd=Path(__file__).parent)
        
        if result.returncode == 0:
            print("✅ CLI帮助信息显示正常")
            print(f"   - 帮助文本长度: {len(result.stdout)} 字符")
        else:
            print(f"❌ CLI帮助信息显示失败: {result.stderr}")
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"❌ CLI测试失败: {e}")
        return False


async def run_all_tests():
    """运行所有测试"""
    print("🧪 开始增强版 arXiv 爬虫功能测试")
    print("=" * 50)
    
    test_results = {}
    
    # 1. 测试配置加载
    config = await test_config_loading()
    test_results["config_loading"] = config is not None
    
    # 2. 测试爬虫初始化
    crawler = await test_enhanced_crawler_initialization()
    test_results["crawler_init"] = crawler is not None
    
    # 3. 测试每日爬取
    daily_result = await test_daily_crawl_small()
    test_results["daily_crawl"] = daily_result is not None
    
    # 4. 测试分类爬取
    category_result = await test_category_crawl_small()
    test_results["category_crawl"] = category_result is not None
    
    # 5. 测试关键词爬取
    keyword_result = await test_keyword_crawl_small()
    test_results["keyword_crawl"] = keyword_result is not None
    
    # 6. 测试保存功能
    save_result = await test_save_functionality()
    test_results["save_functionality"] = save_result is not None
    
    # 7. 测试CLI
    cli_result = test_cli_help()
    test_results["cli_help"] = cli_result
    
    # 汇总结果
    print("\n" + "=" * 50)
    print("🎯 测试结果汇总")
    print("=" * 50)
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:20s}: {status}")
        if result:
            passed += 1
    
    print(f"\n📊 总体结果: {passed}/{total} 测试通过")
    
    if passed == total:
        print("🎉 所有测试通过！增强版功能正常工作")
    else:
        print("⚠️ 部分测试失败，请检查相关功能")
    
    return test_results


if __name__ == "__main__":
    # 检查配置文件是否存在
    if not Path("config_enhanced.json").exists():
        print("❌ 找不到配置文件 config_enhanced.json")
        print("请确保配置文件在当前目录中")
        sys.exit(1)
    
    # 运行测试
    asyncio.run(run_all_tests())
