#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
结构化GitHub Trending爬虫
按时间维度分类爬取，参考arXiv架构实现结构化存储
"""

import sys
import os
import time
import json
import hashlib
import asyncio
import aiohttp
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set
from bs4 import BeautifulSoup

# 导入配置
from github_config import GITHUB_CONFIG, get_api_headers, get_trending_url, get_repo_api_url

# 添加共享模块路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'shared'))
from utils import save_json, save_markdown, clean_text


class StructuredGitHubSpider:
    """结构化GitHub爬虫，支持时间维度分类和arXiv式存储"""
    
    def __init__(self, base_output_dir: str = "crawled_data"):
        self.config = GITHUB_CONFIG
        self.api_headers = get_api_headers()
        self.base_output_dir = Path(base_output_dir)
        
        # 创建基础目录结构
        self._setup_directory_structure()
        
        # 去重集合 - 跨时间维度去重
        self.processed_repos: Set[str] = set()
        self.load_processed_repos()
        
        # 请求统计
        self.api_requests_count = 0
        self.web_requests_count = 0
        self.start_time = time.time()
        
        print("🚀 结构化GitHub爬虫初始化完成")
        print(f"   📁 输出目录: {self.base_output_dir}")
        print(f"   🔄 已处理项目: {len(self.processed_repos)} 个")
    
    def _setup_directory_structure(self):
        """创建目录结构，参考arXiv架构"""
        directories = [
            # 主数据目录
            self.base_output_dir,
            
            # 按时间维度分类的工具目录
            self.base_output_dir / "tools" / "daily",
            self.base_output_dir / "tools" / "weekly", 
            self.base_output_dir / "tools" / "monthly",
            
            # 聚合数据目录
            self.base_output_dir / "data" / "daily",
            self.base_output_dir / "data" / "weekly",
            self.base_output_dir / "data" / "monthly",
            
            # 排行榜目录
            self.base_output_dir / "rankings" / "daily",
            self.base_output_dir / "rankings" / "weekly", 
            self.base_output_dir / "rankings" / "monthly",
            
            # 去重记录目录
            self.base_output_dir / "metadata"
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
        
        print("📁 目录结构创建完成")
    
    def load_processed_repos(self):
        """加载已处理的仓库记录"""
        processed_file = self.base_output_dir / "metadata" / "processed_repos.json"
        
        if processed_file.exists():
            try:
                with open(processed_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.processed_repos = set(data.get('processed_repos', []))
                print(f"📋 加载已处理仓库: {len(self.processed_repos)} 个")
            except Exception as e:
                print(f"⚠️ 加载已处理仓库失败: {e}")
                self.processed_repos = set()
        else:
            self.processed_repos = set()
    
    def save_processed_repos(self):
        """保存已处理的仓库记录"""
        processed_file = self.base_output_dir / "metadata" / "processed_repos.json"
        
        data = {
            'processed_repos': list(self.processed_repos),
            'last_updated': datetime.now().isoformat(),
            'total_count': len(self.processed_repos)
        }
        
        try:
            with open(processed_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠️ 保存已处理仓库失败: {e}")
    
    async def crawl_all_time_ranges(self, languages: List[str] = None) -> Dict[str, List[Dict]]:
        """爬取所有时间维度的Trending数据"""
        # 只爬取所有语言（不按语言分类）
        languages = [None]  # None表示所有语言
        
        time_ranges = ["daily", "weekly", "monthly"]
        all_results = {}
        
        for time_range in time_ranges:
            print(f"\n🎯 开始爬取 {time_range} trending (所有语言)...")
            time_results = []
            
            try:
                # 爬取所有语言的trending仓库
                repos = await self.crawl_trending_repos(None, time_range)
                
                # 过滤和处理
                processed_repos = await self.process_and_filter_repos(repos, time_range)
                
                time_results.extend(processed_repos)
                
                print(f"  ✅ 获得AI工具: {len(processed_repos)} 个")
                
            except Exception as e:
                print(f"  ❌ {time_range} 爬取失败: {e}")
                import traceback
                print(f"  📋 错误详情: {traceback.format_exc()}")
                continue
            
            # 保存该时间维度的结果
            all_results[time_range] = time_results
            await self.save_time_range_results(time_results, time_range)
            
            print(f"🎉 {time_range} 爬取完成: {len(time_results)} 个AI工具")
            
            # 时间维度间延迟
            if time_range != time_ranges[-1]:
                print("⏳ 等待5秒后继续下一个时间维度...")
                await asyncio.sleep(5)
        
        # 生成跨时间维度的汇总报告
        await self.generate_comprehensive_report(all_results)
        
        # 保存去重记录
        self.save_processed_repos()
        
        return all_results
    
    async def crawl_trending_repos(self, language: str = None, since: str = "daily") -> List[Dict]:
        """爬取单个时间维度的trending仓库"""
        # 获取trending页面数据
        trending_repos = await self._get_trending_from_web(language, since)
        
        # 使用API获取详细信息
        detailed_repos = []
        for repo in trending_repos:
            try:
                # 获取API详细信息
                api_data = await self._get_repo_details_from_api(repo)
                
                if api_data:
                    # 合并数据
                    enhanced_repo = {**repo, **api_data}
                    enhanced_repo['time_range'] = since
                    enhanced_repo['language_filter'] = language
                    detailed_repos.append(enhanced_repo)
                
                # 频率控制
                await asyncio.sleep(self.config['crawl_config']['request_delay'])
                
            except Exception as e:
                print(f"  ❌ 处理仓库失败: {e}")
                continue
        
        return detailed_repos
    
    async def process_and_filter_repos(self, repos: List[Dict], time_range: str) -> List[Dict]:
        """处理和过滤仓库数据"""
        processed_repos = []
        
        for i, repo in enumerate(repos):
            try:
                # 显示处理进度
                if i % 10 == 0:
                    print(f"    🔄 处理进度: {i}/{len(repos)}")
                
                # 基础数据验证
                if not repo or not isinstance(repo, dict):
                    print(f"    ⚠️ 无效仓库数据: {type(repo)}")
                    continue
                
                repo_name = repo.get('name', 'Unknown')
                if not repo_name or repo_name == 'Unknown':
                    print(f"    ⚠️ 缺少仓库名称: {repo}")
                    continue
                
                # 生成唯一标识
                repo_id = self._generate_repo_id(repo)
                if not repo_id:
                    print(f"    ⚠️ 无法生成仓库ID: {repo_name}")
                    continue
                
                # 检查是否已处理（去重）
                if repo_id in self.processed_repos:
                    print(f"    ⏩ 跳过重复项目: {repo_name}")
                    continue
                
                # AI相关性检查
                if not self._is_ai_related(repo):
                    continue
                
                # 质量评估
                try:
                    repo['quality_score'] = self._calculate_quality_score(repo)
                except Exception as e:
                    print(f"    ⚠️ 质量评分失败: {repo_name} - {e}")
                    repo['quality_score'] = 0
                
                # 添加处理信息
                repo['repo_id'] = repo_id
                repo['crawl_timestamp'] = datetime.now().isoformat()
                repo['time_range'] = time_range
                
                # 为该工具创建单独的存储目录
                try:
                    await self._create_individual_tool_directory(repo, time_range)
                except Exception as e:
                    print(f"    ⚠️ 创建目录失败: {repo_name} - {e}")
                    continue
                
                processed_repos.append(repo)
                
                # 标记为已处理
                self.processed_repos.add(repo_id)
                
                print(f"    ✅ 新AI工具: {repo_name} (质量分: {repo['quality_score']:.1f})")
                
            except Exception as e:
                print(f"    ❌ 处理仓库异常: {repo.get('name', 'Unknown')} - {e}")
                import traceback
                print(f"    📋 异常详情: {traceback.format_exc()}")
                continue
        
        print(f"  📊 处理完成: {len(processed_repos)}/{len(repos)} 个有效AI工具")
        return processed_repos
    
    def _generate_repo_id(self, repo: Dict) -> str:
        """生成仓库的唯一标识符"""
        try:
            # 使用仓库全名作为唯一标识
            full_name = repo.get('full_name') or repo.get('name', '')
            
            if not full_name:
                # 如果没有全名，使用URL生成
                url = repo.get('url', '')
                if url:
                    # 从URL提取仓库信息
                    url_clean = url.replace('https://github.com/', '').replace('http://github.com/', '')
                    parts = url_clean.split('/')
                    if len(parts) >= 2:
                        full_name = f"{parts[0]}/{parts[1]}"
            
            if not full_name:
                # 最后尝试从name字段提取
                name = repo.get('name', '')
                if '/' in name:
                    full_name = name
                else:
                    # 使用owner和repo_name组合
                    owner = repo.get('owner', '')
                    repo_name = repo.get('repo_name', '')
                    if owner and repo_name:
                        full_name = f"{owner}/{repo_name}"
            
            if not full_name:
                return ""
            
            # 标准化处理
            repo_id = full_name.lower().replace('/', '_').replace('-', '_').replace(' ', '_')
            
            # 移除特殊字符
            import re
            repo_id = re.sub(r'[^\w_]', '', repo_id)
            
            return repo_id
            
        except Exception as e:
            print(f"    ⚠️ 生成仓库ID异常: {e}")
            return ""
    
    async def _create_individual_tool_directory(self, repo: Dict, time_range: str):
        """为每个工具创建单独的存储目录，参考arXiv架构"""
        try:
            repo_id = repo.get('repo_id', 'unknown')
            repo_name = repo.get('name', 'unknown')
            
            # 安全处理仓库名称
            safe_repo_name = repo_name.replace('/', '_').replace('\\', '_').replace(':', '_')
            safe_repo_name = ''.join(c for c in safe_repo_name if c.isalnum() or c in '_-')[:50]  # 限制长度
            
            # 创建目录名：repo_id_简化名称
            dir_name = f"{repo_id}_{safe_repo_name}"
            tool_dir = self.base_output_dir / "tools" / time_range / dir_name
            
            # 确保目录创建成功
            try:
                tool_dir.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                print(f"      ❌ 创建目录失败: {dir_name} - {e}")
                return
            
            # 生成content.md文件
            try:
                content_md = self._generate_tool_content_md(repo)
                content_file = tool_dir / "content.md"
                
                with open(content_file, 'w', encoding='utf-8') as f:
                    f.write(content_md)
            except Exception as e:
                print(f"      ⚠️ 生成content.md失败: {dir_name} - {e}")
            
            # 生成metadata.json文件
            try:
                metadata = self._extract_metadata(repo)
                metadata_file = tool_dir / "metadata.json"
                
                with open(metadata_file, 'w', encoding='utf-8') as f:
                    json.dump(metadata, f, ensure_ascii=False, indent=2)
            except Exception as e:
                print(f"      ⚠️ 生成metadata.json失败: {dir_name} - {e}")
            
            print(f"      📁 创建工具目录: {dir_name}")
            
        except Exception as e:
            print(f"      ❌ 创建工具目录异常: {e}")
            import traceback
            print(f"      📋 异常详情: {traceback.format_exc()}")
    
    def _generate_tool_content_md(self, repo: Dict) -> str:
        """生成工具的Markdown内容，参考arXiv格式"""
        name = repo.get('name', 'Unknown Tool')
        description = repo.get('description', '暂无描述')
        url = repo.get('url', '#')
        stars = repo.get('stars', 0)
        forks = repo.get('forks', 0)
        language = repo.get('language', 'Unknown')
        license_name = repo.get('license', 'Unknown')
        topics = repo.get('topics', [])
        created_at = repo.get('created_at', '')
        updated_at = repo.get('updated_at', '')
        quality_score = repo.get('quality_score', 0)
        time_range = repo.get('time_range', 'daily')
        readme_content = repo.get('readme_content', '')
        
        # 处理README内容
        readme_section = '暂无README文件'
        if readme_content:
            # 清理和格式化README内容
            readme_lines = readme_content.strip().split('\n')
            formatted_readme = []
            
            for line in readme_lines:
                # 移除过多的空行
                if line.strip() or (formatted_readme and formatted_readme[-1].strip()):
                    formatted_readme.append(line)
            
            if formatted_readme:
                readme_section = '\n'.join(formatted_readme)
            else:
                readme_section = '无有效README内容'
        
        # 格式化时间
        created_date = ''
        updated_date = ''
        try:
            if created_at:
                from dateutil import parser
                dt = parser.parse(created_at)
                created_date = dt.strftime('%Y-%m-%d')
        except Exception as e:
            print(f"    ⚠️ 创建时间解析失败: {e}")
            created_date = '未知'
        
        try:
            if updated_at:
                from dateutil import parser
                dt = parser.parse(updated_at)
                updated_date = dt.strftime('%Y-%m-%d')
        except Exception as e:
            print(f"    ⚠️ 更新时间解析失败: {e}")
            updated_date = '未知'
        
        content = f"""# {name}

## 基本信息
- **项目名称**: {name}
- **GitHub ID**: {repo.get('repo_id', 'unknown')}
- **创建日期**: {created_date}
- **最后更新**: {updated_date}
- **主要语言**: {language}
- **开源许可**: {license_name}
- **趋势范围**: {time_range}

## 链接
- **GitHub链接**: {url}
- **Stars数量**: {stars:,}
- **Forks数量**: {forks:,}

## 项目描述
{description}

## 📝 README 详情
{readme_section}

## 技术标签
{', '.join(topics) if topics else '暂无标签'}

## 项目统计
- **⭐ Stars**: {stars:,}
- **🍴 Forks**: {forks:,}
- **👁️ Watchers**: {repo.get('watchers', 0):,}
- **📂 Issues**: {repo.get('open_issues', 0)}
- **📦 大小**: {repo.get('size', 0)} KB

## 项目特点
"""
        
        # 添加项目特点
        features = []
        if repo.get('has_wiki'):
            features.append("📚 包含Wiki文档")
        if repo.get('has_pages'):
            features.append("📖 包含GitHub Pages")
        if repo.get('archived'):
            features.append("📦 项目已归档")
        if repo.get('topics'):
            features.append(f"🏷️ 包含 {len(repo['topics'])} 个技术标签")
        
        if features:
            content += '\n'.join(f"- {feature}" for feature in features)
        else:
            content += "- 暂无特殊特点"
        
        content += f"""

## 质量评估
- **质量评分**: {quality_score:.1f}/100
- **活跃度**: {'高' if self._is_active_repo(repo) else '中等'}
- **社区热度**: {'高' if stars > 1000 else '中等' if stars > 100 else '一般'}

## 处理信息
- **爬取时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **数据来源**: GitHub Trending
- **文件哈希**: {hashlib.md5(name.encode()).hexdigest()[:8]}
"""
        
        return content
    
    def _is_active_repo(self, repo: Dict) -> bool:
        """判断仓库是否活跃（最近30天有更新）"""
        updated_at = repo.get('updated_at')
        if not updated_at:
            return False
        
        try:
            from dateutil import parser
            from datetime import timezone
            
            update_date = parser.parse(updated_at)
            
            # 统一时区处理
            if update_date.tzinfo is None:
                update_date = update_date.replace(tzinfo=timezone.utc)
            
            current_time = datetime.now(update_date.tzinfo)
            days_ago = (current_time - update_date).days
            
            return days_ago < 30
        except Exception:
            return False
    
    def _extract_metadata(self, repo: Dict) -> Dict:
        """提取仓库元数据"""
        return {
            "id": repo.get('repo_id'),
            "name": repo.get('name'),
            "full_name": repo.get('full_name'),
            "description": repo.get('description'),
            "url": repo.get('url'),
            "language": repo.get('language'),
            "stars": repo.get('stars', 0),
            "forks": repo.get('forks', 0),
            "watchers": repo.get('watchers', 0),
            "open_issues": repo.get('open_issues', 0),
            "topics": repo.get('topics', []),
            "license": repo.get('license'),
            "created_at": repo.get('created_at'),
            "updated_at": repo.get('updated_at'),
            "quality_score": repo.get('quality_score', 0),
            "time_range": repo.get('time_range'),
            "crawl_timestamp": repo.get('crawl_timestamp'),
            "ai_related": True,
            "source": "github_trending"
        }
    
    async def save_time_range_results(self, repos: List[Dict], time_range: str):
        """保存特定时间范围的结果"""
        if not repos:
            return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 保存聚合数据JSON
        data_file = self.base_output_dir / "data" / time_range / f"github_trending_{time_range}_{timestamp}.json"
        
        aggregated_data = {
            'crawl_info': {
                'timestamp': timestamp,
                'time_range': time_range,
                'total_tools': len(repos),
                'api_requests': self.api_requests_count,
                'web_requests': self.web_requests_count
            },
            'tools': repos
        }
        
        save_json(aggregated_data, str(data_file))
        
        # 生成排行榜
        await self._generate_ranking(repos, time_range, timestamp)
        
        print(f"    💾 保存 {time_range} 数据: {len(repos)} 个工具")
    
    async def _generate_ranking(self, repos: List[Dict], time_range: str, timestamp: str):
        """生成热度排行榜"""
        if not repos:
            return
        
        # 按质量分排序
        sorted_repos = sorted(repos, key=lambda x: x.get('quality_score', 0), reverse=True)
        
        ranking_md = f"""# GitHub Trending AI工具排行榜 - {time_range.title()}

## 📊 排行榜信息
- **时间范围**: {time_range}
- **生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **工具总数**: {len(repos)}

## 🏆 Top 20 AI工具排行榜

"""
        
        for i, repo in enumerate(sorted_repos[:20], 1):
            name = repo.get('name', 'Unknown')
            desc = repo.get('description', '无描述')[:100]
            stars = repo.get('stars', 0)
            quality = repo.get('quality_score', 0)
            url = repo.get('url', '#')
            language = repo.get('language', 'Unknown')
            
            # 添加奖牌表情
            medal = ""
            if i == 1:
                medal = "🥇 "
            elif i == 2:
                medal = "🥈 "
            elif i == 3:
                medal = "🥉 "
            else:
                medal = f"{i}. "
            
            ranking_md += f"""### {medal}[{name}]({url})

**描述**: {desc}{'...' if len(repo.get('description', '')) > 100 else ''}

**技术信息**:
- 💫 Stars: {stars:,}
- 💻 语言: {language}
- 🎯 质量评分: {quality:.1f}/100

---

"""
        
        # 保存排行榜
        ranking_file = self.base_output_dir / "rankings" / time_range / f"ranking_{time_range}_{timestamp}.md"
        save_markdown(ranking_md, str(ranking_file))
        
        print(f"    🏆 生成 {time_range} 排行榜")
    
    async def generate_comprehensive_report(self, all_results: Dict[str, List[Dict]]):
        """生成综合报告"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 统计信息
        total_tools = sum(len(repos) for repos in all_results.values())
        daily_count = len(all_results.get('daily', []))
        weekly_count = len(all_results.get('weekly', []))
        monthly_count = len(all_results.get('monthly', []))
        
        report_md = f"""# GitHub Trending AI工具综合报告

## 📊 总体统计
- **报告生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **AI工具总数**: {total_tools}
- **去重后唯一工具**: {len(self.processed_repos)}
- **API请求总数**: {self.api_requests_count}
- **网页请求总数**: {self.web_requests_count}

## 📈 时间维度分布
- **📅 Daily Trending**: {daily_count} 个工具
- **📅 Weekly Trending**: {weekly_count} 个工具  
- **📅 Monthly Trending**: {monthly_count} 个工具

## 🏆 各时间维度Top 5

"""
        
        for time_range, repos in all_results.items():
            if not repos:
                continue
            
            sorted_repos = sorted(repos, key=lambda x: x.get('quality_score', 0), reverse=True)
            
            report_md += f"""### {time_range.title()} Top 5

"""
            
            for i, repo in enumerate(sorted_repos[:5], 1):
                name = repo.get('name', 'Unknown')
                stars = repo.get('stars', 0)
                quality = repo.get('quality_score', 0)
                url = repo.get('url', '#')
                
                report_md += f"{i}. [{name}]({url}) - {stars:,} ⭐ (质量分: {quality:.1f})\n"
            
            report_md += "\n"
        
        # 语言分布统计
        language_stats = {}
        for repos in all_results.values():
            for repo in repos:
                lang = repo.get('language', 'Unknown')
                language_stats[lang] = language_stats.get(lang, 0) + 1
        
        report_md += """## 💻 编程语言分布

"""
        
        sorted_languages = sorted(language_stats.items(), key=lambda x: x[1], reverse=True)
        for lang, count in sorted_languages[:10]:
            report_md += f"- **{lang}**: {count} 个工具\n"
        
        # 保存综合报告
        report_file = self.base_output_dir / f"comprehensive_report_{timestamp}.md"
        save_markdown(report_md, str(report_file))
        
        print(f"📋 生成综合报告: {report_file.name}")
    
    async def _get_trending_from_web(self, language: str = None, since: str = "daily") -> List[Dict]:
        """从Trending页面获取基础仓库列表"""
        trending_url = get_trending_url(language, since)
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(trending_url, timeout=30) as response:
                    if response.status == 200:
                        html = await response.text()
                        self.web_requests_count += 1
                        
                        soup = BeautifulSoup(html, 'html.parser')
                        repos = []
                        
                        # 解析Trending页面
                        articles = soup.find_all('article', class_='Box-row')
                        
                        for article in articles:
                            repo = self._parse_trending_repo(article)
                            if repo:
                                repos.append(repo)
                        
                        return repos
                    else:
                        print(f"❌ 获取Trending页面失败: {response.status}")
                        return []
                        
        except Exception as e:
            print(f"❌ 获取Trending页面异常: {e}")
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
            
            return repo if repo.get('name') else None
            
        except Exception as e:
            return None
    
    async def _get_repo_details_from_api(self, repo: Dict) -> Optional[Dict]:
        """使用GitHub API获取详细仓库信息"""
        try:
            # 验证必要字段
            owner = repo.get('owner')
            repo_name = repo.get('repo_name')
            
            if not owner or not repo_name:
                # 尝试从其他字段提取
                full_name = repo.get('full_name') or repo.get('name', '')
                if '/' in full_name:
                    parts = full_name.split('/')
                    owner = parts[0]
                    repo_name = parts[1] if len(parts) > 1 else parts[0]
                else:
                    print(f"    ⚠️ 缺少owner或repo_name: {repo.get('name', 'Unknown')}")
                    return None
            
            api_url = get_repo_api_url(owner, repo_name)
            
            async with aiohttp.ClientSession() as session:
                async with session.get(api_url, headers=self.api_headers) as response:
                    self.api_requests_count += 1
                    
                    if response.status == 200:
                        data = await response.json()
                        
                        # 提取关键信息
                        result = {
                            'full_name': data.get('full_name'),
                            'stars': data.get('stargazers_count', 0),
                            'forks': data.get('forks_count', 0),
                            'watchers': data.get('watchers_count', 0),
                            'open_issues': data.get('open_issues_count', 0),
                            'size': data.get('size', 0),
                            'created_at': data.get('created_at'),
                            'updated_at': data.get('updated_at'),
                            'license': data.get('license', {}).get('name') if data.get('license') else None,
                            'topics': data.get('topics', []),
                            'has_wiki': data.get('has_wiki', False),
                            'has_pages': data.get('has_pages', False),
                            'archived': data.get('archived', False),
                        }
                        
                        # 获取README内容
                        readme_content = await self._get_readme_content(session, owner, repo_name)
                        if readme_content:
                            result['readme_content'] = readme_content
                        
                        return result
                        
                    elif response.status == 403:
                        print(f"    ⚠️ API限制 (403): {owner}/{repo_name}")
                        return None
                    elif response.status == 404:
                        print(f"    ⚠️ 仓库不存在 (404): {owner}/{repo_name}")
                        return None
                    else:
                        print(f"    ⚠️ API请求失败 ({response.status}): {owner}/{repo_name}")
                        return None
                        
        except Exception as e:
            print(f"    ❌ API请求异常: {repo.get('name', 'Unknown')} - {e}")
            return None
    
    async def _get_readme_content(self, session: aiohttp.ClientSession, owner: str, repo_name: str) -> Optional[str]:
        """获取仓库的README内容"""
        try:
            # GitHub API endpoint for README
            readme_url = f"https://api.github.com/repos/{owner}/{repo_name}/readme"
            
            async with session.get(readme_url, headers=self.api_headers) as response:
                self.api_requests_count += 1
                
                if response.status == 200:
                    data = await response.json()
                    
                    # README内容是base64编码的
                    import base64
                    content = data.get('content', '')
                    if content:
                        try:
                            # 解码base64内容
                            decoded_content = base64.b64decode(content).decode('utf-8')
                            
                            # 简化README内容，取前1500字符
                            if len(decoded_content) > 1500:
                                decoded_content = decoded_content[:1500] + "\n\n... (内容过长，已截断)"
                            
                            return decoded_content
                        except Exception as decode_error:
                            print(f"    ⚠️ README解码失败: {decode_error}")
                            return None
                elif response.status == 404:
                    # 没有README文件
                    return None
                else:
                    print(f"    ⚠️ README获取失败 ({response.status}): {owner}/{repo_name}")
                    return None
                    
        except Exception as e:
            print(f"    ⚠️ README请求异常: {e}")
            return None
    
    def _is_ai_related(self, repo: Dict) -> bool:
        """判断仓库是否与AI相关"""
        text_to_check = " ".join([
            repo.get('name', ''),
            repo.get('description', ''),
            " ".join(repo.get('topics', []))
        ]).lower()
        
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
                
                # 统一时区处理
                if update_date.tzinfo is None:
                    # 如果没有时区信息，假设为UTC
                    from datetime import timezone
                    update_date = update_date.replace(tzinfo=timezone.utc)
                
                current_time = datetime.now(update_date.tzinfo)
                days_ago = (current_time - update_date).days
                
                if days_ago <= 7:
                    score += 25
                elif days_ago <= 30:
                    score += 20
                elif days_ago <= 90:
                    score += 15
                elif days_ago <= 365:
                    score += 10
            except Exception as e:
                print(f"    ⚠️ 时间解析失败: {e}")
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


async def main():
    """主函数"""
    print("🚀 结构化GitHub Trending爬虫启动")
    print("=" * 60)
    
    spider = StructuredGitHubSpider()
    
    try:
        # 爬取所有时间维度的数据
        all_results = await spider.crawl_all_time_ranges()
        
        print(f"\n🎉 所有任务完成!")
        print(f"   📊 Daily: {len(all_results.get('daily', []))} 个工具")
        print(f"   📊 Weekly: {len(all_results.get('weekly', []))} 个工具")
        print(f"   📊 Monthly: {len(all_results.get('monthly', []))} 个工具")
        print(f"   🔄 去重后总计: {len(spider.processed_repos)} 个唯一工具")
        print(f"   🌐 总API请求: {spider.api_requests_count}")
        print(f"   📄 总网页请求: {spider.web_requests_count}")
        
    except Exception as e:
        print(f"❌ 爬取过程出现错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
