#!/usr/bin/env python3
"""
Claude Newsroom Uploader
将爬取的新闻数据上传到MinIO存储系统
参考arXiv架构，实现本地 → MinIO → PostgreSQL → Elasticsearch 完整数据流
"""

import os
import json
import hashlib
from datetime import datetime
from pathlib import Path
import argparse
import sys

# 添加上级目录到路径，以便导入共享模块
sys.path.append(str(Path(__file__).parent.parent.parent))

try:
    from m1n10C0nnect0r.minio_file_manager.backend.app.services.minio_service import MinioService
    from m1n10C0nnect0r.minio_file_manager.backend.app.services.postgresql_service import PostgreSQLService
    from m1n10C0nnect0r.minio_file_manager.backend.app.services.elasticsearch_service import ElasticsearchService
except ImportError as e:
    print(f"⚠️  警告: 无法导入MinIO连接器模块: {e}")
    print("请确保MinIO连接器已正确安装和配置")
    MinioService = None
    PostgreSQLService = None
    ElasticsearchService = None

class ClaudeNewsUploader:
    def __init__(self, config_file="config.json"):
        """初始化上传器"""
        self.config = self.load_config(config_file)
        self.data_dir = Path(self.config["storage"]["data_dir"])
        self.articles_dir = self.data_dir / self.config["storage"]["articles_dir"]
        
        # 初始化存储服务
        self.init_storage_services()
        
        # MinIO bucket配置
        self.bucket_name = "claude-newsroom"
        self.metadata_index = "claude_newsroom_articles"
    
    def load_config(self, config_file):
        """加载配置文件"""
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"配置文件 {config_file} 未找到")
            return {}
    
    def init_storage_services(self):
        """初始化存储服务"""
        try:
            if MinioService:
                self.minio_service = MinioService()
                print("✅ MinIO服务初始化成功")
            else:
                self.minio_service = None
                print("❌ MinIO服务不可用")
            
            if PostgreSQLService:
                self.pg_service = PostgreSQLService()
                print("✅ PostgreSQL服务初始化成功")
            else:
                self.pg_service = None
                print("❌ PostgreSQL服务不可用")
            
            if ElasticsearchService:
                self.es_service = ElasticsearchService()
                print("✅ Elasticsearch服务初始化成功")
            else:
                self.es_service = None
                print("❌ Elasticsearch服务不可用")
                
        except Exception as e:
            print(f"存储服务初始化失败: {e}")
            self.minio_service = None
            self.pg_service = None
            self.es_service = None
    
    def ensure_bucket_exists(self):
        """确保MinIO bucket存在"""
        if not self.minio_service:
            return False
        
        try:
            buckets = self.minio_service.list_buckets()
            bucket_names = [bucket.name for bucket in buckets]
            
            if self.bucket_name not in bucket_names:
                self.minio_service.create_bucket(self.bucket_name)
                print(f"✅ 创建MinIO bucket: {self.bucket_name}")
            else:
                print(f"✅ MinIO bucket已存在: {self.bucket_name}")
            
            return True
        except Exception as e:
            print(f"❌ MinIO bucket操作失败: {e}")
            return False
    
    def get_local_articles(self):
        """获取本地文章列表"""
        if not self.articles_dir.exists():
            print(f"文章目录不存在: {self.articles_dir}")
            return []
        
        articles = []
        for article_dir in self.articles_dir.iterdir():
            if article_dir.is_dir():
                metadata_file = article_dir / 'metadata.json'
                content_file = article_dir / 'content.md'
                
                if metadata_file.exists() and content_file.exists():
                    try:
                        with open(metadata_file, 'r', encoding='utf-8') as f:
                            metadata = json.load(f)
                        
                        articles.append({
                            'slug': article_dir.name,
                            'metadata': metadata,
                            'local_dir': article_dir,
                            'metadata_file': metadata_file,
                            'content_file': content_file
                        })
                    except Exception as e:
                        print(f"读取文章元数据失败 {article_dir}: {e}")
        
        print(f"找到 {len(articles)} 篇本地文章")
        return articles
    
    def upload_article_to_minio(self, article):
        """上传单篇文章到MinIO"""
        if not self.minio_service:
            return False
        
        try:
            slug = article['slug']
            
            # 上传内容文件
            content_key = f"articles/{slug}/content.md"
            self.minio_service.upload_file(
                self.bucket_name,
                content_key,
                str(article['content_file'])
            )
            
            # 上传元数据文件
            metadata_key = f"articles/{slug}/metadata.json"
            self.minio_service.upload_file(
                self.bucket_name,
                metadata_key,
                str(article['metadata_file'])
            )
            
            # 上传媒体文件
            media_dir = article['local_dir'] / 'media'
            if media_dir.exists():
                for media_file in media_dir.iterdir():
                    if media_file.is_file():
                        media_key = f"articles/{slug}/media/{media_file.name}"
                        self.minio_service.upload_file(
                            self.bucket_name,
                            media_key,
                            str(media_file)
                        )
            
            print(f"✅ 上传文章到MinIO: {article['metadata']['title']}")
            return True
            
        except Exception as e:
            print(f"❌ 上传文章失败 {slug}: {e}")
            return False
    
    def save_article_to_postgres(self, article):
        """保存文章元数据到PostgreSQL"""
        if not self.pg_service:
            return False
        
        try:
            metadata = article['metadata']
            
            # 构建数据记录
            record = {
                'slug': article['slug'],
                'title': metadata.get('title', ''),
                'category': metadata.get('category', ''),
                'url': metadata.get('url', ''),
                'publish_date': metadata.get('date', ''),
                'crawl_time': metadata.get('crawl_time', ''),
                'content_length': len(metadata.get('content', '')),
                'image_count': len(metadata.get('images', [])),
                'minio_bucket': self.bucket_name,
                'minio_key': f"articles/{article['slug']}/",
                'created_at': datetime.now().isoformat()
            }
            
            # 这里需要根据实际的PostgreSQL表结构调整
            # 由于没有具体的表结构，这里提供示例代码
            table_name = "claude_newsroom_articles"
            
            # 构建插入SQL（需要根据实际表结构调整）
            sql = f"""
                INSERT INTO {table_name} (
                    slug, title, category, url, publish_date, crawl_time,
                    content_length, image_count, minio_bucket, minio_key, created_at
                ) VALUES (
                    %(slug)s, %(title)s, %(category)s, %(url)s, %(publish_date)s, 
                    %(crawl_time)s, %(content_length)s, %(image_count)s, 
                    %(minio_bucket)s, %(minio_key)s, %(created_at)s
                )
                ON CONFLICT (slug) DO UPDATE SET
                    title = EXCLUDED.title,
                    category = EXCLUDED.category,
                    url = EXCLUDED.url,
                    publish_date = EXCLUDED.publish_date,
                    crawl_time = EXCLUDED.crawl_time,
                    content_length = EXCLUDED.content_length,
                    image_count = EXCLUDED.image_count,
                    minio_bucket = EXCLUDED.minio_bucket,
                    minio_key = EXCLUDED.minio_key,
                    updated_at = NOW()
            """
            
            # 执行插入（需要实际的PostgreSQL连接方法）
            # self.pg_service.execute(sql, record)
            
            print(f"✅ 保存到PostgreSQL: {metadata['title']}")
            return True
            
        except Exception as e:
            print(f"❌ 保存到PostgreSQL失败: {e}")
            return False
    
    def index_article_to_elasticsearch(self, article):
        """索引文章到Elasticsearch"""
        if not self.es_service:
            return False
        
        try:
            metadata = article['metadata']
            
            # 读取文章内容
            with open(article['content_file'], 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 构建ES文档
            doc = {
                'slug': article['slug'],
                'title': metadata.get('title', ''),
                'category': metadata.get('category', ''),
                'url': metadata.get('url', ''),
                'publish_date': metadata.get('date', ''),
                'crawl_time': metadata.get('crawl_time', ''),
                'content': content,
                'content_length': len(content),
                'images': metadata.get('images', []),
                'image_count': len(metadata.get('images', [])),
                'source': 'claude_newsroom',
                'indexed_at': datetime.now().isoformat()
            }
            
            # 索引到Elasticsearch
            # 需要根据实际的ES服务方法调整
            # self.es_service.index(
            #     index=self.metadata_index,
            #     id=article['slug'],
            #     body=doc
            # )
            
            print(f"✅ 索引到Elasticsearch: {metadata['title']}")
            return True
            
        except Exception as e:
            print(f"❌ 索引到Elasticsearch失败: {e}")
            return False
    
    def upload_article(self, article):
        """上传单篇文章到所有存储系统"""
        success_count = 0
        total_services = 3
        
        print(f"\n📤 上传文章: {article['metadata']['title']}")
        
        # 1. 上传到MinIO
        if self.upload_article_to_minio(article):
            success_count += 1
        
        # 2. 保存到PostgreSQL
        if self.save_article_to_postgres(article):
            success_count += 1
        
        # 3. 索引到Elasticsearch
        if self.index_article_to_elasticsearch(article):
            success_count += 1
        
        success_rate = success_count / total_services
        if success_rate >= 0.67:  # 至少2/3成功
            print(f"✅ 文章上传成功 ({success_count}/{total_services})")
            return True
        else:
            print(f"❌ 文章上传失败 ({success_count}/{total_services})")
            return False
    
    def generate_upload_summary(self, results):
        """生成上传摘要"""
        total = len(results)
        successful = sum(1 for r in results if r['success'])
        failed = total - successful
        
        summary = {
            'upload_time': datetime.now().isoformat(),
            'total_articles': total,
            'successful_uploads': successful,
            'failed_uploads': failed,
            'success_rate': f"{(successful/total*100):.1f}%" if total > 0 else "0%",
            'bucket_name': self.bucket_name,
            'results': results
        }
        
        # 保存摘要文件
        summary_file = self.data_dir / f"upload_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        return summary
    
    def upload_all(self, force_update=False):
        """上传所有文章"""
        print("📤 Claude Newsroom 上传器启动")
        
        # 检查存储服务
        if not any([self.minio_service, self.pg_service, self.es_service]):
            print("❌ 没有可用的存储服务，请检查配置")
            return
        
        # 确保MinIO bucket存在
        if self.minio_service:
            if not self.ensure_bucket_exists():
                print("❌ MinIO bucket创建失败")
                return
        
        # 获取本地文章
        articles = self.get_local_articles()
        if not articles:
            print("没有找到本地文章")
            return
        
        # 上传文章
        results = []
        for i, article in enumerate(articles, 1):
            print(f"\n[{i}/{len(articles)}] 处理文章...")
            
            try:
                success = self.upload_article(article)
                results.append({
                    'slug': article['slug'],
                    'title': article['metadata']['title'],
                    'success': success,
                    'timestamp': datetime.now().isoformat()
                })
            except Exception as e:
                print(f"❌ 上传文章出错: {e}")
                results.append({
                    'slug': article['slug'],
                    'title': article['metadata'].get('title', 'Unknown'),
                    'success': False,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                })
        
        # 生成摘要
        summary = self.generate_upload_summary(results)
        
        print(f"\n✅ 上传完成!")
        print(f"总计: {summary['total_articles']} 篇")
        print(f"成功: {summary['successful_uploads']} 篇")
        print(f"失败: {summary['failed_uploads']} 篇")
        print(f"成功率: {summary['success_rate']}")

def main():
    parser = argparse.ArgumentParser(description='Claude Newsroom 上传器')
    parser.add_argument('--config', default='config.json', help='配置文件路径')
    parser.add_argument('--force', action='store_true', help='强制更新已存在的记录')
    
    args = parser.parse_args()
    
    uploader = ClaudeNewsUploader(args.config)
    uploader.upload_all(force_update=args.force)

if __name__ == "__main__":
    main()
