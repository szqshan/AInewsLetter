#!/usr/bin/env python3
"""
Stability AI网站页面结构分析工具
"""

import json
import asyncio
from playwright.async_api import async_playwright
from pathlib import Path
import time

class StabilityPageAnalyzer:
    def __init__(self):
        self.base_url = "https://stability.ai"
        self.blog_url = "https://stability.ai/blog"
        self.results = {
            "page_info": {},
            "network_requests": [],
            "page_structure": {},
            "selectors": {}
        }
    
    async def analyze_blog_page(self):
        """分析博客列表页面"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            )
            page = await context.new_page()
            
            # 监听网络请求
            requests = []
            page.on("request", lambda request: requests.append({
                "url": request.url,
                "method": request.method,
                "resource_type": request.resource_type
            }))
            
            try:
                print(f"正在访问 {self.blog_url}...")
                await page.goto(self.blog_url, wait_until="networkidle")
                await page.wait_for_timeout(3000)  # 等待页面完全加载
                
                # 获取页面基本信息
                title = await page.title()
                url = page.url
                
                self.results["page_info"] = {
                    "title": title,
                    "url": url,
                    "timestamp": time.time()
                }
                
                print(f"页面标题: {title}")
                print(f"页面URL: {url}")
                
                # 分析页面结构
                await self.analyze_page_structure(page)
                
                # 分析文章列表
                await self.analyze_article_list(page)
                
                # 保存网络请求
                self.results["network_requests"] = requests[:50]  # 保存前50个请求
                
                # 截图保存
                await page.screenshot(path="blog_page_screenshot.png", full_page=True)
                print("已保存页面截图: blog_page_screenshot.png")
                
            except Exception as e:
                print(f"分析博客页面时出错: {e}")
            
            finally:
                await browser.close()
    
    async def analyze_page_structure(self, page):
        """分析页面整体结构"""
        try:
            # 获取主要容器结构
            structure_js = """
            () => {
                const structure = {};
                
                // 查找主要容器
                const containers = ['main', 'article', '.blog', '.content', '#content'];
                containers.forEach(selector => {
                    const element = document.querySelector(selector);
                    if (element) {
                        structure[selector] = {
                            exists: true,
                            className: element.className,
                            id: element.id,
                            children_count: element.children.length
                        };
                    }
                });
                
                // 查找导航
                const nav = document.querySelector('nav') || document.querySelector('.nav');
                if (nav) {
                    structure.navigation = {
                        className: nav.className,
                        links_count: nav.querySelectorAll('a').length
                    };
                }
                
                return structure;
            }
            """
            
            structure = await page.evaluate(structure_js)
            self.results["page_structure"] = structure
            print("页面结构分析完成")
            
        except Exception as e:
            print(f"分析页面结构时出错: {e}")
    
    async def analyze_article_list(self, page):
        """分析文章列表结构"""
        try:
            # 查找文章列表的各种可能选择器
            selectors_to_test = [
                "article",
                ".blog-post",
                ".post",
                "[data-testid*='post']",
                "[class*='blog']",
                "[class*='article']",
                ".card",
                "[href*='/blog/']"
            ]
            
            articles_info = []
            
            for selector in selectors_to_test:
                try:
                    elements = await page.query_selector_all(selector)
                    if elements:
                        print(f"找到 {len(elements)} 个元素匹配选择器: {selector}")
                        
                        # 分析前几个元素的结构
                        for i, element in enumerate(elements[:3]):
                            element_info = await element.evaluate("""
                                element => ({
                                    tagName: element.tagName,
                                    className: element.className,
                                    innerHTML_length: element.innerHTML.length,
                                    text_content: element.textContent.substring(0, 100),
                                    has_link: !!element.querySelector('a'),
                                    has_image: !!element.querySelector('img'),
                                    link_href: element.querySelector('a')?.href,
                                    image_src: element.querySelector('img')?.src
                                })
                            """)
                            
                            articles_info.append({
                                "selector": selector,
                                "index": i,
                                "info": element_info
                            })
                
                except Exception as e:
                    print(f"测试选择器 {selector} 时出错: {e}")
            
            self.results["selectors"]["articles"] = articles_info
            
            # 尝试提取文章链接
            await self.extract_article_links(page)
            
        except Exception as e:
            print(f"分析文章列表时出错: {e}")
    
    async def extract_article_links(self, page):
        """提取文章链接"""
        try:
            links_js = """
            () => {
                const links = [];
                const linkElements = document.querySelectorAll('a[href*="/blog/"], a[href*="/news/"], a[href*="/article/"]');
                
                linkElements.forEach((link, index) => {
                    if (index < 10) {  // 只取前10个
                        links.push({
                            href: link.href,
                            text: link.textContent.trim().substring(0, 100),
                            className: link.className,
                            parent_tag: link.parentElement.tagName,
                            parent_class: link.parentElement.className
                        });
                    }
                });
                
                return links;
            }
            """
            
            links = await page.evaluate(links_js)
            self.results["selectors"]["article_links"] = links
            
            print(f"找到 {len(links)} 个文章链接")
            for link in links[:5]:
                print(f"  - {link['text'][:50]}... -> {link['href']}")
            
        except Exception as e:
            print(f"提取文章链接时出错: {e}")
    
    async def analyze_single_article(self, article_url):
        """分析单篇文章页面"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            )
            page = await context.new_page()
            
            try:
                print(f"正在分析文章页面: {article_url}")
                await page.goto(article_url, wait_until="networkidle")
                await page.wait_for_timeout(2000)
                
                # 分析文章结构
                article_structure = await page.evaluate("""
                () => {
                    const structure = {};
                    
                    // 查找标题
                    const titleSelectors = ['h1', '.title', '[class*="title"]', '.headline'];
                    titleSelectors.forEach(selector => {
                        const element = document.querySelector(selector);
                        if (element && element.textContent.trim()) {
                            structure.title = {
                                selector: selector,
                                text: element.textContent.trim(),
                                className: element.className
                            };
                        }
                    });
                    
                    // 查找正文内容
                    const contentSelectors = ['.content', '.article-content', '.post-content', 'article', 'main'];
                    contentSelectors.forEach(selector => {
                        const element = document.querySelector(selector);
                        if (element) {
                            structure.content = {
                                selector: selector,
                                text_length: element.textContent.length,
                                html_length: element.innerHTML.length,
                                className: element.className,
                                paragraphs_count: element.querySelectorAll('p').length,
                                images_count: element.querySelectorAll('img').length
                            };
                        }
                    });
                    
                    // 查找图片
                    const images = Array.from(document.querySelectorAll('img')).map(img => ({
                        src: img.src,
                        alt: img.alt,
                        className: img.className,
                        parent_tag: img.parentElement.tagName
                    }));
                    
                    structure.images = images.slice(0, 10);  // 前10张图片
                    
                    // 查找发布日期
                    const dateSelectors = ['.date', '.published', '[datetime]', '.timestamp'];
                    dateSelectors.forEach(selector => {
                        const element = document.querySelector(selector);
                        if (element) {
                            structure.date = {
                                selector: selector,
                                text: element.textContent.trim(),
                                datetime: element.getAttribute('datetime')
                            };
                        }
                    });
                    
                    return structure;
                }
                """)
                
                self.results["article_structure"] = article_structure
                
                # 截图保存
                await page.screenshot(path="article_page_screenshot.png", full_page=True)
                print("已保存文章页面截图: article_page_screenshot.png")
                
            except Exception as e:
                print(f"分析文章页面时出错: {e}")
            
            finally:
                await browser.close()
    
    def save_results(self):
        """保存分析结果"""
        output_file = "stability_analysis_results.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        print(f"分析结果已保存到: {output_file}")
    
    def print_summary(self):
        """打印分析摘要"""
        print("\n" + "="*50)
        print("Stability AI 网站分析摘要")
        print("="*50)
        
        if "page_info" in self.results:
            print(f"页面标题: {self.results['page_info'].get('title', 'Unknown')}")
            print(f"页面URL: {self.results['page_info'].get('url', 'Unknown')}")
        
        if "network_requests" in self.results:
            api_requests = [r for r in self.results["network_requests"] if r["resource_type"] in ["xhr", "fetch"]]
            print(f"网络请求总数: {len(self.results['network_requests'])}")
            print(f"API请求数: {len(api_requests)}")
            
            if api_requests:
                print("发现的API请求:")
                for req in api_requests[:5]:
                    print(f"  - {req['method']} {req['url']}")
        
        if "selectors" in self.results and "article_links" in self.results["selectors"]:
            links = self.results["selectors"]["article_links"]
            print(f"找到文章链接数: {len(links)}")

async def main():
    analyzer = StabilityPageAnalyzer()
    
    print("开始分析Stability AI博客页面...")
    await analyzer.analyze_blog_page()
    
    # 如果找到文章链接，分析第一篇文章
    if analyzer.results.get("selectors", {}).get("article_links"):
        first_article = analyzer.results["selectors"]["article_links"][0]
        if first_article["href"]:
            print(f"\n开始分析第一篇文章: {first_article['href']}")
            await analyzer.analyze_single_article(first_article["href"])
    
    analyzer.save_results()
    analyzer.print_summary()

if __name__ == "__main__":
    asyncio.run(main())