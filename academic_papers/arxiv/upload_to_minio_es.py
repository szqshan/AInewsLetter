#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
arXiv论文数据上传到MinIO和Elasticsearch
通过MinIO连接器API上传论文数据
"""

import json
import requests
import asyncio
import aiohttp
import sys
from pathlib import Path
from typing import List, Dict, Any
import logging
from datetime import datetime
import argparse

# 添加src目录到Python路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

from arxiv_system.utils.file_utils import load_config, setup_logging


class ArxivUploader:
    """arXiv论文上传器"""
    
    def __init__(self, config_path: str = "config_enhanced.json"):
        """初始化上传器"""
        self.config = load_config(config_path)
        self.oss_config = self.config.get("oss", {})
        
        self.api_endpoint = self.oss_config.get("api_endpoint", "http://localhost:9011")
        self.upload_endpoint = self.oss_config.get("upload_endpoint", "/api/documents/upload-articles")
        self.es_endpoint = self.oss_config.get("elasticsearch_endpoint", "/api/elasticsearch/articles")
        self.bucket_name = self.oss_config.get("bucket_name", "arxiv-papers")
        
        self.logger = logging.getLogger(__name__)
        
        print(f"🔧 配置信息:")
        print(f"   API地址: {self.api_endpoint}")
        print(f"   上传端点: {self.upload_endpoint}")
        print(f"   ES端点: {self.es_endpoint}")
        print(f"   存储桶: {self.bucket_name}")
    
    def check_service_health(self) -> bool:
        """检查MinIO连接器服务健康状态"""
        try:
            response = requests.get(f"{self.api_endpoint}/health", timeout=10)
            if response.status_code == 200:
                print("✅ MinIO连接器服务正常运行")
                return True
            else:
                print(f"❌ MinIO连接器服务异常，状态码: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ 无法连接到MinIO连接器服务: {e}")
            return False
    
    def load_papers_from_file(self, file_path: str) -> List[Dict[str, Any]]:
        """从JSON文件加载论文数据"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                papers = json.load(f)
            
            if isinstance(papers, list):
                print(f"📄 从 {file_path} 加载了 {len(papers)} 篇论文")
                return papers
            else:
                print(f"❌ 文件格式错误，期望列表格式")
                return []
                
        except Exception as e:
            print(f"❌ 加载文件失败 {file_path}: {e}")
            return []
    
    def convert_to_upload_format(self, papers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """将arXiv论文数据转换为上传格式"""
        converted_papers = []
        
        for paper in papers:
            # 转换为MinIO连接器期望的格式
            converted_paper = {
                "title": paper.get("title", "").strip(),
                "content": paper.get("abstract", "").strip(),
                "authors": paper.get("authors", []),
                "published_date": paper.get("published", ""),
                "url": paper.get("url", ""),
                "arxiv_id": paper.get("arxiv_id", ""),
                "categories": paper.get("categories", []),
                "pdf_url": paper.get("pdf_url", ""),
                "source": "arxiv",
                "source_id": paper.get("arxiv_id", ""),
                "tags": paper.get("categories", []),
                "metadata": {
                    "updated": paper.get("updated", ""),
                    "primary_category": paper.get("primary_category", ""),
                    "updated_date": paper.get("updated", "")
                }
            }
            
            # 确保必要字段不为空
            if converted_paper["title"] and converted_paper["content"]:
                converted_papers.append(converted_paper)
            else:
                self.logger.warning(f"跳过无效论文: {paper.get('arxiv_id', 'unknown')}")
        
        print(f"📋 转换完成: {len(converted_papers)} 篇有效论文")
        return converted_papers
    
    def upload_papers_to_minio_es(self, papers: List[Dict[str, Any]], 
                                 batch_size: int = 50) -> Dict[str, Any]:
        """批量上传论文到MinIO和Elasticsearch"""
        print(f"☁️ 开始批量上传 {len(papers)} 篇论文...")
        
        total_uploaded = 0
        total_failed = 0
        failed_papers = []
        
        # 分批上传
        for i in range(0, len(papers), batch_size):
            batch = papers[i:i + batch_size]
            batch_num = i // batch_size + 1
            total_batches = (len(papers) + batch_size - 1) // batch_size
            
            print(f"\n📦 上传批次 {batch_num}/{total_batches} ({len(batch)} 篇论文)")
            
            try:
                # 准备上传数据
                upload_data = {
                    "articles": batch,
                    "bucket_name": self.bucket_name,
                    "batch_size": len(batch)
                }
                
                # 发送POST请求
                response = requests.post(
                    f"{self.api_endpoint}{self.upload_endpoint}",
                    json=upload_data,
                    timeout=300,  # 5分钟超时
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    result = response.json()
                    uploaded_count = result.get("uploaded_count", 0)
                    total_uploaded += uploaded_count
                    print(f"   ✅ 批次上传成功: {uploaded_count} 篇")
                    
                    # 显示详细结果
                    if "results" in result:
                        for res in result["results"]:
                            if res.get("success"):
                                print(f"      📄 {res.get('title', 'Unknown')[:50]}...")
                            else:
                                print(f"      ❌ 失败: {res.get('error', 'Unknown error')}")
                else:
                    print(f"   ❌ 批次上传失败: HTTP {response.status_code}")
                    print(f"      错误信息: {response.text}")
                    total_failed += len(batch)
                    failed_papers.extend([p.get("arxiv_id", "unknown") for p in batch])
                    
            except Exception as e:
                print(f"   ❌ 批次上传异常: {e}")
                total_failed += len(batch)
                failed_papers.extend([p.get("arxiv_id", "unknown") for p in batch])
        
        # 汇总结果
        result = {
            "total_papers": len(papers),
            "uploaded_count": total_uploaded,
            "failed_count": total_failed,
            "failed_papers": failed_papers,
            "success_rate": (total_uploaded / len(papers)) * 100 if len(papers) > 0 else 0
        }
        
        print(f"\n🎯 上传完成统计:")
        print(f"   总论文数: {result['total_papers']}")
        print(f"   成功上传: {result['uploaded_count']}")
        print(f"   失败数量: {result['failed_count']}")
        print(f"   成功率: {result['success_rate']:.1f}%")
        
        return result
    
    def query_elasticsearch(self, query: str = "*", size: int = 10) -> Dict[str, Any]:
        """查询Elasticsearch中的论文数据"""
        try:
            search_data = {
                "query": query,
                "size": size,
                "from": 0
            }
            
            response = requests.post(
                f"{self.api_endpoint}{self.es_endpoint}/search",
                json=search_data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                total_hits = result.get("total", 0)
                hits = result.get("hits", [])
                
                print(f"🔍 Elasticsearch查询结果:")
                print(f"   总文档数: {total_hits}")
                print(f"   返回结果: {len(hits)}")
                
                if hits:
                    print(f"   最新论文示例:")
                    for i, hit in enumerate(hits[:3], 1):
                        source = hit.get("_source", {})
                        title = source.get("title", "Unknown")[:60]
                        arxiv_id = source.get("arxiv_id", "Unknown")
                        print(f"      {i}. {title}... (ID: {arxiv_id})")
                
                return result
            else:
                print(f"❌ Elasticsearch查询失败: HTTP {response.status_code}")
                return {}
                
        except Exception as e:
            print(f"❌ Elasticsearch查询异常: {e}")
            return {}
    
    def get_elasticsearch_stats(self) -> Dict[str, Any]:
        """获取Elasticsearch统计信息"""
        try:
            response = requests.get(
                f"{self.api_endpoint}{self.es_endpoint}/stats",
                timeout=30
            )
            
            if response.status_code == 200:
                stats = response.json()
                print(f"📊 Elasticsearch统计信息:")
                print(f"   索引名称: {stats.get('index_name', 'Unknown')}")
                print(f"   文档总数: {stats.get('doc_count', 0)}")
                print(f"   存储大小: {stats.get('store_size', 'Unknown')}")
                
                return stats
            else:
                print(f"❌ 获取ES统计失败: HTTP {response.status_code}")
                return {}
                
        except Exception as e:
            print(f"❌ 获取ES统计异常: {e}")
            return {}


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="上传arXiv论文到MinIO和Elasticsearch")
    parser.add_argument("--file", required=True, help="论文JSON文件路径")
    parser.add_argument("--batch-size", type=int, default=50, help="批次大小")
    parser.add_argument("--query", action="store_true", help="上传后查询验证")
    parser.add_argument("--stats", action="store_true", help="显示ES统计信息")
    parser.add_argument("--config", default="config_enhanced.json", help="配置文件路径")
    
    args = parser.parse_args()
    
    # 设置日志
    setup_logging()
    
    print("🚀 arXiv论文上传工具")
    print("=" * 50)
    
    # 初始化上传器
    uploader = ArxivUploader(args.config)
    
    # 检查服务健康状态
    if not uploader.check_service_health():
        print("❌ MinIO连接器服务不可用，请先启动服务")
        sys.exit(1)
    
    # 加载论文数据
    papers = uploader.load_papers_from_file(args.file)
    if not papers:
        print("❌ 没有找到有效的论文数据")
        sys.exit(1)
    
    # 转换数据格式
    converted_papers = uploader.convert_to_upload_format(papers)
    if not converted_papers:
        print("❌ 没有有效的论文可以上传")
        sys.exit(1)
    
    # 上传论文
    result = uploader.upload_papers_to_minio_es(converted_papers, args.batch_size)
    
    # 查询验证
    if args.query:
        print("\n" + "=" * 50)
        uploader.query_elasticsearch("*", 5)
    
    # 显示统计信息
    if args.stats:
        print("\n" + "=" * 50)
        uploader.get_elasticsearch_stats()
    
    # 保存上传结果
    result_file = f"upload_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(result_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    print(f"\n📄 上传结果已保存到: {result_file}")
    
    if result["success_rate"] >= 90:
        print("🎉 上传成功！")
        sys.exit(0)
    else:
        print("⚠️ 部分上传失败，请检查错误信息")
        sys.exit(1)


if __name__ == "__main__":
    main()
