#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Semantic Scholar 无API密钥爬虫
使用公共API，严格控制请求频率，避免被限制
"""

import asyncio
import json
import logging
import os
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
import aiohttp
import aiofiles

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SemanticScholarPublicCrawler:
    """Semantic Scholar公共API爬虫
    
    严格遵守频率限制：
    - 无API密钥：100 requests/5min (约1.33 RPS)
    - 实际使用：0.5 RPS (每2秒1次请求)
    """
    
    def __init__(self, output_dir: str = "crawled_data"):
        self.base_url = "https://api.semanticscholar.org/graph/v1"
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 超严格的频率控制
        self.request_interval = 10.0  # 每10秒1次请求
        self.last_request_time = 0
        
        # 请求统计
        self.request_count = 0
        self.session_start_time = time.time()
        
        # 会话配置
        self.session = None
        self.headers = {
            'User-Agent': 'AI-Newsletter-Scholar-Crawler/1.0',
            'Accept': 'application/json'
        }
        
        # 数据存储
        self.papers_data = []
        self.failed_requests = []
        
    async def __aenter__(self):
        """异步上下文管理器入口"""
        connector = aiohttp.TCPConnector(limit=1)  # 限制并发连接数
        timeout = aiohttp.ClientTimeout(total=30)
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers=self.headers
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        if self.session:
            await self.session.close()
    
    async def _rate_limit(self):
        """严格的频率限制"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.request_interval:
            sleep_time = self.request_interval - time_since_last
            logger.info(f"🕒 频率限制等待 {sleep_time:.1f} 秒")
            await asyncio.sleep(sleep_time)
        
        self.last_request_time = time.time()
        self.request_count += 1
        
        # 每50次请求输出统计信息
        if self.request_count % 50 == 0:
            elapsed = time.time() - self.session_start_time
            avg_rps = self.request_count / elapsed
            logger.info(f"📊 请求统计: {self.request_count} 次请求, 平均 {avg_rps:.2f} RPS")
    
    async def _make_request(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        """发起API请求，包含重试机制"""
        await self._rate_limit()
        
        url = f"{self.base_url}/{endpoint}"
        logger.info(f"🌐 请求URL: {url}")
        logger.info(f"📝 请求参数: {params}")
        
        for attempt in range(3):  # 最多重试3次
            try:
                async with self.session.get(url, params=params) as response:
                    logger.info(f"📡 响应状态: {response.status}")
                    
                    if response.status == 200:
                        try:
                            data = await response.json()
                            logger.info(f"✅ 请求成功: {endpoint}, 数据类型: {type(data)}")
                            if isinstance(data, dict) and 'data' in data:
                                logger.info(f"📊 返回数据数量: {len(data.get('data', []))}")
                            return data
                        except Exception as json_error:
                            logger.error(f"❌ JSON解析错误: {json_error}")
                            response_text = await response.text()
                            logger.error(f"❌ 响应内容: {response_text[:500]}")
                            return None
                        
                    elif response.status == 429:
                        # 被限制频率
                        retry_after = int(response.headers.get('Retry-After', 60))
                        logger.warning(f"⚠️ 频率限制，等待 {retry_after} 秒后重试")
                        await asyncio.sleep(retry_after)
                        continue
                        
                    elif response.status == 404:
                        logger.warning(f"⚠️ 资源未找到: {endpoint}")
                        return None
                        
                    else:
                        response_text = await response.text()
                        logger.error(f"❌ HTTP错误 {response.status}: {endpoint}")
                        logger.error(f"❌ 响应内容: {response_text[:500]}")
                        if attempt < 2:  # 不是最后一次尝试
                            await asyncio.sleep(5)  # 等待5秒后重试
                        
            except aiohttp.ClientError as e:
                logger.error(f"❌ 网络错误 (尝试 {attempt + 1}/3): {e}")
                if attempt < 2:
                    await asyncio.sleep(5)
            except Exception as e:
                logger.error(f"❌ 未知错误: {e}")
                import traceback
                logger.error(f"❌ 错误详情: {traceback.format_exc()}")
                break
        
        # 记录失败的请求
        self.failed_requests.append({
            'endpoint': endpoint,
            'params': params,
            'timestamp': datetime.now().isoformat()
        })
        return None
    
    async def search_papers(self, query: str, limit: int = 100, offset: int = 0) -> Optional[Dict]:
        """搜索论文"""
        # 基础字段，避免请求过多数据
        fields = [
            'paperId', 'title', 'abstract', 'authors', 'year',
            'citationCount', 'referenceCount', 'influentialCitationCount',
            'fieldsOfStudy', 'venue', 'url'
        ]
        
        params = {
            'query': query,
            'limit': min(limit, 100),  # API限制
            'offset': offset,
            'fields': ','.join(fields)
        }
        
        logger.info(f"🔍 搜索论文: {query} (limit={limit}, offset={offset})")
        return await self._make_request('paper/search', params)
    
    async def get_paper_details(self, paper_id: str) -> Optional[Dict]:
        """获取论文详情"""
        fields = [
            'paperId', 'title', 'abstract', 'authors', 'year',
            'citationCount', 'referenceCount', 'influentialCitationCount',
            'fieldsOfStudy', 'venue', 'journal', 'url', 'externalIds',
            'publicationDate', 'publicationTypes'
        ]
        
        params = {'fields': ','.join(fields)}
        
        logger.info(f"📄 获取论文详情: {paper_id}")
        return await self._make_request(f'paper/{paper_id}', params)
    
    def filter_relevant_papers(self, papers: List[Dict]) -> List[Dict]:
        """过滤相关论文"""
        filtered = []
        
        for paper in papers:
            # 基本过滤条件
            year = paper.get('year')
            citation_count = paper.get('citationCount', 0)
            title = paper.get('title', '')
            abstract = paper.get('abstract', '')
            
            # 年份过滤：只要2020年以后的论文（更容易找到数据）
            if not year or year < 2020:
                continue
            
            # 引用数过滤：至少有1次引用（降低门槛）
            if citation_count < 1:
                continue
            
            # 标题和摘要不能为空
            if not title or not abstract:
                continue
            
            # 检查是否与AI相关
            if self._is_ai_related(paper):
                filtered.append(paper)
        
        return filtered
    
    def _is_ai_related(self, paper: Dict) -> bool:
        """判断论文是否与AI相关"""
        # 检查研究领域
        fields_of_study = paper.get('fieldsOfStudy', [])
        ai_fields = {'Computer Science', 'Mathematics', 'Engineering'}
        
        if not any(field in ai_fields for field in fields_of_study):
            return False
        
        # 检查标题和摘要中的AI关键词
        title = paper.get('title', '').lower()
        abstract = paper.get('abstract', '').lower()
        text = f"{title} {abstract}"
        
        ai_keywords = [
            'artificial intelligence', 'machine learning', 'deep learning',
            'neural network', 'transformer', 'attention', 'bert', 'gpt',
            'computer vision', 'natural language', 'nlp', 'reinforcement learning',
            'convolutional', 'recurrent', 'lstm', 'gan', 'generative',
            'classification', 'detection', 'recognition', 'prediction'
        ]
        
        return any(keyword in text for keyword in ai_keywords)
    
    async def crawl_ai_papers(self, max_papers: int = 500):
        """爬取AI相关论文"""
        logger.info(f"🚀 开始爬取AI论文，目标数量: {max_papers}")
        
        # AI相关搜索查询
        search_queries = [
            "artificial intelligence",
            "machine learning", 
            "deep learning",
            "neural networks",
            "computer vision",
            "natural language processing",
            "transformer models",
            "reinforcement learning"
        ]
        
        all_papers = []
        papers_per_query = max_papers // len(search_queries)
        
        for query in search_queries:
            logger.info(f"🔍 搜索查询: {query}")
            
            offset = 0
            papers_collected = 0
            
            while papers_collected < papers_per_query:
                # 计算本次请求数量
                limit = min(100, papers_per_query - papers_collected)
                
                # 搜索论文
                result = await self.search_papers(query, limit, offset)
                
                if not result or not isinstance(result, dict) or 'data' not in result:
                    logger.warning(f"❌ 搜索失败或无数据: {query}, result: {result}")
                    break
                
                papers = result.get('data', [])
                if not papers or not isinstance(papers, list):
                    logger.info(f"📭 无更多结果: {query}")
                    break
                
                # 过滤相关论文
                relevant_papers = self.filter_relevant_papers(papers)
                
                for paper in relevant_papers:
                    paper['search_query'] = query
                    paper['crawl_timestamp'] = datetime.now().isoformat()
                    all_papers.append(paper)
                
                papers_collected += len(papers)
                offset += len(papers)
                
                logger.info(f"📊 已收集 {len(relevant_papers)}/{len(papers)} 相关论文")
                
                # 如果返回的论文数少于请求数，说明没有更多结果
                if len(papers) < limit:
                    break
        
        # 去重
        unique_papers = self._deduplicate_papers(all_papers)
        logger.info(f"📋 去重后论文数量: {len(unique_papers)}")
        
        self.papers_data = unique_papers
        return unique_papers
    
    def _deduplicate_papers(self, papers: List[Dict]) -> List[Dict]:
        """去重论文"""
        seen_ids = set()
        seen_titles = set()
        unique_papers = []
        
        for paper in papers:
            paper_id = paper.get('paperId')
            title = paper.get('title', '').lower().strip()
            
            # 按论文ID去重
            if paper_id and paper_id in seen_ids:
                continue
            
            # 按标题去重
            if title and title in seen_titles:
                continue
            
            if paper_id:
                seen_ids.add(paper_id)
            if title:
                seen_titles.add(title)
            
            unique_papers.append(paper)
        
        return unique_papers
    
    async def save_results(self):
        """保存爬取结果"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 保存论文数据
        papers_file = self.output_dir / f"papers_{timestamp}.json"
        async with aiofiles.open(papers_file, 'w', encoding='utf-8') as f:
            await f.write(json.dumps(self.papers_data, ensure_ascii=False, indent=2))
        
        # 保存摘要报告
        summary_file = self.output_dir / f"summary_{timestamp}.md"
        summary = self._generate_summary()
        async with aiofiles.open(summary_file, 'w', encoding='utf-8') as f:
            await f.write(summary)
        
        # 保存失败的请求
        if self.failed_requests:
            failed_file = self.output_dir / f"failed_requests_{timestamp}.json"
            async with aiofiles.open(failed_file, 'w', encoding='utf-8') as f:
                await f.write(json.dumps(self.failed_requests, ensure_ascii=False, indent=2))
        
        logger.info(f"💾 结果已保存:")
        logger.info(f"   论文数据: {papers_file}")
        logger.info(f"   摘要报告: {summary_file}")
        if self.failed_requests:
            logger.info(f"   失败请求: {failed_file}")
    
    def _generate_summary(self) -> str:
        """生成爬取摘要报告"""
        total_papers = len(self.papers_data)
        
        # 按年份统计
        papers_by_year = {}
        for paper in self.papers_data:
            year = paper.get('year', 'Unknown')
            papers_by_year[year] = papers_by_year.get(year, 0) + 1
        
        # 按领域统计
        papers_by_field = {}
        for paper in self.papers_data:
            fields = paper.get('fieldsOfStudy', [])
            for field in fields:
                papers_by_field[field] = papers_by_field.get(field, 0) + 1
        
        # 引用统计
        citations = [paper.get('citationCount', 0) for paper in self.papers_data]
        avg_citations = sum(citations) / len(citations) if citations else 0
        max_citations = max(citations) if citations else 0
        
        summary = f"""# Semantic Scholar 爬取摘要报告

## 基本信息
- **爬取时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **论文总数**: {total_papers}
- **请求总数**: {self.request_count}
- **失败请求**: {len(self.failed_requests)}

## 数据统计

### 按年份分布
"""
        
        for year in sorted(papers_by_year.keys(), reverse=True):
            count = papers_by_year[year]
            summary += f"- **{year}**: {count} 篇\n"
        
        summary += "\n### 按研究领域分布\n"
        sorted_fields = sorted(papers_by_field.items(), key=lambda x: x[1], reverse=True)
        for field, count in sorted_fields[:10]:  # 只显示前10个
            summary += f"- **{field}**: {count} 篇\n"
        
        summary += f"""
### 引用统计
- **平均引用数**: {avg_citations:.1f}
- **最高引用数**: {max_citations}
- **引用数 > 100**: {len([c for c in citations if c > 100])} 篇
- **引用数 > 50**: {len([c for c in citations if c > 50])} 篇

## 高质量论文 (引用数 > 100)
"""
        
        high_quality_papers = [p for p in self.papers_data if p.get('citationCount', 0) > 100]
        high_quality_papers.sort(key=lambda x: x.get('citationCount', 0), reverse=True)
        
        for paper in high_quality_papers[:10]:  # 显示前10篇
            title = paper.get('title', '无标题')
            citations = paper.get('citationCount', 0)
            year = paper.get('year', '未知')
            summary += f"- **{title}** ({year}) - {citations} 引用\n"
        
        if self.failed_requests:
            summary += f"\n## 失败请求\n"
            summary += f"- **失败请求数**: {len(self.failed_requests)}\n"
            summary += f"- **建议**: 检查网络连接和API限制\n"
        
        return summary


async def main():
    """主函数"""
    print("🔬 Semantic Scholar 无API密钥爬虫")
    print("=" * 50)
    
    # 创建输出目录
    output_dir = "academic_papers/semantic_scholar/crawled_data"
    
    async with SemanticScholarPublicCrawler(output_dir) as crawler:
        try:
            # 爬取AI论文
            papers = await crawler.crawl_ai_papers(max_papers=200)  # 从小数量开始
            
            print(f"\n📊 爬取完成!")
            print(f"   论文数量: {len(papers)}")
            print(f"   请求总数: {crawler.request_count}")
            
            # 保存结果
            await crawler.save_results()
            
            print("\n✅ 所有任务完成!")
            
        except KeyboardInterrupt:
            print("\n⚠️ 用户中断爬取")
            if crawler.papers_data:
                await crawler.save_results()
                print("💾 已保存部分结果")
        except Exception as e:
            print(f"\n❌ 爬取过程中出现错误: {e}")
            if crawler.papers_data:
                await crawler.save_results()
                print("💾 已保存部分结果")


if __name__ == "__main__":
    asyncio.run(main())
