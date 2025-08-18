#!/usr/bin/env python3
"""
工具函数和辅助类
"""

import json
import hashlib
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from urllib.parse import urlparse


class ArticleUtils:
    """文章处理工具类"""
    
    @staticmethod
    def clean_text(text: str) -> str:
        """清理文本内容"""
        if not text:
            return ""
        
        # 去除多余空白
        text = re.sub(r'\s+', ' ', text.strip())
        
        # 去除特殊字符
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', text)
        
        return text
    
    @staticmethod
    def extract_keywords(text: str, max_keywords: int = 10) -> List[str]:
        """从文本中提取关键词"""
        if not text:
            return []
        
        # 简单的关键词提取（基于词频）
        words = re.findall(r'\b[a-zA-Z\u4e00-\u9fff]{3,}\b', text.lower())
        
        # 统计词频
        word_count = {}
        for word in words:
            word_count[word] = word_count.get(word, 0) + 1
        
        # 按频率排序并返回前N个
        sorted_words = sorted(word_count.items(), key=lambda x: x[1], reverse=True)
        return [word for word, count in sorted_words[:max_keywords]]
    
    @staticmethod
    def calculate_reading_time(text: str, words_per_minute: int = 200) -> int:
        """计算阅读时间（分钟）"""
        if not text:
            return 0
        
        word_count = len(text.split())
        return max(1, word_count // words_per_minute)
    
    @staticmethod
    def generate_summary(text: str, max_sentences: int = 3) -> str:
        """生成简单摘要（取前几句）"""
        if not text:
            return ""
        
        sentences = re.split(r'[.!?。！？]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        return '。'.join(sentences[:max_sentences]) + '。'


class FileUtils:
    """文件处理工具类"""
    
    @staticmethod
    def safe_filename(filename: str) -> str:
        """生成安全的文件名"""
        # 移除或替换非法字符
        safe_name = re.sub(r'[<>:"/\\|?*]', '_', filename)
        safe_name = re.sub(r'\s+', '_', safe_name)
        
        # 限制长度
        if len(safe_name) > 100:
            safe_name = safe_name[:100]
        
        return safe_name
    
    @staticmethod
    def get_file_hash(file_path: Path) -> str:
        """计算文件MD5哈希"""
        if not file_path.exists():
            return ""
        
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    @staticmethod
    def ensure_dir(path: Path) -> Path:
        """确保目录存在"""
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    @staticmethod
    def backup_file(file_path: Path, backup_suffix: str = ".bak") -> Optional[Path]:
        """备份文件"""
        if not file_path.exists():
            return None
        
        backup_path = file_path.with_suffix(file_path.suffix + backup_suffix)
        backup_path.write_bytes(file_path.read_bytes())
        return backup_path


class DataValidator:
    """数据验证工具类"""
    
    @staticmethod
    def validate_article_data(article_data: Dict) -> List[str]:
        """验证文章数据完整性"""
        errors = []
        
        required_fields = ['url', 'title', 'content', 'slug', 'crawl_time']
        for field in required_fields:
            if field not in article_data or not article_data[field]:
                errors.append(f"缺少必需字段: {field}")
        
        # 验证URL格式
        if 'url' in article_data:
            parsed = urlparse(article_data['url'])
            if not parsed.scheme or not parsed.netloc:
                errors.append("无效的URL格式")
        
        # 验证内容长度
        if 'content' in article_data:
            if len(article_data['content']) < 50:
                errors.append("文章内容过短")
        
        return errors
    
    @staticmethod
    def validate_config(config: Dict) -> List[str]:
        """验证配置文件"""
        errors = []
        
        required_sections = ['api', 'crawler', 'storage', 'logging']
        for section in required_sections:
            if section not in config:
                errors.append(f"配置文件缺少节: {section}")
        
        # 验证API配置
        if 'api' in config:
            api_config = config['api']
            if 'posts_endpoint' not in api_config:
                errors.append("API配置缺少posts_endpoint")
        
        # 验证爬虫配置
        if 'crawler' in config:
            crawler_config = config['crawler']
            if 'delay' in crawler_config and crawler_config['delay'] < 1:
                errors.append("爬虫延迟时间过短，建议至少1秒")
        
        return errors


class ProgressTracker:
    """进度跟踪工具类"""
    
    def __init__(self, total: int):
        self.total = total
        self.current = 0
        self.start_time = datetime.now()
    
    def update(self, increment: int = 1):
        """更新进度"""
        self.current += increment
    
    def get_progress(self) -> Dict[str, Any]:
        """获取进度信息"""
        elapsed = datetime.now() - self.start_time
        progress_pct = (self.current / self.total * 100) if self.total > 0 else 0
        
        # 估算剩余时间
        if self.current > 0:
            avg_time_per_item = elapsed.total_seconds() / self.current
            remaining_items = self.total - self.current
            estimated_remaining = remaining_items * avg_time_per_item
        else:
            estimated_remaining = 0
        
        return {
            'current': self.current,
            'total': self.total,
            'progress_pct': progress_pct,
            'elapsed_seconds': elapsed.total_seconds(),
            'estimated_remaining_seconds': estimated_remaining
        }
    
    def format_progress(self) -> str:
        """格式化进度信息"""
        info = self.get_progress()
        return f"{info['current']}/{info['total']} ({info['progress_pct']:.1f}%)"


class ConfigManager:
    """配置管理工具类"""
    
    @staticmethod
    def load_config(config_path: str) -> Dict:
        """加载配置文件"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"配置文件不存在: {config_path}")
        except json.JSONDecodeError as e:
            raise ValueError(f"配置文件格式错误: {e}")
    
    @staticmethod
    def save_config(config: Dict, config_path: str):
        """保存配置文件"""
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
    
    @staticmethod
    def merge_configs(base_config: Dict, override_config: Dict) -> Dict:
        """合并配置文件"""
        merged = base_config.copy()
        
        for key, value in override_config.items():
            if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
                merged[key] = ConfigManager.merge_configs(merged[key], value)
            else:
                merged[key] = value
        
        return merged


class ReportGenerator:
    """报告生成工具类"""
    
    @staticmethod
    def generate_crawl_report(crawl_stats: Dict) -> str:
        """生成爬取报告"""
        template = """
# Hugging Face博客爬取报告

## 基本统计
- 爬取时间: {crawl_time}
- 总发现文章: {total_found}
- 成功爬取: {successful}
- 失败文章: {failed}
- 成功率: {success_rate:.1f}%

## 数据存储
- 存储目录: {storage_dir}
- 文章目录数: {article_dirs}
- 媒体文件数: {media_files}

## 错误分析
{error_summary}

---
*报告生成时间: {report_time}*
        """
        
        return template.format(
            crawl_time=crawl_stats.get('crawl_time', 'Unknown'),
            total_found=crawl_stats.get('total_found', 0),
            successful=crawl_stats.get('successful', 0),
            failed=crawl_stats.get('failed', 0),
            success_rate=crawl_stats.get('success_rate', 0),
            storage_dir=crawl_stats.get('storage_dir', ''),
            article_dirs=crawl_stats.get('article_dirs', 0),
            media_files=crawl_stats.get('media_files', 0),
            error_summary=crawl_stats.get('error_summary', '无错误'),
            report_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        )
    
    @staticmethod
    def generate_article_index(articles_dir: Path) -> str:
        """生成文章索引"""
        if not articles_dir.exists():
            return "# 文章索引\n\n目录不存在"
        
        index_content = "# Hugging Face博客文章索引\n\n"
        
        article_count = 0
        for article_dir in articles_dir.iterdir():
            if article_dir.is_dir():
                metadata_path = article_dir / "metadata.json"
                if metadata_path.exists():
                    try:
                        with open(metadata_path, 'r', encoding='utf-8') as f:
                            metadata = json.load(f)
                        
                        article_count += 1
                        index_content += f"## {article_count}. {metadata.get('title', 'Unknown Title')}\n\n"
                        index_content += f"- **URL**: {metadata.get('url', '')}\n"
                        index_content += f"- **Slug**: {metadata.get('slug', '')}\n"
                        index_content += f"- **字数**: {metadata.get('word_count', 0)}\n"
                        index_content += f"- **爬取时间**: {metadata.get('crawl_time', '')}\n"
                        index_content += f"- **本地路径**: `{article_dir.name}/`\n\n"
                        
                    except Exception as e:
                        index_content += f"## {article_count + 1}. 解析失败: {article_dir.name}\n\n"
                        index_content += f"- **错误**: {str(e)}\n\n"
        
        index_content += f"\n---\n**总计**: {article_count} 篇文章\n"
        index_content += f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        
        return index_content


if __name__ == "__main__":
    # 简单测试
    print("工具函数测试...")
    
    # 测试文本清理
    text = "  这是一个\n\n测试文本  \t  "
    cleaned = ArticleUtils.clean_text(text)
    print(f"清理前: {repr(text)}")
    print(f"清理后: {repr(cleaned)}")
    
    # 测试关键词提取
    content = "机器学习和人工智能是现代科技的重要组成部分。深度学习在图像识别和自然语言处理方面取得了重大突破。"
    keywords = ArticleUtils.extract_keywords(content)
    print(f"关键词: {keywords}")
    
    # 测试阅读时间计算
    reading_time = ArticleUtils.calculate_reading_time(content)
    print(f"阅读时间: {reading_time} 分钟")
    
    print("测试完成")