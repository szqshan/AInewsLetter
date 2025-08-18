#!/usr/bin/env python3
"""
Hugging Face Blog Network Analysis Tool
使用Playwright监控和分析网络请求
"""

import asyncio
import json
import re
from datetime import datetime
from urllib.parse import urlparse, parse_qs
from playwright.async_api import async_playwright

class NetworkAnalyzer:
    def __init__(self):
        self.requests = []
        self.responses = []
        self.api_endpoints = []
        self.xhr_requests = []
        
    def parse_request(self, request):
        """解析请求信息"""
        url_parts = urlparse(request.url)
        
        request_info = {
            'timestamp': datetime.now().isoformat(),
            'method': request.method,
            'url': request.url,
            'domain': url_parts.netloc,
            'path': url_parts.path,
            'query_params': parse_qs(url_parts.query),
            'headers': dict(request.headers),
            'resource_type': request.resource_type,
            'post_data': request.post_data if request.post_data else None
        }
        
        return request_info
    
    async def parse_response(self, response):
        """解析响应信息"""
        try:
            content_type = response.headers.get('content-type', '')
            
            response_info = {
                'url': response.url,
                'status': response.status,
                'headers': dict(response.headers),
                'content_type': content_type,
                'size': len(await response.body()) if response.ok else 0
            }
            
            # 如果是JSON响应，尝试解析内容
            if 'application/json' in content_type and response.ok:
                try:
                    response_info['json_data'] = await response.json()
                except:
                    response_info['json_data'] = None
            
            return response_info
        except Exception as e:
            return {
                'url': response.url,
                'status': response.status,
                'error': str(e)
            }
    
    def is_api_request(self, request_info):
        """判断是否为API请求"""
        # 检查URL特征
        url = request_info['url'].lower()
        path = request_info['path'].lower()
        
        api_indicators = [
            '/api/',
            'application/json' in request_info['headers'].get('accept', '').lower(),
            request_info['resource_type'] in ['xhr', 'fetch'],
            'json' in path,
            'graphql' in path,
        ]
        
        return any(api_indicators)

async def analyze_huggingface_blog():
    """分析Hugging Face博客的网络请求"""
    analyzer = NetworkAnalyzer()
    
    async with async_playwright() as p:
        # 启动浏览器
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        
        # 设置网络监听器
        def handle_request(request):
            request_info = analyzer.parse_request(request)
            analyzer.requests.append(request_info)
            
            if analyzer.is_api_request(request_info):
                analyzer.api_endpoints.append(request_info)
                print(f"🔍 发现API请求: {request.method} {request.url}")
        
        async def handle_response(response):
            response_info = await analyzer.parse_response(response)
            analyzer.responses.append(response_info)
            
            # 如果是API响应，打印详细信息
            for req in analyzer.api_endpoints:
                if req['url'] == response.url:
                    print(f"📊 API响应: {response.status} - {response.url}")
                    if response_info.get('json_data'):
                        print(f"   JSON数据类型: {type(response_info['json_data'])}")
                        if isinstance(response_info['json_data'], dict):
                            print(f"   JSON键: {list(response_info['json_data'].keys())}")
        
        page.on("request", handle_request)
        page.on("response", handle_response)
        
        print("🚀 开始分析Hugging Face博客页面...")
        
        # 1. 访问主页面
        print("\n📖 1. 访问博客主页...")
        await page.goto("https://huggingface.co/blog/zh", wait_until="networkidle")
        await page.wait_for_timeout(3000)
        
        # 2. 等待页面完全加载并尝试找到分页元素
        print("\n🔄 2. 查找分页元素...")
        try:
            # 查找分页按钮或链接
            pagination_selectors = [
                'a[href*="page"]',
                'button[aria-label*="next"]',
                'a[aria-label*="next"]',
                '.pagination a',
                '[class*="pagination"] a',
                'a[href*="offset"]',
                'a[href*="cursor"]'
            ]
            
            pagination_found = False
            for selector in pagination_selectors:
                elements = await page.query_selector_all(selector)
                if elements:
                    print(f"   找到分页元素: {selector}")
                    pagination_found = True
                    break
            
            if not pagination_found:
                print("   未找到明显的分页元素，检查滚动加载...")
                # 尝试滚动看是否有懒加载
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await page.wait_for_timeout(2000)
                
        except Exception as e:
            print(f"   分页检查出错: {e}")
        
        # 3. 点击进入一篇文章
        print("\n📰 3. 进入文章详情页...")
        try:
            # 查找文章链接
            article_selectors = [
                'a[href*="/blog/"]',
                'article a',
                '.blog-post a',
                'h2 a',
                'h3 a'
            ]
            
            article_link = None
            for selector in article_selectors:
                links = await page.query_selector_all(selector)
                for link in links:
                    href = await link.get_attribute('href')
                    if href and '/blog/' in href and href != '/blog/zh':
                        article_link = link
                        break
                if article_link:
                    break
            
            if article_link:
                href = await article_link.get_attribute('href')
                print(f"   点击文章: {href}")
                await article_link.click()
                await page.wait_for_load_state("networkidle")
                await page.wait_for_timeout(2000)
            else:
                print("   未找到文章链接")
                
        except Exception as e:
            print(f"   进入文章详情页出错: {e}")
        
        # 4. 分析Console日志
        print("\n🔍 4. 检查页面控制台...")
        logs = []
        
        def handle_console(msg):
            logs.append({
                'type': msg.type,
                'text': msg.text,
                'location': msg.location
            })
        
        page.on("console", handle_console)
        await page.wait_for_timeout(1000)
        
        # 5. 执行一些JavaScript来获取更多信息
        print("\n🔬 5. 执行页面分析脚本...")
        page_info = await page.evaluate("""
            () => {
                const info = {
                    url: window.location.href,
                    title: document.title,
                    meta_tags: [],
                    scripts: [],
                    api_related_elements: []
                };
                
                // 获取meta标签
                document.querySelectorAll('meta').forEach(meta => {
                    info.meta_tags.push({
                        name: meta.name || meta.property,
                        content: meta.content
                    });
                });
                
                // 获取script标签
                document.querySelectorAll('script[src]').forEach(script => {
                    info.scripts.push(script.src);
                });
                
                // 查找可能的API相关元素
                const apiElements = document.querySelectorAll('[data-api], [data-endpoint], [data-graphql]');
                apiElements.forEach(el => {
                    info.api_related_elements.push({
                        tagName: el.tagName,
                        attributes: Object.fromEntries([...el.attributes].map(attr => [attr.name, attr.value]))
                    });
                });
                
                return info;
            }
        """)
        
        await browser.close()
        
        # 生成分析报告
        await generate_analysis_report(analyzer, page_info, logs)

async def generate_analysis_report(analyzer, page_info, logs):
    """生成详细的分析报告"""
    
    report = {
        'analysis_time': datetime.now().isoformat(),
        'summary': {
            'total_requests': len(analyzer.requests),
            'total_responses': len(analyzer.responses),
            'api_requests': len(analyzer.api_endpoints),
            'page_info': page_info
        },
        'api_endpoints': [],
        'network_patterns': {},
        'recommendations': []
    }
    
    print("\n" + "="*80)
    print("📊 HUGGING FACE 博客网络分析报告")
    print("="*80)
    
    print(f"\n📈 统计概览:")
    print(f"   总请求数: {report['summary']['total_requests']}")
    print(f"   总响应数: {report['summary']['total_responses']}")
    print(f"   API请求数: {report['summary']['api_requests']}")
    print(f"   当前页面: {page_info['url']}")
    
    # 分析API端点
    print(f"\n🔍 发现的API端点:")
    if analyzer.api_endpoints:
        for api_req in analyzer.api_endpoints:
            print(f"\n   📡 {api_req['method']} {api_req['url']}")
            print(f"      域名: {api_req['domain']}")
            print(f"      路径: {api_req['path']}")
            print(f"      资源类型: {api_req['resource_type']}")
            
            if api_req['query_params']:
                print(f"      查询参数: {api_req['query_params']}")
            
            # 查找对应的响应
            for resp in analyzer.responses:
                if resp['url'] == api_req['url']:
                    print(f"      响应状态: {resp['status']}")
                    print(f"      内容类型: {resp.get('content_type', 'unknown')}")
                    if resp.get('json_data'):
                        print(f"      JSON数据结构: {type(resp['json_data'])}")
                        if isinstance(resp['json_data'], dict):
                            print(f"      JSON字段: {list(resp['json_data'].keys())[:10]}")
                    break
            
            report['api_endpoints'].append({
                'method': api_req['method'],
                'url': api_req['url'],
                'domain': api_req['domain'],
                'path': api_req['path'],
                'query_params': api_req['query_params'],
                'headers': api_req['headers']
            })
    else:
        print("   ⚠️  未发现明显的API端点")
    
    # 分析域名模式
    print(f"\n🌐 域名分析:")
    domains = {}
    for req in analyzer.requests:
        domain = req['domain']
        domains[domain] = domains.get(domain, 0) + 1
    
    for domain, count in sorted(domains.items(), key=lambda x: x[1], reverse=True):
        print(f"   {domain}: {count} 个请求")
    
    # 分析资源类型
    print(f"\n📁 资源类型分析:")
    resource_types = {}
    for req in analyzer.requests:
        res_type = req['resource_type']
        resource_types[res_type] = resource_types.get(res_type, 0) + 1
    
    for res_type, count in sorted(resource_types.items(), key=lambda x: x[1], reverse=True):
        print(f"   {res_type}: {count} 个请求")
    
    # 查找GraphQL相关请求
    print(f"\n🔍 GraphQL/特殊API检查:")
    graphql_found = False
    for req in analyzer.requests:
        if 'graphql' in req['url'].lower() or 'graphql' in req.get('post_data', '').lower():
            print(f"   发现GraphQL请求: {req['url']}")
            graphql_found = True
    
    if not graphql_found:
        print("   未发现GraphQL请求")
    
    # 分析可能的博客API模式
    print(f"\n📝 博客API模式分析:")
    blog_patterns = []
    for req in analyzer.requests:
        url = req['url']
        if any(pattern in url.lower() for pattern in ['blog', 'post', 'article', 'content']):
            blog_patterns.append(url)
    
    if blog_patterns:
        print("   发现可能的博客相关请求:")
        for pattern in blog_patterns[:10]:  # 显示前10个
            print(f"     {pattern}")
    else:
        print("   未发现明显的博客API模式")
    
    # 生成建议
    print(f"\n💡 分析建议:")
    
    if len(analyzer.api_endpoints) == 0:
        print("   1. 该网站可能主要使用服务端渲染(SSR)")
        print("   2. 建议使用HTML解析方式获取博客内容")
        print("   3. 可以尝试查看页面源码中的内嵌JSON数据")
        report['recommendations'].extend([
            "使用HTML解析方式",
            "检查页面内嵌JSON数据",
            "考虑使用Playwright进行动态内容获取"
        ])
    else:
        print("   1. 发现了API端点，可以考虑直接使用API")
        print("   2. 需要进一步测试API的稳定性和完整性")
        print("   3. 检查API是否需要特殊的认证或限流处理")
        report['recommendations'].extend([
            "优先使用发现的API端点",
            "测试API稳定性",
            "检查API认证要求"
        ])
    
    # 保存详细报告
    with open('/home/shan/Huggingface_blog/network_analysis_report.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 详细报告已保存到: /home/shan/Huggingface_blog/network_analysis_report.json")
    
    return report

if __name__ == "__main__":
    asyncio.run(analyze_huggingface_blog())