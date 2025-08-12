#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
清空MinIO存储桶脚本
"""

import sys
import os

# 添加项目路径到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
backend_path = os.path.join(project_root, 'minio-file-manager', 'backend')
sys.path.insert(0, backend_path)

from minio import Minio
from app.core.config import get_settings

def clear_minio_buckets(bucket_names=None):
    """清空指定的MinIO存储桶"""
    
    settings = get_settings()
    
    # 创建MinIO客户端
    client = Minio(
        settings.minio_endpoint,
        access_key=settings.minio_access_key,
        secret_key=settings.minio_secret_key,
        secure=settings.minio_use_ssl
    )
    
    print("="*60)
    print("🗑️  清空 MinIO 存储桶")
    print("="*60)
    
    total_deleted = 0
    
    try:
        # 如果没有指定桶，获取所有桶
        if bucket_names is None:
            buckets = client.list_buckets()
            bucket_names = [b.name for b in buckets]
            print(f"找到 {len(bucket_names)} 个存储桶")
        
        for bucket_name in bucket_names:
            try:
                # 检查桶是否存在
                if not client.bucket_exists(bucket_name):
                    print(f"\n📦 存储桶: {bucket_name}")
                    print(f"   ⚠️  存储桶不存在")
                    continue
                
                # 列出并删除所有对象
                objects = client.list_objects(bucket_name, recursive=True)
                object_list = list(objects)
                
                print(f"\n📦 存储桶: {bucket_name}")
                print(f"   当前对象数: {len(object_list)}")
                
                if len(object_list) > 0:
                    # 删除所有对象
                    deleted_count = 0
                    for obj in object_list:
                        try:
                            client.remove_object(bucket_name, obj.object_name)
                            deleted_count += 1
                        except Exception as e:
                            print(f"   ❌ 删除 {obj.object_name} 失败: {str(e)[:50]}")
                    
                    total_deleted += deleted_count
                    print(f"   ✅ 已删除 {deleted_count} 个对象")
                else:
                    print(f"   ℹ️  存储桶已经是空的")
                    
            except Exception as e:
                print(f"\n📦 存储桶: {bucket_name}")
                print(f"   ❌ 错误: {str(e)[:100]}")
    
    except Exception as e:
        print(f"❌ 连接MinIO失败: {str(e)}")
        return 0
    
    print("\n" + "="*60)
    print(f"✅ 清理完成！共删除 {total_deleted} 个对象")
    print("="*60)
    
    return total_deleted

def main():
    """主函数"""
    
    # 默认要清理的存储桶（可以根据需要修改）
    DEFAULT_BUCKETS = [
        'test-bucket',
        'test-articles', 
        'test-documents',
        'newsletter-articles',
        'newsletter-articles-nlp'
    ]
    
    if len(sys.argv) > 1:
        if sys.argv[1] == '-y':
            # 直接清理默认桶
            clear_minio_buckets(DEFAULT_BUCKETS)
        elif sys.argv[1] == '--all':
            # 清理所有桶
            if len(sys.argv) > 2 and sys.argv[2] == '-y':
                clear_minio_buckets(None)  # None表示清理所有桶
            else:
                print("⚠️  警告：这将清空所有MinIO存储桶中的数据！")
                confirm = input("\n确认清空所有存储桶？(yes/no): ")
                if confirm.lower() in ['yes', 'y']:
                    clear_minio_buckets(None)
                else:
                    print("❌ 操作已取消")
        else:
            # 清理指定的桶
            buckets = sys.argv[1:]
            print(f"将清空以下存储桶: {', '.join(buckets)}")
            confirm = input("\n确认清空？(yes/no): ")
            if confirm.lower() in ['yes', 'y']:
                clear_minio_buckets(buckets)
            else:
                print("❌ 操作已取消")
    else:
        print("使用方法:")
        print("  python3 clear_minio.py              # 交互式清理默认存储桶")
        print("  python3 clear_minio.py -y           # 直接清理默认存储桶")
        print("  python3 clear_minio.py --all        # 清理所有存储桶（需确认）")
        print("  python3 clear_minio.py --all -y     # 直接清理所有存储桶")
        print("  python3 clear_minio.py bucket1 bucket2  # 清理指定存储桶")
        print("\n默认存储桶:", ", ".join(DEFAULT_BUCKETS))
        
        confirm = input("\n是否清理默认存储桶？(yes/no): ")
        if confirm.lower() in ['yes', 'y']:
            clear_minio_buckets(DEFAULT_BUCKETS)
        else:
            print("❌ 操作已取消")

if __name__ == "__main__":
    main()