"""\n本地数据保存模块\n负责将爬取的文章数据保存到本地文件系统\n"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from loguru import logger

from spider import ArticleDetail


class LocalSaver:
    """本地文件保存器"""
    
    def __init__(self, config: Dict = None):
        """初始化本地保存器"""
        self.config = config or {}
        logger.info("本地保存器初始化成功")
    
    def _generate_doc_id(self, url: str) -> str:
        """生成文档ID"""
        import hashlib
        return hashlib.md5(url.encode('utf-8')).hexdigest()
    
    def save_to_local(self, article: ArticleDetail, output_dir: str = "./crawled_data") -> str:
        """保存到本地文件系统，使用规范化的目录结构"""
        base_path = Path(output_dir)
        base_path.mkdir(parents=True, exist_ok=True)
        
        # 使用文章标题作为目录名（清理特殊字符）
        import re
        clean_title = re.sub(r'[^\w\u4e00-\u9fff\s-]', '', article.title)
        clean_title = re.sub(r'\s+', '-', clean_title.strip())
        # 限制长度，防止目录名过长
        if len(clean_title) > 50:
            clean_title = clean_title[:50]

        # 创建文章目录
        article_dir = base_path / clean_title
        article_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建媒体目录
        media_dir = article_dir / "media"
        media_dir.mkdir(exist_ok=True)
        
        # 图片已在spider中下载，这里只需要记录
        downloaded_images = article.images  # 现在article.images已经是本地文件名列表
        
        # 生成唯一ID
        unique_id = self._generate_doc_id(article.url)
        
        # 保存metadata.json
        metadata_path = article_dir / "metadata.json"
        metadata = {
            "id": unique_id,
            "title": article.title,
            "url": article.url,
            "author": article.author,
            "publish_date": article.publish_date,
            "tags": article.tags,
            "word_count": article.word_count,
            "source": "OpenAI Newsroom",
            "crawl_time": datetime.now().isoformat(),
            "file_size": len(article.content),
            "images": downloaded_images,  # 保存本地图片文件名
            "original_images": article.metadata.get('original_images', [])  # 保存原始图片URL
        }
        
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        
        # 保存content.md
        content_path = article_dir / "content.md"
        markdown_content = self._convert_to_markdown(article, downloaded_images)
        with open(content_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        logger.info(f"文章已保存到目录: {article_dir}")
        return str(article_dir)
    
    def process_articles(self, articles: List[ArticleDetail], 
                        output_dir: str = "./crawled_data") -> Dict[str, int]:
        """处理文章列表，保存到本地"""
        results = {
            "total": len(articles),
            "local_saved": 0,
            "failed": 0
        }
        
        for article in articles:
            try:
                self.save_to_local(article, output_dir)
                results["local_saved"] += 1
                        
            except Exception as e:
                logger.error(f"保存文章失败: {article.title}, 错误: {str(e)}")
                results["failed"] += 1
        
        return results
    
    def _convert_to_markdown(self, article: ArticleDetail, local_images: List[str] = None) -> str:
        """转换为Markdown格式"""
        # 使用本地图片路径或原始URL
        images_to_show = local_images if local_images else article.images
        image_list = ''
        if images_to_show:
            if local_images:
                # 本地图片使用相对路径
                image_list = chr(10).join(f'- ![{i+1}](./media/{img})' for i, img in enumerate(images_to_show))
            else:
                # 原始URL
                image_list = chr(10).join(f'- ![{i+1}]({img})' for i, img in enumerate(images_to_show))
        else:
            image_list = '无图片'
            
        md_content = f"""# {article.title}

**来源**: {article.source}  
**URL**: {article.url}  
**作者**: {article.author or '未知'}  
**发布日期**: {article.publish_date or '未知'}  
**字数**: {article.word_count}  
**标签**: {', '.join(article.tags) if article.tags else '无'}

---

{article.content}

---

## 图片列表

{image_list}

---

**抓取时间**: {article.metadata.get('scraped_at', datetime.now().isoformat())}
"""
        return md_content


# 为了保持向后兼容性，保留DataUploader别名
DataUploader = LocalSaver