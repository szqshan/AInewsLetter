"""
索引初始化服务
在应用启动时自动创建和配置 Elasticsearch 索引
"""

from typing import Dict, Any
import asyncio
import json
import os
from pathlib import Path
from elasticsearch import AsyncElasticsearch
from app.services.elasticsearch_service import elasticsearch_service
from app.core.config import get_settings
import logging

logger = logging.getLogger(__name__)


class IndexInitializer:
    """索引初始化器"""
    
    def __init__(self):
        self.settings = get_settings()
        self.es_service = elasticsearch_service
        self._mapping_configs = None
        
    def _get_mapping_file_path(self) -> str:
        """获取mapping配置文件路径"""
        # 获取当前文件的目录，然后构建到配置文件的路径
        current_dir = Path(__file__).parent.parent.parent  # 回到backend目录
        config_path = current_dir / "config" / "elasticsearch_mappings.json"
        return str(config_path)
    
    def _load_mapping_configs(self) -> Dict[str, Any]:
        """从JSON文件加载索引映射配置"""
        if self._mapping_configs is not None:
            return self._mapping_configs
            
        config_file = self._get_mapping_file_path()
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                self._mapping_configs = json.load(f)
                logger.info(f"成功加载索引配置文件: {config_file}")
                return self._mapping_configs
        except FileNotFoundError:
            logger.error(f"索引配置文件未找到: {config_file}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"索引配置文件JSON格式错误: {e}")
            raise
        except Exception as e:
            logger.error(f"加载索引配置文件失败: {e}")
            raise
    
        
    async def initialize_indices(self):
        """初始化minio_articles索引"""
        try:
            client = await self.es_service.get_client()
            
            # 加载配置文件
            mapping_configs = self._load_mapping_configs()
            
            # 只创建minio_articles索引
            if "minio_articles" in mapping_configs:
                await self._create_index_if_not_exists(
                    client,
                    "minio_articles",
                    mapping_configs["minio_articles"]
                )
            else:
                logger.error("配置文件中未找到minio_articles索引配置")
                raise ValueError("minio_articles索引配置缺失")
            
            # 标记索引已初始化
            self.es_service._indices_initialized = True
            logger.info("minio_articles索引初始化完成")
            
        except Exception as e:
            logger.error(f"索引初始化失败: {e}")
            raise
    
    async def _create_index_if_not_exists(
        self,
        client: AsyncElasticsearch,
        index_name: str,
        mapping: Dict[str, Any]
    ):
        """创建索引（如果不存在）"""
        try:
            # 检查索引是否存在
            if await client.indices.exists(index=index_name):
                logger.info(f"索引 {index_name} 已存在")
                
                # 可选：更新映射（仅添加新字段）
                # await client.indices.put_mapping(
                #     index=index_name,
                #     body=mapping.get("mappings", {})
                # )
                
            else:
                # 创建新索引
                await client.indices.create(
                    index=index_name,
                    body=mapping
                )
                logger.info(f"成功创建索引: {index_name}")
                
        except Exception as e:
            error_msg = str(e)
            logger.error(f"创建索引 {index_name} 失败: {error_msg}")
            
            # 检查是否是分词器相关错误
            if "no [ik_max_word] or [ik_smart] tokenizer" in error_msg:
                logger.error("错误原因: IK分词器未安装,请先安装elasticsearch-analysis-ik插件")
            elif "Invalid mapping type" in error_msg:
                logger.error("错误原因: 索引映射配置无效,请检查mapping定义")
            elif "index already exists" in error_msg:
                logger.error("错误原因: 索引已存在")
            else:
                logger.error(f"错误原因: {error_msg}")
    

# 创建全局实例
index_initializer = IndexInitializer()


async def initialize_on_startup():
    """在应用启动时调用的初始化函数"""
    await index_initializer.initialize_indices()