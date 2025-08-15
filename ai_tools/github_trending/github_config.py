#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitHub爬虫配置文件
包含API Token和相关配置
"""

import os

# GitHub API配置
GITHUB_CONFIG = {
    # GitHub Personal Access Token
    "api_token": os.getenv("GITHUB_TOKEN", ""),  # 使用环境变量
    
    # API基础配置
    "api_base_url": "https://api.github.com",
    "trending_url": "https://github.com/trending",
    
    # 请求限制配置
    "rate_limits": {
        "authenticated": 5000,  # 每小时5000次请求
        "unauthenticated": 60,  # 每小时60次请求
        "search": 30,           # 每分钟30次搜索请求
    },
    
    # 请求头配置
    "headers": {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "AI-Newsletter-GitHub-Crawler/1.0"
    },
    
    # 爬取配置
    "crawl_config": {
        "languages": ["python", "javascript", "typescript", "jupyter-notebook"],
        "time_ranges": ["daily", "weekly"],
        "max_repos_per_language": 50,
        "request_delay": 1.0,  # API请求间隔（秒）
    },
    
    # AI相关关键词
    "ai_keywords": [
        # 核心AI关键词
        "artificial intelligence", "machine learning", "deep learning", "neural network",
        "transformer", "llm", "large language model", "gpt", "bert", "chatbot",
        
        # 技术框架
        "pytorch", "tensorflow", "keras", "scikit-learn", "huggingface",
        "openai", "anthropic", "langchain", "llamaindex",
        
        # 应用领域
        "computer vision", "nlp", "natural language processing", 
        "stable diffusion", "diffusion model", "generative ai",
        "reinforcement learning", "recommendation system",
        
        # 新兴技术
        "multimodal", "embedding", "vector database", "rag",
        "fine-tuning", "prompt engineering", "ai agent"
    ],
    
    # 质量过滤配置
    "quality_filters": {
        "min_stars": 10,
        "min_forks": 2,
        "max_days_since_update": 365,
        "exclude_archived": True,
        "exclude_forks": True,
    }
}


def get_api_headers():
    """获取带认证的API请求头"""
    headers = GITHUB_CONFIG["headers"].copy()
    headers["Authorization"] = f"token {GITHUB_CONFIG['api_token']}"
    return headers


def get_trending_url(language=None, since="daily"):
    """构建Trending页面URL"""
    url = GITHUB_CONFIG["trending_url"]
    
    if language:
        url += f"/{language}"
    
    url += f"?since={since}"
    return url


def get_repo_api_url(owner, repo):
    """构建仓库API URL"""
    return f"{GITHUB_CONFIG['api_base_url']}/repos/{owner}/{repo}"


def get_search_api_url():
    """获取搜索API URL"""
    return f"{GITHUB_CONFIG['api_base_url']}/search/repositories"


if __name__ == "__main__":
    print("🔧 GitHub配置信息:")
    print(f"   API Token: {GITHUB_CONFIG['api_token'][:20]}...")
    print(f"   API Base URL: {GITHUB_CONFIG['api_base_url']}")
    print(f"   认证请求头: {get_api_headers()}")
    print("✅ 配置加载成功")
