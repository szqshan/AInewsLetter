#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化版Semantic Scholar爬虫测试
用于调试和验证基本功能
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime


async def simple_test():
    """简单测试爬虫功能"""
    print("🔬 Semantic Scholar 简化测试")
    print("=" * 40)
    
    base_url = "https://api.semanticscholar.org/graph/v1"
    
    headers = {
        'User-Agent': 'AI-Newsletter-Test/1.0',
        'Accept': 'application/json'
    }
    
    async with aiohttp.ClientSession(headers=headers) as session:
        # 测试1: 简单搜索
        print("\n📝 测试1: 基本搜索功能")
        search_url = f"{base_url}/paper/search"
        
        params = {
            'query': 'machine learning',
            'limit': 10,
            'fields': 'paperId,title,year,citationCount,abstract'
        }
        
        print(f"🌐 请求: {search_url}")
        print(f"📋 参数: {params}")
        
        try:
            await asyncio.sleep(1)  # 礼貌等待
            
            async with session.get(search_url, params=params) as response:
                print(f"📡 状态码: {response.status}")
                
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ 搜索成功!")
                    
                    if isinstance(data, dict) and 'data' in data:
                        papers = data['data']
                        print(f"📚 找到论文: {len(papers)} 篇")
                        
                        # 过滤测试
                        filtered_papers = []
                        for paper in papers:
                            year = paper.get('year')
                            citations = paper.get('citationCount', 0)
                            title = paper.get('title', '')
                            
                            print(f"📄 论文: {title[:50]}... (年份:{year}, 引用:{citations})")
                            
                            # 简化过滤条件
                            if year and year >= 2015 and citations >= 0:
                                filtered_papers.append(paper)
                        
                        print(f"✅ 过滤后: {len(filtered_papers)} 篇论文")
                        
                        if filtered_papers:
                            print("\n📋 第一篇论文详情:")
                            first_paper = filtered_papers[0]
                            for key, value in first_paper.items():
                                if isinstance(value, str) and len(value) > 100:
                                    print(f"  {key}: {value[:100]}...")
                                else:
                                    print(f"  {key}: {value}")
                        
                        return filtered_papers
                    else:
                        print(f"❌ 响应格式错误: {data}")
                        return None
                else:
                    text = await response.text()
                    print(f"❌ 请求失败 {response.status}: {text[:200]}")
                    return None
                    
        except Exception as e:
            print(f"❌ 请求异常: {e}")
            import traceback
            print(traceback.format_exc())
            return None


async def test_multiple_queries():
    """测试多个查询"""
    print("\n🔄 测试2: 多查询搜索")
    
    queries = ["artificial intelligence", "deep learning", "neural networks"]
    all_results = []
    
    for query in queries:
        print(f"\n🔍 搜索: {query}")
        
        # 这里调用简化的搜索
        base_url = "https://api.semanticscholar.org/graph/v1"
        headers = {
            'User-Agent': 'AI-Newsletter-Test/1.0',
            'Accept': 'application/json'
        }
        
        async with aiohttp.ClientSession(headers=headers) as session:
            params = {
                'query': query,
                'limit': 5,
                'fields': 'paperId,title,year,citationCount'
            }
            
            search_url = f"{base_url}/paper/search"
            
            try:
                await asyncio.sleep(2)  # 频率控制
                
                async with session.get(search_url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if isinstance(data, dict) and 'data' in data:
                            papers = data['data']
                            print(f"  ✅ 找到 {len(papers)} 篇论文")
                            all_results.extend(papers)
                        else:
                            print(f"  ❌ 数据格式错误")
                    else:
                        print(f"  ❌ 请求失败: {response.status}")
                        
            except Exception as e:
                print(f"  ❌ 异常: {e}")
    
    print(f"\n📊 总计找到: {len(all_results)} 篇论文")
    return all_results


async def main():
    """主测试函数"""
    try:
        # 测试1: 基本功能
        papers1 = await simple_test()
        
        if papers1:
            print(f"\n✅ 基本测试通过: {len(papers1)} 篇论文")
            
            # 测试2: 多查询
            papers2 = await test_multiple_queries()
            
            print(f"\n🎉 所有测试完成!")
            print(f"   基本搜索: {len(papers1) if papers1 else 0} 篇")
            print(f"   多查询搜索: {len(papers2) if papers2 else 0} 篇")
            
            # 保存测试结果
            if papers1 or papers2:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"test_results_{timestamp}.json"
                
                test_data = {
                    'basic_search': papers1 or [],
                    'multi_query': papers2 or [],
                    'timestamp': timestamp
                }
                
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(test_data, f, ensure_ascii=False, indent=2)
                
                print(f"💾 测试结果已保存: {filename}")
        else:
            print("\n❌ 基本测试失败")
            
    except Exception as e:
        print(f"\n❌ 测试过程出错: {e}")
        import traceback
        print(traceback.format_exc())


if __name__ == "__main__":
    asyncio.run(main())
