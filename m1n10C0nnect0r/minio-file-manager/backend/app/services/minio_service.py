from minio import Minio
from minio.error import MinioException
from minio.commonconfig import CopySource
from starlette.concurrency import run_in_threadpool
from typing import List, BinaryIO, Optional, Dict, Any
from datetime import timedelta
import io
from app.core.config import get_settings


class MinioService:
    def __init__(self):
        settings = get_settings()
        self.client = Minio(
            endpoint=settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=settings.minio_use_ssl
        )
    
    def _sanitize_metadata_for_s3(self, metadata: Optional[Dict[str, Any]]) -> Optional[Dict[str, str]]:
        """将元数据清洗为仅包含 ASCII 的键值对，以满足 S3/MinIO 的限制。
        非 ASCII 的键或值将被跳过，返回给 MinIO 的仅为 ASCII-safe 元数据。
        原始元数据保留用于 Elasticsearch 索引。
        """
        if not metadata:
            return None
        safe: Dict[str, str] = {}
        for key, value in metadata.items():
            try:
                key_str = str(key)
                val_str = str(value)
                key_str.encode("ascii")
                val_str.encode("ascii")
                safe[key_str] = val_str
            except Exception:
                # 跳过非 ASCII 的键值
                continue
        return safe if safe else None
    
    async def list_buckets(self) -> List[Dict[str, Any]]:
        try:
            buckets = await run_in_threadpool(self.client.list_buckets)
            return [
                {
                    "name": bucket.name,
                    "creation_date": bucket.creation_date.isoformat() if bucket.creation_date else None
                }
                for bucket in buckets
            ]
        except MinioException as e:
            raise Exception(f"Error listing buckets: {str(e)}")
    
    async def create_bucket(self, bucket_name: str) -> Dict[str, str]:
        try:
            if await run_in_threadpool(self.client.bucket_exists, bucket_name):
                raise Exception(f"Bucket '{bucket_name}' already exists")
            
            await run_in_threadpool(self.client.make_bucket, bucket_name)
            return {"message": f"Bucket '{bucket_name}' created successfully"}
        except MinioException as e:
            raise Exception(f"Error creating bucket: {str(e)}")
    
    async def delete_bucket(self, bucket_name: str) -> Dict[str, str]:
        try:
            if not await run_in_threadpool(self.client.bucket_exists, bucket_name):
                raise Exception(f"Bucket '{bucket_name}' does not exist")
            
            objects = await run_in_threadpool(lambda: list(self.client.list_objects(bucket_name)))
            if objects:
                raise Exception(f"Bucket '{bucket_name}' is not empty")
            
            await run_in_threadpool(self.client.remove_bucket, bucket_name)
            return {"message": f"Bucket '{bucket_name}' deleted successfully"}
        except MinioException as e:
            raise Exception(f"Error deleting bucket: {str(e)}")
    
    async def list_objects(self, bucket_name: str, prefix: str = "", recursive: bool = True) -> List[Dict[str, Any]]:
        try:
            if not await run_in_threadpool(self.client.bucket_exists, bucket_name):
                raise Exception(f"Bucket '{bucket_name}' does not exist")
            
            objects = await run_in_threadpool(
                lambda: list(self.client.list_objects(bucket_name, prefix=prefix, recursive=recursive))
            )
            return [
                {
                    "name": obj.object_name,
                    "size": obj.size,
                    "etag": obj.etag,
                    "last_modified": obj.last_modified.isoformat() if obj.last_modified else None,
                    "is_dir": obj.is_dir
                }
                for obj in objects
            ]
        except MinioException as e:
            raise Exception(f"Error listing objects: {str(e)}")
    
    async def upload_file(self, bucket_name: str, object_name: str, file_data: BinaryIO, 
                         content_type: str = "application/octet-stream", metadata: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        try:
            if not self.client.bucket_exists(bucket_name):
                raise Exception(f"Bucket '{bucket_name}' does not exist")
            
            file_data.seek(0, 2)
            file_size = file_data.tell()
            file_data.seek(0)
            
            # 仅将 ASCII-safe 的元数据写入 MinIO，避免非 ASCII 导致失败
            s3_metadata = self._sanitize_metadata_for_s3(metadata)
            
            result = await run_in_threadpool(
                lambda: self.client.put_object(
                    bucket_name=bucket_name,
                    object_name=object_name,
                    data=file_data,
                    length=file_size,
                    content_type=content_type,
                    metadata=s3_metadata
                )
            )
            
            upload_result = {
                "bucket": bucket_name,
                "object_name": object_name,
                "etag": result.etag,
                "version_id": result.version_id
            }
            
            # 同步索引到Elasticsearch
            try:
                from app.services.elasticsearch_service import elasticsearch_service
                file_info = {
                    "content_type": content_type,
                    "size": file_size,
                    "etag": result.etag,
                    # 保留原始元数据用于 ES（允许非 ASCII）
                    "metadata": metadata or {},
                    "last_modified": None  # MinIO会自动设置
                }
                await elasticsearch_service.index_file(bucket_name, object_name, file_info)
            except Exception as es_error:
                # ES索引失败不影响文件上传
                print(f"Elasticsearch indexing failed: {es_error}")
            
            return upload_result
        except MinioException as e:
            raise Exception(f"Error uploading file: {str(e)}")
    
    async def download_file(self, bucket_name: str, object_name: str) -> tuple[bytes, Dict[str, Any]]:
        try:
            def _read_object():
                resp = self.client.get_object(bucket_name, object_name)
                try:
                    data_bytes = resp.read()
                    meta = {
                        "content_type": resp.content_type,
                        "etag": resp.etag,
                        "last_modified": resp.last_modified.isoformat() if resp.last_modified else None,
                        "size": len(data_bytes)
                    }
                    return data_bytes, meta
                finally:
                    resp.close()
                    resp.release_conn()
            data, metadata = await run_in_threadpool(_read_object)
            return data, metadata
        except MinioException as e:
            raise Exception(f"Error downloading file: {str(e)}")
    
    async def delete_object(self, bucket_name: str, object_name: str) -> Dict[str, str]:
        try:
            await run_in_threadpool(self.client.remove_object, bucket_name, object_name)
            
            # 从Elasticsearch中删除索引
            try:
                from app.services.elasticsearch_service import elasticsearch_service
                await elasticsearch_service.delete_file(bucket_name, object_name)
            except Exception as es_error:
                # ES删除失败不影响文件删除
                print(f"Elasticsearch deletion failed: {es_error}")
                
            return {"message": f"Object '{object_name}' deleted successfully from bucket '{bucket_name}'"}
        except MinioException as e:
            raise Exception(f"Error deleting object: {str(e)}")
    
    async def get_object_info(self, bucket_name: str, object_name: str) -> Dict[str, Any]:
        try:
            stat = await run_in_threadpool(self.client.stat_object, bucket_name, object_name)
            return {
                "name": stat.object_name,
                "size": stat.size,
                "etag": stat.etag,
                "content_type": stat.content_type,
                "last_modified": stat.last_modified.isoformat() if stat.last_modified else None,
                "metadata": stat.metadata
            }
        except MinioException as e:
            raise Exception(f"Error getting object info: {str(e)}")
    
    async def generate_presigned_url(self, bucket_name: str, object_name: str, 
                                   expires: int = 3600, method: str = "GET") -> str:
        try:
            if method.upper() == "GET":
                url = await run_in_threadpool(
                    self.client.presigned_get_object,
                    bucket_name,
                    object_name,
                    timedelta(seconds=expires)
                )
            elif method.upper() == "PUT":
                url = await run_in_threadpool(
                    self.client.presigned_put_object,
                    bucket_name,
                    object_name,
                    timedelta(seconds=expires)
                )
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            return url
        except MinioException as e:
            raise Exception(f"Error generating presigned URL: {str(e)}")
    
    async def copy_object(self, source_bucket: str, source_object: str, 
                         dest_bucket: str, dest_object: str) -> Dict[str, Any]:
        try:
            result = await run_in_threadpool(
                self.client.copy_object,
                dest_bucket,
                dest_object,
                CopySource(source_bucket, source_object)
            )
            
            return {
                "source": f"{source_bucket}/{source_object}",
                "destination": f"{dest_bucket}/{dest_object}",
                "etag": result.etag,
                "version_id": result.version_id
            }
        except MinioException as e:
            raise Exception(f"Error copying object: {str(e)}")
    
    async def set_bucket_policy(self, bucket_name: str, policy: Dict[str, Any]) -> Dict[str, str]:
        try:
            import json
            policy_json = json.dumps(policy)
            await run_in_threadpool(self.client.set_bucket_policy, bucket_name, policy_json)
            return {"message": f"Policy set successfully for bucket '{bucket_name}'"}
        except MinioException as e:
            raise Exception(f"Error setting bucket policy: {str(e)}")
    
    async def get_bucket_policy(self, bucket_name: str) -> Dict[str, Any]:
        try:
            import json
            policy = await run_in_threadpool(self.client.get_bucket_policy, bucket_name)
            return json.loads(policy) if policy else {}
        except MinioException as e:
            raise Exception(f"Error getting bucket policy: {str(e)}")
    
    async def make_bucket_public(self, bucket_name: str) -> Dict[str, str]:
        """设置桶为公开读取"""
        try:
            public_policy = {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": {"AWS": "*"},
                        "Action": ["s3:GetObject"],
                        "Resource": [f"arn:aws:s3:::{bucket_name}/*"]
                    },
                    {
                        "Effect": "Allow",
                        "Principal": {"AWS": "*"},
                        "Action": ["s3:ListBucket"],
                        "Resource": [f"arn:aws:s3:::{bucket_name}"]
                    }
                ]
            }
            
            import json
            policy_json = json.dumps(public_policy)
            await run_in_threadpool(self.client.set_bucket_policy, bucket_name, policy_json)
            return {"message": f"Bucket '{bucket_name}' is now public"}
        except MinioException as e:
            raise Exception(f"Error making bucket public: {str(e)}")
    
    async def make_bucket_private(self, bucket_name: str) -> Dict[str, str]:
        """移除桶的公开访问策略"""
        try:
            import json
            private_policy = json.dumps({
                "Version": "2012-10-17",
                "Statement": []
            })
            await run_in_threadpool(self.client.set_bucket_policy, bucket_name, private_policy)
            return {"message": f"Bucket '{bucket_name}' is now private"}
        except MinioException as e:
            raise Exception(f"Error making bucket private: {str(e)}")
    
    async def get_public_url(self, bucket_name: str, object_name: str) -> Dict[str, Any]:
        """获取文件的公开访问URL（如果桶是公开的）"""
        try:
            # 检查文件是否存在
            await run_in_threadpool(self.client.stat_object, bucket_name, object_name)
            
            # 构建公开访问URL
            settings = get_settings()
            endpoint = settings.minio_endpoint
            
            # 构建URL
            protocol = "https" if settings.minio_use_ssl else "http"
            public_url = f"{protocol}://{endpoint}/{bucket_name}/{object_name}"
            
            # 检查桶是否有公开访问策略
            is_public = False
            try:
                import json
                policy = await run_in_threadpool(self.client.get_bucket_policy, bucket_name)
                if policy:
                    policy_dict = json.loads(policy)
                    # 检查是否有允许公开访问的策略
                    for statement in policy_dict.get("Statement", []):
                        if statement.get("Effect") == "Allow":
                            principal = statement.get("Principal", {})
                            # 检查Principal格式（可能是字符串 "*" 或 {"AWS": "*"} 或 {"AWS": ["*"]}）
                            is_public_principal = False
                            if principal == "*":
                                is_public_principal = True
                            elif isinstance(principal, dict):
                                aws_principal = principal.get("AWS")
                                if aws_principal == "*" or (isinstance(aws_principal, list) and "*" in aws_principal):
                                    is_public_principal = True
                            
                            # 检查Action
                            actions = statement.get("Action", [])
                            if isinstance(actions, str):
                                actions = [actions]
                            
                            if is_public_principal and "s3:GetObject" in actions:
                                is_public = True
                                break
            except Exception as e:
                # 如果出现错误，记录但不影响URL生成
                print(f"Policy check error: {e}")
                pass
            
            return {
                "public_url": public_url,
                "is_public": is_public,
                "bucket": bucket_name,
                "object": object_name,
                "note": "此URL仅在桶设置为公开访问时有效" if not is_public else "此URL可以直接访问"
            }
        except MinioException as e:
            raise Exception(f"Error getting public URL: {str(e)}")


minio_service = MinioService()