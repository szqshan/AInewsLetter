#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
展示Elasticsearch索引详细信息脚本
"""

import sys
import os
import json
from datetime import datetime

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

# 要检查的索引列表
INDICES = ['minio_files', 'minio_documents', 'minio_articles', 'newsletter_articles']

def format_bytes(bytes_value):
    """格式化字节大小"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.2f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.2f} TB"

def show_es_index_details(index_name=None):
    """展示ES索引的详细信息"""
    
    auth = HTTPBasicAuth(ES_USER, ES_PASSWORD)
    
    print("="*80)
    print("📊 Elasticsearch 索引详细信息")
    print(f"🔗 服务器: {ES_HOST}")
    print(f"📅 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    # 如果指定了索引名，只显示该索引
    indices_to_check = [index_name] if index_name else INDICES
    
    for index in indices_to_check:
        try:
            print(f"\n{'='*60}")
            print(f"📁 索引: {index}")
            print("="*60)
            
            # 检查索引是否存在
            response = requests.head(f'{ES_HOST}/{index}', auth=auth)
            
            if response.status_code != 200:
                print("❌ 索引不存在")
                continue
            
            # 1. 获取索引统计信息
            stats_resp = requests.get(f'{ES_HOST}/{index}/_stats', auth=auth)
            if stats_resp.status_code == 200:
                stats = stats_resp.json()['indices'][index]['total']
                
                print("\n📈 基本统计:")
                print(f"   文档数量: {stats['docs']['count']:,}")
                print(f"   已删除文档: {stats['docs']['deleted']:,}")
                print(f"   存储大小: {format_bytes(stats['store']['size_in_bytes'])}")
                
                if 'segments' in stats:
                    print(f"   段数量: {stats['segments']['count']}")
            
            # 2. 获取索引映射（字段结构）
            mapping_resp = requests.get(f'{ES_HOST}/{index}/_mapping', auth=auth)
            if mapping_resp.status_code == 200:
                mapping = mapping_resp.json()[index]['mappings']
                properties = mapping.get('properties', {})
                
                print("\n📋 字段结构:")
                for field_name, field_info in list(properties.items())[:15]:  # 只显示前15个字段
                    field_type = field_info.get('type', 'unknown')
                    print(f"   - {field_name}: {field_type}")
                
                if len(properties) > 15:
                    print(f"   ... 还有 {len(properties) - 15} 个字段")
            
            # 3. 获取索引设置
            settings_resp = requests.get(f'{ES_HOST}/{index}/_settings', auth=auth)
            if settings_resp.status_code == 200:
                settings = settings_resp.json()[index]['settings']['index']
                
                print("\n⚙️ 索引设置:")
                print(f"   分片数: {settings.get('number_of_shards', 'N/A')}")
                print(f"   副本数: {settings.get('number_of_replicas', 'N/A')}")
                print(f"   创建时间: {datetime.fromtimestamp(int(settings.get('creation_date', 0))/1000).strftime('%Y-%m-%d %H:%M:%S') if settings.get('creation_date') else 'N/A'}")
            
            # 4. 获取最新的文档样本
            sample_resp = requests.get(
                f'{ES_HOST}/{index}/_search',
                json={
                    'size': 3,
                    'sort': [{'_doc': {'order': 'desc'}}],
                    '_source': True
                },
                auth=auth
            )
            
            if sample_resp.status_code == 200:
                hits = sample_resp.json()['hits']['hits']
                
                if hits:
                    print("\n📄 最新文档样本:")
                    for i, hit in enumerate(hits, 1):
                        source = hit['_source']
                        
                        # 尝试获取标题或对象名
                        title = source.get('title', source.get('object_name', source.get('file_name', 'N/A')))
                        if isinstance(title, str) and len(title) > 60:
                            title = title[:60] + "..."
                        
                        # 尝试获取时间
                        time_field = source.get('upload_time', source.get('created_at', source.get('createdAt', 'N/A')))
                        
                        print(f"\n   {i}. ID: {hit['_id'][:20]}...")
                        print(f"      标题/名称: {title}")
                        print(f"      上传时间: {time_field}")
                        
                        # 显示其他关键字段
                        if 'bucket' in source:
                            print(f"      存储桶: {source['bucket']}")
                        if 'size' in source:
                            print(f"      大小: {format_bytes(source['size'])}")
                        if 'content_type' in source:
                            print(f"      类型: {source['content_type']}")
            
            # 5. 获取字段值统计（针对特定字段）
            if stats_resp.status_code == 200 and stats['docs']['count'] > 0:
                # 尝试获取bucket字段的聚合
                agg_resp = requests.get(
                    f'{ES_HOST}/{index}/_search',
                    json={
                        'size': 0,
                        'aggs': {
                            'buckets': {
                                'terms': {
                                    'field': 'bucket.keyword' if 'bucket' in properties else 'bucket',
                                    'size': 5
                                }
                            },
                            'types': {
                                'terms': {
                                    'field': 'content_type.keyword' if 'content_type' in properties else 'content_type',
                                    'size': 5
                                }
                            }
                        }
                    },
                    auth=auth
                )
                
                if agg_resp.status_code == 200:
                    aggs = agg_resp.json().get('aggregations', {})
                    
                    if 'buckets' in aggs and aggs['buckets']['buckets']:
                        print("\n📊 按存储桶分布 (前5):")
                        for bucket in aggs['buckets']['buckets']:
                            print(f"   - {bucket['key']}: {bucket['doc_count']} 个文档")
                    
                    if 'types' in aggs and aggs['types']['buckets']:
                        print("\n📊 按文件类型分布 (前5):")
                        for type_bucket in aggs['types']['buckets']:
                            print(f"   - {type_bucket['key']}: {type_bucket['doc_count']} 个文档")
                
        except Exception as e:
            print(f"❌ 获取索引信息失败: {str(e)[:100]}")
    
    print("\n" + "="*80)
    print("✅ 索引信息展示完成")
    print("="*80)

def main():
    """主函数"""
    if len(sys.argv) > 1:
        # 如果提供了参数，显示特定索引
        index_name = sys.argv[1]
        if index_name == '--all':
            # 显示所有索引
            try:
                auth = HTTPBasicAuth(ES_USER, ES_PASSWORD)
                resp = requests.get(f'{ES_HOST}/_cat/indices?format=json', auth=auth)
                if resp.status_code == 200:
                    all_indices = [idx['index'] for idx in resp.json() if not idx['index'].startswith('.')]
                    for idx in all_indices:
                        show_es_index_details(idx)
                else:
                    print("❌ 无法获取索引列表")
            except Exception as e:
                print(f"❌ 错误: {str(e)}")
        else:
            # 显示指定索引
            show_es_index_details(index_name)
    else:
        # 默认显示预定义的索引
        show_es_index_details()
        
        print("\n💡 提示:")
        print("  python3 show_es_details.py                 # 显示默认索引")
        print("  python3 show_es_details.py minio_files     # 显示特定索引")
        print("  python3 show_es_details.py --all           # 显示所有索引")

if __name__ == "__main__":
    main()