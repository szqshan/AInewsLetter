#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
清空Elasticsearch索引脚本
"""

import sys
import os

# 添加项目路径到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
backend_path = os.path.join(project_root, 'minio-file-manager', 'backend')
sys.path.insert(0, backend_path)

import requests
from requests.auth import HTTPBasicAuth

# Elasticsearch配置
ES_HOST = 'http://60.205.160.74:9200'
ES_USER = 'elastic'
ES_PASSWORD = '8ErO981de92@!p'

# 要清空的索引列表
INDICES = ['minio_files', 'minio_documents', 'minio_articles', 'newsletter_articles']

def clear_es_indices():
    """清空所有Elasticsearch索引"""
    
    auth = HTTPBasicAuth(ES_USER, ES_PASSWORD)
    total_deleted = 0
    
    print("="*60)
    print("🗑️  清空 Elasticsearch 索引")
    print("="*60)
    
    for index in INDICES:
        try:
            # 检查索引是否存在
            response = requests.head(f'{ES_HOST}/{index}', auth=auth)
            
            if response.status_code == 200:
                # 获取文档数量
                count_resp = requests.get(f'{ES_HOST}/{index}/_count', auth=auth)
                if count_resp.status_code == 200:
                    doc_count = count_resp.json()['count']
                else:
                    doc_count = 'unknown'
                
                print(f"\n📁 索引: {index}")
                print(f"   当前文档数: {doc_count}")
                
                if doc_count > 0:
                    # 删除所有文档
                    delete_resp = requests.post(
                        f'{ES_HOST}/{index}/_delete_by_query',
                        json={'query': {'match_all': {}}},
                        auth=auth
                    )
                    
                    if delete_resp.status_code == 200:
                        deleted = delete_resp.json().get('deleted', 0)
                        total_deleted += deleted
                        print(f"   ✅ 已删除 {deleted} 个文档")
                    else:
                        print(f"   ❌ 删除失败: HTTP {delete_resp.status_code}")
                else:
                    print(f"   ℹ️  索引已经是空的")
                    
            elif response.status_code == 404:
                print(f"\n📁 索引: {index}")
                print(f"   ⚠️  索引不存在")
            else:
                print(f"\n📁 索引: {index}")
                print(f"   ❌ 检查失败: HTTP {response.status_code}")
                
        except Exception as e:
            print(f"\n📁 索引: {index}")
            print(f"   ❌ 错误: {str(e)}")
    
    print("\n" + "="*60)
    print(f"✅ 清理完成！共删除 {total_deleted} 个文档")
    print("="*60)
    
    return total_deleted

if __name__ == "__main__":
    # 确认清空操作
    if len(sys.argv) > 1 and sys.argv[1] == '-y':
        # 直接执行
        clear_es_indices()
    else:
        print("⚠️  警告：这将清空所有Elasticsearch索引中的数据！")
        print("索引包括: " + ", ".join(INDICES))
        confirm = input("\n确认清空？(yes/no): ")
        
        if confirm.lower() in ['yes', 'y']:
            clear_es_indices()
        else:
            print("❌ 操作已取消")