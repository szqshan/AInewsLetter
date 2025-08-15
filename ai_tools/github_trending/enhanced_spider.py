#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强版GitHub Trending爬虫
结合网页爬虫和GitHub API，提供更丰富的数据
"""

import sys
import os
import time
import json
import requests
import asyncio
import aiohttp
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from bs4 import BeautifulSoup

# 导入配置
from github_config import GITHUB_CONFIG, get_api_headers, get_trending_url, get_repo_api_url

# 添加共享模块路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'shared'))
from utils import save_json, save_markdown, clean_text


class EnhancedGitHubSpider:
    """增强版GitHub爬虫，支持API Token"""
    
    def __init__(self):
        self.config = GITHUB_CONFIG
        self.api_headers = get_api_headers()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': self.config['headers']['User-Agent']
        })
        
        # 请求统计
        self.api_requests_count = 0
        self.web_requests_count = 0
        self.start_time = time.time()
        
        # 数据存储
        self.output_dir = Path("crawled_data")
        self.output_dir.mkdir(exist_ok=True)
        
        print("🚀 GitHub增强爬虫初始化完成")
        print(f"   API Token: {self.config['api_token'][:20]}...")
        print(f"   输出目录: {self.output_dir}")
    
    async def crawl_trending_repos(self, language: str = None, since: str = "daily") -> List[Dict]:
        """爬取Trending仓库（网页 + API混合模式）"""
        print(f"\n🔍 爬取Trending仓库: {language or 'all'} languages, {since}")
        
        # 步骤1: 从Trending页面获取基础列表
        trending_repos = await self._get_trending_from_web(language, since)
        print(f"📊 从Trending页面获取: {len(trending_repos)} 个仓库")
        
        # 步骤2: 使用API获取详细信息
        enhanced_repos = []
        for i, repo in enumerate(trending_repos):
            try:
                print(f"🔄 处理仓库 {i+1}/{len(trending_repos)}: {repo.get('name', 'Unknown')}")
                
                # 获取API详细信息
                api_data = await self._get_repo_details_from_api(repo)
                
                if api_data:
                    # 合并数据
                    enhanced_repo = {**repo, **api_data}
                    
                    # AI相关性检查
                    if self._is_ai_related(enhanced_repo):
                        # 质量评估
                        enhanced_repo['quality_score'] = self._calculate_quality_score(enhanced_repo)
                        enhanced_repos.append(enhanced_repo)
                        print(f"  ✅ AI相关仓库，质量分: {enhanced_repo['quality_score']:.1f}")
                    else:
                        print(f"  ⏩ 非AI相关，跳过")
                else:
                    print(f"  ❌ API获取失败")
                
                # 频率控制
                await asyncio.sleep(self.config['crawl_config']['request_delay'])
                
            except Exception as e:
                print(f"  ❌ 处理失败: {e}")
                continue
        
        print(f"🎉 最终获得 {len(enhanced_repos)} 个AI相关仓库")
        return enhanced_repos
    
    async def _get_trending_from_web(self, language: str = None, since: str = "daily") -> List[Dict]:
        """从Trending页面获取基础仓库列表"""
        trending_url = get_trending_url(language, since)
        
        try:
            response = self.session.get(trending_url, timeout=30)
            response.raise_for_status()
            self.web_requests_count += 1
            
            soup = BeautifulSoup(response.content, 'html.parser')
            repos = []
            
            # 解析Trending页面
            articles = soup.find_all('article', class_='Box-row')
            
            for article in articles:
                repo = self._parse_trending_repo(article)
                if repo:
                    repos.append(repo)
            
            return repos
            
        except Exception as e:
            print(f"❌ 获取Trending页面失败: {e}")
            return []
    
    def _parse_trending_repo(self, article) -> Optional[Dict]:
        """解析Trending页面的仓库信息"""
        try:
            repo = {}
            
            # 仓库名称和链接
            title_elem = article.find('h2', class_='h3')
            if title_elem:
                link_elem = title_elem.find('a')
                if link_elem:
                    href = link_elem.get('href', '')
                    repo['name'] = href.strip('/')
                    repo['url'] = f"https://github.com{href}"
                    
                    # 提取owner和repo名
                    parts = href.strip('/').split('/')
                    if len(parts) >= 2:
                        repo['owner'] = parts[0]
                        repo['repo_name'] = parts[1]
            
            # 描述
            desc_elem = article.find('p', class_='col-9')
            if desc_elem:
                repo['description'] = clean_text(desc_elem.get_text())
            
            # 编程语言
            lang_elem = article.find('span', {'itemprop': 'programmingLanguage'})
            if lang_elem:
                repo['language'] = lang_elem.get_text().strip()
            
            # Stars
            star_elem = article.find('a', href=lambda x: x and '/stargazers' in x)
            if star_elem:
                star_text = star_elem.get_text().strip()
                repo['stars_trending'] = self._parse_number(star_text)
            
            # 今日Stars
            today_elem = article.find('span', string=lambda x: x and 'stars today' in x)
            if today_elem:
                today_text = today_elem.get_text()
                import re
                match = re.search(r'(\d+)', today_text)
                if match:
                    repo['stars_today'] = int(match.group(1))
            
            # 添加元数据
            repo['crawl_source'] = 'trending_page'
            repo['crawl_timestamp'] = datetime.now().isoformat()
            
            return repo if repo.get('name') else None
            
        except Exception as e:
            print(f"❌ 解析仓库失败: {e}")
            return None
    
    async def _get_repo_details_from_api(self, repo: Dict) -> Optional[Dict]:
        """使用GitHub API获取详细仓库信息"""
        if not repo.get('owner') or not repo.get('repo_name'):
            return None
        
        api_url = get_repo_api_url(repo['owner'], repo['repo_name'])
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(api_url, headers=self.api_headers) as response:
                    self.api_requests_count += 1
                    
                    if response.status == 200:
                        data = await response.json()
                        
                        # 提取关键信息
                        api_info = {
                            'full_name': data.get('full_name'),
                            'stars': data.get('stargazers_count', 0),
                            'forks': data.get('forks_count', 0),
                            'watchers': data.get('watchers_count', 0),
                            'open_issues': data.get('open_issues_count', 0),
                            'size': data.get('size', 0),
                            'created_at': data.get('created_at'),
                            'updated_at': data.get('updated_at'),
                            'pushed_at': data.get('pushed_at'),
                            'license': data.get('license', {}).get('name') if data.get('license') else None,
                            'topics': data.get('topics', []),
                            'has_wiki': data.get('has_wiki', False),
                            'has_pages': data.get('has_pages', False),
                            'archived': data.get('archived', False),
                            'disabled': data.get('disabled', False),
                            'default_branch': data.get('default_branch'),
                            'subscribers_count': data.get('subscribers_count', 0),
                            'network_count': data.get('network_count', 0),
                            'api_source': True
                        }
                        
                        return api_info
                        
                    elif response.status == 403:
                        print(f"⚠️ API限制，跳过: {repo['name']}")
                        return None
                    else:
                        print(f"❌ API请求失败 {response.status}: {repo['name']}")
                        return None
                        
        except Exception as e:
            print(f"❌ API请求异常: {e}")
            return None
    
    def _is_ai_related(self, repo: Dict) -> bool:
        """判断仓库是否与AI相关"""
        # 检查文本内容
        text_to_check = " ".join([
            repo.get('name', ''),
            repo.get('description', ''),
            " ".join(repo.get('topics', []))
        ]).lower()
        
        # 关键词匹配
        for keyword in self.config['ai_keywords']:
            if keyword.lower() in text_to_check:
                return True
        
        return False
    
    def _calculate_quality_score(self, repo: Dict) -> float:
        """计算仓库质量分数（0-100）"""
        score = 0
        
        # Stars权重 (40%)
        stars = repo.get('stars', 0)
        if stars >= 10000:
            score += 40
        elif stars >= 1000:
            score += 30
        elif stars >= 100:
            score += 20
        elif stars >= 10:
            score += 10
        
        # 活跃度权重 (25%)
        updated_at = repo.get('updated_at')
        if updated_at:
            try:
                from dateutil import parser
                update_date = parser.parse(updated_at)
                days_ago = (datetime.now(update_date.tzinfo) - update_date).days
                
                if days_ago <= 7:
                    score += 25
                elif days_ago <= 30:
                    score += 20
                elif days_ago <= 90:
                    score += 15
                elif days_ago <= 365:
                    score += 10
            except:
                pass
        
        # 社区参与度权重 (20%)
        forks = repo.get('forks', 0)
        watchers = repo.get('watchers', 0)
        
        community_score = min((forks * 0.5 + watchers * 0.3) / 10, 20)
        score += community_score
        
        # 项目完整性权重 (15%)
        if repo.get('license'):
            score += 5
        if repo.get('has_wiki'):
            score += 3
        if repo.get('topics'):
            score += min(len(repo['topics']) * 1, 7)
        
        return min(score, 100)
    
    def _parse_number(self, text: str) -> int:
        """解析数字（处理k, m等单位）"""
        try:
            text = text.strip().lower().replace(',', '')
            if 'k' in text:
                return int(float(text.replace('k', '')) * 1000)
            elif 'm' in text:
                return int(float(text.replace('m', '')) * 1000000)
            else:
                import re
                numbers = re.findall(r'\d+', text)
                return int(numbers[0]) if numbers else 0
        except:
            return 0
    
    async def save_results(self, repos: List[Dict], language: str = None, since: str = "daily"):
        """保存爬取结果"""
        if not repos:
            print("⚠️ 没有数据可保存")
            return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        lang_suffix = f"_{language}" if language else "_all"
        
        # 保存JSON
        json_file = self.output_dir / f"github_trending_{since}{lang_suffix}_{timestamp}.json"
        
        # 添加统计信息
        metadata = {
            'crawl_info': {
                'timestamp': timestamp,
                'language': language,
                'since': since,
                'total_repos': len(repos),
                'api_requests': self.api_requests_count,
                'web_requests': self.web_requests_count,
                'duration_seconds': time.time() - self.start_time
            },
            'repos': repos
        }
        
        save_json(metadata, str(json_file))
        
        # 保存Markdown报告
        md_file = self.output_dir / f"github_trending_{since}{lang_suffix}_{timestamp}.md"
        markdown_content = self._generate_markdown_report(repos, language, since, metadata['crawl_info'])
        save_markdown(markdown_content, str(md_file))
        
        print(f"\n💾 结果已保存:")
        print(f"   📄 JSON: {json_file}")
        print(f"   📝 Markdown: {md_file}")
    
    def _generate_markdown_report(self, repos: List[Dict], language: str, since: str, crawl_info: Dict) -> str:
        """生成Markdown格式报告"""
        lang_name = language or "All Languages"
        
        content = f"""# GitHub Trending AI Tools - {lang_name} ({since.title()})

## 📊 爬取信息
- **时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **语言**: {lang_name}
- **时间范围**: {since}
- **总仓库数**: {crawl_info['total_repos']}
- **API请求**: {crawl_info['api_requests']} 次
- **网页请求**: {crawl_info['web_requests']} 次
- **耗时**: {crawl_info['duration_seconds']:.1f} 秒

## 🏆 高质量AI工具 (按质量分排序)

"""
        
        # 按质量分排序
        sorted_repos = sorted(repos, key=lambda x: x.get('quality_score', 0), reverse=True)
        
        for i, repo in enumerate(sorted_repos, 1):
            name = repo.get('name', 'Unknown')
            desc = repo.get('description', '无描述')
            stars = repo.get('stars', 0)
            stars_today = repo.get('stars_today', 0)
            forks = repo.get('forks', 0)
            language = repo.get('language', 'Unknown')
            quality = repo.get('quality_score', 0)
            url = repo.get('url', '#')
            topics = repo.get('topics', [])
            license_name = repo.get('license', 'No License')
            
            content += f"""### {i}. [{name}]({url})

**描述**: {desc}

**技术信息**:
- 💫 Stars: {stars:,} (+{stars_today} 今日)
- 🍴 Forks: {forks:,}
- 💻 语言: {language}
- 📜 许可证: {license_name}
- 🎯 质量评分: {quality:.1f}/100

"""
            
            if topics:
                content += f"**标签**: {', '.join(topics[:10])}\n\n"
            
            # 项目特点
            features = []
            if repo.get('has_wiki'):
                features.append("📚 Wiki")
            if repo.get('has_pages'):
                features.append("📖 Pages")
            if repo.get('archived'):
                features.append("📦 已归档")
            
            if features:
                content += f"**特点**: {' | '.join(features)}\n\n"
            
            content += "---\n\n"
        
        # 添加统计摘要
        if repos:
            total_stars = sum(repo.get('stars', 0) for repo in repos)
            avg_stars = total_stars / len(repos)
            top_languages = {}
            
            for repo in repos:
                lang = repo.get('language', 'Unknown')
                top_languages[lang] = top_languages.get(lang, 0) + 1
            
            content += f"""## 📈 统计摘要

- **总Stars数**: {total_stars:,}
- **平均Stars**: {avg_stars:.0f}
- **最热项目**: {sorted_repos[0].get('name', 'Unknown')} ({sorted_repos[0].get('stars', 0):,} stars)

### 🔤 编程语言分布
"""
            
            for lang, count in sorted(top_languages.items(), key=lambda x: x[1], reverse=True):
                content += f"- **{lang}**: {count} 个项目\n"
        
        return content


async def main():
    """主函数"""
    print("🚀 GitHub增强爬虫启动")
    print("=" * 50)
    
    spider = EnhancedGitHubSpider()
    
    # 配置爬取参数
    languages = ["python", "javascript", None]  # None表示所有语言
    time_ranges = ["daily"]
    
    for time_range in time_ranges:
        for language in languages:
            try:
                lang_name = language or "all"
                print(f"\n🎯 开始爬取: {lang_name} - {time_range}")
                
                # 爬取仓库
                repos = await spider.crawl_trending_repos(language, time_range)
                
                # 保存结果
                await spider.save_results(repos, language, time_range)
                
                print(f"✅ 完成: {lang_name} - {len(repos)} 个AI仓库")
                
                # 语言间延迟
                if language != languages[-1]:
                    print("⏳ 等待10秒后继续...")
                    await asyncio.sleep(10)
                    
            except Exception as e:
                print(f"❌ 爬取失败: {e}")
                continue
    
    print(f"\n🎉 所有任务完成!")
    print(f"   📊 总API请求: {spider.api_requests_count}")
    print(f"   🌐 总网页请求: {spider.web_requests_count}")


if __name__ == "__main__":
    asyncio.run(main())
