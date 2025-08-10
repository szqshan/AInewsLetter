#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
清理MinIO存储桶中的混乱文件
"""

import requests
import json
import sys
from pathlib import Path

# 添加src目录到Python路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

from arxiv_system.utils.file_utils import load_config

def clean_bucket():
    """清理arxiv-papers存储桶"""
    config = load_config("config_enhanced.json")
    api_endpoint = config.get("oss", {}).get("api_endpoint", "http://localhost:9011")
    bucket_name = config.get("oss", {}).get("bucket_name", "arxiv-papers")
    
    print(f"🧹 开始清理存储桶: {bucket_name}")
    
    try:
        # 获取所有文件列表
        response = requests.get(f"{api_endpoint}/api/v1/objects/{bucket_name}?recursive=true")
        if response.status_code == 200:
            objects = response.json()
            print(f"📁 找到 {len(objects)} 个对象")
            
            # 删除所有文件
            deleted_count = 0
            for obj in objects:
                object_name = obj["name"]
                print(f"🗑️ 删除: {object_name}")
                
                delete_response = requests.delete(
                    f"{api_endpoint}/api/v1/objects/{bucket_name}/{object_name}"
                )
                if delete_response.status_code == 200:
                    deleted_count += 1
                else:
                    print(f"❌ 删除失败: {object_name}")
            
            print(f"✅ 清理完成！删除了 {deleted_count}/{len(objects)} 个文件")
        else:
            print(f"❌ 获取文件列表失败: {response.status_code}")
    
    except Exception as e:
        print(f"❌ 清理异常: {e}")

if __name__ == "__main__":
    clean_bucket()

