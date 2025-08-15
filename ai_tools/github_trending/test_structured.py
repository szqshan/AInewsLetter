#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
结构化GitHub爬虫测试脚本
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

# 导入爬虫
from structured_spider import StructuredGitHubSpider


async def quick_test():
    """快速测试功能"""
    print("🧪 结构化GitHub爬虫快速测试")
    print("=" * 40)
    
    # 创建测试目录
    test_dir = "test_crawled_data"
    spider = StructuredGitHubSpider(test_dir)
    
    try:
        print("\n🔍 测试爬取单个时间维度 (daily, 所有语言)...")
        
        # 测试爬取daily trending所有语言项目
        repos = await spider.crawl_trending_repos(None, "daily")
        print(f"   📊 从trending页面获取: {len(repos)} 个仓库")
        
        # 处理和过滤
        processed = await spider.process_and_filter_repos(repos, "daily")
        print(f"   🎯 AI相关工具: {len(processed)} 个")
        
        if processed:
            print("\n📋 发现的AI工具:")
            for i, repo in enumerate(processed[:3], 1):
                name = repo.get('name', 'Unknown')
                desc = repo.get('description', '无描述')[:60]
                stars = repo.get('stars', 0)
                quality = repo.get('quality_score', 0)
                
                print(f"   {i}. {name}")
                print(f"      📝 {desc}...")
                print(f"      ⭐ Stars: {stars:,}, 质量分: {quality:.1f}")
            
            # 保存测试结果
            await spider.save_time_range_results(processed, "daily")
            spider.save_processed_repos()
            
            print(f"\n✅ 测试成功!")
            print(f"   📁 测试数据保存在: {test_dir}/")
            print(f"   🔍 工具详情目录: {test_dir}/tools/daily/")
            print(f"   📊 聚合数据: {test_dir}/data/daily/")
            print(f"   🏆 排行榜: {test_dir}/rankings/daily/")
            
            return True
        else:
            print("⚠️ 未发现AI相关工具")
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_directory_structure():
    """测试目录结构创建"""
    print("\n🏗️ 测试目录结构创建...")
    
    test_dir = Path("test_structure")
    spider = StructuredGitHubSpider(str(test_dir))
    
    # 检查目录结构
    expected_dirs = [
        test_dir / "tools" / "daily",
        test_dir / "tools" / "weekly", 
        test_dir / "tools" / "monthly",
        test_dir / "data" / "daily",
        test_dir / "data" / "weekly",
        test_dir / "data" / "monthly",
        test_dir / "rankings" / "daily",
        test_dir / "rankings" / "weekly",
        test_dir / "rankings" / "monthly",
        test_dir / "metadata"
    ]
    
    all_exist = True
    for dir_path in expected_dirs:
        if dir_path.exists():
            print(f"   ✅ {dir_path.relative_to(test_dir)}")
        else:
            print(f"   ❌ {dir_path.relative_to(test_dir)}")
            all_exist = False
    
    if all_exist:
        print("✅ 目录结构创建测试通过")
        return True
    else:
        print("❌ 目录结构创建测试失败") 
        return False


def test_deduplication():
    """测试去重功能"""
    print("\n🔄 测试去重功能...")
    
    spider = StructuredGitHubSpider("test_dedup")
    
    # 模拟重复仓库
    repo1 = {"name": "microsoft/vscode", "url": "https://github.com/microsoft/vscode"}
    repo2 = {"name": "microsoft/vscode", "url": "https://github.com/microsoft/vscode"}
    repo3 = {"name": "facebook/react", "url": "https://github.com/facebook/react"}
    
    id1 = spider._generate_repo_id(repo1)
    id2 = spider._generate_repo_id(repo2)
    id3 = spider._generate_repo_id(repo3)
    
    print(f"   仓库1 ID: {id1}")
    print(f"   仓库2 ID: {id2}")
    print(f"   仓库3 ID: {id3}")
    
    if id1 == id2:
        print("   ✅ 相同仓库生成相同ID")
    else:
        print("   ❌ 相同仓库生成不同ID")
        return False
    
    if id1 != id3:
        print("   ✅ 不同仓库生成不同ID")
    else:
        print("   ❌ 不同仓库生成相同ID")
        return False
    
    print("✅ 去重功能测试通过")
    return True


def test_ai_detection():
    """测试AI识别功能"""
    print("\n🤖 测试AI识别功能...")
    
    spider = StructuredGitHubSpider("test_ai")
    
    # 测试用例
    test_cases = [
        {
            "name": "tensorflow/tensorflow",
            "description": "An Open Source Machine Learning Framework for Everyone",
            "topics": ["machine-learning", "deep-learning"],
            "expected": True
        },
        {
            "name": "microsoft/vscode", 
            "description": "Visual Studio Code - lightweight but powerful source code editor",
            "topics": ["editor", "typescript"],
            "expected": False
        },
        {
            "name": "openai/gpt-4",
            "description": "GPT-4 language model implementation",
            "topics": ["nlp", "language-model"],
            "expected": True
        }
    ]
    
    all_correct = True
    for case in test_cases:
        result = spider._is_ai_related(case)
        status = "✅" if result == case["expected"] else "❌"
        print(f"   {status} {case['name']}: {result} (期望: {case['expected']})")
        
        if result != case["expected"]:
            all_correct = False
    
    if all_correct:
        print("✅ AI识别功能测试通过")
        return True
    else:
        print("❌ AI识别功能测试失败")
        return False


async def main():
    """主测试函数"""
    print("🚀 结构化GitHub爬虫完整测试套件")
    print("=" * 50)
    
    tests = [
        ("目录结构创建", test_directory_structure()),
        ("去重功能", test_deduplication()),
        ("AI识别功能", test_ai_detection()),
        ("完整爬取流程", quick_test())
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_coro in tests:
        print(f"\n📝 执行测试: {test_name}")
        print("-" * 30)
        
        try:
            if asyncio.iscoroutine(test_coro):
                result = await test_coro
            else:
                result = test_coro
            
            if result:
                passed += 1
                print(f"✅ {test_name}: 通过")
            else:
                print(f"❌ {test_name}: 失败")
                
        except Exception as e:
            print(f"❌ {test_name}: 异常 - {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过! 结构化爬虫可以正常使用")
        print("\n💡 下一步:")
        print("   1. 运行完整爬取: python run_structured_crawler.py")
        print("   2. 检查存储集成: python storage_integrator.py --check")
        print("   3. 上传到存储架构: python storage_integrator.py --upload")
    else:
        print("⚠️ 部分测试失败，请检查问题后重试")
    
    return passed == total


if __name__ == "__main__":
    asyncio.run(main())
