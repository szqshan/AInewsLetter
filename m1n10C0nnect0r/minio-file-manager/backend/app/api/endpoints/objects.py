from fastapi import APIRouter, HTTPException, UploadFile, File, Response, Path, Query, Body, Form
from typing import List, Optional, Dict, Any
from app.schemas.minio_schemas import (
    ObjectResponse,
    ObjectInfoResponse,
    UploadResponse,
    MessageResponse,
    CopyObjectRequest,
    CopyObjectResponse,
    PresignedUrlRequest,
    PresignedUrlResponse,
    PublicUrlResponse
)
from app.services.minio_service import minio_service
from app.services.document_pipeline_service import document_pipeline_service
from app.core.config import get_settings
import io
import json

router = APIRouter(
    prefix="/objects", 
    tags=["文件对象管理"],
    responses={
        400: {"description": "请求参数错误"},
        404: {"description": "资源不存在"},
        500: {"description": "服务器内部错误"}
    }
)


@router.get(
    "/{bucket_name}", 
    response_model=List[ObjectResponse], 
    summary="列出存储桶中的对象",
    description="""
    获取指定存储桶中的所有对象（文件和文件夹）列表。
    
    ### 功能说明
    - 支持分层浏览和递归列出
    - 可以按前缀过滤对象
    - 返回对象的基本信息和元数据
    
    ### 参数说明
    - **bucket_name**: 存储桶名称
    - **prefix**: 对象名称前缀，用于过滤（如：'photos/2024/'）
    - **recursive**: 是否递归列出所有子目录的对象
    
    ### 返回信息
    - **name**: 对象的完整路径名
    - **size**: 文件大小（字节）
    - **etag**: 对象的 MD5 哈希值
    - **last_modified**: 最后修改时间
    - **is_dir**: 是否为目录
    
    ### 使用场景
    - 文件浏览器界面
    - 批量操作前的文件列表获取
    - 存储空间统计分析
    """,
    response_description="对象列表"
)
async def list_objects(
    bucket_name: str = Path(..., description="存储桶名称", example="my-bucket"),
    prefix: str = Query("", description="对象前缀过滤", example="documents/"),
    recursive: bool = Query(True, description="是否递归列出所有子目录")
):
    try:
        return await minio_service.list_objects(bucket_name, prefix, recursive)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/{bucket_name}/upload", 
    response_model=UploadResponse, 
    summary="上传文件",
    description="""
    上传文件到指定的存储桶。
    
    ### 功能说明
    - 支持任意类型和大小的文件上传
    - 可以自定义文件在存储桶中的路径
    - 支持添加自定义元数据
    - 自动检测文件类型（MIME type）
    
    ### 参数说明
    - **bucket_name**: 目标存储桶名称
    - **file**: 要上传的文件（multipart/form-data）
    - **object_name**: 自定义文件名/路径（可选，默认使用原文件名）
    - **metadata**: JSON 格式的自定义元数据（可选）
    
    ### 元数据示例
    ```json
    {
      "author": "张三",
      "department": "技术部",
      "version": "1.0",
      "tags": "重要,项目文档"
    }
    ```
    
    ### 最佳实践
    - 使用有意义的文件路径组织结构（如：year/month/filename）
    - 大文件建议先压缩再上传
    - 敏感文件上传前应加密
    - 添加元数据便于后续检索和管理
    
    ### 限制说明
    - 单个文件最大 5TB
    - 文件名不能包含特殊字符
    - 元数据总大小不超过 2KB
    """,
    response_description="上传成功信息",
    status_code=201
)
async def upload_file(
    bucket_name: str = Path(..., description="存储桶名称", example="my-bucket"),
    file: UploadFile = File(..., description="要上传的文件"),
    object_name: Optional[str] = Query(None, description="自定义对象名称/路径", example="docs/report.pdf"),
    metadata: Optional[str] = Form(None, description="JSON格式的元数据", example='{"author":"张三","version":"1.0"}'),
    metadata_q: Optional[str] = Query(None, description="（兼容）通过查询参数传递的JSON元数据"),
    use_pipeline: bool = Query(True, description="是否使用文档处理管道（MD/HTML文件自动索引到ES）")
):
    try:
        object_name = object_name or file.filename
        file_data = await file.read()
        
        metadata_dict = None
        metadata_input = metadata if metadata is not None else metadata_q
        if metadata_input:
            try:
                metadata_dict = json.loads(metadata_input)
            except:
                raise ValueError("Invalid metadata format")
        
        settings = get_settings()
        
        if use_pipeline and settings.document_pipeline_enabled and document_pipeline_service.is_document_file(object_name, file.content_type):
            pipeline_result = await document_pipeline_service.process_upload(
                bucket_name=bucket_name,
                file_name=object_name,
                file_content=file_data,
                content_type=file.content_type
            )
            
            if pipeline_result['error']:
                raise HTTPException(status_code=500, detail=f"Pipeline error: {pipeline_result['error']}")
            
            response = UploadResponse(
                bucket=bucket_name,
                object_name=object_name,
                etag=pipeline_result.get('etag', ''),
                size=len(file_data),
                message="文件已成功上传到MinIO并索引到Elasticsearch",
                public_url=pipeline_result.get('public_url'),
                es_indexed=pipeline_result.get('es_indexed', False),
                es_document_id=pipeline_result.get('es_document_id')
            )
            return response
        else:
            file_stream = io.BytesIO(file_data)
            result = await minio_service.upload_file(
                bucket_name=bucket_name,
                object_name=object_name,
                file_data=file_stream,
                content_type=file.content_type or "application/octet-stream",
                metadata=metadata_dict
            )
            return result
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/{bucket_name}/{object_name:path}/download", 
    summary="下载文件",
    description="""
    从存储桶下载指定的文件。
    
    ### 功能说明
    - 直接下载文件到本地
    - 保持原始文件格式和内容
    - 支持断点续传
    - 自动设置正确的 Content-Type
    
    ### 参数说明
    - **bucket_name**: 存储桶名称
    - **object_name**: 文件的完整路径（支持多级目录）
    
    ### 响应头信息
    - **Content-Type**: 文件的 MIME 类型
    - **Content-Disposition**: 下载文件名
    - **ETag**: 文件的 MD5 哈希值
    - **Last-Modified**: 最后修改时间
    
    ### 使用场景
    - 用户下载个人文件
    - 批量下载前的单文件测试
    - 程序化文件获取
    
    ### 注意事项
    - 大文件下载可能需要较长时间
    - 建议对大文件使用预签名 URL
    - 下载统计和限速需要额外实现
    """,
    response_description="文件内容",
    responses={
        200: {
            "description": "文件内容",
            "content": {
                "application/octet-stream": {
                    "schema": {
                        "type": "string",
                        "format": "binary"
                    }
                }
            }
        },
        404: {"description": "文件不存在"}
    }
)
async def download_file(
    bucket_name: str = Path(..., description="存储桶名称", example="my-bucket"),
    object_name: str = Path(..., description="文件路径", example="documents/report.pdf")
):
    try:
        data, metadata = await minio_service.download_file(bucket_name, object_name)
        
        return Response(
            content=data,
            media_type=metadata.get("content_type", "application/octet-stream"),
            headers={
                "Content-Disposition": f'attachment; filename="{object_name.split("/")[-1]}"',
                "ETag": metadata.get("etag", ""),
                "Last-Modified": metadata.get("last_modified", "")
            }
        )
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get(
    "/{bucket_name}/{object_name:path}/info", 
    response_model=ObjectInfoResponse, 
    summary="获取文件信息",
    description="""
    获取文件的详细元数据信息，不下载文件内容。
    
    ### 功能说明
    - 快速获取文件属性
    - 不消耗下载流量
    - 包含所有系统和自定义元数据
    
    ### 返回信息
    - **name**: 文件名称
    - **size**: 文件大小（字节）
    - **etag**: MD5 哈希值
    - **content_type**: MIME 类型
    - **last_modified**: 最后修改时间
    - **metadata**: 自定义元数据
    
    ### 使用场景
    - 文件详情展示
    - 下载前确认文件信息
    - 文件完整性校验（通过 ETag）
    - 元数据管理和搜索
    """,
    response_description="文件元数据信息"
)
async def get_object_info(
    bucket_name: str = Path(..., description="存储桶名称", example="my-bucket"),
    object_name: str = Path(..., description="文件路径", example="documents/report.pdf")
):
    try:
        return await minio_service.get_object_info(bucket_name, object_name)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete(
    "/{bucket_name}/{object_name:path}", 
    response_model=MessageResponse, 
    summary="删除文件",
    description="""
    删除存储桶中的指定文件。
    
    ### 功能说明
    - 永久删除文件，不可恢复
    - 支持删除任意路径的文件
    - 删除后立即释放存储空间
    
    ### 注意事项
    - 删除操作不可撤销
    - 删除前请确认文件已备份
    - 批量删除建议使用专门的批量接口
    - 删除文件夹需要先删除其中的所有文件
    
    ### 权限要求
    - 需要对存储桶的写入权限
    - 某些受保护的文件可能无法删除
    """,
    response_description="删除成功消息"
)
async def delete_object(
    bucket_name: str = Path(..., description="存储桶名称", example="my-bucket"),
    object_name: str = Path(..., description="要删除的文件路径", example="documents/old-report.pdf")
):
    try:
        return await minio_service.delete_object(bucket_name, object_name)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/copy", 
    response_model=CopyObjectResponse, 
    summary="复制文件",
    description="""
    在存储桶之间或同一存储桶内复制文件。
    
    ### 功能说明
    - 支持跨存储桶复制
    - 保留原文件的所有元数据
    - 原文件保持不变
    - 支持重命名复制
    
    ### 使用场景
    - 文件备份
    - 创建文件副本进行编辑
    - 在不同项目间共享文件
    - 文件版本管理
    
    ### 参数说明
    - **source_bucket**: 源存储桶名称
    - **source_object**: 源文件路径
    - **dest_bucket**: 目标存储桶名称
    - **dest_object**: 目标文件路径（可以重命名）
    
    ### 注意事项
    - 大文件复制可能需要较长时间
    - 目标路径已存在时会覆盖
    - 需要对源和目标存储桶都有相应权限
    
    ### 示例
    ```json
    {
      "source_bucket": "documents",
      "source_object": "2024/report.pdf",
      "dest_bucket": "backup",
      "dest_object": "2024/report-backup.pdf"
    }
    ```
    """,
    response_description="复制成功信息"
)
async def copy_object(
    request: CopyObjectRequest = Body(..., description="复制请求参数")
):
    try:
        return await minio_service.copy_object(
            source_bucket=request.source_bucket,
            source_object=request.source_object,
            dest_bucket=request.dest_bucket,
            dest_object=request.dest_object
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/presigned-url", 
    response_model=PresignedUrlResponse, 
    summary="生成预签名 URL",
    description="""
    生成临时访问链接，允许在限定时间内直接访问或上传文件。
    
    ### 功能说明
    - 生成具有时效性的访问链接
    - 无需认证即可通过链接访问
    - 支持下载（GET）和上传（PUT）操作
    - 链接过期后自动失效
    
    ### 应用场景
    
    #### 1. 文件分享
    - 分享私有文件给外部用户
    - 设置访问时限保护文件安全
    - 无需创建账号即可访问
    
    #### 2. 直接上传
    - 前端直接上传到 MinIO，减轻服务器压力
    - 移动端大文件上传
    - 第三方系统集成
    
    #### 3. 临时下载
    - 生成一次性下载链接
    - 付费内容的限时访问
    - 审计和访问控制
    
    ### 参数说明
    - **bucket_name**: 存储桶名称
    - **object_name**: 文件路径
    - **expires**: 有效期（秒），最大 604800（7天）
    - **method**: 操作类型（GET 下载 / PUT 上传）
    
    ### 安全建议
    - 合理设置过期时间，避免链接长期有效
    - 对敏感文件使用较短的有效期
    - 定期审计生成的链接
    - 配合访问日志进行监控
    
    ### 示例
    ```json
    {
      "bucket_name": "documents",
      "object_name": "reports/2024/annual-report.pdf",
      "expires": 3600,
      "method": "GET"
    }
    ```
    
    生成的 URL 示例：
    ```
    http://minio-server:9000/documents/reports/2024/annual-report.pdf
    ?X-Amz-Algorithm=AWS4-HMAC-SHA256
    &X-Amz-Credential=...
    &X-Amz-Date=...
    &X-Amz-Expires=3600
    &X-Amz-SignedHeaders=host
    &X-Amz-Signature=...
    ```
    """,
    response_description="预签名 URL 信息"
)
async def generate_presigned_url(
    request: PresignedUrlRequest = Body(..., description="预签名 URL 请求参数")
):
    try:
        url = await minio_service.generate_presigned_url(
            bucket_name=request.bucket_name,
            object_name=request.object_name,
            expires=request.expires,
            method=request.method
        )
        return PresignedUrlResponse(url=url, expires_in=request.expires)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/{bucket_name}/{object_name:path}/public-url",
    response_model=PublicUrlResponse,
    summary="获取文件公开访问URL",
    description="""
    获取指定文件的公开访问URL地址。
    
    ### 功能说明
    - 返回文件的直接访问URL
    - 检查桶是否设置为公开访问
    - 提供URL有效性说明
    - 不需要任何认证即可获取URL
    
    ### 返回信息
    - **public_url**: 完整的公开访问URL
    - **is_public**: 桶是否真正设置为公开访问
    - **bucket**: 存储桶名称
    - **object**: 文件路径
    - **note**: URL使用说明
    
    ### 使用场景
    - 获取文件的分享链接
    - 嵌入网页或应用中
    - 批量获取文件URL
    - 验证公开访问设置
    
    ### 注意事项
    - 只有桶设置为公开时，返回的URL才能正常访问
    - 私有桶的文件需要使用预签名URL
    - URL格式：`http://minio-server:port/bucket/object`
    
    ### 与预签名URL的区别
    - **公开URL**: 永久有效，但需要桶为公开访问
    - **预签名URL**: 临时有效，适用于私有桶
    
    ### 示例返回
    ```json
    {
      "public_url": "http://60.205.160.74:9000/public-docs/manual.pdf",
      "is_public": true,
      "bucket": "public-docs",
      "object": "manual.pdf",
      "note": "此URL可以直接访问"
    }
    ```
    """,
    response_description="公开访问URL信息"
)
async def get_public_url(
    bucket_name: str = Path(..., description="存储桶名称", example="public-docs"),
    object_name: str = Path(..., description="文件路径", example="documents/manual.pdf")
):
    try:
        return await minio_service.get_public_url(bucket_name, object_name)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))