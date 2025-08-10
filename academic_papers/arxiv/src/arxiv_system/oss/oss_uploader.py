#!/usr/bin/env python3
"""
Arxiv OSS Uploader - 基于nlpSp1der架构的简化版OSS上传模块
"""

import os
import json
import asyncio
import aiohttp
import aiofiles
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import re
import logging
from urllib.parse import quote

logger = logging.getLogger(__name__)

class MinIOUploader:
    """MinIO客户端，用于上传文件到OSS"""
    
    def __init__(self, endpoint: str = "http://localhost:9011", public_base_url: str = "http://localhost:9000", access_key: str = "", secret_key: str = ""):
        self.endpoint = endpoint.rstrip('/')
        self.public_base_url = public_base_url.rstrip('/')
        self.api_base = f"{self.endpoint}/api/v1"
        self.access_key = access_key
        self.secret_key = secret_key
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
            
    async def create_bucket(self, bucket_name: str) -> bool:
        """创建存储桶"""
        try:
            async with self.session.post(
                f"{self.api_base}/buckets",
                json={"bucket_name": bucket_name}
            ) as resp:
                if resp.status == 201:
                    logger.info(f"✅ Created bucket: {bucket_name}")
                    return True
                elif resp.status == 400:
                    # Bucket might already exist
                    logger.info(f"ℹ️  Bucket already exists: {bucket_name}")
                    return True
                else:
                    error = await resp.text()
                    logger.error(f"Failed to create bucket {bucket_name}: {error}")
                    return False
        except Exception as e:
            logger.error(f"Error creating bucket {bucket_name}: {e}")
            return False
            
    async def make_bucket_public(self, bucket_name: str) -> bool:
        """设置桶为公开访问"""
        try:
            async with self.session.put(
                f"{self.api_base}/buckets/{bucket_name}/make-public"
            ) as resp:
                if resp.status == 200:
                    logger.info(f"✅ Made bucket public: {bucket_name}")
                    return True
                else:
                    error = await resp.text()
                    logger.error(f"Failed to make bucket public {bucket_name}: {error}")
                    return False
        except Exception as e:
            logger.error(f"Error making bucket public {bucket_name}: {e}")
            return False
            
    async def upload_file(self, bucket_name: str, object_name: str, file_path: str, metadata: Optional[Dict] = None) -> Optional[str]:
        """上传文件到MinIO并返回公开URL"""
        try:
            # Read file
            async with aiofiles.open(file_path, 'rb') as f:
                file_data = await f.read()
                
            # Prepare form data
            data = aiohttp.FormData()
            data.add_field('file', file_data, filename=os.path.basename(file_path))
            
            # Build URL with query parameters
            url = f"{self.api_base}/objects/{bucket_name}/upload"
            params = {'object_name': object_name}
            if metadata:
                params['metadata'] = json.dumps(metadata)
                
            async with self.session.post(url, data=data, params=params) as resp:
                if resp.status == 201:
                    result = await resp.json()
                    # Construct public URL using public base URL
                    public_url = f"{self.public_base_url}/{bucket_name}/{object_name}"
                    logger.debug(f"✅ Uploaded: {object_name} -> {public_url}")
                    return public_url
                else:
                    error = await resp.text()
                    logger.error(f"Failed to upload {object_name}: {error}")
                    return None
        except Exception as e:
            logger.error(f"Error uploading {file_path}: {e}")
            return None
            
    async def upload_json(self, bucket_name: str, object_name: str, data: Dict) -> Optional[str]:
        """上传JSON数据到MinIO"""
        try:
            # Convert to JSON bytes
            json_data = json.dumps(data, ensure_ascii=False, indent=2).encode('utf-8')
            
            # Prepare form data
            form_data = aiohttp.FormData()
            form_data.add_field('file', json_data, filename=os.path.basename(object_name))
            
            # Build URL with query parameters
            url = f"{self.api_base}/objects/{bucket_name}/upload"
            params = {'object_name': object_name}
                
            async with self.session.post(url, data=form_data, params=params) as resp:
                if resp.status == 201:
                    result = await resp.json()
                    # Construct public URL
                    public_url = f"{self.public_base_url}/{bucket_name}/{object_name}"
                    logger.debug(f"✅ Uploaded JSON: {object_name} -> {public_url}")
                    return public_url
                else:
                    error = await resp.text()
                    logger.error(f"Failed to upload JSON {object_name}: {error}")
                    return None
        except Exception as e:
            logger.error(f"Error uploading JSON {object_name}: {e}")
            return None

class ArxivOSSUploader:
    """Arxiv论文OSS上传器"""
    
    def __init__(self, base_dir: str = "crawled_data", endpoint: str = "http://localhost:9011"):
        self.base_dir = Path(base_dir)
        self.endpoint = endpoint
        self.progress_file = self.base_dir / "oss_upload_progress.json"
        self.progress = self.load_progress()
        
    def load_progress(self) -> Dict:
        """加载上传进度"""
        if self.progress_file.exists():
            with open(self.progress_file, 'r') as f:
                return json.load(f)
        return {"uploaded_articles": [], "stats": {}}
        
    def save_progress(self):
        """保存上传进度"""
        with open(self.progress_file, 'w') as f:
            json.dump(self.progress, f, indent=2)
            
    def get_bucket_name(self, source: str = "arxiv-papers") -> str:
        """根据数据源获取bucket名称"""
        # 清理名称，确保符合bucket命名规则
        bucket_name = source.lower().replace('_', '-').replace(' ', '-')
        bucket_name = re.sub(r'[^a-z0-9-]', '', bucket_name)
        return bucket_name
        
    async def upload_article(self, client: MinIOUploader, article_dir: Path, bucket_name: str) -> bool:
        """上传单个论文及其所有资源"""
        article_id = article_dir.name
        
        # Skip if already uploaded
        if article_id in self.progress.get("uploaded_articles", []):
            logger.info(f"⏭️  Skipping already uploaded: {article_id}")
            return True
            
        logger.info(f"📤 Uploading article: {article_id}")
        
        try:
            # Load metadata
            metadata_file = article_dir / "metadata.json"
            if not metadata_file.exists():
                logger.warning(f"No metadata found for {article_id}")
                return False
                
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
                
            # Load content
            content_file = article_dir / "content.md"
            if not content_file.exists():
                logger.warning(f"No content found for {article_id}")
                return False
                
            # Upload PDF file if exists
            pdf_file = article_dir / f"{article_id}.pdf"
            if pdf_file.exists():
                oss_path = f"articles/{article_id}/{pdf_file.name}"
                pdf_url = await client.upload_file(bucket_name, oss_path, str(pdf_file))
                if pdf_url:
                    metadata['oss_urls']['pdf'] = pdf_url
                    logger.debug(f"  📄 Uploaded PDF: {pdf_file.name}")
                    
            # Upload content.md
            oss_path = f"articles/{article_id}/content.md"
            content_url = await client.upload_file(bucket_name, oss_path, str(content_file))
            if content_url:
                metadata['oss_urls']['content'] = content_url
                logger.debug(f"  📝 Uploaded content: content.md")
                
            # Update metadata with OSS URLs and upload timestamp
            metadata['oss_urls']['uploaded_at'] = datetime.now().isoformat()
            metadata['oss_urls']['bucket'] = bucket_name
            
            # Upload updated metadata
            oss_path = f"articles/{article_id}/metadata.json"
            metadata_url = await client.upload_json(bucket_name, oss_path, metadata)
            if metadata_url:
                metadata['oss_urls']['metadata'] = metadata_url
                logger.debug(f"  📋 Uploaded metadata: metadata.json")
                
                # Save updated metadata locally
                with open(metadata_file, 'w', encoding='utf-8') as f:
                    json.dump(metadata, f, ensure_ascii=False, indent=2)
                    
            # Mark as uploaded
            self.progress["uploaded_articles"].append(article_id)
            self.save_progress()
            
            logger.info(f"✅ Successfully uploaded: {article_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error uploading article {article_id}: {e}")
            return False
            
    async def upload_all(self, bucket_name: str = None, resume: bool = True) -> Dict[str, any]:
        """上传所有论文到OSS"""
        if not bucket_name:
            bucket_name = self.get_bucket_name()
            
        start_time = datetime.now()
        
        try:
            async with MinIOUploader(self.endpoint) as client:
                # Create bucket and make it public
                logger.info(f"🪣 Setting up bucket: {bucket_name}")
                if not await client.create_bucket(bucket_name):
                    raise Exception("Failed to create bucket")
                    
                if not await client.make_bucket_public(bucket_name):
                    raise Exception("Failed to make bucket public")
                    
                # Get all article directories
                articles_dir = self.base_dir / "articles"
                if not articles_dir.exists():
                    raise Exception(f"Articles directory not found: {articles_dir}")
                    
                article_dirs = sorted([d for d in articles_dir.iterdir() if d.is_dir()])
                
                logger.info(f"📊 Found {len(article_dirs)} articles to process")
                
                # Upload articles
                success_count = 0
                failed_count = 0
                sample_urls = []
                
                for article_dir in article_dirs:
                    if await self.upload_article(client, article_dir, bucket_name):
                        success_count += 1
                        # Collect sample URLs
                        if success_count <= 3:
                            sample_urls.append(f"{client.public_base_url}/{bucket_name}/articles/{article_dir.name}/metadata.json")
                    else:
                        failed_count += 1
                        
                    # Small delay to avoid overwhelming the server
                    await asyncio.sleep(0.1)
                    
                # Upload global metadata files
                logger.info("📋 Uploading global metadata files...")
                
                data_dir = self.base_dir / "data"
                if data_dir.exists():
                    for json_file in data_dir.glob("*.json"):
                        object_name = f"data/{json_file.name}"
                        with open(json_file, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                        
                        await client.upload_json(bucket_name, object_name, data)
                        logger.info(f"  ✅ Uploaded {object_name}")
                        
                # Save final stats
                self.progress["stats"] = {
                    "total_articles": len(article_dirs),
                    "uploaded": success_count,
                    "failed": failed_count,
                    "timestamp": datetime.now().isoformat(),
                    "bucket": bucket_name,
                    "endpoint": self.endpoint
                }
                self.save_progress()
                
                # Print summary
                elapsed_time = (datetime.now() - start_time).total_seconds()
                logger.info("\n" + "="*50)
                logger.info("📊 Upload Summary:")
                logger.info(f"  Total articles: {len(article_dirs)}")
                logger.info(f"  ✅ Successfully uploaded: {success_count}")
                logger.info(f"  ❌ Failed: {failed_count}")
                logger.info(f"  🪣 Bucket: {bucket_name}")
                logger.info(f"  🌐 Endpoint: {self.endpoint}")
                logger.info(f"  📍 Public URL base: {client.public_base_url}/{bucket_name}/")
                logger.info(f"  ⏱️  Elapsed time: {elapsed_time:.2f}s")
                logger.info("="*50)
                
                return {
                    'success': True,
                    'uploaded_files': success_count,
                    'elapsed_time_seconds': int(elapsed_time),
                    'sample_urls': sample_urls,
                    'bucket_name': bucket_name
                }
            
        except Exception as e:
            elapsed_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"Upload failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'uploaded_files': 0,
                'elapsed_time_seconds': int(elapsed_time)
            }