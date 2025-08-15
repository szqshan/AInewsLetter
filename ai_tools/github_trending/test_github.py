#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitHub Trending爬虫测试脚本
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from spider import GitHubTrendingSpider
import json
from datetime import datetime


def test_github_crawler():
    """测试GitHub爬虫"""
    print("🐙 GitHub Trending AI工具爬虫测试")
    print("=" * 50)
    
    try:
        # 创建爬虫实例
        spider = GitHubTrendingSpider()
        
        # 测试爬取Python相关的每日趋势
        print("🐍 爬取Python相关的AI工具 (每日趋势)...")
        repos = spider.get_trending_repos(language='python', since='daily')
        
        print(f"✅ 找到 {len(repos)} 个AI相关的Python工具")
        
        if repos:
            print("\n📊 前3个工具:")
            for i, repo in enumerate(repos[:3], 1):
                print(f"\n{i}. {repo.get('name', 'Unknown')}")
                print(f"   描述: {repo.get('description', '无描述')[:100]}...")
                print(f"   Stars: {repo.get('stars', 0):,} (+{repo.get('stars_today', 0)} 今日)")
                print(f"   语言: {repo.get('language', 'Unknown')}")
                print(f"   链接: {repo.get('url', '无链接')}")
                
                if repo.get('quality_score'):
                    score = repo['quality_score'].get('total_score', 0)
                    print(f"   质量评分: {score:.1f}/100")
            
            # 保存测试结果
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            test_file = f"test_results_{timestamp}.json"
            
            try:
                with open(test_file, 'w', encoding='utf-8') as f:
                    json.dump(repos, f, ensure_ascii=False, indent=2)
                print(f"\n💾 测试结果已保存: {test_file}")
            except Exception as e:
                print(f"\n⚠️ 保存结果失败: {e}")
            
            return True
        else:
            print("❌ 未找到AI相关工具")
            return False
            
    except Exception as e:
        print(f"❌ 测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_multiple_languages():
    """测试多种编程语言"""
    print("\n🌐 测试多种编程语言的AI工具")
    print("-" * 30)
    
    spider = GitHubTrendingSpider()
    languages = ['python', 'javascript', None]  # None表示所有语言
    all_results = {}
    
    for lang in languages:
        lang_name = lang or "all_languages"
        print(f"\n🔍 爬取 {lang_name} 的AI工具...")
        
        try:
            repos = spider.get_trending_repos(language=lang, since='daily')
            all_results[lang_name] = repos
            print(f"  ✅ 找到 {len(repos)} 个工具")
            
            # 显示最热门的工具
            if repos:
                top_repo = max(repos, key=lambda x: x.get('stars', 0))
                print(f"  🌟 最热门: {top_repo.get('name')} ({top_repo.get('stars', 0):,} stars)")
            
        except Exception as e:
            print(f"  ❌ 爬取失败: {e}")
            all_results[lang_name] = []
    
    # 统计总结
    total_repos = sum(len(repos) for repos in all_results.values())
    print(f"\n📈 总结:")
    print(f"   总工具数: {total_repos}")
    for lang, repos in all_results.items():
        print(f"   {lang}: {len(repos)} 个工具")
    
    return all_results


if __name__ == "__main__":
    print("🚀 开始GitHub爬虫测试...")
    
    # 基础测试
    success = test_github_crawler()
    
    if success:
        print("\n" + "="*50)
        # 扩展测试
        test_multiple_languages()
        
        print("\n✅ 所有测试完成!")
        print("\n💡 GitHub Trending爬虫可以正常工作")
        print("   这是一个相对容易实现的爬虫选择!")
    else:
        print("\n❌ 基础测试失败")
        print("   可能需要检查网络连接或GitHub页面结构变化")
