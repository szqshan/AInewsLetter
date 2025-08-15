#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试Semantic Scholar API连接
"""

import asyncio
import aiohttp
import json


async def test_api():
    """测试API连接"""
    print("🔬 测试Semantic Scholar API连接")
    print("=" * 40)
    
    base_url = "https://api.semanticscholar.org/graph/v1"
    
    # 测试简单搜索
    search_url = f"{base_url}/paper/search"
    params = {
        'query': 'machine learning',
        'limit': 5,
        'fields': 'paperId,title,year,citationCount'
    }
    
    headers = {
        'User-Agent': 'Test-Client/1.0',
        'Accept': 'application/json'
    }
    
    try:
        async with aiohttp.ClientSession(headers=headers) as session:
            print(f"🌐 请求URL: {search_url}")
            print(f"📝 参数: {params}")
            
            async with session.get(search_url, params=params) as response:
                print(f"📡 状态码: {response.status}")
                print(f"📋 响应头: {dict(response.headers)}")
                
                if response.status == 200:
                    try:
                        data = await response.json()
                        print(f"✅ 请求成功!")
                        print(f"📊 数据结构: {type(data)}")
                        
                        if isinstance(data, dict):
                            print(f"🔑 数据键: {list(data.keys())}")
                            
                            if 'data' in data:
                                papers = data['data']
                                print(f"📚 论文数量: {len(papers)}")
                                
                                if papers:
                                    print("\n📄 第一篇论文:")
                                    first_paper = papers[0]
                                    for key, value in first_paper.items():
                                        print(f"  {key}: {value}")
                            else:
                                print("⚠️ 响应中没有'data'字段")
                        else:
                            print(f"❌ 期望dict类型，实际: {type(data)}")
                            print(f"内容: {data}")
                            
                    except json.JSONDecodeError as e:
                        print(f"❌ JSON解析失败: {e}")
                        text = await response.text()
                        print(f"响应内容: {text[:500]}")
                        
                else:
                    text = await response.text()
                    print(f"❌ 请求失败: {response.status}")
                    print(f"响应内容: {text[:500]}")
                    
    except Exception as e:
        print(f"❌ 连接错误: {e}")
        import traceback
        print(f"详细错误: {traceback.format_exc()}")


if __name__ == "__main__":
    asyncio.run(test_api())
