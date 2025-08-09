#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitHub Trending AI Tools 爬虫
用于爬取GitHub Trending中的AI相关工具和项目
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'shared'))

from config import GITHUB_CONFIG, ensure_directories
from utils import safe_request, save_json, save_markdown, generate_filename
from quality_scorer import QualityScorer
import requests
from bs4 import BeautifulSoup
import time
import json
from datetime import datetime
import re

class GitHubTrendingSpider:
    def __init__(self):
        self.base_url = "https://github.com/trending"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.quality_scorer = QualityScorer()
        
        # AI相关关键词
        self.ai_keywords = [
            'artificial intelligence', 'machine learning', 'deep learning', 'neural network',
            'transformer', 'llm', 'large language model', 'gpt', 'bert', 'chatbot',
            'computer vision', 'nlp', 'natural language processing', 'pytorch', 'tensorflow',
            'huggingface', 'openai', 'stable diffusion', 'diffusion model', 'generative ai'
        ]
        
        # 确保目录存在
        self.data_dir = os.path.join(os.path.dirname(__file__), 'data')
        self.markdown_dir = os.path.join(self.data_dir, 'markdown')
        ensure_directories([self.data_dir, self.markdown_dir])
    
    def get_trending_repos(self, language=None, since="daily"):
        """
        获取GitHub Trending仓库
        
        Args:
            language: 编程语言过滤 (python, javascript, etc.)
            since: 时间范围 (daily, weekly, monthly)
        """
        repos = []
        
        try:
            # 构建URL
            params = {'since': since}
            if language:
                params['l'] = language
            
            response = safe_request(self.session.get, self.base_url, params=params)
            if not response:
                return repos
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 查找仓库列表
            repo_articles = soup.find_all('article', class_='Box-row')
            
            for article in repo_articles:
                repo = self._parse_repo(article)
                if repo and self._is_ai_related(repo):
                    # 获取详细信息
                    detailed_repo = self._get_repo_details(repo)
                    if detailed_repo:
                        # 质量评估
                        detailed_repo['quality_score'] = self.quality_scorer.score_tool(detailed_repo)
                        repos.append(detailed_repo)
                
                # 避免请求过于频繁
                time.sleep(2)
        
        except Exception as e:
            print(f"获取trending仓库时出错: {e}")
        
        return repos
    
    def _parse_repo(self, article):
        """
        解析仓库基本信息
        """
        try:
            repo = {}
            
            # 仓库名称和链接
            title_elem = article.find('h2', class_='h3')
            if title_elem:
                link_elem = title_elem.find('a')
                if link_elem:
                    repo['name'] = link_elem.get_text().strip().replace('\n', '').replace(' ', '')
                    repo['url'] = 'https://github.com' + link_elem.get('href', '')
            
            # 描述
            desc_elem = article.find('p', class_='col-9')
            if desc_elem:
                repo['description'] = desc_elem.get_text().strip()
            
            # 编程语言
            lang_elem = article.find('span', {'itemprop': 'programmingLanguage'})
            if lang_elem:
                repo['language'] = lang_elem.get_text().strip()
            
            # Stars和Forks
            star_elem = article.find('a', href=re.compile(r'/stargazers$'))
            if star_elem:
                star_text = star_elem.get_text().strip()
                repo['stars'] = self._parse_number(star_text)
            
            fork_elem = article.find('a', href=re.compile(r'/forks$'))
            if fork_elem:
                fork_text = fork_elem.get_text().strip()
                repo['forks'] = self._parse_number(fork_text)
            
            # 今日Stars
            today_stars_elem = article.find('span', class_='d-inline-block')
            if today_stars_elem and 'stars today' in today_stars_elem.get_text():
                today_text = today_stars_elem.get_text()
                repo['stars_today'] = self._parse_number(today_text.split()[0])
            
            # 添加元数据
            repo['scraped_at'] = datetime.now().isoformat()
            repo['source'] = 'GitHub Trending'
            repo['type'] = 'ai_tool'
            
            return repo
        
        except Exception as e:
            print(f"解析仓库信息时出错: {e}")
            return None
    
    def _is_ai_related(self, repo):
        """
        判断仓库是否与AI相关
        """
        text_to_check = f"{repo.get('name', '')} {repo.get('description', '')}".lower()
        
        for keyword in self.ai_keywords:
            if keyword.lower() in text_to_check:
                return True
        
        return False
    
    def _get_repo_details(self, repo):
        """
        获取仓库详细信息
        """
        try:
            if not repo.get('url'):
                return repo
            
            response = safe_request(self.session.get, repo['url'])
            if not response:
                return repo
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # README内容
            readme_elem = soup.find('article', class_='markdown-body')
            if readme_elem:
                repo['readme_preview'] = readme_elem.get_text()[:500] + '...' if len(readme_elem.get_text()) > 500 else readme_elem.get_text()
            
            # 最近更新时间
            update_elem = soup.find('relative-time')
            if update_elem:
                repo['last_updated'] = update_elem.get('datetime', '')
            
            # Issues和Pull Requests数量
            nav_elem = soup.find('nav', {'data-pjax': '#js-repo-pjax-container'})
            if nav_elem:
                # Issues
                issues_elem = nav_elem.find('a', href=re.compile(r'/issues$'))
                if issues_elem:
                    issues_text = issues_elem.get_text()
                    repo['open_issues'] = self._parse_number(re.search(r'\d+', issues_text).group() if re.search(r'\d+', issues_text) else '0')
                
                # Pull Requests
                pr_elem = nav_elem.find('a', href=re.compile(r'/pulls$'))
                if pr_elem:
                    pr_text = pr_elem.get_text()
                    repo['open_prs'] = self._parse_number(re.search(r'\d+', pr_text).group() if re.search(r'\d+', pr_text) else '0')
            
            # 贡献者数量
            contributors_elem = soup.find('a', href=re.compile(r'/graphs/contributors$'))
            if contributors_elem:
                contrib_text = contributors_elem.get_text()
                repo['contributors'] = self._parse_number(re.search(r'\d+', contrib_text).group() if re.search(r'\d+', contrib_text) else '1')
            
            # 许可证
            license_elem = soup.find('a', href=re.compile(r'/blob/.*/LICENSE'))
            if license_elem:
                repo['license'] = license_elem.get_text().strip()
            
            return repo
        
        except Exception as e:
            print(f"获取仓库详细信息时出错: {e}")
            return repo
    
    def _parse_number(self, text):
        """
        解析数字（处理k, m等单位）
        """
        try:
            text = text.strip().lower()
            if 'k' in text:
                return int(float(text.replace('k', '')) * 1000)
            elif 'm' in text:
                return int(float(text.replace('m', '')) * 1000000)
            else:
                return int(re.sub(r'[^\d]', '', text))
        except:
            return 0
    
    def save_results(self, repos, language=None, since="daily"):
        """
        保存结果
        """
        if not repos:
            print("No AI-related repositories found")
            return
        
        # 生成文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        lang_suffix = f"_{language}" if language else ""
        filename = generate_filename(f"github_trending_{since}{lang_suffix}_{timestamp}")
        
        # 保存JSON
        json_path = os.path.join(self.data_dir, f"{filename}.json")
        save_json(repos, json_path)
        
        # 保存Markdown
        markdown_content = self._generate_markdown(repos, language, since)
        markdown_path = os.path.join(self.markdown_dir, f"{filename}.md")
        save_markdown(markdown_content, markdown_path)
        
        print(f"已保存 {len(repos)} 个AI工具到:")
        print(f"JSON: {json_path}")
        print(f"Markdown: {markdown_path}")
    
    def _generate_markdown(self, repos, language, since):
        """
        生成Markdown格式的报告
        """
        content = f"# GitHub Trending AI Tools ({since.title()})\n\n"
        if language:
            content += f"**编程语言**: {language}\n"
        content += f"**爬取时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        content += f"**工具数量**: {len(repos)}\n\n"
        
        # 按质量评分排序
        sorted_repos = sorted(repos, key=lambda x: x.get('quality_score', {}).get('total_score', 0), reverse=True)
        
        for i, repo in enumerate(sorted_repos, 1):
            content += f"## {i}. {repo.get('name', 'Unknown')}\n\n"
            
            if repo.get('description'):
                content += f"**描述**: {repo['description']}\n\n"
            
            content += f"**语言**: {repo.get('language', 'Unknown')}\n\n"
            content += f"**Stars**: {repo.get('stars', 0):,} (今日 +{repo.get('stars_today', 0)})\n\n"
            content += f"**Forks**: {repo.get('forks', 0):,}\n\n"
            content += f"**质量评分**: {repo.get('quality_score', {}).get('total_score', 0):.1f}/100\n\n"
            
            if repo.get('contributors'):
                content += f"**贡献者**: {repo['contributors']}\n\n"
            
            if repo.get('license'):
                content += f"**许可证**: {repo['license']}\n\n"
            
            if repo.get('readme_preview'):
                content += f"**README预览**: {repo['readme_preview']}\n\n"
            
            if repo.get('url'):
                content += f"**链接**: {repo['url']}\n\n"
            
            content += "---\n\n"
        
        return content

def main():
    """
    主函数
    """
    spider = GitHubTrendingSpider()
    
    # 获取不同语言的trending AI工具
    languages = ['python', 'javascript', 'typescript', None]  # None表示所有语言
    time_ranges = ['daily', 'weekly']
    
    for time_range in time_ranges:
        for language in languages:
            lang_name = language or "all"
            print(f"\nGetting {time_range} trending AI tools ({lang_name})...")
            
            repos = spider.get_trending_repos(language=language, since=time_range)
            spider.save_results(repos, language=language, since=time_range)
            
            # 避免请求过于频繁
            time.sleep(10)

if __name__ == "__main__":
    main()