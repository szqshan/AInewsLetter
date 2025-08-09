#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全局配置文件
统一管理所有爬虫的配置参数
"""

import os
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent

# 数据存储路径
DATA_ROOT = PROJECT_ROOT / "data"
RAW_DATA_PATH = DATA_ROOT / "raw"
PROCESSED_DATA_PATH = DATA_ROOT / "processed"
EXPORTS_PATH = DATA_ROOT / "exports"

# 爬虫通用配置
COMMON_CONFIG = {
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "request_delay": 1,  # 请求间隔（秒）
    "timeout": 30,  # 请求超时时间
    "max_retries": 3,  # 最大重试次数
    "concurrent_limit": 5,  # 并发限制
}

# 各平台特定配置
ARXIV_CONFIG = {
    'base_url': 'http://export.arxiv.org/api/query',
    'max_results': 100,
    'categories': ['cs.AI', 'cs.LG', 'cs.CL', 'cs.CV'],
    'search_terms': [
        'artificial intelligence',
        'machine learning', 
        'deep learning',
        'neural network',
        'transformer',
        'large language model'
    ]
}

# Google Scholar配置
GOOGLE_SCHOLAR_CONFIG = {
    'base_url': 'https://scholar.google.com/scholar',
    'max_results': 50,
    'search_terms': [
        'artificial intelligence 2024',
        'machine learning transformer',
        'large language model'
    ]
}

# Hugging Face配置
HUGGINGFACE_CONFIG = {
    'base_url': 'https://huggingface.co/papers',
    'max_results': 30,
    'days_back': 7
}

# GitHub配置
GITHUB_CONFIG = {
    'base_url': 'https://github.com/trending',
    'languages': ['python', 'javascript', 'typescript'],
    'time_ranges': ['daily', 'weekly'],
    'ai_keywords': [
        'artificial intelligence', 'machine learning', 'deep learning',
        'neural network', 'transformer', 'llm', 'large language model',
        'gpt', 'bert', 'chatbot', 'computer vision', 'nlp'
    ]
}

PLATFORM_CONFIGS = {
    "arxiv": ARXIV_CONFIG,
    "papers_with_code": {
        "base_url": "https://paperswithcode.com/api/v1/",
        "api_key": None,  # 如果需要API密钥
    },
    "huggingface": HUGGINGFACE_CONFIG,
    "github": GITHUB_CONFIG
}

# 质量评估配置
QUALITY_CONFIG = {
    "min_citation_count": 5,  # 最小引用数
    "top_venues": ["NIPS", "ICML", "ICLR", "ACL", "EMNLP", "CVPR", "ICCV"],  # 顶级会议
    "quality_weights": {
        "citation_count": 0.4,
        "venue_score": 0.3,
        "author_score": 0.2,
        "recency": 0.1,
    }
}

# 输出格式配置
OUTPUT_CONFIG = {
    "formats": ["json", "markdown", "csv"],
    "markdown_template": "default",
    "include_pdf": True,
    "include_abstract": True,
}

# 日志配置
LOGGING_CONFIG = {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "file": PROJECT_ROOT / "logs" / "spider.log",
}

# 确保必要目录存在
def ensure_directories(additional_dirs=None):
    """确保所有必要的目录都存在"""
    directories = [
        DATA_ROOT,
        RAW_DATA_PATH,
        PROCESSED_DATA_PATH,
        EXPORTS_PATH,
        PROJECT_ROOT / "logs",
    ]
    
    # 添加额外的目录
    if additional_dirs:
        for dir_path in additional_dirs:
            if isinstance(dir_path, str):
                directories.append(Path(dir_path))
            else:
                directories.append(dir_path)
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)

if __name__ == "__main__":
    ensure_directories()
    print("Success: Configuration loaded and directory structure created")
