#!/usr/bin/env python3
"""
最终API测试和博客数据提取方案
"""

import json
import requests
from urllib.parse import urljoin, urlparse
import time
import re

class HuggingFaceBlogAPI:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json',
            'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3',
        })
        self.base_url = "https://huggingface.co"
        
    def test_posts_api_with_different_params(self):
        """测试Posts API的不同参数组合来获取更多博客相关内容"""
        print("🔬 测试不同参数组合来获取博客内容...")
        
        api_url = f"{self.base_url}/api/posts"
        
        # 高级参数测试
        advanced_params = [
            # 测试更大的limit值
            {'limit': 50},
            {'limit': 100},
            
            # 测试分页
            {'page': 0, 'limit': 50},
            {'page': 1, 'limit': 50},
            {'page': 2, 'limit': 50},
            
            # 测试offset
            {'offset': 0, 'limit': 50},
            {'offset': 50, 'limit': 50},
            {'offset': 100, 'limit': 50},
            
            # 测试日期范围
            {'since': '2025-08-01', 'limit': 50},
            {'since': '2025-07-01', 'limit': 50},
            {'since': '2025-06-01', 'limit': 50},
            
            # 测试trending
            {'sort': 'trending', 'limit': 50},
            
            # 测试博客相关过滤器
            {'type': 'blog', 'limit': 50},
            {'category': 'blog', 'limit': 50},
            {'filter': 'blog', 'limit': 50},
            {'tag': 'blog', 'limit': 50},
        ]
        
        all_blog_posts = {}  # 用slug作为key去重
        
        for params in advanced_params:
            print(f"   测试参数: {params}")
            
            try:
                response = self.session.get(api_url, params=params, timeout=15)
                
                if response.status_code == 200:
                    data = response.json()
                    posts = data.get('socialPosts', [])
                    
                    blog_posts_found = 0
                    
                    for post in posts:
                        content = post.get('rawContent', '').lower()
                        
                        # 更严格的博客检测
                        blog_indicators = [
                            'huggingface.co/blog/' in content,
                            '✅ new article' in content,
                            'blog post' in content,
                            'new blog' in content,
                            '/blog/' in content and 'article' in content
                        ]
                        
                        if any(blog_indicators):
                            slug = post.get('slug')
                            if slug not in all_blog_posts:
                                all_blog_posts[slug] = post
                                blog_posts_found += 1
                    
                    print(f"      找到 {blog_posts_found} 个新的博客posts")
                    
                else:
                    print(f"      失败: {response.status_code}")
                    
            except Exception as e:
                print(f"      错误: {e}")
            
            time.sleep(0.5)
        
        print(f"\n   总共发现 {len(all_blog_posts)} 个唯一的博客相关posts")
        return list(all_blog_posts.values())
    
    def extract_blog_links_from_posts(self, posts):
        """从posts中提取所有博客链接"""
        print(f"\n📎 从 {len(posts)} 个posts中提取博客链接...")
        
        blog_links = []
        
        for post in posts:
            content = post.get('rawContent', '')
            
            # 提取博客链接的正则表达式
            patterns = [
                r'https://huggingface\.co/blog/[^\s\)\]"\'>]+',
                r'huggingface\.co/blog/[^\s\)\]"\'>]+',
                r'/blog/[^\s\)\]"\'>]+(?=\s|$|[\)\]"\'>])'
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, content)
                for match in matches:
                    # 清理和标准化链接
                    if not match.startswith('http'):
                        match = 'https://huggingface.co' + (match if match.startswith('/') else '/' + match)
                    
                    # 移除末尾的标点符号
                    match = re.sub(r'[,\.\)\]"\'>]+$', '', match)
                    
                    if match not in blog_links:
                        blog_links.append(match)
                        
                        # 提取额外信息
                        blog_info = {
                            'url': match,
                            'found_in_post': post.get('slug'),
                            'post_author': post.get('author', {}).get('name'),
                            'post_date': post.get('publishedAt'),
                            'post_content_preview': content[:200] + '...'
                        }
                        
                        # 分析链接结构
                        parsed = urlparse(match)
                        path_parts = parsed.path.strip('/').split('/')
                        if len(path_parts) >= 2 and path_parts[0] == 'blog':
                            if len(path_parts) == 2:
                                # /blog/zh 格式
                                blog_info['type'] = 'language_homepage'
                                blog_info['language'] = path_parts[1]
                            elif len(path_parts) >= 3:
                                # /blog/author/title 格式
                                blog_info['type'] = 'article'
                                blog_info['author'] = path_parts[1]
                                blog_info['article_slug'] = path_parts[2]
                        
                        print(f"   发现博客链接: {match}")
                        if 'type' in blog_info:
                            print(f"      类型: {blog_info['type']}")
                            if blog_info['type'] == 'article':
                                print(f"      作者: {blog_info.get('author')}")
                                print(f"      文章: {blog_info.get('article_slug')}")
        
        return blog_links
    
    def test_blog_page_direct_access(self):
        """直接测试博客页面的访问"""
        print(f"\n🌐 直接测试博客页面访问...")
        
        blog_urls = [
            'https://huggingface.co/blog',
            'https://huggingface.co/blog/zh',
            'https://huggingface.co/blog/en',
            'https://huggingface.co/blog/latest',
            'https://huggingface.co/blog/all',
        ]
        
        results = []
        
        for url in blog_urls:
            print(f"   测试: {url}")
            
            try:
                response = self.session.get(url, timeout=10)
                
                result = {
                    'url': url,
                    'status_code': response.status_code,
                    'content_type': response.headers.get('content-type', ''),
                    'size': len(response.content)
                }
                
                if response.status_code == 200:
                    print(f"      ✅ 成功访问")
                    
                    # 检查是否包含分页信息
                    content = response.text
                    if '?p=' in content or 'page=' in content:
                        result['has_pagination'] = True
                        print(f"      📄 包含分页")
                    
                    # 检查是否包含JSON数据
                    json_pattern = r'<script[^>]*>.*?window\.__[A-Z_]+__\s*=\s*(\{.*?\});'
                    json_matches = re.findall(json_pattern, content, re.DOTALL)
                    if json_matches:
                        result['embedded_json_count'] = len(json_matches)
                        print(f"      📊 包含 {len(json_matches)} 个内嵌JSON对象")
                        
                        # 尝试解析第一个JSON
                        try:
                            first_json = json.loads(json_matches[0])
                            if isinstance(first_json, dict):
                                result['json_keys'] = list(first_json.keys())[:10]
                                print(f"      🔑 JSON键: {result['json_keys']}")
                        except:
                            pass
                    
                else:
                    print(f"      ❌ 失败: {response.status_code}")
                
                results.append(result)
                
            except Exception as e:
                print(f"      ⚠️  错误: {e}")
                results.append({
                    'url': url,
                    'error': str(e)
                })
            
            time.sleep(0.5)
        
        return results
    
    def generate_final_recommendations(self):
        """生成最终的数据获取建议"""
        print("\n" + "="*80)
        print("🎯 HUGGING FACE 博客数据获取最终分析报告")
        print("="*80)
        
        # 1. 测试更多posts参数
        print("\n1️⃣ 扩展Posts API测试")
        blog_posts = self.test_posts_api_with_different_params()
        
        # 2. 提取博客链接
        print("\n2️⃣ 博客链接提取")
        if blog_posts:
            blog_links = self.extract_blog_links_from_posts(blog_posts)
        else:
            blog_links = []
        
        # 3. 直接测试博客页面
        print("\n3️⃣ 直接博客页面测试")
        blog_page_results = self.test_blog_page_direct_access()
        
        # 4. 生成最终建议
        print("\n4️⃣ 最终建议")
        
        successful_blog_pages = [r for r in blog_page_results if r.get('status_code') == 200]
        has_embedded_json = any(r.get('embedded_json_count', 0) > 0 for r in successful_blog_pages)
        
        print(f"\n📊 发现的数据源:")
        print(f"   Posts API中的博客相关内容: {len(blog_posts)} 个")
        print(f"   提取的博客链接: {len(blog_links)} 个")
        print(f"   可访问的博客页面: {len(successful_blog_pages)} 个")
        print(f"   包含内嵌JSON的页面: {sum(1 for r in successful_blog_pages if r.get('embedded_json_count', 0) > 0)} 个")
        
        # 推荐最佳方案
        recommendations = []
        
        if len(blog_posts) > 0:
            recommendations.append({
                'priority': 1,
                'method': 'Posts API + 博客链接提取',
                'description': f'使用 /api/posts 获取社交动态，从中提取 {len(blog_links)} 个博客链接',
                'api_endpoint': 'https://huggingface.co/api/posts',
                'parameters': ['limit=50', 'since=2025-06-01', 'sort=trending'],
                'pros': ['包含完整的博客文章链接', '可以获取文章发布时间和作者信息', 'JSON格式便于处理'],
                'cons': ['需要从动态中过滤博客内容', '可能无法获取历史文章'],
                'implementation': 'requests + 正则表达式提取博客链接'
            })
        
        if has_embedded_json:
            recommendations.append({
                'priority': 2,
                'method': '博客页面内嵌JSON数据',
                'description': '直接访问博客页面，解析内嵌的JSON数据',
                'api_endpoint': 'https://huggingface.co/blog/zh',
                'parameters': ['分页参数: ?p=0,1,2...'],
                'pros': ['可能包含完整的博客列表', '数据结构化', '支持分页'],
                'cons': ['需要解析HTML中的JavaScript', '可能需要处理反爬虫机制'],
                'implementation': 'requests + BeautifulSoup + JSON解析'
            })
        
        recommendations.append({
            'priority': 3,
            'method': '传统HTML解析',
            'description': '直接解析博客页面的HTML结构',
            'api_endpoint': 'https://huggingface.co/blog/zh',
            'parameters': ['分页参数: ?p=0,1,2...'],
            'pros': ['最稳定可靠', '不依赖API稳定性', '可以获取所有公开信息'],
            'cons': ['需要处理复杂的HTML结构', '性能相对较低', '可能受页面改版影响'],
            'implementation': 'requests + BeautifulSoup + CSS选择器'
        })
        
        print(f"\n🥇 推荐的数据获取方案 (按优先级排序):")
        
        for i, rec in enumerate(recommendations, 1):
            print(f"\n   {i}. {rec['method']} (优先级: {rec['priority']})")
            print(f"      描述: {rec['description']}")
            print(f"      端点: {rec['api_endpoint']}")
            print(f"      参数: {', '.join(rec['parameters'])}")
            print(f"      优点: {', '.join(rec['pros'])}")
            print(f"      缺点: {', '.join(rec['cons'])}")
            print(f"      实现: {rec['implementation']}")
        
        # 保存完整报告
        final_report = {
            'analysis_time': time.strftime('%Y-%m-%d %H:%M:%S'),
            'summary': {
                'blog_posts_from_api': len(blog_posts),
                'extracted_blog_links': len(blog_links),
                'accessible_blog_pages': len(successful_blog_pages),
                'pages_with_embedded_json': sum(1 for r in successful_blog_pages if r.get('embedded_json_count', 0) > 0)
            },
            'blog_posts': blog_posts,
            'blog_links': blog_links,
            'blog_page_results': blog_page_results,
            'recommendations': recommendations
        }
        
        with open('/home/shan/Huggingface_blog/final_analysis_report.json', 'w', encoding='utf-8') as f:
            json.dump(final_report, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"\n💾 完整报告已保存到: /home/shan/Huggingface_blog/final_analysis_report.json")
        
        return final_report

def main():
    analyzer = HuggingFaceBlogAPI()
    analyzer.generate_final_recommendations()

if __name__ == "__main__":
    main()