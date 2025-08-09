# Reddit AI 社区爬虫技术文档

## 目标网站信息

- **网站名称**: Reddit AI Communities
- **网站地址**: https://www.reddit.com/
- **目标子版块**: r/MachineLearning, r/artificial, r/deeplearning, r/ChatGPT, r/OpenAI, r/compsci
- **网站类型**: 社交媒体平台/论坛
- **内容类型**: 讨论帖、新闻分享、技术问答、项目展示
- **更新频率**: 实时更新，每日数百条新帖
- **语言**: 英文为主

## 爬虫方案概述

### 技术架构
- **爬虫类型**: 社交媒体爬虫
- **主要技术**: Python + PRAW (Reddit API) + requests + BeautifulSoup
- **数据格式**: JSON API → JSON → Markdown
- **特色功能**: 实时讨论、社区热度、用户互动分析

### 核心功能
1. **多子版块监控**: 同时监控多个AI相关子版块
2. **热门内容筛选**: 基于upvotes和评论数筛选优质内容
3. **实时更新**: 获取最新发布的帖子和热门讨论
4. **用户行为分析**: 分析用户参与度和讨论质量
5. **内容分类**: 自动分类技术讨论、新闻、项目等
6. **情感分析**: 分析社区对特定技术的态度

## 爬取方式详解

### 1. Reddit API 配置

#### API认证设置
```python
REDDIT_CONFIG = {
    'client_id': 'your_client_id',
    'client_secret': 'your_client_secret',
    'user_agent': 'AI_News_Spider/1.0 by YourUsername',
    'username': 'your_username',  # 可选
    'password': 'your_password',  # 可选
    
    'target_subreddits': [
        'MachineLearning',
        'artificial', 
        'deeplearning',
        'ChatGPT',
        'OpenAI',
        'compsci',
        'ArtificialIntelligence',
        'MLQuestions',
        'LanguageTechnology',
        'computervision'
    ],
    
    'content_filters': {
        'min_score': 10,
        'min_comments': 3,
        'max_age_hours': 168,  # 一周内的内容
        'exclude_domains': ['reddit.com', 'redd.it'],
        'require_flair': False
    }
}
```

### 2. Reddit 爬虫实现

#### 主爬虫类
```python
import praw
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import re
import json
import logging
from typing import List, Dict, Optional, Set
from urllib.parse import urlparse
import time
from collections import defaultdict
import statistics

class RedditAISpider:
    def __init__(self, config: Dict):
        self.config = config
        
        # 初始化Reddit API客户端
        self.reddit = praw.Reddit(
            client_id=config['client_id'],
            client_secret=config['client_secret'],
            user_agent=config['user_agent'],
            username=config.get('username'),
            password=config.get('password')
        )
        
        # 设置请求会话（用于外部链接）
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': config['user_agent']
        })
        
        self.logger = logging.getLogger("RedditAISpider")
        
        # 缓存已处理的帖子ID
        self.processed_posts: Set[str] = set()
        
        # 子版块统计
        self.subreddit_stats = defaultdict(lambda: {
            'total_posts': 0,
            'total_score': 0,
            'total_comments': 0,
            'avg_score': 0,
            'avg_comments': 0
        })
    
    def get_subreddit_posts(self, subreddit_name: str, 
                           sort_method: str = 'hot', 
                           time_filter: str = 'week',
                           limit: int = 100) -> List[Dict]:
        """获取指定子版块的帖子"""
        try:
            self.logger.info(f"Fetching posts from r/{subreddit_name} (sort: {sort_method}, limit: {limit})")
            
            subreddit = self.reddit.subreddit(subreddit_name)
            
            # 根据排序方法获取帖子
            if sort_method == 'hot':
                submissions = subreddit.hot(limit=limit)
            elif sort_method == 'new':
                submissions = subreddit.new(limit=limit)
            elif sort_method == 'top':
                submissions = subreddit.top(time_filter=time_filter, limit=limit)
            elif sort_method == 'rising':
                submissions = subreddit.rising(limit=limit)
            else:
                submissions = subreddit.hot(limit=limit)
            
            posts = []
            for submission in submissions:
                try:
                    # 检查是否已处理
                    if submission.id in self.processed_posts:
                        continue
                    
                    # 应用过滤器
                    if not self.passes_filters(submission):
                        continue
                    
                    post_data = self.extract_post_data(submission, subreddit_name)
                    if post_data:
                        posts.append(post_data)
                        self.processed_posts.add(submission.id)
                        
                        # 更新统计
                        self.update_subreddit_stats(subreddit_name, submission)
                    
                except Exception as e:
                    self.logger.warning(f"Error processing submission {submission.id}: {e}")
                    continue
            
            self.logger.info(f"Collected {len(posts)} posts from r/{subreddit_name}")
            return posts
            
        except Exception as e:
            self.logger.error(f"Error fetching posts from r/{subreddit_name}: {e}")
            return []
    
    def passes_filters(self, submission) -> bool:
        """检查帖子是否通过过滤器"""
        filters = self.config.get('content_filters', {})
        
        # 分数过滤
        min_score = filters.get('min_score', 0)
        if submission.score < min_score:
            return False
        
        # 评论数过滤
        min_comments = filters.get('min_comments', 0)
        if submission.num_comments < min_comments:
            return False
        
        # 时间过滤
        max_age_hours = filters.get('max_age_hours', 168)
        post_age = datetime.utcnow() - datetime.utcfromtimestamp(submission.created_utc)
        if post_age.total_seconds() > max_age_hours * 3600:
            return False
        
        # 域名过滤
        exclude_domains = filters.get('exclude_domains', [])
        if hasattr(submission, 'url') and submission.url:
            domain = urlparse(submission.url).netloc.lower()
            if any(excluded in domain for excluded in exclude_domains):
                return False
        
        # 标签过滤（如果需要）
        require_flair = filters.get('require_flair', False)
        if require_flair and not submission.link_flair_text:
            return False
        
        return True
    
    def extract_post_data(self, submission, subreddit_name: str) -> Optional[Dict]:
        """提取帖子数据"""
        try:
            # 基础信息
            post_data = {
                'post_id': submission.id,
                'title': submission.title,
                'author': str(submission.author) if submission.author else '[deleted]',
                'subreddit': subreddit_name,
                'url': submission.url,
                'permalink': f"https://reddit.com{submission.permalink}",
                'score': submission.score,
                'upvote_ratio': submission.upvote_ratio,
                'num_comments': submission.num_comments,
                'created_utc': submission.created_utc,
                'created_datetime': datetime.utcfromtimestamp(submission.created_utc).isoformat(),
                'is_self': submission.is_self,
                'selftext': submission.selftext if submission.is_self else '',
                'link_flair_text': submission.link_flair_text,
                'source': 'Reddit',
                'source_type': 'social_media'
            }
            
            # 生成唯一ID
            post_data['article_id'] = self.generate_article_id(post_data)
            
            # 提取外部链接内容（如果不是自发帖）
            if not submission.is_self and submission.url:
                external_content = self.extract_external_content(submission.url)
                if external_content:
                    post_data['external_content'] = external_content
            
            # 提取热门评论
            top_comments = self.extract_top_comments(submission)
            if top_comments:
                post_data['top_comments'] = top_comments
            
            # 内容分析
            content_analysis = self.analyze_post_content(post_data)
            post_data['content_analysis'] = content_analysis
            
            # 计算质量分数
            post_data['quality_score'] = self.calculate_quality_score(post_data)
            
            # 计算热度分数
            post_data['popularity_score'] = self.calculate_popularity_score(post_data)
            
            return post_data
            
        except Exception as e:
            self.logger.error(f"Error extracting post data for {submission.id}: {e}")
            return None
    
    def extract_external_content(self, url: str) -> Optional[Dict]:
        """提取外部链接内容"""
        try:
            # 跳过Reddit内部链接
            if 'reddit.com' in url or 'redd.it' in url:
                return None
            
            self.logger.info(f"Extracting external content from: {url}")
            
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 提取标题
            title = ''
            title_selectors = ['title', 'h1', 'meta[property="og:title"]']
            for selector in title_selectors:
                elem = soup.select_one(selector)
                if elem:
                    title = elem.get('content') if elem.name == 'meta' else elem.get_text(strip=True)
                    if title:
                        break
            
            # 提取描述
            description = ''
            desc_selectors = [
                'meta[name="description"]',
                'meta[property="og:description"]',
                'meta[name="twitter:description"]'
            ]
            for selector in desc_selectors:
                elem = soup.select_one(selector)
                if elem:
                    description = elem.get('content', '')
                    if description:
                        break
            
            # 提取主要内容
            content = self.extract_main_content(soup)
            
            # 识别内容类型
            content_type = self.identify_content_type(url, title, content)
            
            external_content = {
                'url': url,
                'title': title,
                'description': description,
                'content': content[:2000] if content else '',  # 限制长度
                'content_type': content_type,
                'domain': urlparse(url).netloc,
                'word_count': len(content.split()) if content else 0
            }
            
            return external_content
            
        except Exception as e:
            self.logger.warning(f"Failed to extract external content from {url}: {e}")
            return None
    
    def extract_main_content(self, soup: BeautifulSoup) -> str:
        """提取网页主要内容"""
        # 移除不需要的元素
        for tag in soup.find_all(['script', 'style', 'nav', 'header', 'footer', 'aside']):
            tag.decompose()
        
        # 尝试多种内容选择器
        content_selectors = [
            'article', 'main', '.content', '.post-content',
            '.entry-content', '.article-content', '.blog-post'
        ]
        
        for selector in content_selectors:
            content_elem = soup.select_one(selector)
            if content_elem:
                text = content_elem.get_text(separator=' ', strip=True)
                if len(text) > 200:
                    return text
        
        # 备用方案：获取所有段落
        paragraphs = soup.find_all('p')
        if paragraphs:
            content_parts = []
            for p in paragraphs:
                text = p.get_text(strip=True)
                if len(text) > 30:
                    content_parts.append(text)
            
            if content_parts:
                return ' '.join(content_parts)
        
        return ''
    
    def identify_content_type(self, url: str, title: str, content: str) -> str:
        """识别内容类型"""
        domain = urlparse(url).netloc.lower()
        combined_text = (title + ' ' + content).lower()
        
        # 学术论文
        if any(site in domain for site in ['arxiv.org', 'acm.org', 'ieee.org', 'springer.com']):
            return 'academic_paper'
        
        # 技术博客
        if any(site in domain for site in ['medium.com', 'towardsdatascience.com', 'blog']):
            return 'blog_post'
        
        # GitHub项目
        if 'github.com' in domain:
            return 'github_project'
        
        # 新闻网站
        if any(site in domain for site in ['techcrunch.com', 'venturebeat.com', 'wired.com']):
            return 'news_article'
        
        # 官方文档
        if any(word in domain for word in ['docs', 'documentation', 'api']):
            return 'documentation'
        
        # 视频内容
        if any(site in domain for site in ['youtube.com', 'vimeo.com']):
            return 'video'
        
        # 基于内容关键词判断
        if any(word in combined_text for word in ['paper', 'research', 'study']):
            return 'research_content'
        elif any(word in combined_text for word in ['tutorial', 'guide', 'how to']):
            return 'tutorial'
        elif any(word in combined_text for word in ['release', 'announcement', 'launch']):
            return 'announcement'
        
        return 'general_content'
    
    def extract_top_comments(self, submission, max_comments: int = 5) -> List[Dict]:
        """提取热门评论"""
        try:
            # 获取评论（按分数排序）
            submission.comments.replace_more(limit=0)  # 不展开"more comments"
            comments = submission.comments.list()
            
            # 过滤和排序评论
            valid_comments = []
            for comment in comments:
                if (hasattr(comment, 'body') and 
                    hasattr(comment, 'score') and 
                    comment.score > 1 and 
                    len(comment.body) > 20 and
                    comment.body != '[deleted]'):
                    valid_comments.append(comment)
            
            # 按分数排序
            valid_comments.sort(key=lambda x: x.score, reverse=True)
            
            top_comments = []
            for comment in valid_comments[:max_comments]:
                comment_data = {
                    'comment_id': comment.id,
                    'author': str(comment.author) if comment.author else '[deleted]',
                    'body': comment.body[:500],  # 限制长度
                    'score': comment.score,
                    'created_utc': comment.created_utc,
                    'created_datetime': datetime.utcfromtimestamp(comment.created_utc).isoformat()
                }
                top_comments.append(comment_data)
            
            return top_comments
            
        except Exception as e:
            self.logger.warning(f"Error extracting comments: {e}")
            return []
    
    def analyze_post_content(self, post_data: Dict) -> Dict:
        """分析帖子内容"""
        analysis = {}
        
        # 合并所有文本内容
        text_parts = [post_data.get('title', '')]
        if post_data.get('selftext'):
            text_parts.append(post_data['selftext'])
        if post_data.get('external_content', {}).get('content'):
            text_parts.append(post_data['external_content']['content'])
        
        combined_text = ' '.join(text_parts).lower()
        
        # AI技术领域关键词
        tech_keywords = {
            'machine_learning': ['machine learning', 'ml', 'supervised', 'unsupervised', 'training'],
            'deep_learning': ['deep learning', 'neural network', 'cnn', 'rnn', 'transformer'],
            'nlp': ['nlp', 'natural language', 'language model', 'bert', 'gpt', 'text processing'],
            'computer_vision': ['computer vision', 'cv', 'image', 'object detection', 'segmentation'],
            'reinforcement_learning': ['reinforcement learning', 'rl', 'reward', 'policy', 'agent'],
            'ai_safety': ['ai safety', 'alignment', 'bias', 'fairness', 'ethics', 'responsible ai'],
            'robotics': ['robotics', 'robot', 'autonomous', 'control', 'manipulation']
        }
        
        # 内容类型关键词
        content_type_keywords = {
            'question': ['question', 'help', 'how to', 'what is', 'why', 'advice'],
            'discussion': ['discussion', 'thoughts', 'opinion', 'debate', 'what do you think'],
            'news': ['news', 'announcement', 'release', 'breakthrough', 'published'],
            'project': ['project', 'built', 'created', 'implementation', 'code', 'github'],
            'research': ['paper', 'research', 'study', 'findings', 'results', 'experiment'],
            'tutorial': ['tutorial', 'guide', 'walkthrough', 'step by step', 'learn']
        }
        
        # 分析技术领域
        for tech, keywords in tech_keywords.items():
            mentions = sum(combined_text.count(keyword) for keyword in keywords)
            analysis[f'{tech}_mentions'] = mentions
        
        # 确定主要技术领域
        tech_scores = {k.replace('_mentions', ''): v for k, v in analysis.items() if k.endswith('_mentions')}
        if tech_scores:
            analysis['primary_tech_area'] = max(tech_scores.items(), key=lambda x: x[1])[0]
        
        # 分析内容类型
        for content_type, keywords in content_type_keywords.items():
            score = sum(combined_text.count(keyword) for keyword in keywords)
            analysis[f'{content_type}_score'] = score
        
        # 确定主要内容类型
        type_scores = {k.replace('_score', ''): v for k, v in analysis.items() if k.endswith('_score')}
        if type_scores:
            analysis['primary_content_type'] = max(type_scores.items(), key=lambda x: x[1])[0]
        
        # 情感分析（简单版本）
        positive_words = ['great', 'amazing', 'excellent', 'awesome', 'fantastic', 'love', 'best']
        negative_words = ['bad', 'terrible', 'awful', 'hate', 'worst', 'disappointing', 'useless']
        
        positive_count = sum(combined_text.count(word) for word in positive_words)
        negative_count = sum(combined_text.count(word) for word in negative_words)
        
        if positive_count > negative_count:
            analysis['sentiment'] = 'positive'
        elif negative_count > positive_count:
            analysis['sentiment'] = 'negative'
        else:
            analysis['sentiment'] = 'neutral'
        
        analysis['sentiment_score'] = positive_count - negative_count
        
        # 检测是否包含代码
        code_indicators = ['```', 'import ', 'def ', 'class ', 'function', 'github.com']
        analysis['contains_code'] = any(indicator in combined_text for indicator in code_indicators)
        
        # 检测是否为求助帖
        help_indicators = ['help', 'stuck', 'problem', 'issue', 'error', 'not working']
        analysis['is_help_request'] = any(indicator in combined_text for indicator in help_indicators)
        
        return analysis
    
    def calculate_quality_score(self, post_data: Dict) -> float:
        """计算帖子质量分数"""
        score = 5.0  # 基础分数
        
        # 分数和评论数加分
        reddit_score = post_data.get('score', 0)
        num_comments = post_data.get('num_comments', 0)
        
        # 基于Reddit分数
        if reddit_score > 100:
            score += 2.0
        elif reddit_score > 50:
            score += 1.5
        elif reddit_score > 20:
            score += 1.0
        elif reddit_score > 10:
            score += 0.5
        
        # 基于评论数
        if num_comments > 50:
            score += 1.5
        elif num_comments > 20:
            score += 1.0
        elif num_comments > 10:
            score += 0.5
        
        # 基于upvote比例
        upvote_ratio = post_data.get('upvote_ratio', 0.5)
        if upvote_ratio > 0.9:
            score += 1.0
        elif upvote_ratio > 0.8:
            score += 0.5
        
        # 内容质量加分
        content_analysis = post_data.get('content_analysis', {})
        
        # 技术深度
        tech_mentions = sum(v for k, v in content_analysis.items() if k.endswith('_mentions'))
        if tech_mentions > 5:
            score += 1.0
        elif tech_mentions > 2:
            score += 0.5
        
        # 外部内容加分
        external_content = post_data.get('external_content')
        if external_content:
            content_type = external_content.get('content_type', '')
            if content_type in ['academic_paper', 'research_content']:
                score += 1.5
            elif content_type in ['blog_post', 'tutorial']:
                score += 1.0
            elif content_type == 'github_project':
                score += 1.2
        
        # 包含代码加分
        if content_analysis.get('contains_code'):
            score += 0.5
        
        # 有质量评论加分
        top_comments = post_data.get('top_comments', [])
        if len(top_comments) > 3:
            score += 0.5
        
        return min(score, 10.0)
    
    def calculate_popularity_score(self, post_data: Dict) -> float:
        """计算热度分数"""
        score = post_data.get('score', 0)
        comments = post_data.get('num_comments', 0)
        upvote_ratio = post_data.get('upvote_ratio', 0.5)
        
        # 时间衰减因子
        created_time = datetime.utcfromtimestamp(post_data.get('created_utc', 0))
        age_hours = (datetime.utcnow() - created_time).total_seconds() / 3600
        time_decay = max(0.1, 1 - (age_hours / 168))  # 一周内线性衰减
        
        # 计算热度分数
        popularity = (score * upvote_ratio + comments * 2) * time_decay
        
        return round(popularity, 2)
    
    def get_all_subreddits_posts(self, sort_method: str = 'hot', 
                                time_filter: str = 'week',
                                posts_per_subreddit: int = 50) -> List[Dict]:
        """获取所有目标子版块的帖子"""
        all_posts = []
        
        for subreddit_name in self.config['target_subreddits']:
            try:
                posts = self.get_subreddit_posts(
                    subreddit_name, 
                    sort_method=sort_method,
                    time_filter=time_filter,
                    limit=posts_per_subreddit
                )
                all_posts.extend(posts)
                
                # 添加延迟避免API限制
                time.sleep(1)
                
            except Exception as e:
                self.logger.error(f"Error processing subreddit {subreddit_name}: {e}")
                continue
        
        # 去重（基于URL或标题）
        unique_posts = self.deduplicate_posts(all_posts)
        
        # 按质量分数排序
        unique_posts.sort(key=lambda x: x.get('quality_score', 0), reverse=True)
        
        self.logger.info(f"Total unique posts collected: {len(unique_posts)}")
        return unique_posts
    
    def deduplicate_posts(self, posts: List[Dict]) -> List[Dict]:
        """帖子去重"""
        seen_urls = set()
        seen_titles = set()
        unique_posts = []
        
        for post in posts:
            url = post.get('url', '')
            title = post.get('title', '').lower().strip()
            
            # 基于URL去重
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_posts.append(post)
            # 基于标题去重（如果没有URL或URL重复）
            elif title and title not in seen_titles:
                seen_titles.add(title)
                unique_posts.append(post)
        
        return unique_posts
    
    def update_subreddit_stats(self, subreddit_name: str, submission):
        """更新子版块统计"""
        stats = self.subreddit_stats[subreddit_name]
        stats['total_posts'] += 1
        stats['total_score'] += submission.score
        stats['total_comments'] += submission.num_comments
        
        # 计算平均值
        stats['avg_score'] = stats['total_score'] / stats['total_posts']
        stats['avg_comments'] = stats['total_comments'] / stats['total_posts']
    
    def get_trending_topics(self, posts: List[Dict], min_mentions: int = 3) -> List[Dict]:
        """分析热门话题"""
        topic_mentions = defaultdict(int)
        topic_posts = defaultdict(list)
        
        for post in posts:
            content_analysis = post.get('content_analysis', {})
            
            # 统计技术领域提及
            for key, value in content_analysis.items():
                if key.endswith('_mentions') and value > 0:
                    topic = key.replace('_mentions', '')
                    topic_mentions[topic] += value
                    topic_posts[topic].append(post)
        
        # 筛选热门话题
        trending_topics = []
        for topic, mentions in topic_mentions.items():
            if mentions >= min_mentions:
                posts_list = topic_posts[topic]
                avg_quality = statistics.mean([p.get('quality_score', 0) for p in posts_list])
                avg_popularity = statistics.mean([p.get('popularity_score', 0) for p in posts_list])
                
                trending_topics.append({
                    'topic': topic,
                    'total_mentions': mentions,
                    'post_count': len(posts_list),
                    'avg_quality_score': round(avg_quality, 2),
                    'avg_popularity_score': round(avg_popularity, 2),
                    'sample_posts': posts_list[:3]  # 示例帖子
                })
        
        # 按提及次数排序
        trending_topics.sort(key=lambda x: x['total_mentions'], reverse=True)
        
        return trending_topics
    
    def generate_article_id(self, post_data: Dict) -> str:
        """生成文章唯一ID"""
        import hashlib
        content = f"{post_data.get('post_id', '')}{post_data.get('subreddit', '')}reddit"
        return hashlib.md5(content.encode('utf-8')).hexdigest()[:16]
    
    def generate_subreddit_report(self) -> Dict:
        """生成子版块统计报告"""
        report = {
            'total_subreddits': len(self.subreddit_stats),
            'subreddit_details': dict(self.subreddit_stats),
            'top_subreddits_by_activity': [],
            'top_subreddits_by_quality': [],
            'report_timestamp': datetime.utcnow().isoformat()
        }
        
        # 按活跃度排序
        by_activity = sorted(
            self.subreddit_stats.items(),
            key=lambda x: x[1]['total_posts'],
            reverse=True
        )
        report['top_subreddits_by_activity'] = [
            {'subreddit': name, 'stats': stats} for name, stats in by_activity[:10]
        ]
        
        # 按平均质量排序
        by_quality = sorted(
            self.subreddit_stats.items(),
            key=lambda x: x[1]['avg_score'],
            reverse=True
        )
        report['top_subreddits_by_quality'] = [
            {'subreddit': name, 'stats': stats} for name, stats in by_quality[:10]
        ]
        
        return report
```

### 3. 实时监控实现

#### 实时监控器
```python
class RedditRealTimeMonitor:
    def __init__(self, spider: RedditAISpider):
        self.spider = spider
        self.monitoring = False
        self.last_check = {}
        
    def start_monitoring(self, check_interval: int = 300):  # 5分钟检查一次
        """开始实时监控"""
        self.monitoring = True
        
        while self.monitoring:
            try:
                new_posts = []
                
                for subreddit_name in self.spider.config['target_subreddits']:
                    # 获取最新帖子
                    recent_posts = self.spider.get_subreddit_posts(
                        subreddit_name, 
                        sort_method='new',
                        limit=20
                    )
                    
                    # 过滤新帖子
                    last_check_time = self.last_check.get(subreddit_name, 0)
                    truly_new_posts = [
                        post for post in recent_posts 
                        if post.get('created_utc', 0) > last_check_time
                    ]
                    
                    new_posts.extend(truly_new_posts)
                    
                    # 更新最后检查时间
                    if recent_posts:
                        self.last_check[subreddit_name] = max(
                            post.get('created_utc', 0) for post in recent_posts
                        )
                
                if new_posts:
                    self.process_new_posts(new_posts)
                
                time.sleep(check_interval)
                
            except Exception as e:
                self.spider.logger.error(f"Error in real-time monitoring: {e}")
                time.sleep(60)  # 错误时等待更长时间
    
    def process_new_posts(self, posts: List[Dict]):
        """处理新帖子"""
        # 按质量分数过滤
        high_quality_posts = [p for p in posts if p.get('quality_score', 0) > 7.0]
        
        if high_quality_posts:
            self.spider.logger.info(f"Found {len(high_quality_posts)} high-quality new posts")
            
            # 这里可以添加通知逻辑，如发送邮件、推送等
            for post in high_quality_posts:
                self.spider.logger.info(f"High-quality post: {post['title']} (Score: {post['quality_score']})")
    
    def stop_monitoring(self):
        """停止监控"""
        self.monitoring = False
```

## 反爬虫应对策略

### 1. Reddit API 限制处理
```python
class RedditRateLimiter:
    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self.request_times = []
    
    def wait_if_needed(self):
        now = time.time()
        
        # 清理超过1分钟的记录
        self.request_times = [t for t in self.request_times if now - t < 60]
        
        # 如果请求过于频繁，等待
        if len(self.request_times) >= self.requests_per_minute:
            sleep_time = 60 - (now - self.request_times[0])
            if sleep_time > 0:
                time.sleep(sleep_time)
        
        self.request_times.append(now)
```

### 2. 错误处理和重试
```python
def handle_reddit_exceptions(func):
    """Reddit API异常处理装饰器"""
    def wrapper(*args, **kwargs):
        max_retries = 3
        for attempt in range(max_retries):
            try:
                return func(*args, **kwargs)
            except praw.exceptions.RedditAPIException as e:
                if 'RATELIMIT' in str(e):
                    wait_time = 60 * (attempt + 1)
                    time.sleep(wait_time)
                else:
                    raise e
            except Exception as e:
                if attempt == max_retries - 1:
                    raise e
                time.sleep(2 ** attempt)
        return None
    return wrapper
```

## 配置参数

### 爬虫配置
```python
REDDIT_SPIDER_CONFIG = {
    'api_config': {
        'client_id': 'your_client_id',
        'client_secret': 'your_client_secret',
        'user_agent': 'AI_News_Spider/1.0',
        'rate_limit': 60  # 每分钟请求数
    },
    'target_subreddits': [
        'MachineLearning', 'artificial', 'deeplearning',
        'ChatGPT', 'OpenAI', 'compsci', 'ArtificialIntelligence'
    ],
    'content_filters': {
        'min_score': 10,
        'min_comments': 3,
        'max_age_hours': 168,
        'min_word_count': 50
    },
    'quality_thresholds': {
        'high_quality_score': 7.0,
        'trending_mentions': 3,
        'popular_score': 50.0
    },
    'monitoring': {
        'real_time_enabled': True,
        'check_interval_seconds': 300,
        'notification_threshold': 8.0
    }
}
```

## 数据输出格式

### JSON格式
```json
{
  "article_id": "reddit_ml_001",
  "post_id": "abc123",
  "title": "New breakthrough in transformer architecture",
  "author": "ai_researcher",
  "subreddit": "MachineLearning",
  "url": "https://arxiv.org/abs/2024.01234",
  "permalink": "https://reddit.com/r/MachineLearning/comments/abc123/",
  "score": 156,
  "upvote_ratio": 0.94,
  "num_comments": 23,
  "created_datetime": "2024-01-15T10:30:00Z",
  "is_self": false,
  "selftext": "",
  "link_flair_text": "Research",
  "source": "Reddit",
  "source_type": "social_media",
  "external_content": {
    "url": "https://arxiv.org/abs/2024.01234",
    "title": "Efficient Attention Mechanisms for Large Language Models",
    "description": "We propose a new attention mechanism...",
    "content": "Abstract: In this paper, we introduce...",
    "content_type": "academic_paper",
    "domain": "arxiv.org",
    "word_count": 1250
  },
  "top_comments": [
    {
      "comment_id": "def456",
      "author": "ml_expert",
      "body": "This is really interesting work. The efficiency gains...",
      "score": 45,
      "created_datetime": "2024-01-15T11:00:00Z"
    }
  ],
  "content_analysis": {
    "primary_tech_area": "deep_learning",
    "primary_content_type": "research",
    "sentiment": "positive",
    "sentiment_score": 3,
    "contains_code": false,
    "is_help_request": false,
    "machine_learning_mentions": 5,
    "deep_learning_mentions": 8,
    "nlp_mentions": 3
  },
  "quality_score": 8.5,
  "popularity_score": 142.3,
  "crawl_metadata": {
    "crawl_timestamp": "2024-01-15T12:00:00Z",
    "spider_version": "1.0",
    "processing_time_ms": 1500
  }
}
```

## 常见问题与解决方案

### 1. API限制问题
**问题**: Reddit API有严格的速率限制
**解决**: 
- 使用官方PRAW库
- 实现智能速率限制
- 合理设置请求间隔

### 2. 内容质量过滤
**问题**: Reddit内容质量参差不齐
**解决**: 
- 多维度质量评分
- 基于社区反馈过滤
- 人工验证重要内容

### 3. 实时性要求
**问题**: 需要及时获取热门讨论
**解决**: 
- 实现实时监控
- 优化检查频率
- 设置智能通知

### 4. 外部链接处理
**问题**: 外部链接可能失效或需要特殊处理
**解决**: 
- 实现链接有效性检查
- 支持多种内容类型
- 优雅处理失败情况

## 维护建议

### 定期维护任务
1. **API密钥管理**: 定期更新和轮换API密钥
2. **子版块监控**: 监控目标子版块的活跃度变化
3. **质量评估**: 评估内容质量评分的准确性
4. **性能优化**: 优化爬取效率和资源使用

### 扩展方向
1. **情感分析增强**: 使用更先进的NLP模型
2. **用户行为分析**: 分析用户参与模式
3. **跨平台整合**: 整合其他社交媒体平台
4. **智能推荐**: 基于用户兴趣推荐内容

## 相关资源

- [Reddit API Documentation](https://www.reddit.com/dev/api/)
- [PRAW Documentation](https://praw.readthedocs.io/)
- [Reddit Developer Platform](https://www.reddit.com/prefs/apps/)
- [Reddit Content Policy](https://www.redditinc.com/policies/content-policy)
- [Reddit API Terms](https://www.reddit.com/wiki/api-terms)