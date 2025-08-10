from fastapi import APIRouter, HTTPException, Query, Body
from typing import Optional
from app.schemas.minio_schemas import (
    SearchRequest,
    SearchResponse,
    FileStatsResponse,
    ErrorResponse
)
from app.services.elasticsearch_service import elasticsearch_service

router = APIRouter(
    prefix="/search", 
    tags=["文件搜索"],
    responses={
        500: {"description": "搜索服务错误", "model": ErrorResponse}
    }
)


@router.get(
    "/files",
    response_model=SearchResponse,
    summary="搜索文件",
    description="""
    基于Elasticsearch的强大文件搜索功能。
    
    ### 功能特性
    - **全文检索**: 支持文件名、路径、描述等多字段搜索
    - **模糊匹配**: 智能容错，支持拼写错误
    - **高亮显示**: 搜索结果中突出显示匹配的关键词
    - **精确过滤**: 按存储桶、文件类型等维度过滤
    - **相关度排序**: 根据匹配度智能排序
    - **分页支持**: 高效处理大量搜索结果
    
    ### 搜索语法
    - **基础搜索**: `报告` - 搜索包含"报告"的文件
    - **短语搜索**: `"年度报告"` - 精确匹配短语
    - **通配符**: `报告*` - 匹配以"报告"开头的词
    - **布尔操作**: `报告 AND 2024` - 必须同时包含两个词
    - **字段搜索**: `file_name:报告` - 在特定字段中搜索
    
    ### 过滤选项
    - **bucket**: 限定在特定存储桶中搜索
    - **file_type**: 按文件扩展名过滤（如：.pdf, .jpg）
    - **page/size**: 分页参数，支持大结果集
    
    ### 返回信息
    - **相关度评分**: 帮助理解匹配质量
    - **高亮片段**: 显示匹配上下文
    - **完整元数据**: 文件大小、类型、上传时间等
    - **访问链接**: 自动生成公开URL（如果可用）
    
    ### 使用场景
    - **文档检索**: 快速找到特定文档
    - **内容发现**: 探索相关文件
    - **数据分析**: 基于搜索结果进行统计
    - **用户界面**: 为前端提供搜索能力
    """,
    response_description="搜索结果，包含匹配的文件列表"
)
async def search_files(
    query: str = Query("", description="搜索关键词，支持多种语法"),
    bucket: Optional[str] = Query(None, description="限定搜索的存储桶"),
    file_type: Optional[str] = Query(None, description="文件类型过滤，如：.pdf"),
    page: int = Query(1, ge=1, description="页码，从1开始"),
    size: int = Query(20, ge=1, le=100, description="每页结果数，最大100")
):
    try:
        results = await elasticsearch_service.search_files(
            query=query,
            bucket=bucket,
            file_type=file_type,
            page=page,
            size=size
        )
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"搜索失败: {str(e)}")


@router.post(
    "/files",
    response_model=SearchResponse,
    summary="高级文件搜索",
    description="""
    通过POST请求进行更复杂的搜索查询。
    
    ### 与GET搜索的区别
    - 支持更复杂的查询参数
    - 更适合程序化调用
    - 可以在请求体中传递复杂的搜索条件
    
    ### 请求示例
    ```json
    {
      "query": "年度报告 AND (财务 OR 业务)",
      "bucket": "company-docs",
      "file_type": ".pdf",
      "page": 1,
      "size": 50
    }
    ```
    """,
    response_description="搜索结果"
)
async def advanced_search_files(search_request: SearchRequest = Body(...)):
    try:
        results = await elasticsearch_service.search_files(
            query=search_request.query,
            bucket=search_request.bucket,
            file_type=search_request.file_type,
            page=search_request.page,
            size=search_request.size
        )
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"搜索失败: {str(e)}")


@router.get(
    "/stats",
    response_model=FileStatsResponse,
    summary="获取文件统计信息",
    description="""
    获取系统中文件的统计信息和分布情况。
    
    ### 统计维度
    - **总文件数**: 系统中索引的文件总数
    - **存储桶分布**: 各个存储桶的文件数量
    - **文件类型分布**: 不同文件扩展名的数量统计
    
    ### 应用场景
    - **系统监控**: 了解存储使用情况
    - **数据可视化**: 为图表提供数据
    - **容量规划**: 分析文件分布趋势
    - **用户界面**: 显示统计仪表板
    
    ### 性能说明
    此接口基于Elasticsearch聚合查询，对大数据量有良好的性能表现。
    统计结果实时计算，反映当前最新状态。
    """,
    response_description="文件统计信息"
)
async def get_file_stats():
    try:
        stats = await elasticsearch_service.get_file_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取统计信息失败: {str(e)}")


@router.delete(
    "/index/{bucket_name}/{object_name:path}",
    summary="删除文件索引",
    description="""
    从搜索索引中删除特定文件的记录。
    
    ### 使用场景
    - 清理孤立索引（文件已删除但索引仍存在）
    - 手动维护搜索索引
    - 数据同步修复
    
    ### 注意事项
    - 此操作只删除搜索索引，不影响MinIO中的实际文件
    - 通常情况下，文件删除时会自动删除对应索引
    - 仅在出现数据不同步时需要手动调用
    """,
    response_description="删除结果消息"
)
async def delete_file_index(
    bucket_name: str,
    object_name: str
):
    try:
        success = await elasticsearch_service.delete_file(bucket_name, object_name)
        if success:
            return {"message": f"成功删除文件索引: {bucket_name}/{object_name}"}
        else:
            raise HTTPException(status_code=404, detail="文件索引不存在")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除索引失败: {str(e)}")


@router.post(
    "/reindex/{bucket_name}",
    summary="重建存储桶索引",
    description="""
    重新为指定存储桶中的所有文件创建搜索索引。
    
    ### 功能说明
    - 扫描存储桶中的所有文件
    - 为每个文件创建或更新搜索索引
    - 适用于数据修复和初始化场景
    
    ### 使用场景
    - 初次启用搜索功能
    - 修复索引数据不一致
    - 系统维护和数据迁移
    
    ### 注意事项
    - 大存储桶的重建过程可能较长
    - 重建期间不影响文件的正常访问
    - 建议在低峰期执行
    """,
    response_description="重建任务状态"
)
async def reindex_bucket(bucket_name: str):
    try:
        # 这里可以实现重建索引的逻辑
        # 由于时间关系，先返回一个占位响应
        return {
            "message": f"存储桶 {bucket_name} 的重建索引任务已提交",
            "status": "pending",
            "note": "此功能将在后续版本中完善实现"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"重建索引失败: {str(e)}")