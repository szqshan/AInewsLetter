from elasticsearch import AsyncElasticsearch
from typing import Dict, Any, List, Optional
import hashlib
import mimetypes
import os
from datetime import datetime
from app.core.config import get_settings


class ElasticsearchService:
    def __init__(self):
        self.settings = get_settings()
        self.client = None
        self.index_name = self.settings.elasticsearch_index
        self._indices_initialized = False
        
    async def get_client(self) -> AsyncElasticsearch:
        """获取Elasticsearch客户端"""
        if self.client is None:
            # 构建连接URL
            if self.settings.elasticsearch_username and self.settings.elasticsearch_password:
                auth = (self.settings.elasticsearch_username, self.settings.elasticsearch_password)
            else:
                auth = None
            
            scheme = "https" if self.settings.elasticsearch_use_ssl else "http"
            host = f"{scheme}://{self.settings.elasticsearch_host}:{self.settings.elasticsearch_port}"
            
            self.client = AsyncElasticsearch(
                [host],
                basic_auth=auth,
                verify_certs=self.settings.elasticsearch_use_ssl,
                ssl_show_warn=False,
                api_key=None,
                headers={"Accept": "application/vnd.elasticsearch+json;compatible-with=8"}
            )
        return self.client
    
    async def index_file(self, bucket: str, object_name: str, file_info: Dict[str, Any]) -> bool:
        """索引文件信息到Elasticsearch"""
        try:
            client = await self.get_client()
            
            # 生成文档ID
            doc_id = hashlib.md5(f"{bucket}/{object_name}".encode()).hexdigest()
            
            # 提取文件信息
            file_name = os.path.basename(object_name)
            file_extension = os.path.splitext(file_name)[1].lower()
            
            # 构建文档
            document = {
                "bucket": bucket,
                "object_name": object_name,
                "file_name": file_name,
                "file_extension": file_extension,
                "content_type": file_info.get("content_type", ""),
                "file_size": file_info.get("size", 0),
                "etag": file_info.get("etag", ""),
                "upload_time": datetime.utcnow().isoformat(),
                "last_modified": file_info.get("last_modified"),
                "metadata": file_info.get("metadata", {}),
                "file_path": object_name,
                "tags": self._extract_tags(file_info.get("metadata", {})),
                "description": file_info.get("metadata", {}).get("description", "")
            }
            
            # 如果有公开URL信息，添加到文档中
            if "public_url" in file_info:
                document["public_url"] = file_info["public_url"]
                document["is_public"] = file_info.get("is_public", False)
            
            # 索引文档
            await client.index(
                index=self.index_name,
                id=doc_id,
                document=document
            )
            
            return True
        except Exception as e:
            print(f"索引文件失败: {e}")
            return False
    
    async def delete_file(self, bucket: str, object_name: str) -> bool:
        """从Elasticsearch中删除文件索引"""
        try:
            client = await self.get_client()
            doc_id = hashlib.md5(f"{bucket}/{object_name}".encode()).hexdigest()
            
            await client.delete(
                index=self.index_name,
                id=doc_id,
                ignore=[404]  # 忽略不存在的文档
            )
            
            return True
        except Exception as e:
            print(f"删除文件索引失败: {e}")
            return False
    
    async def search_files(self, query: str, bucket: Optional[str] = None, 
                          file_type: Optional[str] = None, page: int = 1, size: int = 20) -> Dict[str, Any]:
        """搜索文件"""
        try:
            client = await self.get_client()
            
            # 构建搜索查询
            search_body = {
                "from": (page - 1) * size,
                "size": size,
                "query": {
                    "bool": {
                        "must": [],
                        "filter": []
                    }
                },
                "sort": [
                    {"upload_time": {"order": "desc"}}
                ],
                "highlight": {
                    "fields": {
                        "file_name": {},
                        "object_name": {},
                        "description": {}
                    }
                }
            }
            
            # 添加搜索条件
            if query and query.strip():
                search_body["query"]["bool"]["must"].append({
                    "multi_match": {
                        "query": query,
                        "fields": [
                            "file_name^3",
                            "object_name^2", 
                            "description",
                            "metadata.*"
                        ],
                        "type": "best_fields",
                        "fuzziness": "AUTO"
                    }
                })
            else:
                search_body["query"]["bool"]["must"].append({"match_all": {}})
            
            # 添加过滤条件
            if bucket:
                search_body["query"]["bool"]["filter"].append({
                    "term": {"bucket": bucket}
                })
            
            if file_type:
                search_body["query"]["bool"]["filter"].append({
                    "term": {"file_extension": file_type}
                })
            
            # 执行搜索
            response = await client.search(
                index=self.index_name,
                body=search_body
            )
            
            # 处理结果
            hits = response["hits"]
            results = []
            
            for hit in hits["hits"]:
                source = hit["_source"]
                result = {
                    "score": float(hit["_score"]) if hit["_score"] is not None else 0.0,
                    "bucket": source["bucket"],
                    "object_name": source["object_name"],
                    "file_name": source["file_name"],
                    "file_size": source["file_size"],
                    "content_type": source["content_type"],
                    "upload_time": source["upload_time"],
                    "public_url": source.get("public_url"),
                    "is_public": source.get("is_public", False)
                }
                
                # 添加高亮信息
                if "highlight" in hit:
                    result["highlight"] = hit["highlight"]
                
                results.append(result)
            
            return {
                "total": hits["total"]["value"],
                "page": page,
                "size": size,
                "results": results
            }
            
        except Exception as e:
            print(f"搜索失败: {e}")
            return {
                "total": 0,
                "page": page,
                "size": size,
                "results": []
            }
    
    async def get_file_stats(self) -> Dict[str, Any]:
        """获取文件统计信息"""
        try:
            client = await self.get_client()
            
            # 总文件数
            count_response = await client.count(index=self.index_name)
            total_files = count_response["count"]
            
            # 按存储桶统计
            bucket_agg = await client.search(
                index=self.index_name,
                body={
                    "size": 0,
                    "aggs": {
                        "buckets": {
                            "terms": {
                                "field": "bucket",
                                "size": 20
                            }
                        }
                    }
                }
            )
            
            # 按文件类型统计
            type_agg = await client.search(
                index=self.index_name,
                body={
                    "size": 0,
                    "aggs": {
                        "file_types": {
                            "terms": {
                                "field": "file_extension",
                                "size": 20
                            }
                        }
                    }
                }
            )
            
            return {
                "total_files": total_files,
                "buckets": [
                    {"bucket": bucket["key"], "count": bucket["doc_count"]}
                    for bucket in bucket_agg["aggregations"]["buckets"]["buckets"]
                ],
                "file_types": [
                    {"extension": ext["key"] or "无扩展名", "count": ext["doc_count"]}
                    for ext in type_agg["aggregations"]["file_types"]["buckets"]
                ]
            }
            
        except Exception as e:
            print(f"获取统计信息失败: {e}")
            return {
                "total_files": 0,
                "buckets": [],
                "file_types": []
            }
    
    def _extract_tags(self, metadata: Dict[str, str]) -> List[str]:
        """从元数据中提取标签"""
        tags = []
        
        # 从元数据的tags字段提取
        if "tags" in metadata:
            tag_str = metadata["tags"]
            if isinstance(tag_str, str):
                tags.extend([tag.strip() for tag in tag_str.split(",") if tag.strip()])
        
        # 从其他字段提取有用信息作为标签
        if "category" in metadata:
            tags.append(metadata["category"])
            
        if "department" in metadata:
            tags.append(metadata["department"])
        
        return list(set(tags))  # 去重
    
    async def close(self):
        """关闭Elasticsearch连接"""
        if self.client:
            await self.client.close()
    

    async def index_document(self, index_name: str, document: Dict[str, Any], document_id: Optional[str] = None) -> Dict[str, Any]:
        """索引文档到指定索引"""
        try:
            client = await self.get_client()
            
            result = await client.index(
                index=index_name,
                id=document_id,
                body=document
            )
            
            return {
                "success": True,
                "id": result["_id"],
                "result": result["result"]
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def search(self, index_name: str, body: Dict[str, Any]) -> Dict[str, Any]:
        """通用搜索方法"""
        try:
            client = await self.get_client()
            return await client.search(index=index_name, body=body)
        except Exception as e:
            print(f"搜索失败: {e}")
            return {"hits": {"total": {"value": 0}, "hits": []}}
    
    async def get_document(self, index_name: str, document_id: str) -> Optional[Dict[str, Any]]:
        """获取单个文档"""
        try:
            client = await self.get_client()
            return await client.get(index=index_name, id=document_id)
        except Exception as e:
            print(f"获取文档失败: {e}")
            return None


# 全局实例
elasticsearch_service = ElasticsearchService()