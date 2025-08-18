#!/usr/bin/env python3
"""
深入分析Hugging Face Posts API
"""

import json
import requests
from urllib.parse import urljoin
import time

class HuggingFacePostsAPI:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json',
            'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3',
        })
        self.base_url = "https://huggingface.co"
        
    def test_posts_api_parameters(self):
        """测试/api/posts的各种参数"""
        print("🧪 测试Posts API的各种参数...")
        
        api_url = f"{self.base_url}/api/posts"
        
        # 测试各种可能的参数
        test_cases = [
            # 基础测试
            {},
            
            # 分页测试
            {'page': 0},
            {'page': 1},
            {'page': 2},
            {'offset': 0},
            {'offset': 10},
            {'offset': 20},
            {'limit': 5},
            {'limit': 10},
            {'limit': 20},
            {'skip': 0},
            {'skip': 10},
            
            # 语言/地区测试
            {'lang': 'zh'},
            {'language': 'zh'},
            {'locale': 'zh'},
            {'locale': 'zh-CN'},
            
            # 排序测试
            {'sort': 'latest'},
            {'sort': 'popular'},
            {'sort': 'trending'},
            {'order': 'desc'},
            {'order': 'asc'},
            
            # 时间范围测试
            {'since': '2025-08-01'},
            {'until': '2025-08-17'},
            {'date': '2025-08-17'},
            
            # 标签/分类测试
            {'tag': 'blog'},
            {'category': 'blog'},
            {'type': 'blog'},
            {'filter': 'blog'},
            
            # 组合测试
            {'page': 1, 'limit': 5},
            {'offset': 10, 'limit': 5},
            {'lang': 'zh', 'limit': 3},
        ]
        
        results = []
        
        for i, params in enumerate(test_cases, 1):
            print(f"\n   测试 {i}/{len(test_cases)}: {params}")
            
            try:
                response = self.session.get(api_url, params=params, timeout=10)
                
                result = {
                    'test_case': i,
                    'params': params,
                    'status_code': response.status_code,
                    'url': response.url,
                    'headers': dict(response.headers),
                    'response_size': len(response.content)
                }
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        result['json_structure'] = {
                            'type': type(data).__name__,
                            'keys': list(data.keys()) if isinstance(data, dict) else None,
                            'total_items': data.get('numTotalItems') if isinstance(data, dict) else None,
                            'posts_count': len(data.get('socialPosts', [])) if isinstance(data, dict) else None
                        }
                        
                        # 分析第一个post的结构
                        if isinstance(data, dict) and 'socialPosts' in data and data['socialPosts']:
                            first_post = data['socialPosts'][0]
                            result['first_post_info'] = {
                                'slug': first_post.get('slug'),
                                'author': first_post.get('author', {}).get('name'),
                                'publishedAt': first_post.get('publishedAt'),
                                'language': first_post.get('identifiedLanguage', {}).get('language'),
                                'impressions': first_post.get('totalUniqueImpressions'),
                                'content_length': len(first_post.get('rawContent', '')),
                                'has_blog_link': 'blog' in first_post.get('rawContent', '').lower()
                            }
                        
                        print(f"      ✅ 成功: {result['json_structure']}")
                    except Exception as e:
                        result['json_error'] = str(e)
                        print(f"      ❌ JSON解析错误: {e}")
                else:
                    print(f"      ❌ 失败: {response.status_code}")
                
                results.append(result)
                
            except Exception as e:
                result = {
                    'test_case': i,
                    'params': params,
                    'error': str(e)
                }
                results.append(result)
                print(f"      ⚠️  请求错误: {e}")
            
            time.sleep(0.5)  # 避免请求过快
        
        return results
    
    def test_blog_specific_apis(self):
        """测试博客相关的特定API"""
        print("\n🔍 测试博客相关的API...")
        
        blog_endpoints = [
            "/api/posts/blog",
            "/api/blog/posts",
            "/api/blog/zh",
            "/api/blog/zh/posts", 
            "/api/posts?type=blog",
            "/api/posts?category=blog",
            "/api/posts?filter=blog",
            "/api/posts?tag=blog",
            "/api/posts?content=blog",
            "/api/posts/recent",
            "/api/posts/latest",
            "/api/posts/popular",
            "/api/social/posts",
            "/api/community/posts",
        ]
        
        results = []
        
        for endpoint in blog_endpoints:
            print(f"   测试: {endpoint}")
            
            try:
                full_url = urljoin(self.base_url, endpoint)
                response = self.session.get(full_url, timeout=10)
                
                result = {
                    'endpoint': endpoint,
                    'full_url': full_url,
                    'status_code': response.status_code,
                    'headers': dict(response.headers),
                    'size': len(response.content)
                }
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        result['success'] = True
                        result['data_type'] = type(data).__name__
                        if isinstance(data, dict):
                            result['keys'] = list(data.keys())
                        print(f"      ✅ 成功!")
                    except:
                        result['success'] = False
                        print(f"      ❌ 非JSON响应")
                else:
                    result['success'] = False
                    print(f"      ❌ 失败: {response.status_code}")
                
                results.append(result)
                
            except Exception as e:
                result = {
                    'endpoint': endpoint,
                    'error': str(e)
                }
                results.append(result)
                print(f"      ⚠️  错误: {e}")
            
            time.sleep(0.3)
        
        return results
    
    def analyze_post_content_for_blogs(self):
        """分析posts中的博客相关内容"""
        print("\n📝 分析posts中的博客相关内容...")
        
        try:
            response = self.session.get(f"{self.base_url}/api/posts", timeout=10)
            if response.status_code != 200:
                print("   无法获取posts数据")
                return None
            
            data = response.json()
            posts = data.get('socialPosts', [])
            
            blog_related_posts = []
            
            for post in posts:
                content = post.get('rawContent', '').lower()
                author_name = post.get('author', {}).get('name', '')
                
                # 检查是否包含博客相关关键词
                blog_keywords = [
                    'blog', 'article', 'tutorial', 'guide', 'documentation',
                    'huggingface.co/blog', 'new article', 'blog post'
                ]
                
                has_blog_content = any(keyword in content for keyword in blog_keywords)
                has_blog_url = 'huggingface.co/blog' in content
                
                if has_blog_content or has_blog_url:
                    # 提取博客链接
                    blog_links = []
                    import re
                    blog_url_pattern = r'https://huggingface\.co/blog/[^\s\)"\']+'
                    blog_matches = re.findall(blog_url_pattern, content)
                    blog_links.extend(blog_matches)
                    
                    blog_info = {
                        'slug': post.get('slug'),
                        'author': author_name,
                        'publishedAt': post.get('publishedAt'),
                        'content_preview': post.get('rawContent', '')[:200] + '...',
                        'has_blog_url': has_blog_url,
                        'blog_links': blog_links,
                        'impressions': post.get('totalUniqueImpressions'),
                        'language': post.get('identifiedLanguage', {}).get('language')
                    }
                    
                    blog_related_posts.append(blog_info)
            
            print(f"   发现 {len(blog_related_posts)} 个博客相关的posts")
            
            # 显示一些示例
            for i, blog_post in enumerate(blog_related_posts[:3], 1):
                print(f"\n   示例 {i}:")
                print(f"     作者: {blog_post['author']}")
                print(f"     时间: {blog_post['publishedAt']}")
                print(f"     博客链接: {blog_post['blog_links']}")
                print(f"     内容预览: {blog_post['content_preview']}")
            
            return blog_related_posts
            
        except Exception as e:
            print(f"   分析出错: {e}")
            return None
    
    def generate_detailed_report(self):
        """生成详细的API分析报告"""
        print("\n" + "="*80)
        print("🔬 HUGGING FACE POSTS API 详细分析报告")
        print("="*80)
        
        # 1. 测试API参数
        print("\n1️⃣ API参数测试")
        param_results = self.test_posts_api_parameters()
        
        # 2. 测试博客相关API
        print("\n2️⃣ 博客相关API测试")
        blog_api_results = self.test_blog_specific_apis()
        
        # 3. 分析博客内容
        print("\n3️⃣ 博客内容分析")
        blog_content = self.analyze_post_content_for_blogs()
        
        # 4. 生成总结报告
        print("\n4️⃣ 分析总结")
        
        # 分析有效的参数
        valid_params = []
        for result in param_results:
            if result.get('status_code') == 200 and result.get('json_structure'):
                posts_count = result['json_structure'].get('posts_count', 0)
                total_items = result['json_structure'].get('total_items', 0)
                if posts_count > 0 or total_items > 0:
                    valid_params.append(result)
        
        print(f"   发现 {len(valid_params)} 个有效的参数组合")
        
        if valid_params:
            print("\n   有效参数组合:")
            for result in valid_params[:5]:  # 显示前5个
                params = result['params']
                posts_count = result['json_structure'].get('posts_count', 0)
                total_items = result['json_structure'].get('total_items', 0)
                print(f"     {params} -> {posts_count} posts (总计: {total_items})")
        
        # 分析成功的博客API
        successful_blog_apis = [r for r in blog_api_results if r.get('success')]
        print(f"\n   发现 {len(successful_blog_apis)} 个成功的博客API端点")
        
        for api in successful_blog_apis:
            print(f"     ✅ {api['endpoint']}")
        
        # 博客内容统计
        if blog_content:
            print(f"\n   博客相关posts统计:")
            print(f"     包含博客内容的posts: {len(blog_content)}")
            
            # 按作者统计
            authors = {}
            for post in blog_content:
                author = post['author']
                authors[author] = authors.get(author, 0) + 1
            
            print(f"     活跃的博客作者:")
            for author, count in sorted(authors.items(), key=lambda x: x[1], reverse=True)[:5]:
                print(f"       {author}: {count} 篇")
        
        # 保存详细报告
        report_data = {
            'analysis_time': time.strftime('%Y-%m-%d %H:%M:%S'),
            'api_parameter_tests': param_results,
            'blog_api_tests': blog_api_results,
            'blog_content_analysis': blog_content,
            'summary': {
                'valid_parameter_combinations': len(valid_params),
                'successful_blog_apis': len(successful_blog_apis),
                'blog_related_posts': len(blog_content) if blog_content else 0
            }
        }
        
        with open('/home/shan/Huggingface_blog/posts_api_detailed_report.json', 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"\n💾 详细报告已保存到: /home/shan/Huggingface_blog/posts_api_detailed_report.json")
        
        return report_data

def main():
    analyzer = HuggingFacePostsAPI()
    analyzer.generate_detailed_report()

if __name__ == "__main__":
    main()