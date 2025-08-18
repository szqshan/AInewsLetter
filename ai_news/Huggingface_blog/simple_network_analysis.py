#!/usr/bin/env python3
"""
Hugging Face Blog 网络分析工具 - 简化版本
使用requests和浏览器开发者工具方法分析网络请求
"""

import json
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time

class HuggingFaceAnalyzer:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive'
        })
        self.base_url = "https://huggingface.co"
        self.api_requests = []
        self.all_requests = []
        
    def analyze_page_structure(self, url):
        """分析页面结构和内嵌数据"""
        print(f"🔍 分析页面: {url}")
        
        try:
            response = self.session.get(url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            analysis = {
                'url': url,
                'status_code': response.status_code,
                'headers': dict(response.headers),
                'page_title': soup.title.string if soup.title else None,
                'scripts': [],
                'json_data': [],
                'api_hints': [],
                'meta_tags': [],
                'links': []
            }
            
            # 分析script标签
            for script in soup.find_all('script'):
                script_info = {}
                if script.get('src'):
                    script_info['type'] = 'external'
                    script_info['src'] = urljoin(url, script['src'])
                else:
                    script_info['type'] = 'inline'
                    if script.string:
                        # 查找内嵌JSON数据
                        content = script.string.strip()
                        if content:
                            # 查找可能的API端点
                            api_patterns = [
                                r'[\'"]https?://[^\'"]*api[^\'"]*[\'"]',
                                r'[\'"]https?://[^\'"]*\.json[\'"]',
                                r'fetch\s*\(\s*[\'"][^\'"]+[\'"]',
                                r'axios\.[^(]+\([\'"][^\'"]+[\'"]',
                                r'\.get\s*\(\s*[\'"][^\'"]+[\'"]',
                                r'\.post\s*\(\s*[\'"][^\'"]+[\'"]'
                            ]
                            
                            for pattern in api_patterns:
                                matches = re.findall(pattern, content, re.IGNORECASE)
                                for match in matches:
                                    # 清理匹配的字符串
                                    clean_match = re.sub(r'[\'\"()fetch\.getpostaxios]', '', match).strip()
                                    if clean_match and clean_match.startswith('http'):
                                        analysis['api_hints'].append(clean_match)
                            
                            # 尝试找到JSON数据
                            try:
                                # 查找可能的JSON对象
                                json_patterns = [
                                    r'\{[^{}]*"[^"]*"[^{}]*:[^{}]*\}',
                                    r'window\.__[A-Z_]+__\s*=\s*(\{.*?\});',
                                    r'data\s*:\s*(\{.*?\})',
                                ]
                                
                                for pattern in json_patterns:
                                    matches = re.findall(pattern, content, re.DOTALL)
                                    for match in matches:
                                        try:
                                            if isinstance(match, tuple):
                                                match = match[0] if match else ""
                                            parsed = json.loads(match)
                                            analysis['json_data'].append({
                                                'data': parsed,
                                                'size': len(str(match))
                                            })
                                        except:
                                            continue
                                            
                            except Exception as e:
                                pass
                                
                analysis['scripts'].append(script_info)
            
            # 分析meta标签
            for meta in soup.find_all('meta'):
                meta_info = {}
                for attr in ['name', 'property', 'content', 'http-equiv']:
                    if meta.get(attr):
                        meta_info[attr] = meta[attr]
                if meta_info:
                    analysis['meta_tags'].append(meta_info)
            
            # 分析链接
            for link in soup.find_all('a', href=True):
                href = link['href']
                if href.startswith('/blog/') and href != '/blog/zh':
                    analysis['links'].append({
                        'href': urljoin(url, href),
                        'text': link.get_text().strip()[:100]
                    })
            
            return analysis
            
        except Exception as e:
            print(f"❌ 分析页面时出错: {e}")
            return None
    
    def test_api_endpoints(self):
        """测试可能的API端点"""
        print("\n🧪 测试可能的API端点...")
        
        potential_endpoints = [
            "/api/blog",
            "/api/blog/zh",
            "/api/v1/blog",
            "/api/posts",
            "/blog/api",
            "/blog/feed",
            "/blog/rss",
            "/_next/data",
            "/api/content",
            "/graphql"
        ]
        
        api_results = []
        
        for endpoint in potential_endpoints:
            full_url = urljoin(self.base_url, endpoint)
            print(f"   测试: {full_url}")
            
            try:
                # 尝试GET请求
                response = self.session.get(full_url, timeout=10)
                
                result = {
                    'url': full_url,
                    'method': 'GET',
                    'status_code': response.status_code,
                    'headers': dict(response.headers),
                    'content_type': response.headers.get('content-type', ''),
                    'size': len(response.content)
                }
                
                if response.status_code == 200:
                    print(f"   ✅ 成功: {response.status_code} - {response.headers.get('content-type', '')}")
                    
                    # 如果是JSON响应，尝试解析
                    if 'application/json' in response.headers.get('content-type', ''):
                        try:
                            result['json_data'] = response.json()
                            print(f"      JSON数据类型: {type(result['json_data'])}")
                        except:
                            result['json_data'] = None
                            
                    # 如果是HTML响应，检查是否包含博客数据
                    elif 'text/html' in response.headers.get('content-type', ''):
                        soup = BeautifulSoup(response.text, 'html.parser')
                        if soup.find_all(['article', '.blog-post', '.post']):
                            print(f"      包含博客结构元素")
                            result['has_blog_structure'] = True
                            
                else:
                    print(f"   ❌ 失败: {response.status_code}")
                
                api_results.append(result)
                
            except requests.exceptions.RequestException as e:
                print(f"   ⚠️  请求错误: {e}")
                api_results.append({
                    'url': full_url,
                    'error': str(e)
                })
            
            time.sleep(0.5)  # 避免请求过快
        
        return api_results
    
    def analyze_blog_page_patterns(self):
        """分析博客页面的分页和加载模式"""
        print("\n📄 分析博客页面模式...")
        
        blog_url = "https://huggingface.co/blog/zh"
        analysis = self.analyze_page_structure(blog_url)
        
        if not analysis:
            return None
        
        # 查找分页相关的模式
        pagination_patterns = []
        
        # 检查URL中的分页参数
        for link in analysis.get('links', []):
            href = link['href']
            if any(param in href for param in ['page=', 'offset=', 'cursor=', 'skip=', 'limit=']):
                pagination_patterns.append({
                    'type': 'url_parameter',
                    'url': href,
                    'text': link['text']
                })
        
        # 检查API hints中的分页
        for hint in analysis.get('api_hints', []):
            if any(param in hint for param in ['page', 'offset', 'cursor', 'limit']):
                pagination_patterns.append({
                    'type': 'api_hint',
                    'url': hint
                })
        
        analysis['pagination_patterns'] = pagination_patterns
        
        return analysis
    
    def generate_comprehensive_report(self):
        """生成综合分析报告"""
        print("\n" + "="*80)
        print("📊 HUGGING FACE 博客综合网络分析报告")
        print("="*80)
        
        # 1. 分析主页面
        print("\n1️⃣ 主页面分析")
        main_analysis = self.analyze_blog_page_patterns()
        
        if main_analysis:
            print(f"   页面标题: {main_analysis.get('page_title', 'N/A')}")
            print(f"   状态码: {main_analysis.get('status_code', 'N/A')}")
            print(f"   发现的链接数量: {len(main_analysis.get('links', []))}")
            print(f"   内嵌JSON数据: {len(main_analysis.get('json_data', []))} 个")
            print(f"   API提示: {len(main_analysis.get('api_hints', []))} 个")
            
            if main_analysis.get('api_hints'):
                print("\n   🔍 发现的API提示:")
                for i, hint in enumerate(main_analysis['api_hints'][:5], 1):
                    print(f"      {i}. {hint}")
            
            if main_analysis.get('pagination_patterns'):
                print("\n   📄 分页模式:")
                for pattern in main_analysis['pagination_patterns'][:3]:
                    print(f"      {pattern['type']}: {pattern.get('url', 'N/A')}")
        
        # 2. 测试API端点
        print("\n2️⃣ API端点测试")
        api_results = self.test_api_endpoints()
        
        successful_apis = [r for r in api_results if r.get('status_code') == 200]
        print(f"   成功的端点: {len(successful_apis)}/{len(api_results)}")
        
        if successful_apis:
            print("\n   ✅ 可用的API端点:")
            for api in successful_apis:
                print(f"      {api['url']} - {api.get('content_type', 'unknown')}")
                if api.get('json_data'):
                    print(f"         返回JSON数据: {type(api['json_data'])}")
        
        # 3. 分析一篇具体文章
        print("\n3️⃣ 文章详情页分析")
        if main_analysis and main_analysis.get('links'):
            first_article = main_analysis['links'][0]['href']
            print(f"   分析文章: {first_article}")
            
            article_analysis = self.analyze_page_structure(first_article)
            if article_analysis:
                print(f"   文章标题: {article_analysis.get('page_title', 'N/A')}")
                print(f"   内嵌数据: {len(article_analysis.get('json_data', []))} 个")
                print(f"   API提示: {len(article_analysis.get('api_hints', []))} 个")
        
        # 4. 生成最终建议
        print("\n4️⃣ 数据获取建议")
        
        has_working_api = len(successful_apis) > 0
        has_json_data = main_analysis and len(main_analysis.get('json_data', [])) > 0
        has_api_hints = main_analysis and len(main_analysis.get('api_hints', [])) > 0
        
        if has_working_api:
            print("   ✅ 发现可用的API端点，建议优先使用API方式")
            print("   📋 API使用方案:")
            for api in successful_apis:
                if api.get('json_data'):
                    print(f"      - 使用 {api['url']} 获取JSON数据")
                    print(f"        响应类型: {type(api['json_data'])}")
        elif has_json_data:
            print("   📄 页面包含内嵌JSON数据，建议解析页面中的数据")
            print("   📋 页面解析方案:")
            print("      - 请求HTML页面")
            print("      - 提取script标签中的JSON数据")
            print("      - 解析数据结构获取博客信息")
        elif has_api_hints:
            print("   🔍 发现API提示但需要进一步测试")
            print("   📋 进一步调查方案:")
            print("      - 使用浏览器开发者工具监控实际请求")
            print("      - 测试发现的API提示URL")
        else:
            print("   📄 建议使用传统HTML解析方式")
            print("   📋 HTML解析方案:")
            print("      - 请求博客列表页面")
            print("      - 使用BeautifulSoup解析文章链接")
            print("      - 逐个请求文章详情页面")
        
        # 5. 保存详细报告
        report_data = {
            'analysis_time': time.strftime('%Y-%m-%d %H:%M:%S'),
            'main_page_analysis': main_analysis,
            'api_test_results': api_results,
            'successful_apis': successful_apis,
            'recommendations': {
                'has_working_api': has_working_api,
                'has_json_data': has_json_data,
                'has_api_hints': has_api_hints,
                'recommended_approach': 'api' if has_working_api else ('json_parsing' if has_json_data else 'html_parsing')
            }
        }
        
        with open('/home/shan/Huggingface_blog/comprehensive_analysis_report.json', 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"\n💾 详细报告已保存到: /home/shan/Huggingface_blog/comprehensive_analysis_report.json")
        
        return report_data

def main():
    analyzer = HuggingFaceAnalyzer()
    report = analyzer.generate_comprehensive_report()
    
    print("\n🎯 总结:")
    recommended = report['recommendations']['recommended_approach']
    if recommended == 'api':
        print("   推荐使用API方式获取数据")
    elif recommended == 'json_parsing':
        print("   推荐解析页面内嵌JSON数据")
    else:
        print("   推荐使用传统HTML解析方式")

if __name__ == "__main__":
    main()