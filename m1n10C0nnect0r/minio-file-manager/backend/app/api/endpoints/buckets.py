from fastapi import APIRouter, HTTPException, Path
from typing import List
from app.schemas.minio_schemas import (
    BucketResponse,
    BucketCreateRequest,
    MessageResponse,
    BucketPolicyRequest,
    ErrorResponse
)
from app.services.minio_service import minio_service

router = APIRouter(
    prefix="/buckets", 
    tags=["存储桶管理"],
    responses={
        400: {"description": "请求参数错误", "model": ErrorResponse},
        500: {"description": "服务器内部错误", "model": ErrorResponse}
    }
)


@router.get(
    "", 
    response_model=List[BucketResponse], 
    summary="获取存储桶列表",
    description="""
    获取 MinIO 中所有存储桶的列表。
    
    ### 功能说明
    - 返回所有存储桶的名称和创建时间
    - 不需要任何参数
    - 按创建时间排序
    
    ### 返回数据
    - **name**: 存储桶名称
    - **creation_date**: 创建时间（ISO 8601 格式）
    
    ### 使用场景
    - 在前端展示所有可用的存储桶
    - 选择存储桶进行文件操作
    - 管理和监控存储资源
    """,
    response_description="存储桶列表"
)
async def list_buckets():
    try:
        return await minio_service.list_buckets()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "", 
    response_model=MessageResponse, 
    summary="创建新存储桶",
    description="""
    创建一个新的 MinIO 存储桶。
    
    ### 功能说明
    - 创建指定名称的存储桶
    - 存储桶名称必须全局唯一
    - 自动应用默认的存储策略
    
    ### 命名规则
    - 长度：3-63 个字符
    - 只能包含小写字母、数字和连字符（-）
    - 必须以字母或数字开头和结尾
    - 不能包含连续的连字符
    - 不能是 IP 地址格式
    
    ### 注意事项
    - 存储桶名称创建后不能修改
    - 删除存储桶前必须清空所有文件
    - 建议使用有意义的命名，如：project-docs、user-avatars
    
    ### 错误处理
    - 400：存储桶名称不符合规则或已存在
    - 500：服务器创建失败
    """,
    response_description="创建成功消息",
    status_code=201
)
async def create_bucket(request: BucketCreateRequest):
    try:
        return await minio_service.create_bucket(request.bucket_name)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete(
    "/{bucket_name}", 
    response_model=MessageResponse, 
    summary="删除存储桶",
    description="""
    删除指定的存储桶。
    
    ### 功能说明
    - 永久删除存储桶及其配置
    - 只能删除空的存储桶
    - 删除操作不可恢复
    
    ### 前置条件
    - 存储桶必须存在
    - 存储桶必须为空（没有任何对象）
    - 没有其他服务正在使用该存储桶
    
    ### 注意事项
    - 删除前请确保已备份重要数据
    - 删除后存储桶名称立即可被重新使用
    - 相关的访问策略也会被删除
    
    ### 错误处理
    - 400：存储桶不存在或非空
    - 500：服务器删除失败
    """,
    response_description="删除成功消息"
)
async def delete_bucket(
    bucket_name: str = Path(..., description="要删除的存储桶名称", example="my-bucket")
):
    try:
        return await minio_service.delete_bucket(bucket_name)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/{bucket_name}/policy", 
    summary="获取存储桶策略",
    description="""
    获取指定存储桶的访问策略。
    
    ### 功能说明
    - 返回存储桶的完整策略文档
    - 策略以 JSON 格式返回
    - 包含所有访问规则和权限设置
    
    ### 策略内容
    - **Version**: 策略版本
    - **Statement**: 策略语句数组
    - **Effect**: 允许(Allow)或拒绝(Deny)
    - **Principal**: 策略应用的用户或角色
    - **Action**: 允许的操作列表
    - **Resource**: 策略应用的资源
    
    ### 使用场景
    - 审核存储桶的安全设置
    - 调试访问权限问题
    - 复制策略到其他存储桶
    """,
    response_description="存储桶策略文档"
)
async def get_bucket_policy(
    bucket_name: str = Path(..., description="存储桶名称", example="my-bucket")
):
    try:
        return await minio_service.get_bucket_policy(bucket_name)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put(
    "/{bucket_name}/policy", 
    response_model=MessageResponse, 
    summary="设置存储桶策略",
    description="""
    为存储桶设置新的访问策略。
    
    ### 功能说明
    - 完全替换现有的存储桶策略
    - 立即生效，无需重启服务
    - 支持细粒度的权限控制
    
    ### 策略示例
    ```json
    {
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
    ```
    
    ### 常用策略类型
    - **公开读取**：允许匿名用户读取对象
    - **私有**：仅授权用户可以访问
    - **只读**：允许读取但不能修改
    - **读写**：完全访问权限
    
    ### 注意事项
    - 错误的策略可能导致数据泄露
    - 建议先在测试环境验证策略
    - 保留策略的备份以便回滚
    """,
    response_description="设置成功消息"
)
async def set_bucket_policy(
    bucket_name: str = Path(..., description="存储桶名称", example="my-bucket"),
    request: BucketPolicyRequest = ...
):
    try:
        return await minio_service.set_bucket_policy(bucket_name, request.policy)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put(
    "/{bucket_name}/make-public",
    response_model=MessageResponse,
    summary="设置桶为公开访问",
    description="""
    将存储桶设置为公开读取模式，允许任何人访问桶中的文件。
    
    ### 功能说明
    - 一键设置桶为公开访问
    - 允许匿名用户读取桶中的所有文件
    - 允许匿名用户列出桶中的文件
    - 文件可以通过直接URL访问
    
    ### 安全警告 ⚠️
    - **此操作会使桶中的所有文件公开可访问**
    - **请确保桶中没有敏感或私密信息**
    - **公开的文件可被搜索引擎索引**
    - **任何人都可以下载桶中的文件**
    
    ### 使用场景
    - 托管静态网站资源
    - 分享公开文档
    - 提供公共下载资源
    - CDN 内容分发
    
    ### 访问方式
    设置为公开后，文件可通过以下方式访问：
    ```
    http://minio-server:9000/{bucket_name}/{object_name}
    ```
    """,
    response_description="设置成功消息"
)
async def make_bucket_public(
    bucket_name: str = Path(..., description="要设置为公开的存储桶名称", example="public-files")
):
    try:
        return await minio_service.make_bucket_public(bucket_name)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put(
    "/{bucket_name}/make-private",
    response_model=MessageResponse,
    summary="设置桶为私有访问",
    description="""
    将存储桶设置为私有模式，移除所有公开访问权限。
    
    ### 功能说明
    - 移除桶的所有公开访问策略
    - 恢复为默认的私有访问模式
    - 只有授权用户可以访问
    
    ### 效果
    - 匿名用户无法访问桶中的文件
    - 需要有效的认证才能读取文件
    - 通过直接URL无法访问文件
    
    ### 使用场景
    - 保护敏感数据
    - 限制文件访问
    - 恢复安全设置
    """,
    response_description="设置成功消息"
)
async def make_bucket_private(
    bucket_name: str = Path(..., description="要设置为私有的存储桶名称", example="private-files")
):
    try:
        return await minio_service.make_bucket_private(bucket_name)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))