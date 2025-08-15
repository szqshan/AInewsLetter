#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
超保守的Semantic Scholar API测试
使用极低的请求频率避免429错误
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime


class ConservativeCrawler:
    """超保守的爬虫，避免频率限制"""
    
    def __init__(self):
        self.base_url = "https://api.semanticscholar.org/graph/v1"
        self.request_interval = 15.0  # 每15秒1次请求
        self.last_request_time = 0
        self.request_count = 0
        
        self.headers = {
            'User-Agent': 'Academic-Research-Tool/1.0',
            'Accept': 'application/json'
        }
        
    async def wait_for_rate_limit(self):
        """等待频率限制"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.request_interval:
            sleep_time = self.request_interval - time_since_last
            print(f"⏰ 频率控制等待 {sleep_time:.1f} 秒...")
            await asyncio.sleep(sleep_time)
        
        self.last_request_time = time.time()
        self.request_count += 1
        
    async def safe_request(self, session, url, params):
        """安全的API请求"""
        await self.wait_for_rate_limit()
        
        print(f"🌐 请求 #{self.request_count}: {url}")
        print(f"📝 参数: {params}")
        
        try:
            async with session.get(url, params=params) as response:
                print(f"📡 响应状态: {response.status}")
                
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ 请求成功")
                    return data
                    
                elif response.status == 429:
                    retry_after = response.headers.get('Retry-After', '300')
                    print(f"🚫 频率限制! 建议等待 {retry_after} 秒")
                    
                    # 等待更长时间
                    wait_time = max(int(retry_after), 300)  # 至少等待5分钟
                    print(f"😴 等待 {wait_time} 秒后重试...")
                    await asyncio.sleep(wait_time)
                    
                    # 重试一次
                    await self.wait_for_rate_limit()
                    async with session.get(url, params=params) as retry_response:
                        if retry_response.status == 200:
                            return await retry_response.json()
                        else:
                            print(f"❌ 重试失败: {retry_response.status}")
                            return None
                else:
                    text = await response.text()
                    print(f"❌ 请求失败 {response.status}: {text[:200]}")
                    return None
                    
        except Exception as e:
            print(f"❌ 请求异常: {e}")
            return None
    
    async def test_single_search(self):
        """测试单个搜索请求"""
        print("\n🔍 测试单个搜索请求")
        print("-" * 30)
        
        async with aiohttp.ClientSession(headers=self.headers) as session:
            search_url = f"{self.base_url}/paper/search"
            
            params = {
                'query': 'machine learning',
                'limit': 5,
                'fields': 'paperId,title,year,citationCount'
            }
            
            result = await self.safe_request(session, search_url, params)
            
            if result and isinstance(result, dict) and 'data' in result:
                papers = result['data']
                print(f"📚 找到 {len(papers)} 篇论文:")
                
                for i, paper in enumerate(papers, 1):
                    title = paper.get('title', '无标题')[:60]
                    year = paper.get('year', '未知')
                    citations = paper.get('citationCount', 0)
                    print(f"  {i}. {title}... ({year}, {citations}引用)")
                
                return papers
            else:
                print("❌ 搜索失败或无数据")
                return None
    
    async def test_multiple_searches(self):
        """测试多个搜索（非常保守）"""
        print("\n🔄 测试多个搜索请求")
        print("-" * 30)
        
        queries = ["artificial intelligence", "deep learning"]  # 只测试2个
        all_papers = []
        
        async with aiohttp.ClientSession(headers=self.headers) as session:
            for i, query in enumerate(queries, 1):
                print(f"\n📝 搜索 {i}/{len(queries)}: {query}")
                
                search_url = f"{self.base_url}/paper/search"
                params = {
                    'query': query,
                    'limit': 3,  # 减少数量
                    'fields': 'paperId,title,year,citationCount'
                }
                
                result = await self.safe_request(session, search_url, params)
                
                if result and isinstance(result, dict) and 'data' in result:
                    papers = result['data']
                    print(f"  ✅ 找到 {len(papers)} 篇论文")
                    all_papers.extend(papers)
                else:
                    print(f"  ❌ 搜索失败: {query}")
        
        print(f"\n📊 总计: {len(all_papers)} 篇论文")
        return all_papers


async def main():
    """主测试函数"""
    print("🐌 Semantic Scholar 超保守测试")
    print("=" * 50)
    print("⚠️  使用极低频率请求，避免429错误")
    print("⏰ 每个请求间隔15秒，请耐心等待...")
    print("=" * 50)
    
    crawler = ConservativeCrawler()
    
    try:
        start_time = time.time()
        
        # 测试1: 单个搜索
        papers1 = await crawler.test_single_search()
        
        if papers1:
            print(f"\n✅ 单个搜索成功: {len(papers1)} 篇论文")
            
            # 继续测试多个搜索
            papers2 = await crawler.test_multiple_searches()
            
            if papers2:
                print(f"✅ 多个搜索成功: {len(papers2)} 篇论文")
            
            # 保存结果
            all_papers = (papers1 or []) + (papers2 or [])
            if all_papers:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"conservative_test_{timestamp}.json"
                
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(all_papers, f, ensure_ascii=False, indent=2)
                
                print(f"💾 结果已保存: {filename}")
        
        elapsed = time.time() - start_time
        print(f"\n⏱️  总耗时: {elapsed:.1f} 秒")
        print(f"📊 总请求: {crawler.request_count} 次")
        print(f"📈 平均间隔: {elapsed/max(crawler.request_count, 1):.1f} 秒/请求")
        
    except KeyboardInterrupt:
        print("\n⚠️ 用户中断测试")
    except Exception as e:
        print(f"\n❌ 测试异常: {e}")
        import traceback
        print(traceback.format_exc())


if __name__ == "__main__":
    asyncio.run(main())
