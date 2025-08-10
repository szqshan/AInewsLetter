#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复版：按文件夹结构上传arXiv论文到MinIO和Elasticsearch
每篇论文上传主要文件，保持清洁的MinIO结构
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

from arxiv_system.utils.file_utils import load_config, setup_logging


class PaperFolderUploaderFixed:
    """修复版论文文件夹上传器"""
    
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
    
    def find_paper_folders(self, articles_dir: str) -> List[str]:
        """查找所有论文文件夹"""
        paper_folders = []
        
        if not os.path.exists(articles_dir):
            print(f"❌ 目录不存在: {articles_dir}")
            return paper_folders
        
        for item in os.listdir(articles_dir):
            item_path = os.path.join(articles_dir, item)
            if os.path.isdir(item_path):
                # 检查是否包含必要文件
                content_md = os.path.join(item_path, "content.md")
                metadata_json = os.path.join(item_path, "metadata.json")
                
                if os.path.exists(content_md) and os.path.exists(metadata_json):
                    paper_folders.append(item_path)
        
        print(f"📁 找到 {len(paper_folders)} 个论文文件夹")
        return paper_folders
    
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
    
    def upload_paper_folder_as_single_file(self, paper_folder: str) -> Dict[str, Any]:
        """将论文文件夹作为单个增强的Markdown文件上传
        
        Args:
            paper_folder: 论文文件夹路径
            
        Returns:
            上传结果
        """
        try:
            folder_name = os.path.basename(paper_folder)
            
            # 读取所有相关文件
            files_data = self._collect_all_file_data(paper_folder)
            
            arxiv_id = files_data["metadata"].get('id', 'unknown')
            title = files_data["metadata"].get('title', 'Unknown')
            
            print(f"📄 上传论文: {arxiv_id} - {title[:50]}...")
            
            # 创建增强的Markdown内容
            enhanced_markdown = self._create_enhanced_markdown(files_data)
            
            # 创建完整的元数据
            complete_metadata = self._create_complete_metadata(files_data, folder_name)
            
            # 保持文件夹结构 - 上传主要content.md文件
            object_name = f"{folder_name}/content.md"
            
            # 准备上传数据
            markdown_bytes = enhanced_markdown.encode('utf-8')
            
            files = {'file': (f"{folder_name}.md", markdown_bytes, 'text/markdown')}
            data = {
                'object_name': object_name,
                'metadata': json.dumps(complete_metadata),
                'use_pipeline': 'true'  # 启用ES索引
            }
            
            response = requests.post(
                f"{self.api_endpoint}/api/v1/objects/{self.bucket_name}/upload",
                files=files,
                data=data,
                timeout=120
            )
            
            if response.status_code in [200, 201]:
                result = response.json()
                return {
                    "success": True,
                    "arxiv_id": arxiv_id,
                    "title": title,
                    "folder_name": folder_name,
                    "object_name": object_name,
                    "public_url": result.get("public_url", ""),
                    "es_indexed": result.get("es_indexed", False),
                    "es_document_id": result.get("es_document_id", "")
                }
            else:
                return {
                    "success": False,
                    "arxiv_id": arxiv_id,
                    "error": f"HTTP {response.status_code}: {response.text}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "arxiv_id": "unknown",
                "folder_name": os.path.basename(paper_folder) if paper_folder else "unknown"
            }
    
    def _collect_all_file_data(self, paper_folder: str) -> Dict[str, Any]:
        """收集文件夹中的所有数据"""
        files_data = {
            "metadata": {},
            "content": "",
            "abstract": "",
            "authors": {},
            "categories": {},
            "links": {}
        }
        
        # 读取metadata.json
        metadata_path = os.path.join(paper_folder, "metadata.json")
        if os.path.exists(metadata_path):
            with open(metadata_path, 'r', encoding='utf-8') as f:
                files_data["metadata"] = json.load(f)
        
        # 读取content.md
        content_path = os.path.join(paper_folder, "content.md")
        if os.path.exists(content_path):
            with open(content_path, 'r', encoding='utf-8') as f:
                files_data["content"] = f.read()
        
        # 读取abstract.txt
        abstract_path = os.path.join(paper_folder, "abstract.txt")
        if os.path.exists(abstract_path):
            with open(abstract_path, 'r', encoding='utf-8') as f:
                files_data["abstract"] = f.read()
        
        # 读取authors.json
        authors_path = os.path.join(paper_folder, "authors.json")
        if os.path.exists(authors_path):
            with open(authors_path, 'r', encoding='utf-8') as f:
                files_data["authors"] = json.load(f)
        
        # 读取categories.json
        categories_path = os.path.join(paper_folder, "categories.json")
        if os.path.exists(categories_path):
            with open(categories_path, 'r', encoding='utf-8') as f:
                files_data["categories"] = json.load(f)
        
        # 读取links.json
        links_path = os.path.join(paper_folder, "links.json")
        if os.path.exists(links_path):
            with open(links_path, 'r', encoding='utf-8') as f:
                files_data["links"] = json.load(f)
        
        return files_data
    
    def _create_enhanced_markdown(self, files_data: Dict[str, Any]) -> str:
        """创建增强的Markdown内容，包含所有信息"""
        metadata = files_data["metadata"]
        authors_data = files_data["authors"]
        categories_data = files_data["categories"]
        links_data = files_data["links"]
        
        # 基本信息
        title = metadata.get('title', 'Unknown Title')
        arxiv_id = metadata.get('id', 'unknown')
        published = metadata.get('published', '')
        updated = metadata.get('updated', '')
        abstract = files_data.get("abstract", metadata.get('abstract', ''))
        
        # 作者信息
        authors = metadata.get('authors', [])
        author_count = authors_data.get('author_count', len(authors))
        first_author = authors_data.get('first_author', authors[0] if authors else '')
        last_author = authors_data.get('last_author', authors[-1] if authors else '')
        
        # 分类信息
        categories = metadata.get('categories', [])
        primary_category = metadata.get('primary_category', '')
        is_ai_related = categories_data.get('is_ai_related', False)
        
        # 链接信息
        arxiv_url = links_data.get('arxiv_url', metadata.get('url', ''))
        pdf_url = links_data.get('pdf_url', metadata.get('pdf_url', ''))
        
        # 处理信息
        processed_date = metadata.get('processed_date', '')
        wordcount = metadata.get('wordcount', 0)
        
        # 构建增强的Markdown
        enhanced_content = f"""# {title}

## 📋 基本信息

- **arXiv ID**: {arxiv_id}
- **发布日期**: {published}
- **更新日期**: {updated}
- **主要分类**: {primary_category}
- **AI相关**: {'✅ 是' if is_ai_related else '❌ 否'}

## 👥 作者信息

- **作者总数**: {author_count}
- **第一作者**: {first_author}
- **最后作者**: {last_author}
- **完整作者列表**: {', '.join(authors)}

## 🏷️ 分类标签

- **主要分类**: {primary_category}
- **所有分类**: {', '.join(categories)}
- **分类总数**: {len(categories)}

## 🔗 相关链接

- **arXiv页面**: [{arxiv_url}]({arxiv_url})
- **PDF下载**: [{pdf_url}]({pdf_url})

## 📄 论文摘要

{abstract}

## 🔧 处理信息

- **处理时间**: {processed_date}
- **字数统计**: {wordcount}
- **数据来源**: arXiv爬虫系统增强版

---

*此文档包含完整的论文元数据和标签信息*
"""
        
        return enhanced_content
    
    def _create_complete_metadata(self, files_data: Dict[str, Any], folder_name: str) -> Dict[str, Any]:
        """创建完整的元数据用于MinIO和ES"""
        metadata = files_data["metadata"]
        authors_data = files_data["authors"]
        categories_data = files_data["categories"]
        
        return {
            # 基本信息
            "arxiv_id": metadata.get('id', ''),
            "title": metadata.get('title', ''),
            "published": metadata.get('published', ''),
            "updated": metadata.get('updated', ''),
            
            # 作者信息
            "authors": ', '.join(metadata.get('authors', [])),
            "author_count": authors_data.get('author_count', 0),
            "first_author": authors_data.get('first_author', ''),
            "last_author": authors_data.get('last_author', ''),
            
            # 分类信息
            "categories": ', '.join(metadata.get('categories', [])),
            "primary_category": metadata.get('primary_category', ''),
            "category_count": categories_data.get('category_count', 0),
            "is_ai_related": categories_data.get('is_ai_related', False),
            
            # 技术信息
            "wordcount": metadata.get('wordcount', 0),
            "processed_date": metadata.get('processed_date', ''),
            "folder_name": folder_name,
            "source": "arxiv_crawler_enhanced",
            
            # 链接信息
            "arxiv_url": metadata.get('url', ''),
            "pdf_url": metadata.get('pdf_url', ''),
            
            # 文件信息
            "file_type": "markdown",
            "content_type": "text/markdown"
        }
    
    def upload_paper_folders_batch(self, paper_folders: List[str]) -> Dict[str, Any]:
        """批量上传论文文件夹"""
        print(f"📚 开始批量上传 {len(paper_folders)} 个论文文件夹...")
        
        total_uploaded = 0
        total_failed = 0
        failed_folders = []
        successful_folders = []
        
        for i, paper_folder in enumerate(paper_folders, 1):
            folder_name = os.path.basename(paper_folder)
            print(f"\n📁 上传进度 {i}/{len(paper_folders)}: {folder_name}")
            
            result = self.upload_paper_folder_as_single_file(paper_folder)
            
            if result["success"]:
                total_uploaded += 1
                successful_folders.append(result)
                print(f"   ✅ 上传成功")
                if result.get("es_indexed"):
                    print(f"   📊 已索引到Elasticsearch")
                if result.get("public_url"):
                    print(f"   🔗 公开URL: {result['public_url']}")
            else:
                total_failed += 1
                failed_folders.append(result)
                print(f"   ❌ 上传失败: {result.get('error', 'Unknown error')}")
            
            # 避免请求过于频繁
            if i % 10 == 0:
                print(f"   💤 休息2秒...")
                import time
                time.sleep(2)
        
        # 汇总结果
        result = {
            "total_folders": len(paper_folders),
            "uploaded_count": total_uploaded,
            "failed_count": total_failed,
            "failed_folders": failed_folders,
            "successful_folders": successful_folders,
            "success_rate": (total_uploaded / len(paper_folders)) * 100 if len(paper_folders) > 0 else 0
        }
        
        print(f"\n🎯 上传完成统计:")
        print(f"   总文件夹数: {result['total_folders']}")
        print(f"   成功上传: {result['uploaded_count']}")
        print(f"   失败数量: {result['failed_count']}")
        print(f"   成功率: {result['success_rate']:.1f}%")
        
        return result


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="修复版：按文件夹结构上传arXiv论文")
    parser.add_argument("--articles-dir", default="crawled_data/articles", help="论文文件夹目录")
    parser.add_argument("--config", default="config_enhanced.json", help="配置文件路径")
    
    args = parser.parse_args()
    
    # 设置日志
    setup_logging()
    
    print("🚀 修复版论文文件夹上传工具")
    print("=" * 50)
    
    # 初始化上传器
    uploader = PaperFolderUploaderFixed(args.config)
    
    # 创建存储桶
    if not uploader.create_bucket_if_not_exists():
        print("❌ 存储桶创建/检查失败")
        sys.exit(1)
    
    # 查找论文文件夹
    paper_folders = uploader.find_paper_folders(args.articles_dir)
    if not paper_folders:
        print("❌ 没有找到有效的论文文件夹")
        sys.exit(1)
    
    # 上传论文文件夹
    result = uploader.upload_paper_folders_batch(paper_folders)
    
    # 保存上传结果
    result_file = f"fixed_folder_upload_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
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
