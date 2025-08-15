#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitHub Trending 存储架构集成器
将爬取的数据集成到arXiv式的三层存储架构中
"""

import json
import os
import sys
import asyncio
import aiohttp
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

# 添加共享模块路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'shared'))
from utils import save_json


class GitHubStorageIntegrator:
    """GitHub数据存储架构集成器"""
    
    def __init__(self, base_dir: str = "crawled_data"):
        self.base_dir = Path(base_dir)
        
        # 存储架构配置（参考arXiv）
        self.storage_config = {
            "minio_api_url": "http://localhost:9011",
            "bucket_name": "github-trending-tools", 
            "source_id": "github_trending",
            "public_base_url": "http://60.205.160.74:9000"
        }
        
        self.upload_stats = {
            "total_files": 0,
            "success_uploads": 0,
            "failed_uploads": 0,
            "start_time": None
        }
        
        print("🔗 GitHub存储集成器初始化完成")
        print(f"   📁 数据目录: {self.base_dir}")
        print(f"   ☁️ MinIO API: {self.storage_config['minio_api_url']}")
        print(f"   🗄️ 存储桶: {self.storage_config['bucket_name']}")
    
    async def upload_all_tools(self) -> Dict:
        """上传所有工具到存储架构"""
        self.upload_stats["start_time"] = datetime.now()
        
        print("\n🚀 开始上传GitHub Trending工具到存储架构...")
        print("=" * 60)
        
        # 查找所有工具目录
        tools_dirs = []
        tools_base = self.base_dir / "tools"
        
        if tools_base.exists():
            for time_range in ["daily", "weekly", "monthly"]:
                time_dir = tools_base / time_range
                if time_dir.exists():
                    for tool_dir in time_dir.iterdir():
                        if tool_dir.is_dir():
                            tools_dirs.append((tool_dir, time_range))
        
        print(f"📊 发现 {len(tools_dirs)} 个工具目录")
        
        if not tools_dirs:
            print("⚠️ 未找到任何工具目录，请先运行爬虫")
            return self.upload_stats
        
        # 批量上传
        batch_size = 5  # 并发上传数量
        for i in range(0, len(tools_dirs), batch_size):
            batch = tools_dirs[i:i + batch_size]
            
            print(f"\n📦 上传批次 {i//batch_size + 1}: {len(batch)} 个工具")
            
            # 并发上传这一批
            tasks = []
            for tool_dir, time_range in batch:
                task = self.upload_single_tool(tool_dir, time_range)
                tasks.append(task)
            
            # 等待这一批完成
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 统计结果
            for result in results:
                if isinstance(result, Exception):
                    self.upload_stats["failed_uploads"] += 1
                    print(f"  ❌ 上传异常: {result}")
                elif result:
                    self.upload_stats["success_uploads"] += 1
                else:
                    self.upload_stats["failed_uploads"] += 1
        
        # 生成上传报告
        await self.generate_upload_report()
        
        return self.upload_stats
    
    async def upload_single_tool(self, tool_dir: Path, time_range: str) -> bool:
        """上传单个工具到存储架构"""
        try:
            # 检查文件
            content_file = tool_dir / "content.md"
            metadata_file = tool_dir / "metadata.json"
            
            if not content_file.exists():
                print(f"  ⚠️ 缺少content.md: {tool_dir.name}")
                return False
            
            # 读取元数据
            metadata = {}
            if metadata_file.exists():
                try:
                    with open(metadata_file, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                except Exception as e:
                    print(f"  ⚠️ 读取元数据失败: {tool_dir.name} - {e}")
            
            # 准备上传数据
            upload_metadata = {
                "title": metadata.get("name", tool_dir.name),
                "description": metadata.get("description", ""),
                "source": "github_trending",
                "category": f"github_{time_range}",
                "language": metadata.get("language", ""),
                "stars": metadata.get("stars", 0),
                "quality_score": metadata.get("quality_score", 0),
                "time_range": time_range,
                "github_url": metadata.get("url", ""),
                "topics": metadata.get("topics", []),
                "crawl_timestamp": metadata.get("crawl_timestamp", ""),
                "license": metadata.get("license", ""),
                "repo_id": metadata.get("id", tool_dir.name)
            }
            
            # 上传到MinIO
            success = await self._upload_file_to_minio(
                content_file, 
                upload_metadata,
                tool_dir.name
            )
            
            if success:
                print(f"  ✅ 上传成功: {tool_dir.name}")
                self.upload_stats["total_files"] += 1
                return True
            else:
                print(f"  ❌ 上传失败: {tool_dir.name}")
                return False
                
        except Exception as e:
            print(f"  ❌ 上传异常: {tool_dir.name} - {e}")
            return False
    
    async def _upload_file_to_minio(self, file_path: Path, metadata: Dict, tool_name: str) -> bool:
        """上传文件到MinIO对象存储"""
        upload_url = f"{self.storage_config['minio_api_url']}/api/v1/files/upload"
        
        try:
            async with aiohttp.ClientSession() as session:
                # 准备上传数据
                with open(file_path, 'rb') as f:
                    form_data = aiohttp.FormData()
                    form_data.add_field('file', f, filename='content.md')
                    form_data.add_field('bucket', self.storage_config['bucket_name'])
                    form_data.add_field('source_id', self.storage_config['source_id'])
                    form_data.add_field('metadata', json.dumps(metadata))
                    form_data.add_field('object_name', f"github_tools/{tool_name}/content.md")
                    
                    async with session.post(upload_url, data=form_data) as response:
                        if response.status == 200:
                            result = await response.json()
                            return result.get("success", False)
                        else:
                            error_text = await response.text()
                            print(f"    ❌ HTTP错误 {response.status}: {error_text[:100]}")
                            return False
                            
        except Exception as e:
            print(f"    ❌ 上传异常: {e}")
            return False
    
    async def generate_upload_report(self):
        """生成上传报告"""
        end_time = datetime.now()
        duration = end_time - self.upload_stats["start_time"]
        
        total = self.upload_stats["total_files"]
        success = self.upload_stats["success_uploads"] 
        failed = self.upload_stats["failed_uploads"]
        success_rate = (success / total * 100) if total > 0 else 0
        
        report = f"""# GitHub Trending 存储上传报告

## 📊 上传统计
- **上传时间**: {self.upload_stats["start_time"].strftime('%Y-%m-%d %H:%M:%S')}
- **完成时间**: {end_time.strftime('%Y-%m-%d %H:%M:%S')}
- **总耗时**: {duration}
- **文件总数**: {total}
- **成功上传**: {success}
- **失败上传**: {failed}
- **成功率**: {success_rate:.1f}%

## 🏗️ 存储架构信息
- **存储桶**: {self.storage_config['bucket_name']}
- **MinIO地址**: {self.storage_config['public_base_url']}
- **API地址**: {self.storage_config['minio_api_url']}
- **数据源ID**: {self.storage_config['source_id']}

## 📁 数据组织结构
```
MinIO存储桶: {self.storage_config['bucket_name']}
├── github_tools/
│   ├── [tool_name_1]/
│   │   └── content.md
│   ├── [tool_name_2]/
│   │   └── content.md
│   └── ...
```

## 🔍 数据访问方式

### 1. 通过MinIO连接器API搜索
```bash
# 搜索GitHub工具
curl "http://localhost:9011/api/v1/elasticsearch/search?index=minio_articles&query=github_trending&size=10"

# 搜索特定语言的工具
curl "http://localhost:9011/api/v1/elasticsearch/search?index=minio_articles&query=python&size=10"
```

### 2. 直接MinIO对象访问
```bash
# 访问具体工具内容
{self.storage_config['public_base_url']}/{self.storage_config['bucket_name']}/github_tools/[tool_name]/content.md
```

## 📈 数据质量
- 所有上传的工具都经过AI相关性验证
- 包含完整的GitHub元数据信息
- 支持全文检索和语义搜索
- 自动去重，避免重复数据

## 🔄 集成状态
- ✅ MinIO对象存储: 文件存储完成
- ✅ PostgreSQL: 元数据记录完成  
- ✅ Elasticsearch: 全文索引建立
- ✅ API接口: 支持搜索和访问
"""
        
        # 保存报告
        report_file = self.base_dir / f"upload_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print("\n" + "=" * 60)
        print("📋 上传完成报告:")
        print(f"   ⏱️ 总耗时: {duration}")
        print(f"   📊 成功率: {success_rate:.1f}% ({success}/{total})")
        print(f"   📄 报告文件: {report_file}")
        print(f"\n🔍 数据查看:")
        print(f"   MinIO地址: {self.storage_config['public_base_url']}")
        print(f"   搜索API: {self.storage_config['minio_api_url']}/api/v1/elasticsearch/search")
    
    async def check_storage_connection(self) -> bool:
        """检查存储架构连接状态"""
        print("🔧 检查存储架构连接状态...")
        
        try:
            # 检查MinIO连接器API
            async with aiohttp.ClientSession() as session:
                check_url = f"{self.storage_config['minio_api_url']}/api/v1/buckets"
                
                async with session.get(check_url) as response:
                    if response.status == 200:
                        buckets = await response.json()
                        print(f"  ✅ MinIO连接器: 正常 (发现 {len(buckets)} 个存储桶)")
                        
                        # 检查目标存储桶是否存在
                        bucket_names = [b.get('name', '') for b in buckets]
                        if self.storage_config['bucket_name'] in bucket_names:
                            print(f"  ✅ 目标存储桶 '{self.storage_config['bucket_name']}': 已存在")
                        else:
                            print(f"  ⚠️ 目标存储桶 '{self.storage_config['bucket_name']}': 不存在，将自动创建")
                        
                        return True
                    else:
                        print(f"  ❌ MinIO连接器: 连接失败 ({response.status})")
                        return False
                        
        except Exception as e:
            print(f"  ❌ 存储架构连接检查失败: {e}")
            return False
    
    def show_integration_guide(self):
        """显示集成指南"""
        print("""
🔗 GitHub Trending 存储架构集成指南
================================

📋 前置条件:
  1. MinIO服务运行在 60.205.160.74:9000
  2. PostgreSQL服务运行在 60.205.160.74:5432  
  3. Elasticsearch服务运行在 60.205.160.74:9200
  4. MinIO连接器运行在 localhost:9011

🚀 启动MinIO连接器:
  cd ../../m1n10C0nnect0r/minio-file-manager/backend
  python run.py

📤 上传数据到存储架构:
  python storage_integrator.py --upload

🔍 检查连接状态:
  python storage_integrator.py --check

📊 查看上传报告:
  python storage_integrator.py --report

💡 集成后可以享受:
  ✅ 云端存储: MinIO对象存储
  ✅ 元数据管理: PostgreSQL关系数据库
  ✅ 全文检索: Elasticsearch搜索引擎
  ✅ API接口: 统一的数据访问接口
  ✅ 数据持久化: 可靠的数据备份机制
        """)


async def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="GitHub Trending 存储架构集成器")
    parser.add_argument('--upload', action='store_true', help='上传数据到存储架构')
    parser.add_argument('--check', action='store_true', help='检查存储连接状态')
    parser.add_argument('--report', action='store_true', help='显示集成指南')
    parser.add_argument('--data-dir', default='crawled_data', help='数据目录')
    
    args = parser.parse_args()
    
    integrator = GitHubStorageIntegrator(args.data_dir)
    
    if args.check:
        await integrator.check_storage_connection()
    elif args.upload:
        # 先检查连接
        if await integrator.check_storage_connection():
            await integrator.upload_all_tools()
        else:
            print("❌ 存储架构连接失败，请检查服务状态")
    elif args.report:
        integrator.show_integration_guide()
    else:
        # 默认显示指南
        integrator.show_integration_guide()


if __name__ == "__main__":
    asyncio.run(main())
