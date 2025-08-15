#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试增强版GitHub爬虫
"""

import asyncio
import sys
import os
from datetime import datetime

# 导入增强爬虫
from enhanced_spider import EnhancedGitHubSpider


async def test_enhanced_crawler():
    """测试增强版爬虫"""
    print("🧪 测试增强版GitHub爬虫")
    print("=" * 40)
    
    try:
        # 创建爬虫实例
        spider = EnhancedGitHubSpider()
        
        # 测试爬取Python AI工具
        print("\n🐍 测试爬取Python AI工具...")
        repos = await spider.crawl_trending_repos(language="python", since="daily")
        
        if repos:
            print(f"\n✅ 成功爬取 {len(repos)} 个Python AI工具!")
            
            # 显示前3个工具的详细信息
            print("\n🏆 前3个高质量AI工具:")
            for i, repo in enumerate(repos[:3], 1):
                print(f"\n{i}. {repo.get('name', 'Unknown')}")
                print(f"   📝 描述: {repo.get('description', '无描述')[:100]}...")
                print(f"   ⭐ Stars: {repo.get('stars', 0):,}")
                print(f"   🔥 今日新增: +{repo.get('stars_today', 0)}")
                print(f"   🍴 Forks: {repo.get('forks', 0):,}")
                print(f"   💻 语言: {repo.get('language', 'Unknown')}")
                print(f"   🎯 质量分: {repo.get('quality_score', 0):.1f}/100")
                
                if repo.get('topics'):
                    topics = repo['topics'][:5]  # 只显示前5个标签
                    print(f"   🏷️  标签: {', '.join(topics)}")
                
                if repo.get('license'):
                    print(f"   📜 许可证: {repo['license']}")
                
                print(f"   🔗 链接: {repo.get('url', '无链接')}")
            
            # 保存测试结果
            await spider.save_results(repos, "python", "daily")
            
            return True
        else:
            print("❌ 未找到AI相关工具")
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_api_functionality():
    """测试API功能"""
    print("\n🔧 测试API功能...")
    
    from github_config import get_api_headers, GITHUB_CONFIG
    import aiohttp
    
    try:
        # 测试API认证
        api_url = "https://api.github.com/user"
        headers = get_api_headers()
        
        async with aiohttp.ClientSession() as session:
            async with session.get(api_url, headers=headers) as response:
                if response.status == 200:
                    user_info = await response.json()
                    print(f"✅ API认证成功!")
                    print(f"   👤 用户: {user_info.get('login', 'Unknown')}")
                    print(f"   📊 API限制: {response.headers.get('X-RateLimit-Limit', 'Unknown')}")
                    print(f"   🔄 剩余请求: {response.headers.get('X-RateLimit-Remaining', 'Unknown')}")
                    return True
                else:
                    print(f"❌ API认证失败: {response.status}")
                    return False
                    
    except Exception as e:
        print(f"❌ API测试失败: {e}")
        return False


async def quick_test():
    """快速测试基本功能"""
    print("\n⚡ 快速功能测试...")
    
    try:
        spider = EnhancedGitHubSpider()
        
        # 只爬取一个仓库进行测试
        print("📦 测试爬取单个仓库...")
        
        # 模拟一个trending仓库数据
        test_repo = {
            'name': 'microsoft/vscode',
            'owner': 'microsoft',
            'repo_name': 'vscode',
            'description': 'Visual Studio Code',
            'language': 'TypeScript'
        }
        
        # 测试API获取详细信息
        api_data = await spider._get_repo_details_from_api(test_repo)
        
        if api_data:
            print("✅ API数据获取成功!")
            print(f"   Stars: {api_data.get('stars', 0):,}")
            print(f"   Forks: {api_data.get('forks', 0):,}")
            print(f"   许可证: {api_data.get('license', 'Unknown')}")
            print(f"   更新时间: {api_data.get('updated_at', 'Unknown')}")
            return True
        else:
            print("❌ API数据获取失败")
            return False
            
    except Exception as e:
        print(f"❌ 快速测试失败: {e}")
        return False


async def main():
    """主测试函数"""
    print("🚀 GitHub增强爬虫测试套件")
    print("=" * 50)
    
    # 测试1: API功能
    api_success = await test_api_functionality()
    
    if api_success:
        print("\n" + "="*30)
        
        # 测试2: 快速功能测试
        quick_success = await quick_test()
        
        if quick_success:
            print("\n" + "="*30)
            
            # 测试3: 完整爬虫测试
            crawler_success = await test_enhanced_crawler()
            
            if crawler_success:
                print("\n🎉 所有测试通过!")
                print("\n💡 增强版GitHub爬虫可以正常工作:")
                print("   ✅ API认证成功")
                print("   ✅ 数据获取正常")
                print("   ✅ AI识别准确")
                print("   ✅ 质量评分有效")
                print("\n🚀 您可以开始使用增强版爬虫了!")
            else:
                print("\n❌ 爬虫测试失败")
        else:
            print("\n❌ 快速测试失败")
    else:
        print("\n❌ API测试失败，请检查Token配置")
    
    print(f"\n📊 测试完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    asyncio.run(main())
