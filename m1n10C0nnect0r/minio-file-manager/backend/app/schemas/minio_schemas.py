from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime


class BucketResponse(BaseModel):
    """存储桶响应模型"""
    name: str = Field(..., description="存储桶名称")
    creation_date: Optional[str] = Field(None, description="创建时间（ISO 8601格式）")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "my-bucket",
                "creation_date": "2024-01-15T10:30:00Z"
            }
        }


class BucketCreateRequest(BaseModel):
    """创建存储桶请求模型"""
    bucket_name: str = Field(
        ..., 
        min_length=3, 
        max_length=63, 
        pattern="^[a-z0-9][a-z0-9.-]*[a-z0-9]$",
        description="存储桶名称（3-63字符，只能包含小写字母、数字和连字符）"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "bucket_name": "project-documents"
            }
        }


class ObjectResponse(BaseModel):
    """文件对象响应模型"""
    name: str = Field(..., description="对象名称/路径")
    size: int = Field(..., description="文件大小（字节）")
    etag: str = Field(..., description="ETag（MD5哈希值）")
    last_modified: Optional[str] = Field(None, description="最后修改时间")
    is_dir: bool = Field(False, description="是否为目录")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "documents/report.pdf",
                "size": 1048576,
                "etag": "d41d8cd98f00b204e9800998ecf8427e",
                "last_modified": "2024-01-15T10:30:00Z",
                "is_dir": False
            }
        }


class ObjectInfoResponse(BaseModel):
    """文件详细信息响应模型"""
    name: str = Field(..., description="文件名称")
    size: int = Field(..., description="文件大小（字节）")
    etag: str = Field(..., description="ETag（MD5哈希值）")
    content_type: str = Field(..., description="MIME类型")
    last_modified: Optional[str] = Field(None, description="最后修改时间")
    metadata: Optional[Dict[str, str]] = Field(None, description="自定义元数据")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "report.pdf",
                "size": 1048576,
                "etag": "d41d8cd98f00b204e9800998ecf8427e",
                "content_type": "application/pdf",
                "last_modified": "2024-01-15T10:30:00Z",
                "metadata": {
                    "author": "张三",
                    "version": "1.0"
                }
            }
        }


class UploadResponse(BaseModel):
    """文件上传响应模型"""
    bucket: str = Field(..., description="存储桶名称")
    object_name: str = Field(..., description="对象名称")
    etag: str = Field(..., description="ETag（MD5哈希值）")
    version_id: Optional[str] = Field(None, description="版本ID（如果启用版本控制）")
    size: Optional[int] = Field(None, description="文件大小（字节）")
    message: Optional[str] = Field(None, description="上传结果消息")
    public_url: Optional[str] = Field(None, description="MinIO公开访问URL")
    es_indexed: Optional[bool] = Field(None, description="是否已索引到Elasticsearch")
    es_document_id: Optional[str] = Field(None, description="Elasticsearch文档ID")

    class Config:
        json_schema_extra = {
            "example": {
                "bucket": "documents",
                "object_name": "2024/report.pdf",
                "etag": "d41d8cd98f00b204e9800998ecf8427e",
                "version_id": None,
                "size": 1048576,
                "message": "文件已成功上传到MinIO并索引到Elasticsearch",
                "public_url": "http://minio:9000/documents/2024/report.pdf",
                "es_indexed": True,
                "es_document_id": "abc123def456"
            }
        }


class PresignedUrlRequest(BaseModel):
    """预签名URL请求模型"""
    bucket_name: str = Field(..., description="存储桶名称")
    object_name: str = Field(..., description="对象名称")
    expires: int = Field(default=3600, ge=1, le=604800, description="有效期（秒，1-604800）")
    method: str = Field(default="GET", pattern="^(GET|PUT)$", description="HTTP方法（GET或PUT）")

    class Config:
        json_schema_extra = {
            "example": {
                "bucket_name": "documents",
                "object_name": "reports/2024/annual-report.pdf",
                "expires": 3600,
                "method": "GET"
            }
        }


class PresignedUrlResponse(BaseModel):
    """预签名URL响应模型"""
    url: str = Field(..., description="预签名URL")
    expires_in: int = Field(..., description="有效期（秒）")

    class Config:
        json_schema_extra = {
            "example": {
                "url": "http://minio:9000/bucket/object?X-Amz-Algorithm=AWS4-HMAC-SHA256&...",
                "expires_in": 3600
            }
        }


class CopyObjectRequest(BaseModel):
    """复制对象请求模型"""
    source_bucket: str = Field(..., description="源存储桶")
    source_object: str = Field(..., description="源对象路径")
    dest_bucket: str = Field(..., description="目标存储桶")
    dest_object: str = Field(..., description="目标对象路径")

    class Config:
        json_schema_extra = {
            "example": {
                "source_bucket": "documents",
                "source_object": "2024/report.pdf",
                "dest_bucket": "backup",
                "dest_object": "2024/report-backup.pdf"
            }
        }


class CopyObjectResponse(BaseModel):
    """复制对象响应模型"""
    source: str = Field(..., description="源文件路径")
    destination: str = Field(..., description="目标文件路径")
    etag: str = Field(..., description="新文件的ETag")
    version_id: Optional[str] = Field(None, description="版本ID")

    class Config:
        json_schema_extra = {
            "example": {
                "source": "documents/2024/report.pdf",
                "destination": "backup/2024/report-backup.pdf",
                "etag": "d41d8cd98f00b204e9800998ecf8427e",
                "version_id": None
            }
        }


class BucketPolicyRequest(BaseModel):
    """存储桶策略请求模型"""
    policy: Dict[str, Any] = Field(..., description="存储桶访问策略（JSON格式）")

    class Config:
        json_schema_extra = {
            "example": {
                "policy": {
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Effect": "Allow",
                            "Principal": {"AWS": "*"},
                            "Action": ["s3:GetObject"],
                            "Resource": ["arn:aws:s3:::my-bucket/*"]
                        }
                    ]
                }
            }
        }


class MessageResponse(BaseModel):
    """通用消息响应模型"""
    message: str = Field(..., description="响应消息")

    class Config:
        json_schema_extra = {
            "example": {
                "message": "操作成功完成"
            }
        }


class PublicUrlResponse(BaseModel):
    """公开URL响应模型"""
    public_url: str = Field(..., description="公开访问URL")
    is_public: bool = Field(..., description="桶是否设置为公开访问")
    bucket: str = Field(..., description="存储桶名称")
    object: str = Field(..., description="对象名称")
    note: str = Field(..., description="说明信息")

    class Config:
        json_schema_extra = {
            "example": {
                "public_url": "http://60.205.160.74:9000/my-bucket/document.pdf",
                "is_public": True,
                "bucket": "my-bucket",
                "object": "document.pdf",
                "note": "此URL可以直接访问"
            }
        }


class SearchRequest(BaseModel):
    """文件搜索请求模型"""
    query: str = Field("", description="搜索关键词")
    bucket: Optional[str] = Field(None, description="限定搜索的存储桶")
    file_type: Optional[str] = Field(None, description="文件类型过滤（如：.pdf）")
    page: int = Field(1, ge=1, description="页码")
    size: int = Field(20, ge=1, le=100, description="每页结果数量")

    class Config:
        json_schema_extra = {
            "example": {
                "query": "报告",
                "bucket": "documents",
                "file_type": ".pdf",
                "page": 1,
                "size": 20
            }
        }


class SearchResult(BaseModel):
    """搜索结果项模型"""
    score: float = Field(..., description="搜索相关度评分")
    bucket: str = Field(..., description="存储桶名称")
    object_name: str = Field(..., description="对象完整路径")
    file_name: str = Field(..., description="文件名")
    file_size: int = Field(..., description="文件大小")
    content_type: str = Field(..., description="文件类型")
    upload_time: str = Field(..., description="上传时间")
    public_url: Optional[str] = Field(None, description="公开访问URL")
    is_public: bool = Field(False, description="是否公开")
    highlight: Optional[Dict[str, List[str]]] = Field(None, description="高亮信息")

    class Config:
        json_schema_extra = {
            "example": {
                "score": 1.5,
                "bucket": "documents",
                "object_name": "reports/annual-report-2024.pdf",
                "file_name": "annual-report-2024.pdf",
                "file_size": 1048576,
                "content_type": "application/pdf",
                "upload_time": "2024-01-15T10:30:00Z",
                "public_url": "http://minio:9000/documents/reports/annual-report-2024.pdf",
                "is_public": True,
                "highlight": {
                    "file_name": ["annual-<em>report</em>-2024.pdf"]
                }
            }
        }


class SearchResponse(BaseModel):
    """搜索响应模型"""
    total: int = Field(..., description="匹配的总结果数")
    page: int = Field(..., description="当前页码")
    size: int = Field(..., description="每页大小")
    results: List[SearchResult] = Field(..., description="搜索结果列表")

    class Config:
        json_schema_extra = {
            "example": {
                "total": 156,
                "page": 1,
                "size": 20,
                "results": []
            }
        }


class FileStatsResponse(BaseModel):
    """文件统计响应模型"""
    total_files: int = Field(..., description="总文件数量")
    buckets: List[Dict[str, Any]] = Field(..., description="按存储桶统计")
    file_types: List[Dict[str, Any]] = Field(..., description="按文件类型统计")

    class Config:
        json_schema_extra = {
            "example": {
                "total_files": 1250,
                "buckets": [
                    {"bucket": "documents", "count": 856},
                    {"bucket": "images", "count": 394}
                ],
                "file_types": [
                    {"extension": ".pdf", "count": 423},
                    {"extension": ".jpg", "count": 287},
                    {"extension": ".docx", "count": 189}
                ]
            }
        }


class ErrorResponse(BaseModel):
    """错误响应模型"""
    detail: str = Field(..., description="错误详情")

    class Config:
        json_schema_extra = {
            "example": {
                "detail": "存储桶不存在或无权访问"
            }
        }