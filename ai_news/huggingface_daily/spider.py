#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hugging Face Daily Papers 爬虫
用于爬取Hugging Face每日论文推荐
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'shared'))

from config import HUGGINGFACE_CONFIG, ensure_directories
from utils import safe_request, save_json, save_markdown, generate_filename
from quality_scorer import QualityScorer
import requests
from bs4 import BeautifulSoup
import time
import json
from datetime import datetime, timedelta
import re

class HuggingFaceDailySpider:
    def __init__(self):
        self.base_url = "https://huggingface.co/papers"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.quality_scorer = QualityScorer()
        
        # 确保目录存在
        self.data_dir = os.path.join(os.path.dirname(__file__), 'data')
        self.markdown_dir = os.path.join(self.data_dir, 'markdown')
        ensure_directories([self.data_dir, self.markdown_dir])
    
    def get_daily_papers(self, days_back=7):
        """
        获取最近几天的论文
        """
        papers = []
        
        try:
            # 获取主页面
            response = safe_request(self.session.get, self.base_url)
            if not response:
                return papers
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 查找论文卡片
            paper_cards = soup.find_all('article', class_='flex')
            
            for card in paper_cards:
                paper = self._parse_paper_card(card)
                if paper:
                    # 检查日期是否在范围内
                    if self._is_recent_paper(paper.get('date'), days_back):
                        # 质量评估
                        paper['quality_score'] = self.quality_scorer.score_news(paper)
                        papers.append(paper)
                
                # 避免请求过于频繁
                time.sleep(1)
        
        except Exception as e:
            print(f"获取论文时出错: {e}")
        
        return papers
    
    def _parse_paper_card(self, card):
        """
        解析论文卡片信息
        """
        try:
            paper = {}
            
            # 标题和链接
            title_elem = card.find('h3')
            if title_elem:
                link_elem = title_elem.find('a')
                if link_elem:
                    paper['title'] = link_elem.get_text().strip()
                    paper['url'] = 'https://huggingface.co' + link_elem.get('href', '')
                else:
                    paper['title'] = title_elem.get_text().strip()
            
            # 作者信息
            author_elem = card.find('p', class_='text-gray-700')
            if author_elem:
                paper['authors'] = author_elem.get_text().strip()
            
            # 摘要
            abstract_elem = card.find('p', class_='text-gray-600')
            if abstract_elem:
                paper['abstract'] = abstract_elem.get_text().strip()
            
            # 点赞数和评论数
            stats_elem = card.find('div', class_='flex items-center')
            if stats_elem:
                # 查找点赞数
                like_elem = stats_elem.find('span', string=re.compile(r'\d+'))
                if like_elem:
                    try:
                        paper['likes'] = int(re.search(r'\d+', like_elem.get_text()).group())
                    except:
                        paper['likes'] = 0
            
            # 日期（通常在URL或其他地方）
            paper['date'] = datetime.now().strftime('%Y-%m-%d')
            
            # 标签/类别
            tag_elems = card.find_all('span', class_='badge')
            if tag_elems:
                paper['tags'] = [tag.get_text().strip() for tag in tag_elems]
            
            # 添加元数据
            paper['scraped_at'] = datetime.now().isoformat()
            paper['source'] = 'Hugging Face Daily Papers'
            paper['type'] = 'ai_news'
            
            return paper
        
        except Exception as e:
            print(f"解析论文卡片时出错: {e}")
            return None
    
    def _is_recent_paper(self, paper_date, days_back):
        """
        检查论文是否在指定天数内
        """
        try:
            if isinstance(paper_date, str):
                paper_dt = datetime.strptime(paper_date, '%Y-%m-%d')
            else:
                paper_dt = datetime.now()
            
            cutoff_date = datetime.now() - timedelta(days=days_back)
            return paper_dt >= cutoff_date
        except:
            return True  # 如果无法解析日期，默认包含
    
    def get_trending_papers(self):
        """
        获取热门论文
        """
        papers = []
        
        try:
            # 访问热门页面
            trending_url = f"{self.base_url}?sort=trending"
            response = safe_request(self.session.get, trending_url)
            if not response:
                return papers
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 解析热门论文
            paper_cards = soup.find_all('article', class_='flex')
            
            for card in paper_cards[:20]:  # 限制数量
                paper = self._parse_paper_card(card)
                if paper:
                    paper['is_trending'] = True
                    paper['quality_score'] = self.quality_scorer.score_news(paper)
                    papers.append(paper)
                
                time.sleep(1)
        
        except Exception as e:
            print(f"获取热门论文时出错: {e}")
        
        return papers
    
    def save_results(self, papers, result_type="daily"):
        """
        保存结果
        """
        if not papers:
            print("No papers found")
            return
        
        # 生成文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = generate_filename(f"huggingface_{result_type}_{timestamp}")
        
        # 保存JSON
        json_path = os.path.join(self.data_dir, f"{filename}.json")
        save_json(papers, json_path)
        
        # 保存Markdown
        markdown_content = self._generate_markdown(papers, result_type)
        markdown_path = os.path.join(self.markdown_dir, f"{filename}.md")
        save_markdown(markdown_content, markdown_path)
        
        print(f"已保存 {len(papers)} 篇论文到:")
        print(f"JSON: {json_path}")
        print(f"Markdown: {markdown_path}")
    
    def _generate_markdown(self, papers, result_type):
        """
        生成Markdown格式的报告
        """
        content = f"# Hugging Face {result_type.title()} Papers\n\n"
        content += f"**爬取时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        content += f"**论文数量**: {len(papers)}\n\n"
        
        # 按质量评分排序
        sorted_papers = sorted(papers, key=lambda x: x.get('quality_score', {}).get('total_score', 0), reverse=True)
        
        for i, paper in enumerate(sorted_papers, 1):
            content += f"## {i}. {paper.get('title', 'Unknown Title')}\n\n"
            
            if paper.get('authors'):
                content += f"**作者**: {paper['authors']}\n\n"
            
            if paper.get('tags'):
                content += f"**标签**: {', '.join(paper['tags'])}\n\n"
            
            content += f"**质量评分**: {paper.get('quality_score', {}).get('total_score', 0):.1f}/100\n\n"
            
            if paper.get('likes'):
                content += f"**点赞数**: {paper['likes']}\n\n"
            
            if paper.get('abstract'):
                content += f"**摘要**: {paper['abstract']}\n\n"
            
            if paper.get('url'):
                content += f"**链接**: {paper['url']}\n\n"
            
            content += "---\n\n"
        
        return content

def main():
    """
    主函数
    """
    spider = HuggingFaceDailySpider()
    
    print("Getting Hugging Face daily papers...")
    daily_papers = spider.get_daily_papers(days_back=3)
    spider.save_results(daily_papers, "daily")
    
    print("\nGetting trending papers...")
    trending_papers = spider.get_trending_papers()
    spider.save_results(trending_papers, "trending")

if __name__ == "__main__":
    main()