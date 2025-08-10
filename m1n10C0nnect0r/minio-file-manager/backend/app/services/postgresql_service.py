#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PostgreSQL数据库服务
处理newsletters表的CRUD操作
"""

import asyncpg
import uuid
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
import json
import hashlib
import logging
from app.core.config import get_settings

# 配置日志记录器
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PostgreSQLService:
    """PostgreSQL数据库服务"""
    
    def __init__(self):
        self.settings = get_settings()
        self.pool = None
        
    async def get_pool(self) -> asyncpg.Pool:
        """获取数据库连接池"""
        if self.pool is None:
            logger.info(
                "初始化PostgreSQL连接池: host=%s port=%s database=%s user=%s",
                self.settings.postgres_host,
                self.settings.postgres_port,
                self.settings.postgres_database,
                self.settings.postgres_user,
            )
            try:
                self.pool = await asyncpg.create_pool(
                    host=self.settings.postgres_host,
                    port=self.settings.postgres_port,
                    database=self.settings.postgres_database,
                    user=self.settings.postgres_user,
                    password=self.settings.postgres_password,
                    min_size=1,
                    max_size=10
                )
            except Exception as e:
                logger.error("创建PostgreSQL连接池失败: %s", str(e))
                logger.error(
                    "请检查数据库配置或创建相应用户/数据库. 例如: POSTGRES_HOST=%s POSTGRES_PORT=%s POSTGRES_DATABASE=%s POSTGRES_USER=%s",
                    self.settings.postgres_host,
                    self.settings.postgres_port,
                    self.settings.postgres_database,
                    self.settings.postgres_user,
                )
                raise
        return self.pool
    
    async def close_pool(self):
        """关闭连接池"""
        if self.pool:
            await self.pool.close()
            self.pool = None
    
    def generate_unique_id(self) -> str:
        """生成唯一ID"""
        return str(uuid.uuid4())
    
    def determine_category(self, filename: str, content: str, metadata: Dict) -> str:
        """判断文章分类，映射到NewsletterCategory枚举"""
        filename_lower = filename.lower()
        content_lower = content.lower() if content else ""
        
        # 根据文件名和内容判断分类 (AI_AGENT, AI_NEWS, AI_PAPERS, AI_CODING, AI_TOOLS)
        if 'agent' in filename_lower or 'ai' in filename_lower or 'llm' in filename_lower:
            return 'AI_AGENT'
        elif 'paper' in filename_lower or 'research' in filename_lower or '论文' in filename_lower:
            return 'AI_PAPERS'
        elif 'code' in filename_lower or 'tutorial' in filename_lower or '教程' in filename_lower:
            return 'AI_CODING'
        elif 'tool' in filename_lower or 'library' in filename_lower or '工具' in filename_lower:
            return 'AI_TOOLS'
        elif metadata.get('has_code', False):
            return 'AI_CODING'
        else:
            return 'AI_NEWS'  # 默认分类
    
    async def insert_newsletter(
        self,
        title: str,
        summary: str,
        content: Optional[str],
        category: str,
        tags: List[Dict[str, Any]],
        author: Optional[str],
        source_url: Optional[str],
        read_time: Optional[int],
        content_file_key: str,
        metadata: Optional[Dict[str, Any]] = None,
        use_auto_id: bool = True  # 新增参数：是否使用数据库自动生成ID
    ) -> Dict[str, Any]:
        """插入新的newsletter记录"""
        
        logger.info("PostgreSQL Service - 开始插入newsletter记录")
        logger.debug(f"Title: {title}")
        logger.debug(f"Category: {category}")
        logger.debug(f"Content File Key: {content_file_key}")
        
        pool = await self.get_pool()
        
        # 根据配置决定是否生成ID
        newsletter_id = None
        if not use_auto_id:
            # 手动生成唯一ID
            newsletter_id = self.generate_unique_id()
            logger.info(f"手动生成的UUID: {newsletter_id}")
        else:
            logger.info("使用数据库自动生成ID")
        
        # 准备tags JSON
        tags_json = json.dumps(tags) if tags else '[]'
        logger.debug(f"Tags JSON: {tags_json}")
        
        # 准备metadata JSON
        metadata_json = json.dumps(metadata) if metadata else '{}'
        logger.debug(f"Metadata keys: {list(metadata.keys()) if metadata else []}")
        
        # 设置时间戳 - 使用无时区的时间戳
        now = datetime.now()
        logger.debug(f"Timestamp: {now.isoformat()}")
        
        # 根据是否自动生成ID构建不同的查询
        if use_auto_id:
            # 使用数据库生成ID（使用gen_random_uuid()或uuid_generate_v4()）
            query = """
                INSERT INTO public.newsletters (
                    id, title, summary, content, category, tags, author,
                    "sourceUrl", "readTime", "viewCount", "likeCount", 
                    "shareCount", "commentCount", featured, "memberOnly",
                    status, "publishedAt", "createdAt", "updatedAt", metadata,
                    "contentFileKey", "contentStorageType"
                ) VALUES (
                    gen_random_uuid()::text, $1, $2, $3, $4::"NewsletterCategory", $5::jsonb, $6,
                    $7, $8, $9, $10, $11, $12, $13, $14,
                    $15::"ContentStatus", $16, $17, $18, $19::jsonb,
                    $20, $21
                )
                RETURNING *
            """
        else:
            # 使用手动生成的ID
            query = """
                INSERT INTO public.newsletters (
                    id, title, summary, content, category, tags, author,
                    "sourceUrl", "readTime", "viewCount", "likeCount", 
                    "shareCount", "commentCount", featured, "memberOnly",
                    status, "publishedAt", "createdAt", "updatedAt", metadata,
                    "contentFileKey", "contentStorageType"
                ) VALUES (
                    $1, $2, $3, $4, $5::"NewsletterCategory", $6::jsonb, $7,
                    $8, $9, $10, $11, $12, $13, $14, $15,
                    $16::"ContentStatus", $17, $18, $19, $20::jsonb,
                    $21, $22
                )
                RETURNING *
            """
        
        try:
            async with pool.acquire() as conn:
                # 不再检查标题重复，允许标题重复
                logger.info(f"准备插入记录，标题: {title}")
                
                # 记录SQL参数
                logger.info("准备执行INSERT语句")
                if use_auto_id:
                    logger.debug(f"SQL参数: 使用数据库自动生成ID, Title={title}, Category={category}, Author={author}")
                else:
                    logger.debug(f"SQL参数: ID={newsletter_id}, Title={title}, Category={category}, Author={author}")
                
                # 准备参数（根据是否自动生成ID）
                if use_auto_id:
                    # 不传递ID，数据库自动生成
                    params = [
                        title,               # $1: title
                        summary,             # $2: summary
                        content,             # $3: content
                        category,            # $4: category (NewsletterCategory)
                        tags_json,           # $5: tags (jsonb)
                        author,              # $6: author
                        source_url,          # $7: sourceUrl
                        read_time,           # $8: readTime
                        0,                   # $9: viewCount
                        0,                   # $10: likeCount
                        0,                   # $11: shareCount
                        0,                   # $12: commentCount
                        False,               # $13: featured
                        False,               # $14: memberOnly
                        'PUBLISHED',         # $15: status (ContentStatus)
                        now,                 # $16: publishedAt
                        now,                 # $17: createdAt
                        now,                 # $18: updatedAt
                        metadata_json,       # $19: metadata (jsonb)
                        content_file_key,    # $20: contentFileKey
                        'markdown'           # $21: contentStorageType
                    ]
                else:
                    # 传递手动生成的ID
                    params = [
                        newsletter_id,        # $1: id (text)
                        title,               # $2: title
                        summary,             # $3: summary
                        content,             # $4: content
                        category,            # $5: category (NewsletterCategory)
                        tags_json,           # $6: tags (jsonb)
                        author,              # $7: author
                        source_url,          # $8: sourceUrl
                        read_time,           # $9: readTime
                        0,                   # $10: viewCount
                        0,                   # $11: likeCount
                        0,                   # $12: shareCount
                        0,                   # $13: commentCount
                        False,               # $14: featured
                        False,               # $15: memberOnly
                        'PUBLISHED',         # $16: status (ContentStatus)
                        now,                 # $17: publishedAt
                        now,                 # $18: createdAt
                        now,                 # $19: updatedAt
                        metadata_json,       # $20: metadata (jsonb)
                        content_file_key,    # $21: contentFileKey
                        'markdown'           # $22: contentStorageType
                    ]
                
                # 插入新记录
                row = await conn.fetchrow(query, *params)
                
                logger.info(f"成功插入记录: ID={row['id']}, Title={row['title']}")
                logger.debug(f"创建时间: {row['createdAt'].isoformat() if row['createdAt'] else None}")
                
                return {
                    'success': True,
                    'id': row['id'],
                    'title': row['title'],
                    'created_at': row['createdAt'].isoformat() if row['createdAt'] else None,
                    'is_duplicate': False
                }
                
        except Exception as e:
            logger.error(f"PostgreSQL插入失败: {str(e)}")
            logger.exception("详细错误信息:")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def get_newsletter_by_id(self, newsletter_id: str) -> Optional[Dict[str, Any]]:
        """根据ID获取newsletter"""
        pool = await self.get_pool()
        
        try:
            async with pool.acquire() as conn:
                row = await conn.fetchrow(
                    "SELECT * FROM public.newsletters WHERE id = $1",
                    newsletter_id
                )
                
                if row:
                    return dict(row)
                return None
                
        except Exception as e:
            print(f"Error getting newsletter: {e}")
            return None
    
    async def update_newsletter_metadata(
        self,
        newsletter_id: str,
        metadata_updates: Dict[str, Any]
    ) -> bool:
        """更新newsletter的metadata字段"""
        pool = await self.get_pool()
        
        try:
            async with pool.acquire() as conn:
                # 获取现有metadata
                existing = await conn.fetchrow(
                    "SELECT metadata FROM public.newsletters WHERE id = $1",
                    newsletter_id
                )
                
                if not existing:
                    return False
                
                # 合并metadata
                current_metadata = existing['metadata'] or {}
                current_metadata.update(metadata_updates)
                
                # 更新记录
                await conn.execute(
                    """
                    UPDATE public.newsletters 
                    SET metadata = $1::jsonb, "updatedAt" = $2
                    WHERE id = $3
                    """,
                    json.dumps(current_metadata),
                    datetime.now(),
                    newsletter_id
                )
                
                return True
                
        except Exception as e:
            print(f"Error updating metadata: {e}")
            return False
    
    async def check_duplicate_by_content_hash(self, content_hash: str) -> Optional[str]:
        """通过内容哈希检查是否存在重复"""
        pool = await self.get_pool()
        
        try:
            async with pool.acquire() as conn:
                row = await conn.fetchrow(
                    """
                    SELECT id FROM public.newsletters 
                    WHERE metadata->>'content_hash' = $1
                    """,
                    content_hash
                )
                
                if row:
                    return row['id']
                return None
                
        except Exception as e:
            print(f"Error checking duplicate: {e}")
            return None


# 创建全局实例
postgresql_service = PostgreSQLService()