from fastapi import APIRouter, HTTPException, Query, Path
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from app.services.document_pipeline_service import document_pipeline_service
from app.core.config import get_settings

router = APIRouter(
    prefix="/documents",
    tags=["文档搜索和推荐"],
    responses={
        400: {"description": "请求参数错误"},
        404: {"description": "资源不存在"},
        500: {"description": "服务器内部错误"}
    }
)


class DocumentSearchResponse(BaseModel):
    """文档搜索响应"""
    total: int = Field(..., description="总结果数")
    documents: List[Dict[str, Any]] = Field(..., description="文档列表")
    
    class Config:
        json_schema_extra = {
            "example": {
                "total": 5,
                "documents": [
                    {
                        "_id": "abc123",
                        "_score": 8.5,
                        "title": "项目文档.md",
                        "bucket_name": "documents",
                        "object_name": "2024/project.md",
                        "minio_public_url": "http://minio:9000/documents/2024/project.md",
                        "document_type": "markdown",
                        "statistics": {
                            "word_count": 1500,
                            "char_count": 9011
                        },
                        "_highlight": {
                            "content": ["...匹配的内容片段..."],
                            "title": ["<mark>项目文档</mark>.md"]
                        }
                    }
                ]
            }
        }


class SimilarDocumentsResponse(BaseModel):
    """相似文档响应"""
    source_document_id: str = Field(..., description="源文档ID")
    similar_documents: List[Dict[str, Any]] = Field(..., description="相似文档列表")
    
    class Config:
        json_schema_extra = {
            "example": {
                "source_document_id": "abc123",
                "similar_documents": [
                    {
                        "_id": "def456",
                        "_score": 7.2,
                        "title": "相关项目说明.md",
                        "bucket_name": "documents",
                        "object_name": "2024/related.md",
                        "minio_public_url": "http://minio:9000/documents/2024/related.md"
                    }
                ]
            }
        }


@router.get(
    "/search",
    response_model=DocumentSearchResponse,
    summary="搜索文档内容",
    description="""
    搜索已索引的文档内容（MD、HTML等），支持模糊搜索和精确搜索。
    
    ### 功能说明
    - 支持全文搜索和模糊匹配
    - 自动高亮匹配内容
    - 可按存储桶和文档类型过滤
    - 返回相关度评分
    
    ### 搜索特性
    - **模糊搜索**：自动纠正拼写错误，支持近似匹配
    - **短语搜索**：支持词组前缀匹配
    - **通配符搜索**：支持 * 通配符
    - **多字段搜索**：同时搜索标题、内容、描述等
    
    ### 参数说明
    - **query**: 搜索关键词
    - **fuzzy**: 是否启用模糊搜索（默认启用）
    - **bucket_name**: 限定搜索的存储桶
    - **document_type**: 限定文档类型（markdown/html/text）
    - **size**: 返回结果数量
    
    ### 返回信息
    - 匹配的文档列表
    - 相关度评分
    - 高亮显示的匹配片段
    - MinIO公开访问URL
    """,
    response_description="搜索结果列表"
)
async def search_documents(
    query: str = Query(..., description="搜索关键词", example="项目文档"),
    fuzzy: bool = Query(True, description="是否启用模糊搜索"),
    bucket_name: Optional[str] = Query(None, description="限定搜索的存储桶", example="documents"),
    document_type: Optional[str] = Query(None, description="文档类型过滤", example="markdown"),
    size: int = Query(20, ge=1, le=100, description="返回结果数量")
):
    try:
        settings = get_settings()
        if not settings.document_pipeline_enabled:
            raise HTTPException(
                status_code=503,
                detail="文档搜索功能未启用，请在配置中启用 document_pipeline_enabled"
            )
        
        documents = await document_pipeline_service.search_documents(
            query=query,
            bucket_name=bucket_name,
            document_type=document_type,
            fuzzy=fuzzy,
            size=size
        )
        
        return DocumentSearchResponse(
            total=len(documents),
            documents=documents
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/similar/{document_id}",
    response_model=SimilarDocumentsResponse,
    summary="获取相似文档",
    description="""
    基于文档内容获取相似的文档推荐。
    
    ### 功能说明
    - 使用 More Like This 算法
    - 基于内容相似度推荐
    - 自动排除源文档本身
    
    ### 算法原理
    - 分析源文档的关键词
    - 查找包含相似关键词的文档
    - 按相似度评分排序
    
    ### 参数说明
    - **document_id**: 源文档的ID（content_hash）
    - **size**: 返回的相似文档数量
    
    ### 使用场景
    - 相关文档推荐
    - 知识发现
    - 内容去重检测
    """,
    response_description="相似文档列表"
)
async def get_similar_documents(
    document_id: str = Path(..., description="文档ID（content_hash）", example="abc123def456"),
    size: int = Query(10, ge=1, le=50, description="返回结果数量")
):
    try:
        settings = get_settings()
        if not settings.document_pipeline_enabled:
            raise HTTPException(
                status_code=503,
                detail="文档推荐功能未启用，请在配置中启用 document_pipeline_enabled"
            )
        
        similar_docs = await document_pipeline_service.get_similar_documents(
            document_id=document_id,
            size=size
        )
        
        if not similar_docs and size > 0:
            raise HTTPException(
                status_code=404,
                detail=f"未找到文档ID: {document_id}"
            )
        
        return SimilarDocumentsResponse(
            source_document_id=document_id,
            similar_documents=similar_docs
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/types",
    summary="获取支持的文档类型",
    description="""
    获取当前配置支持的文档类型列表。
    
    ### 返回信息
    - 启用的文档类型列表
    - 每种类型支持的文件扩展名
    """,
    response_description="文档类型配置"
)
async def get_document_types():
    try:
        settings = get_settings()
        
        return {
            "enabled": settings.document_pipeline_enabled,
            "enabled_types": settings.document_pipeline_types,
            "type_extensions": document_pipeline_service.CONFIGURABLE_DOCUMENT_TYPES,
            "mime_types": document_pipeline_service.MIME_TYPE_MAP
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/stats",
    summary="获取文档索引统计",
    description="""
    获取已索引文档的统计信息。
    
    ### 返回信息
    - 总文档数
    - 按类型分组统计
    - 按存储桶分组统计
    """,
    response_description="统计信息"
)
async def get_document_stats():
    try:
        from app.services.elasticsearch_service import elasticsearch_service
        
        client = await elasticsearch_service.get_client()
        
        stats_query = {
            "size": 0,
            "aggs": {
                "by_type": {
                    "terms": {
                        "field": "document_type",
                        "size": 10
                    }
                },
                "by_bucket": {
                    "terms": {
                        "field": "bucket_name",
                        "size": 20
                    }
                },
                "avg_word_count": {
                    "avg": {
                        "field": "statistics.word_count"
                    }
                },
                "total_size": {
                    "sum": {
                        "field": "size"
                    }
                }
            }
        }
        
        result = await elasticsearch_service.search(
            index_name="minio_documents",
            body=stats_query
        )
        
        total_docs = result['hits']['total']['value']
        
        return {
            "total_documents": total_docs,
            "by_document_type": [
                {"type": bucket["key"], "count": bucket["doc_count"]}
                for bucket in result['aggregations']['by_type']['buckets']
            ],
            "by_bucket": [
                {"bucket": bucket["key"], "count": bucket["doc_count"]}
                for bucket in result['aggregations']['by_bucket']['buckets']
            ],
            "average_word_count": int(result['aggregations']['avg_word_count']['value'] or 0),
            "total_size_bytes": int(result['aggregations']['total_size']['value'] or 0)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))