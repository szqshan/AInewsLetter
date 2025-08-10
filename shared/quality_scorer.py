#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
质量评估模块
用于评估论文、新闻、工具等内容的质量
"""

import re
import math
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)

class QualityScorer:
    """
    内容质量评估器
    """
    
    def __init__(self):
        # 顶级会议和期刊
        self.top_venues = {
            "NIPS": 10, "NeurIPS": 10, "ICML": 10, "ICLR": 10,
            "ACL": 9, "EMNLP": 9, "NAACL": 8, "COLING": 7,
            "CVPR": 10, "ICCV": 10, "ECCV": 9, "AAAI": 8,
            "IJCAI": 8, "KDD": 8, "WWW": 7, "SIGIR": 7,
            "Nature": 10, "Science": 10, "Cell": 9,
            "JMLR": 9, "PAMI": 8, "AIJ": 7
        }
        
        # 知名机构和作者权重
        self.institution_weights = {
            "OpenAI": 10, "Google": 9, "Microsoft": 9, "Facebook": 9,
            "Stanford": 10, "MIT": 10, "CMU": 10, "Berkeley": 9,
            "Harvard": 9, "Oxford": 8, "Cambridge": 8,
            "清华": 8, "北大": 8, "中科院": 7
        }
        
        # 关键词权重
        self.keyword_weights = {
            "GPT": 3, "BERT": 2, "Transformer": 2, "LLM": 3,
            "ChatGPT": 3, "Claude": 2, "Gemini": 2,
            "深度学习": 2, "机器学习": 1, "人工智能": 1,
            "neural network": 1, "deep learning": 2, "machine learning": 1
        }
    
    def score_paper(self, paper: Dict[str, Any]) -> Dict[str, Any]:
        """
        评估论文质量
        
        Args:
            paper: 论文信息字典
        
        Returns:
            包含质量分数的字典
        """
        scores = {
            "citation_score": 0,
            "venue_score": 0,
            "author_score": 0,
            "recency_score": 0,
            "keyword_score": 0,
            "total_score": 0
        }
        
        # 引用数评分
        citation_count = paper.get("citation_count", 0)
        scores["citation_score"] = self._calculate_citation_score(citation_count)
        
        # 会议/期刊评分
        venue = paper.get("venue", "")
        scores["venue_score"] = self._calculate_venue_score(venue)
        
        # 作者/机构评分
        authors = paper.get("authors", [])
        affiliations = paper.get("affiliations", [])
        scores["author_score"] = self._calculate_author_score(authors, affiliations)
        
        # 时效性评分
        publish_date = paper.get("published", "")
        scores["recency_score"] = self._calculate_recency_score(publish_date)
        
        # 关键词评分
        title = paper.get("title", "")
        abstract = paper.get("summary", "")
        scores["keyword_score"] = self._calculate_keyword_score(title + " " + abstract)
        
        # 计算总分
        weights = {
            "citation_score": 0.3,
            "venue_score": 0.25,
            "author_score": 0.2,
            "recency_score": 0.15,
            "keyword_score": 0.1
        }
        
        total = sum(scores[key] * weights[key] for key in weights)
        scores["total_score"] = round(total, 2)
        
        # 添加质量等级
        scores["quality_level"] = self._get_quality_level(scores["total_score"])
        
        return scores
    
    def score_news(self, news: Dict[str, Any]) -> Dict[str, Any]:
        """
        评估新闻质量
        
        Args:
            news: 新闻信息字典
        
        Returns:
            包含质量分数的字典
        """
        scores = {
            "source_score": 0,
            "content_score": 0,
            "engagement_score": 0,
            "recency_score": 0,
            "total_score": 0
        }
        
        # 来源可靠性评分
        source = news.get("source", "")
        scores["source_score"] = self._calculate_source_score(source)
        
        # 内容质量评分
        title = news.get("title", "")
        content = news.get("content", "")
        scores["content_score"] = self._calculate_content_score(title, content)
        
        # 参与度评分（点赞、评论等）
        engagement = news.get("engagement", {})
        scores["engagement_score"] = self._calculate_engagement_score(engagement)
        
        # 时效性评分
        publish_date = news.get("published", "")
        scores["recency_score"] = self._calculate_recency_score(publish_date)
        
        # 计算总分
        weights = {
            "source_score": 0.3,
            "content_score": 0.4,
            "engagement_score": 0.2,
            "recency_score": 0.1
        }
        
        total = sum(scores[key] * weights[key] for key in weights)
        scores["total_score"] = round(total, 2)
        scores["quality_level"] = self._get_quality_level(scores["total_score"])
        
        return scores
    
    def score_tool(self, tool: Dict[str, Any]) -> Dict[str, Any]:
        """
        评估AI工具质量
        
        Args:
            tool: 工具信息字典
        
        Returns:
            包含质量分数的字典
        """
        scores = {
            "popularity_score": 0,
            "functionality_score": 0,
            "maintenance_score": 0,
            "documentation_score": 0,
            "total_score": 0
        }
        
        # 受欢迎程度评分（GitHub星数、下载量等）
        popularity = tool.get("popularity", {})
        scores["popularity_score"] = self._calculate_popularity_score(popularity)
        
        # 功能性评分
        description = tool.get("description", "")
        features = tool.get("features", [])
        scores["functionality_score"] = self._calculate_functionality_score(description, features)
        
        # 维护状态评分
        last_update = tool.get("last_update", "")
        scores["maintenance_score"] = self._calculate_maintenance_score(last_update)
        
        # 文档质量评分
        has_docs = tool.get("has_documentation", False)
        readme_quality = tool.get("readme_quality", 0)
        scores["documentation_score"] = self._calculate_documentation_score(has_docs, readme_quality)
        
        # 计算总分
        weights = {
            "popularity_score": 0.3,
            "functionality_score": 0.3,
            "maintenance_score": 0.25,
            "documentation_score": 0.15
        }
        
        total = sum(scores[key] * weights[key] for key in weights)
        scores["total_score"] = round(total, 2)
        scores["quality_level"] = self._get_quality_level(scores["total_score"])
        
        return scores
    
    def _calculate_citation_score(self, citation_count: int) -> float:
        """计算引用数评分"""
        if citation_count <= 0:
            return 0
        # 使用对数函数，避免极值影响
        return min(10, math.log10(citation_count + 1) * 2)
    
    def _calculate_venue_score(self, venue: str) -> float:
        """计算会议/期刊评分"""
        venue_upper = venue.upper()
        for v, score in self.top_venues.items():
            if v.upper() in venue_upper:
                return score
        return 3  # 默认分数
    
    def _calculate_author_score(self, authors: List[str], affiliations: List[str]) -> float:
        """计算作者/机构评分"""
        max_score = 0
        
        # 检查机构
        for affiliation in affiliations:
            for inst, score in self.institution_weights.items():
                if inst.lower() in affiliation.lower():
                    max_score = max(max_score, score)
        
        return min(10, max_score)
    
    def _calculate_recency_score(self, publish_date: str) -> float:
        """计算时效性评分"""
        try:
            if not publish_date:
                return 5
            
            # Try to parse date
            if isinstance(publish_date, str):
                from dateutil import parser
                pub_date = parser.parse(publish_date)
            else:
                pub_date = publish_date
            
            days_ago = (datetime.now() - pub_date).days
            
            if days_ago <= 7:
                return 10  # 一周内
            elif days_ago <= 30:
                return 8   # 一月内
            elif days_ago <= 90:
                return 6   # 三月内
            elif days_ago <= 365:
                return 4   # 一年内
            else:
                return 2   # 超过一年
        except:
            return 5  # 解析失败，给默认分
    
    def _calculate_keyword_score(self, text: str) -> float:
        """计算关键词评分"""
        text_lower = text.lower()
        score = 0
        
        for keyword, weight in self.keyword_weights.items():
            if keyword.lower() in text_lower:
                score += weight
        
        return min(10, score)
    
    def _calculate_source_score(self, source: str) -> float:
        """计算新闻来源评分"""
        reliable_sources = {
            "openai": 10, "google": 9, "microsoft": 9,
            "arxiv": 10, "nature": 10, "science": 10,
            "mit": 9, "stanford": 9, "berkeley": 8,
            "机器之心": 7, "量子位": 7, "ai科技大本营": 6
        }
        
        source_lower = source.lower()
        for src, score in reliable_sources.items():
            if src in source_lower:
                return score
        
        return 5  # 默认分数
    
    def _calculate_content_score(self, title: str, content: str) -> float:
        """计算内容质量评分"""
        score = 5  # 基础分
        
        # 标题长度合理性
        if 10 <= len(title) <= 100:
            score += 1
        
        # 内容长度
        if len(content) > 500:
            score += 2
        elif len(content) > 200:
            score += 1
        
        # 包含技术关键词
        tech_keywords = ["AI", "机器学习", "深度学习", "算法", "模型", "数据"]
        keyword_count = sum(1 for kw in tech_keywords if kw.lower() in (title + content).lower())
        score += min(2, keyword_count * 0.5)
        
        return min(10, score)
    
    def _calculate_engagement_score(self, engagement: Dict) -> float:
        """计算参与度评分"""
        likes = engagement.get("likes", 0)
        comments = engagement.get("comments", 0)
        shares = engagement.get("shares", 0)
        
        total_engagement = likes + comments * 2 + shares * 3
        
        if total_engagement >= 1000:
            return 10
        elif total_engagement >= 500:
            return 8
        elif total_engagement >= 100:
            return 6
        elif total_engagement >= 10:
            return 4
        else:
            return 2
    
    def _calculate_popularity_score(self, popularity: Dict) -> float:
        """计算工具受欢迎程度评分"""
        stars = popularity.get("github_stars", 0)
        downloads = popularity.get("downloads", 0)
        forks = popularity.get("forks", 0)
        
        score = 0
        
        # GitHub星数评分
        if stars >= 10000:
            score += 4
        elif stars >= 1000:
            score += 3
        elif stars >= 100:
            score += 2
        elif stars >= 10:
            score += 1
        
        # 下载量评分
        if downloads >= 100000:
            score += 3
        elif downloads >= 10000:
            score += 2
        elif downloads >= 1000:
            score += 1
        
        # Fork数评分
        if forks >= 1000:
            score += 3
        elif forks >= 100:
            score += 2
        elif forks >= 10:
            score += 1
        
        return min(10, score)
    
    def _calculate_functionality_score(self, description: str, features: List[str]) -> float:
        """计算功能性评分"""
        score = 5  # 基础分
        
        # 描述质量
        if len(description) > 100:
            score += 2
        elif len(description) > 50:
            score += 1
        
        # 功能数量
        score += min(3, len(features) * 0.5)
        
        return min(10, score)
    
    def _calculate_maintenance_score(self, last_update: str) -> float:
        """计算维护状态评分"""
        try:
            if not last_update:
                return 3
            
            from dateutil import parser
            update_date = parser.parse(last_update)
            days_ago = (datetime.now() - update_date).days
            
            if days_ago <= 30:
                return 10  # 一月内更新
            elif days_ago <= 90:
                return 8   # 三月内更新
            elif days_ago <= 180:
                return 6   # 半年内更新
            elif days_ago <= 365:
                return 4   # 一年内更新
            else:
                return 2   # 超过一年未更新
        except:
            return 5
    
    def _calculate_documentation_score(self, has_docs: bool, readme_quality: int) -> float:
        """计算文档质量评分"""
        score = 0
        
        if has_docs:
            score += 5
        
        score += min(5, readme_quality)
        
        return min(10, score)
    
    def _get_quality_level(self, score: float) -> str:
        """根据分数获取质量等级"""
        if score >= 8.5:
            return "优秀"
        elif score >= 7.0:
            return "良好"
        elif score >= 5.5:
            return "一般"
        elif score >= 4.0:
            return "较差"
        else:
            return "很差"

if __name__ == "__main__":
    # 测试质量评估器
    scorer = QualityScorer()
    
    # 测试论文评分
    test_paper = {
        "title": "GPT-4: A Large-Scale Language Model",
        "summary": "This paper presents GPT-4, a large language model...",
        "citation_count": 1500,
        "venue": "NIPS 2023",
        "authors": ["John Doe", "Jane Smith"],
        "affiliations": ["OpenAI", "Stanford University"],
        "published": "2023-12-01"
    }
    
    paper_scores = scorer.score_paper(test_paper)
    print("📊 论文质量评分:")
    for key, value in paper_scores.items():
        print(f"  {key}: {value}")
    
    print("\n✅ 质量评估器测试完成")
