from fastapi import APIRouter, HTTPException, Query, Path, Body
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from app.services.elasticsearch_service import elasticsearch_service
from app.core.config import get_settings
from elasticsearch import AsyncElasticsearch
import json

router = APIRouter(
    prefix="/elasticsearch",
    tags=["Elasticsearch管理"],
    responses={
        400: {"description": "请求参数错误"},
        404: {"description": "资源不存在"},
        500: {"description": "服务器内部错误"}
    }
)


class IndexInfo(BaseModel):
    """索引信息"""
    index: str
    health: str
    status: str
    uuid: str
    docsCount: int
    docsDeleted: int
    storeSize: str
    priStoreSize: str
    shards: int
    replicas: int


class QueryRequest(BaseModel):
    """查询请求"""
    index: str = Field(..., description="索引名称")
    body: Dict[str, Any] = Field(..., description="查询体")


@router.get(
    "/indices",
    response_model=List[IndexInfo],
    summary="获取所有索引",
    description="获取 Elasticsearch 集群中的所有索引信息"
)
async def get_indices():
    try:
        client = await elasticsearch_service.get_client()
        
        # 获取索引信息
        cat_indices = await client.cat.indices(format='json', h='index,health,status,uuid,docs.count,docs.deleted,store.size,pri.store.size')
        
        # 获取索引设置
        indices_settings = await client.indices.get_settings()
        
        result = []
        for idx in cat_indices:
            index_name = idx['index']
            settings = indices_settings.get(index_name, {}).get('settings', {}).get('index', {})
            
            result.append(IndexInfo(
                index=index_name,
                health=idx.get('health', 'unknown'),
                status=idx.get('status', 'unknown'),
                uuid=idx.get('uuid', ''),
                docsCount=int(idx.get('docs.count', 0) or 0),
                docsDeleted=int(idx.get('docs.deleted', 0) or 0),
                storeSize=idx.get('store.size', '0b'),
                priStoreSize=idx.get('pri.store.size', '0b'),
                shards=int(settings.get('number_of_shards', 1)),
                replicas=int(settings.get('number_of_replicas', 0))
            ))
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/indices/{index}/mapping",
    summary="获取索引映射",
    description="获取指定索引的字段映射"
)
async def get_index_mapping(
    index: str = Path(..., description="索引名称")
):
    try:
        client = await elasticsearch_service.get_client()
        mapping = await client.indices.get_mapping(index=index)
        
        # 返回第一个索引的映射（通常只有一个）
        for idx_name, idx_mapping in mapping.items():
            return idx_mapping
        
        return {}
    except Exception as e:
        if "index_not_found_exception" in str(e):
            raise HTTPException(status_code=404, detail=f"索引 {index} 不存在")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/indices/{index}/settings",
    summary="获取索引设置",
    description="获取指定索引的设置"
)
async def get_index_settings(
    index: str = Path(..., description="索引名称")
):
    try:
        client = await elasticsearch_service.get_client()
        settings = await client.indices.get_settings(index=index)
        
        # 返回第一个索引的设置
        for idx_name, idx_settings in settings.items():
            return idx_settings.get('settings', {}).get('index', {})
        
        return {}
    except Exception as e:
        if "index_not_found_exception" in str(e):
            raise HTTPException(status_code=404, detail=f"索引 {index} 不存在")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/search",
    summary="搜索文档",
    description="在指定索引中搜索文档"
)
async def search_documents(
    index: str = Query("*", description="索引名称，* 表示所有索引"),
    query: str = Query("*", description="搜索查询"),
    size: int = Query(20, ge=1, le=100, description="返回结果数"),
    from_: int = Query(0, ge=0, alias="from", description="偏移量"),
    fuzzy: bool = Query(False, description="是否使用模糊搜索"),
    fields: str = Query("*", description="返回的字段，逗号分隔"),
    sortBy: str = Query("_score", description="排序字段"),
    sortOrder: str = Query("desc", description="排序方向")
):
    try:
        client = await elasticsearch_service.get_client()
        
        # 构建查询
        if query == "*":
            search_query = {"match_all": {}}
        else:
            if fuzzy:
                search_query = {
                    "match": {
                        "_all": {
                            "query": query,
                            "fuzziness": "AUTO"
                        }
                    }
                }
            else:
                search_query = {
                    "query_string": {
                        "query": query,
                        "default_field": "*"
                    }
                }
        
        # 构建排序
        sort = []
        if sortBy != "_score":
            sort.append({sortBy: {"order": sortOrder}})
        
        # 构建请求体
        body = {
            "query": search_query,
            "size": size,
            "from": from_,
            "sort": sort if sort else None,
            "highlight": {
                "fields": {
                    "*": {}
                },
                "fragment_size": 150,
                "number_of_fragments": 3
            }
        }
        
        # 执行搜索
        response = await client.search(index=index, body=body)
        
        return {
            "hits": response["hits"]["hits"],
            "total": response["hits"]["total"]["value"],
            "took": response["took"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/query",
    summary="执行原始查询",
    description="执行原始的 Elasticsearch 查询"
)
async def execute_query(request: QueryRequest):
    try:
        client = await elasticsearch_service.get_client()
        response = await client.search(index=request.index, body=request.body)
        return response
    except Exception as e:
        if "json_parse_exception" in str(e):
            raise HTTPException(status_code=400, detail="查询JSON格式错误")
        if "index_not_found_exception" in str(e):
            raise HTTPException(status_code=404, detail=f"索引 {request.index} 不存在")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/cluster/health",
    summary="获取集群健康状态",
    description="获取 Elasticsearch 集群的健康状态"
)
async def get_cluster_health():
    try:
        client = await elasticsearch_service.get_client()
        health = await client.cluster.health()
        return health
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/cluster/nodes",
    summary="获取节点统计",
    description="获取集群中所有节点的统计信息"
)
async def get_node_stats():
    try:
        client = await elasticsearch_service.get_client()
        
        # 获取节点统计
        nodes_stats = await client.nodes.stats()
        nodes_info = await client.nodes.info()
        
        result = []
        for node_id, node_stats in nodes_stats.get('nodes', {}).items():
            node_info = nodes_info.get('nodes', {}).get(node_id, {})
            
            result.append({
                "name": node_info.get('name', 'unknown'),
                "host": node_info.get('host', 'unknown'),
                "heap_percent": node_stats.get('jvm', {}).get('mem', {}).get('heap_used_percent', 0),
                "ram_percent": node_stats.get('os', {}).get('mem', {}).get('used_percent', 0),
                "cpu": node_stats.get('os', {}).get('cpu', {}).get('percent', 0),
                "load_1m": node_stats.get('os', {}).get('cpu', {}).get('load_average', {}).get('1m', 0),
                "load_5m": node_stats.get('os', {}).get('cpu', {}).get('load_average', {}).get('5m', 0),
                "load_15m": node_stats.get('os', {}).get('cpu', {}).get('load_average', {}).get('15m', 0),
                "disk_used_percent": 0,  # 需要计算
                "node_role": ', '.join(node_info.get('roles', [])),
                "master": 'master' in node_info.get('roles', [])
            })
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete(
    "/indices/{index}",
    summary="删除索引",
    description="删除指定的索引"
)
async def delete_index(
    index: str = Path(..., description="索引名称")
):
    try:
        if index.startswith('.'):
            raise HTTPException(status_code=400, detail="不能删除系统索引")
        
        client = await elasticsearch_service.get_client()
        response = await client.indices.delete(index=index)
        
        return {"message": f"索引 {index} 已删除", "acknowledged": response.get('acknowledged', False)}
    except HTTPException:
        raise
    except Exception as e:
        if "index_not_found_exception" in str(e):
            raise HTTPException(status_code=404, detail=f"索引 {index} 不存在")
        raise HTTPException(status_code=500, detail=str(e))


@router.put(
    "/indices/{index}",
    summary="创建索引",
    description="创建新的索引"
)
async def create_index(
    index: str = Path(..., description="索引名称"),
    body: Dict[str, Any] = Body({}, description="索引配置")
):
    try:
        client = await elasticsearch_service.get_client()
        response = await client.indices.create(index=index, body=body)
        
        return {"message": f"索引 {index} 已创建", "acknowledged": response.get('acknowledged', False)}
    except Exception as e:
        if "resource_already_exists_exception" in str(e):
            raise HTTPException(status_code=400, detail=f"索引 {index} 已存在")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/indices/{index}/doc/{doc_id}",
    summary="获取文档",
    description="获取指定的文档"
)
async def get_document(
    index: str = Path(..., description="索引名称"),
    doc_id: str = Path(..., description="文档ID")
):
    try:
        client = await elasticsearch_service.get_client()
        response = await client.get(index=index, id=doc_id)
        return response
    except Exception as e:
        if "index_not_found_exception" in str(e):
            raise HTTPException(status_code=404, detail=f"索引 {index} 不存在")
        if "404" in str(e):
            raise HTTPException(status_code=404, detail=f"文档 {doc_id} 不存在")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete(
    "/indices/{index}/doc/{doc_id}",
    summary="删除文档",
    description="删除指定的文档"
)
async def delete_document(
    index: str = Path(..., description="索引名称"),
    doc_id: str = Path(..., description="文档ID")
):
    try:
        client = await elasticsearch_service.get_client()
        response = await client.delete(index=index, id=doc_id)
        
        return {
            "message": f"文档 {doc_id} 已删除",
            "result": response.get('result', 'unknown')
        }
    except Exception as e:
        if "index_not_found_exception" in str(e):
            raise HTTPException(status_code=404, detail=f"索引 {index} 不存在")
        if "404" in str(e):
            raise HTTPException(status_code=404, detail=f"文档 {doc_id} 不存在")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/bulk",
    summary="批量操作",
    description="执行批量操作"
)
async def bulk_operations(
    operations: List[Dict[str, Any]] = Body(..., description="批量操作列表")
):
    try:
        client = await elasticsearch_service.get_client()
        
        # 构建批量操作体
        body = []
        for op in operations:
            body.append(op)
        
        response = await client.bulk(body=body)
        
        return {
            "took": response.get('took', 0),
            "errors": response.get('errors', False),
            "items": response.get('items', [])
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))