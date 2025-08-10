#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试OSS上传器
"""

import asyncio
import logging
import sys
from pathlib import Path

# 添加src目录到Python路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

from arxiv_system.oss.oss_uploader import ArxivOSSUploader

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

async def main():
    """主函数"""
    print("🚀 开始使用OSS上传器上传文章...")
    
    # 初始化上传器
    uploader = ArxivOSSUploader(
        base_dir="crawled_data",
        endpoint="http://localhost:9011"
    )
    
    # 检查文章目录
    articles_dir = Path("crawled_data/articles")
    if not articles_dir.exists():
        print("❌ 文章目录不存在:", articles_dir)
        return
    
    article_dirs = [d for d in articles_dir.iterdir() if d.is_dir()]
    print(f"📁 找到 {len(article_dirs)} 个文章文件夹")
    
    if len(article_dirs) == 0:
        print("❌ 没有找到文章文件夹")
        return
    
    # 显示前几个文章信息
    print("\n📋 文章列表 (前5个):")
    for i, article_dir in enumerate(article_dirs[:5]):
        metadata_file = article_dir / "metadata.json"
        if metadata_file.exists():
            import json
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            title = metadata.get('title', '未知标题')[:50]
            print(f"  {i+1}. {article_dir.name}: {title}...")
        else:
            print(f"  {i+1}. {article_dir.name}: (无元数据)")
    
    # 确认上传
    print(f"\n准备上传 {len(article_dirs)} 篇文章到MinIO...")
    print("这将会创建 arxiv-papers 存储桶并保持文件夹结构")
    
    # 开始上传
    result = await uploader.upload_all(bucket_name="arxiv-papers")
    
    if result['success']:
        print("\n🎉 上传完成！")
        print(f"✅ 成功上传: {result['uploaded_files']} 个文章")
        print(f"⏱️  用时: {result['elapsed_time_seconds']} 秒")
        print(f"🪣 存储桶: {result['bucket_name']}")
        
        if result.get('sample_urls'):
            print("\n🔗 示例URL:")
            for url in result['sample_urls']:
                print(f"  {url}")
    else:
        print(f"\n❌ 上传失败: {result.get('error')}")

if __name__ == "__main__":
    asyncio.run(main())

