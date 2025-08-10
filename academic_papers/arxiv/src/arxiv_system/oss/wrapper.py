"""Wrapper for OSS uploader to match main.py interface"""

import time
from pathlib import Path
from typing import Dict, Any
from .oss_uploader import ArxivOSSUploader, MinIOUploader
import re
import asyncio
import json
import logging
from datetime import datetime


class OSSUploader:
    """OSS上传器包装类，用于匹配main.py的接口"""
    
    def __init__(self, config: Dict[str, Any]):
        """使用配置字典初始化"""
        self.config = config
        self.endpoint = config.get('base_url', 'http://localhost:9011')
        self.public_base_url = config.get('public_base_url', 'http://localhost:9000')
        self.bucket_name = config.get('bucket_name', 'arxiv-papers')
        self.uploader = None
        
    async def __aenter__(self):
        """异步上下文管理器入口"""
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        pass
        
    async def upload_all(self, base_dir: Path, resume: bool = True) -> Dict[str, Any]:
        """上传指定目录下的所有文件"""
        start_time = time.time()
        
        try:
            # 创建实际的上传器
            self.uploader = ArxivOSSUploader(
                base_dir=str(base_dir),
                endpoint=self.endpoint
            )
            
            logger = logging.getLogger(__name__)
            
            # 清理bucket名称（确保有效）
            bucket_name = self.bucket_name.lower().replace('_', '-').replace(' ', '-')
            bucket_name = re.sub(r'[^a-z0-9-]', '', bucket_name)
            
            logger.info(f"🚀 Starting OSS upload for arxiv papers...")
            logger.info(f"📁 Base directory: {base_dir}")
            logger.info(f"🪣 Bucket: {bucket_name}")
            logger.info(f"🌐 Endpoint: {self.endpoint}")
            
            # 执行上传
            result = await self.uploader.upload_all(bucket_name=bucket_name, resume=resume)
            
            if result['success']:
                logger.info("🎉 OSS upload completed successfully!")
            else:
                logger.error(f"💥 OSS upload failed: {result.get('error', 'Unknown error')}")
                
            return result
            
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"💥 OSS upload wrapper error: {e}")
            return {
                'success': False,
                'error': str(e),
                'uploaded_files': 0,
                'elapsed_time_seconds': int(time.time() - start_time)
            }