#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试README功能集成
"""
import asyncio
import sys
import os
from pathlib import Path

# 添加当前目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from structured_spider import StructuredGitHubSpider

async def test_readme_integration():
    """测试README集成功能"""
    print("🧪 测试README集成功能")
    print("=" * 50)
    
    # 创建测试爬虫实例
    spider = StructuredGitHubSpider("test_readme_output")
    
    try:
        print("🚀 开始测试爬取...")
        
        # 只爬取daily trending，限制数量
        repos = await spider.crawl_trending_repos(None, "daily")
        print(f"📊 获取到 {len(repos)} 个仓库")
        
        if repos:
            # 只处理前2个仓库进行测试
            test_repos = repos[:2]
            processed = await spider.process_and_filter_repos(test_repos, "daily")
            
            print(f"✅ 处理完成: {len(processed)} 个AI工具")
            
            # 检查README内容
            for repo in processed:
                name = repo.get('name', 'Unknown')
                has_readme = 'readme_content' in repo and repo['readme_content']
                readme_length = len(repo.get('readme_content', '')) if has_readme else 0
                
                print(f"📝 {name}: README {'✅' if has_readme else '❌'} ({readme_length} 字符)")
        
        print("\n🎉 测试完成!")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_readme_integration())
