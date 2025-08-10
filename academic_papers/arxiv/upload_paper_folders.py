#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
按文件夹结构上传arXiv论文到MinIO和Elasticsearch
每篇论文一个文件夹，包含完整的元数据和标签
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
import glob

# 添加src目录到Python路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

from arxiv_system.utils.file_utils import load_config, setup_logging


class PaperFolderUploader:
    """论文文件夹上传器"""
    
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
    
    def upload_paper_folder(self, paper_folder: str) -> Dict[str, Any]:
        """上传单个论文文件夹
        
        Args:
            paper_folder: 论文文件夹路径
            
        Returns:
            上传结果
        """
        try:
            folder_name = os.path.basename(paper_folder)
            
            # 读取metadata.json
            metadata_path = os.path.join(paper_folder, "metadata.json")
            with open(metadata_path, 'r', encoding='utf-8') as f:
                paper_metadata = json.load(f)
            
            arxiv_id = paper_metadata.get('id', 'unknown')
            title = paper_metadata.get('title', 'Unknown')
            
            print(f"📄 上传论文文件夹: {arxiv_id} - {title[:50]}...")
            
            # 收集所有需要上传的文件
            files_to_upload = self._collect_folder_files(paper_folder)
            
            upload_results = []
            
            # 逐个上传文件
            for file_info in files_to_upload:
                result = self._upload_single_file(file_info, folder_name, paper_metadata)
                upload_results.append(result)
                
                if not result["success"]:
                    print(f"   ❌ 文件上传失败: {file_info['relative_path']}")
                else:
                    print(f"   ✅ 文件上传成功: {file_info['relative_path']}")
            
            # 统计结果
            successful_uploads = sum(1 for r in upload_results if r["success"])
            total_files = len(upload_results)
            
            return {
                "success": successful_uploads == total_files,
                "arxiv_id": arxiv_id,
                "title": title,
                "folder_name": folder_name,
                "total_files": total_files,
                "successful_uploads": successful_uploads,
                "upload_results": upload_results
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "arxiv_id": "unknown",
                "folder_name": os.path.basename(paper_folder) if paper_folder else "unknown"
            }
    
    def _collect_folder_files(self, paper_folder: str) -> List[Dict[str, str]]:
        """收集文件夹中的所有文件"""
        files_info = []
        
        for root, dirs, files in os.walk(paper_folder):
            for file in files:
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, paper_folder)
                
                # 确定文件类型
                if file.endswith('.md'):
                    content_type = 'text/markdown'
                elif file.endswith('.json'):
                    content_type = 'application/json'
                elif file.endswith('.txt'):
                    content_type = 'text/plain'
                elif file.endswith(('.png', '.jpg', '.jpeg', '.gif')):
                    content_type = 'image/*'
                elif file.endswith('.pdf'):
                    content_type = 'application/pdf'
                else:
                    content_type = 'application/octet-stream'
                
                files_info.append({
                    "file_path": file_path,
                    "relative_path": relative_path,
                    "filename": file,
                    "content_type": content_type
                })
        
        return files_info
    
    def _upload_single_file(self, file_info: Dict[str, str], 
                           folder_name: str, paper_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """上传单个文件"""
        try:
            file_path = file_info["file_path"]
            relative_path = file_info["relative_path"]
            content_type = file_info["content_type"]
            
            # 构建MinIO对象名（保持文件夹结构）
            object_name = f"{folder_name}/{relative_path}"
            
            # 准备元数据
            metadata = {
                "arxiv_id": paper_metadata.get('id', ''),
                "title": paper_metadata.get('title', ''),
                "authors": ', '.join(paper_metadata.get('authors', [])),
                "categories": ', '.join(paper_metadata.get('categories', [])),
                "primary_category": paper_metadata.get('primary_category', ''),
                "published": paper_metadata.get('published', ''),
                "file_type": relative_path.split('.')[-1] if '.' in relative_path else 'unknown',
                "relative_path": relative_path,
                "source": "arxiv_crawler_enhanced"
            }
            
            # 上传文件
            with open(file_path, 'rb') as f:
                files = {'file': (relative_path, f, content_type)}
                data = {
                    'object_name': object_name,
                    'metadata': json.dumps(metadata),
                    'use_pipeline': 'true' if relative_path == 'content.md' else 'false'
                }
                
                response = requests.post(
                    f"{self.api_endpoint}/api/v1/objects/{self.bucket_name}/upload",
                    files=files,
                    data=data,
                    timeout=60
                )
            
            if response.status_code in [200, 201]:
                result = response.json()
                return {
                    "success": True,
                    "relative_path": relative_path,
                    "object_name": object_name,
                    "public_url": result.get("public_url", ""),
                    "es_indexed": result.get("es_indexed", False)
                }
            else:
                return {
                    "success": False,
                    "relative_path": relative_path,
                    "error": f"HTTP {response.status_code}: {response.text}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "relative_path": file_info.get("relative_path", "unknown"),
                "error": str(e)
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
            
            result = self.upload_paper_folder(paper_folder)
            
            if result["success"]:
                total_uploaded += 1
                successful_folders.append(result)
                print(f"   ✅ 文件夹上传成功: {result['successful_uploads']}/{result['total_files']} 个文件")
            else:
                total_failed += 1
                failed_folders.append(result)
                print(f"   ❌ 文件夹上传失败: {result.get('error', 'Unknown error')}")
            
            # 避免请求过于频繁
            if i % 5 == 0:
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
    parser = argparse.ArgumentParser(description="按文件夹结构上传arXiv论文")
    parser.add_argument("--articles-dir", default="crawled_data/articles", help="论文文件夹目录")
    parser.add_argument("--config", default="config_enhanced.json", help="配置文件路径")
    
    args = parser.parse_args()
    
    # 设置日志
    setup_logging()
    
    print("🚀 论文文件夹上传工具")
    print("=" * 50)
    
    # 初始化上传器
    uploader = PaperFolderUploader(args.config)
    
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
    result_file = f"folder_upload_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
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
