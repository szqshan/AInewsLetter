#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
arXiv论文文章上传到MinIO和Elasticsearch
将论文转换为Markdown文件后上传，利用文档处理管道自动索引
"""

import json
import requests
import sys
import os
from pathlib import Path
from typing import List, Dict, Any
import logging
from datetime import datetime
import argparse

# 添加src目录到Python路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

from arxiv_system.utils.file_utils import load_config, setup_logging, ensure_directory


class ArxivArticleUploader:
    """arXiv论文文章上传器"""
    
    def __init__(self, config_path: str = "config_enhanced.json"):
        """初始化上传器"""
        self.config = load_config(config_path)
        self.oss_config = self.config.get("oss", {})
        
        self.api_endpoint = self.oss_config.get("api_endpoint", "http://localhost:9011")
        self.bucket_name = self.oss_config.get("bucket_name", "arxiv-papers")
        
        self.logger = logging.getLogger(__name__)
        
        print(f"🔧 配置信息:")
        print(f"   API地址: {self.api_endpoint}")
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
    
    def create_bucket_if_not_exists(self) -> bool:
        """创建存储桶（如果不存在）"""
        try:
            # 先检查存储桶是否存在
            response = requests.get(f"{self.api_endpoint}/api/v1/buckets", timeout=10)
            if response.status_code == 200:
                buckets_data = response.json()
                if isinstance(buckets_data, dict):
                    bucket_list = buckets_data.get("buckets", [])
                else:
                    bucket_list = buckets_data if isinstance(buckets_data, list) else []
                bucket_names = [bucket.get("name", "") if isinstance(bucket, dict) else str(bucket) for bucket in bucket_list]
                
                if self.bucket_name in bucket_names:
                    print(f"✅ 存储桶 {self.bucket_name} 已存在")
                    return True
                else:
                    print(f"🔧 创建存储桶 {self.bucket_name}")
                    create_response = requests.post(
                        f"{self.api_endpoint}/api/v1/buckets",
                        json={"name": self.bucket_name},
                        timeout=10
                    )
                    if create_response.status_code == 201:
                        print(f"✅ 存储桶 {self.bucket_name} 创建成功")
                        return True
                    else:
                        print(f"❌ 创建存储桶失败: {create_response.status_code}")
                        return False
            else:
                print(f"❌ 获取存储桶列表失败: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ 检查/创建存储桶异常: {e}")
            return False
    
    def convert_paper_to_markdown(self, paper: Dict[str, Any]) -> str:
        """将论文数据转换为Markdown格式"""
        title = paper.get("title", "").strip()
        abstract = paper.get("abstract", "").strip()
        authors = paper.get("authors", [])
        arxiv_id = paper.get("arxiv_id", "")
        url = paper.get("url", "")
        pdf_url = paper.get("pdf_url", "")
        published = paper.get("published", "")
        categories = paper.get("categories", [])
        primary_category = paper.get("primary_category", "")
        
        # 生成Markdown内容
        markdown_content = f"""# {title}

## 基本信息

- **arXiv ID**: {arxiv_id}
- **发布日期**: {published}
- **主要分类**: {primary_category}
- **所有分类**: {', '.join(categories)}
- **作者**: {', '.join(authors)}

## 链接

- **arXiv页面**: {url}
- **PDF下载**: {pdf_url}

## 摘要

{abstract}
"""
        
        return markdown_content
    
    def upload_paper_as_markdown(self, paper: Dict[str, Any], temp_dir: str) -> Dict[str, Any]:
        """将单篇论文转换为Markdown并上传"""
        try:
            # 检查必要字段
            title = paper.get("title", "").strip()
            abstract = paper.get("abstract", "").strip()
            arxiv_id = paper.get("arxiv_id", "")
            
            if not title or not abstract or not arxiv_id:
                return {
                    "success": False,
                    "error": "缺少必要字段",
                    "arxiv_id": arxiv_id
                }
            
            # 转换为Markdown
            markdown_content = self.convert_paper_to_markdown(paper)
            
            # 创建临时文件
            safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()[:50]
            filename = f"{arxiv_id}_{safe_title}.md"
            file_path = os.path.join(temp_dir, filename)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            
            # 上传到MinIO
            object_name = f"arxiv/{datetime.now().strftime('%Y/%m')}/{filename}"
            
            with open(file_path, 'rb') as f:
                files = {'file': (filename, f, 'text/markdown')}
                data = {
                    'object_name': object_name,
                    'use_pipeline': 'true'  # 启用文档处理管道
                }
                
                response = requests.post(
                    f"{self.api_endpoint}/api/v1/objects/{self.bucket_name}/upload",
                    files=files,
                    data=data,
                    timeout=60
                )
            
            # 删除临时文件
            try:
                os.remove(file_path)
            except:
                pass
            
            if response.status_code in [200, 201]:
                result = response.json()
                return {
                    "success": True,
                    "title": title,
                    "arxiv_id": arxiv_id,
                    "object_name": object_name,
                    "public_url": result.get("public_url", ""),
                    "es_indexed": result.get("es_indexed", False),
                    "es_document_id": result.get("es_document_id", "")
                }
            else:
                return {
                    "success": False,
                    "error": f"上传失败 HTTP {response.status_code}: {response.text}",
                    "arxiv_id": arxiv_id
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "arxiv_id": paper.get("arxiv_id", "unknown")
            }
    
    def upload_papers_batch(self, papers: List[Dict[str, Any]]) -> Dict[str, Any]:
        """批量上传论文"""
        print(f"📚 开始批量上传 {len(papers)} 篇论文...")
        
        # 创建临时目录
        temp_dir = "temp_markdown_files"
        ensure_directory(temp_dir)
        
        total_uploaded = 0
        total_failed = 0
        failed_papers = []
        successful_papers = []
        
        try:
            for i, paper in enumerate(papers, 1):
                print(f"\n📄 上传进度 {i}/{len(papers)}: {paper.get('title', 'Unknown')[:60]}...")
                
                result = self.upload_paper_as_markdown(paper, temp_dir)
                
                if result["success"]:
                    total_uploaded += 1
                    successful_papers.append(result)
                    print(f"   ✅ 上传成功")
                    if result.get("es_indexed"):
                        print(f"   📊 已索引到Elasticsearch")
                    if result.get("public_url"):
                        print(f"   🔗 公开URL: {result['public_url']}")
                else:
                    total_failed += 1
                    failed_papers.append(result)
                    print(f"   ❌ 上传失败: {result.get('error', 'Unknown error')}")
                
                # 避免请求过于频繁
                if i % 10 == 0:
                    print(f"   💤 休息2秒...")
                    import time
                    time.sleep(2)
        
        finally:
            # 清理临时目录
            try:
                import shutil
                shutil.rmtree(temp_dir)
            except:
                pass
        
        # 汇总结果
        result = {
            "total_papers": len(papers),
            "uploaded_count": total_uploaded,
            "failed_count": total_failed,
            "failed_papers": failed_papers,
            "successful_papers": successful_papers,
            "success_rate": (total_uploaded / len(papers)) * 100 if len(papers) > 0 else 0
        }
        
        print(f"\n🎯 上传完成统计:")
        print(f"   总论文数: {result['total_papers']}")
        print(f"   成功上传: {result['uploaded_count']}")
        print(f"   失败数量: {result['failed_count']}")
        print(f"   成功率: {result['success_rate']:.1f}%")
        
        return result
    
    def search_uploaded_papers(self, query: str = "arxiv", size: int = 10) -> Dict[str, Any]:
        """搜索已上传的论文"""
        try:
            response = requests.get(
                f"{self.api_endpoint}/api/v1/documents/search",
                params={
                    "query": query,
                    "size": size,
                    "bucket_name": self.bucket_name
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"🔍 搜索结果:")
                print(f"   总文档数: {result.get('total', 0)}")
                
                documents = result.get('documents', [])
                if documents:
                    print(f"   返回结果: {len(documents)}")
                    print(f"   最新论文示例:")
                    for i, doc in enumerate(documents[:3], 1):
                        title = doc.get("title", "Unknown")[:60]
                        score = doc.get("_score", 0)
                        print(f"      {i}. {title}... (评分: {score:.2f})")
                
                return result
            else:
                print(f"❌ 搜索失败: HTTP {response.status_code}")
                return {}
                
        except Exception as e:
            print(f"❌ 搜索异常: {e}")
            return {}
    
    def get_document_stats(self) -> Dict[str, Any]:
        """获取文档统计信息"""
        try:
            response = requests.get(
                f"{self.api_endpoint}/api/v1/documents/stats",
                timeout=30
            )
            
            if response.status_code == 200:
                stats = response.json()
                print(f"📊 文档统计信息:")
                print(f"   总文档数: {stats.get('total_documents', 0)}")
                print(f"   平均字数: {stats.get('average_word_count', 0)}")
                print(f"   总存储大小: {stats.get('total_size_bytes', 0)} 字节")
                
                by_bucket = stats.get('by_bucket', [])
                if by_bucket:
                    print(f"   按存储桶分布:")
                    for bucket_stat in by_bucket:
                        print(f"      {bucket_stat['bucket']}: {bucket_stat['count']} 个文档")
                
                return stats
            else:
                print(f"❌ 获取统计失败: HTTP {response.status_code}")
                return {}
                
        except Exception as e:
            print(f"❌ 获取统计异常: {e}")
            return {}


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="上传arXiv论文到MinIO和Elasticsearch")
    parser.add_argument("--file", required=True, help="论文JSON文件路径")
    parser.add_argument("--search", action="store_true", help="上传后搜索验证")
    parser.add_argument("--stats", action="store_true", help="显示统计信息")
    parser.add_argument("--config", default="config_enhanced.json", help="配置文件路径")
    
    args = parser.parse_args()
    
    # 设置日志
    setup_logging()
    
    print("🚀 arXiv论文文章上传工具")
    print("=" * 50)
    
    # 初始化上传器
    uploader = ArxivArticleUploader(args.config)
    
    # 检查服务健康状态
    if not uploader.check_service_health():
        print("❌ MinIO连接器服务不可用，请先启动服务")
        sys.exit(1)
    
    # 创建存储桶
    if not uploader.create_bucket_if_not_exists():
        print("❌ 存储桶创建/检查失败")
        sys.exit(1)
    
    # 加载论文数据
    papers = uploader.load_papers_from_file(args.file)
    if not papers:
        print("❌ 没有找到有效的论文数据")
        sys.exit(1)
    
    # 上传论文
    result = uploader.upload_papers_batch(papers)
    
    # 搜索验证
    if args.search:
        print("\n" + "=" * 50)
        uploader.search_uploaded_papers("arxiv", 5)
    
    # 显示统计信息
    if args.stats:
        print("\n" + "=" * 50)
        uploader.get_document_stats()
    
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
