#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Google Scholar 爬虫
用于爬取Google Scholar上的学术论文信息
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'shared'))

from config import GOOGLE_SCHOLAR_CONFIG, ensure_directories
from utils import safe_request, save_json, save_markdown, generate_filename
from quality_scorer import QualityScorer
import requests
from bs4 import BeautifulSoup
import time
import json
from datetime import datetime

class GoogleScholarSpider:
    def __init__(self):
        self.base_url = "https://scholar.google.com/scholar"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.quality_scorer = QualityScorer()
        
        # 确保目录存在
        self.data_dir = os.path.join(os.path.dirname(__file__), 'data')
        self.markdown_dir = os.path.join(self.data_dir, 'markdown')
        ensure_directories([self.data_dir, self.markdown_dir])
    
    def search_papers(self, query, max_results=10):
        """
        搜索论文
        """
        papers = []
        
        params = {
            'q': query,
            'hl': 'en',
            'as_sdt': '0,5',
            'num': min(max_results, 20)  # Google Scholar限制
        }
        
        try:
            response = safe_request(self.session.get, self.base_url, params=params)
            if not response:
                return papers
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 解析搜索结果
            results = soup.find_all('div', class_='gs_r gs_or gs_scl')
            
            for result in results[:max_results]:
                paper = self._parse_paper(result)
                if paper:
                    # 质量评估
                    paper['quality_score'] = self.quality_scorer.score_paper(paper)
                    papers.append(paper)
                
                # 避免被封IP
                time.sleep(2)
        
        except Exception as e:
            print(f"搜索论文时出错: {e}")
        
        return papers
    
    def _parse_paper(self, result_div):
        """
        解析单个论文信息
        """
        try:
            paper = {}
            
            # 标题和链接
            title_elem = result_div.find('h3', class_='gs_rt')
            if title_elem:
                link_elem = title_elem.find('a')
                if link_elem:
                    paper['title'] = link_elem.get_text().strip()
                    paper['url'] = link_elem.get('href', '')
                else:
                    paper['title'] = title_elem.get_text().strip()
                    paper['url'] = ''
            
            # 作者和发表信息
            author_elem = result_div.find('div', class_='gs_a')
            if author_elem:
                author_text = author_elem.get_text()
                paper['authors'] = author_text.split(' - ')[0] if ' - ' in author_text else author_text
                paper['publication_info'] = author_text
            
            # 摘要
            abstract_elem = result_div.find('div', class_='gs_rs')
            if abstract_elem:
                paper['abstract'] = abstract_elem.get_text().strip()
            
            # 引用数
            cite_elem = result_div.find('div', class_='gs_fl')
            if cite_elem:
                cite_links = cite_elem.find_all('a')
                for link in cite_links:
                    if 'Cited by' in link.get_text():
                        cite_text = link.get_text()
                        try:
                            paper['citations'] = int(cite_text.split('Cited by ')[1])
                        except:
                            paper['citations'] = 0
                        break
                else:
                    paper['citations'] = 0
            
            # 添加时间戳
            paper['scraped_at'] = datetime.now().isoformat()
            paper['source'] = 'Google Scholar'
            
            return paper
        
        except Exception as e:
            print(f"解析论文信息时出错: {e}")
            return None
    
    def save_results(self, papers, query):
        """
        保存结果
        """
        if not papers:
            print("No papers found")
            return
        
        # 生成文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = generate_filename(f"google_scholar_{query}_{timestamp}")
        
        # 保存JSON
        json_path = os.path.join(self.data_dir, f"{filename}.json")
        save_json(papers, json_path)
        
        # 保存Markdown
        markdown_content = self._generate_markdown(papers, query)
        markdown_path = os.path.join(self.markdown_dir, f"{filename}.md")
        save_markdown(markdown_content, markdown_path)
        
        print(f"已保存 {len(papers)} 篇论文到:")
        print(f"JSON: {json_path}")
        print(f"Markdown: {markdown_path}")
    
    def _generate_markdown(self, papers, query):
        """
        生成Markdown格式的报告
        """
        content = f"# Google Scholar 搜索结果\n\n"
        content += f"**搜索关键词**: {query}\n"
        content += f"**搜索时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        content += f"**论文数量**: {len(papers)}\n\n"
        
        for i, paper in enumerate(papers, 1):
            content += f"## {i}. {paper.get('title', 'Unknown Title')}\n\n"
            content += f"**作者**: {paper.get('authors', 'Unknown')}\n\n"
            content += f"**发表信息**: {paper.get('publication_info', 'Unknown')}\n\n"
            content += f"**引用数**: {paper.get('citations', 0)}\n\n"
            content += f"**质量评分**: {paper.get('quality_score', {}).get('total_score', 0):.1f}/100\n\n"
            
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
    spider = GoogleScholarSpider()
    
    # 搜索AI相关论文
    queries = [
        "artificial intelligence 2024",
        "machine learning transformer",
        "large language model"
    ]
    
    for query in queries:
        print(f"\nSearching: {query}")
        papers = spider.search_papers(query, max_results=5)
        spider.save_results(papers, query)
        
        # 避免请求过于频繁
        time.sleep(5)

if __name__ == "__main__":
    main()