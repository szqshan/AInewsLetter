#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
from bs4 import BeautifulSoup
import json
from urllib.parse import urljoin, urlparse

class StabilityDiscovery:
    def __init__(self):
        self.base_url = "https://stability.ai"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
    def discover_site_structure(self):
        """Discover the actual site structure"""
        print("Discovering Stability AI site structure...")
        
        try:
            # First, check the main page
            response = self.session.get(self.base_url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            print(f"Main page title: {soup.title.string if soup.title else 'No title'}")
            print(f"Status code: {response.status_code}")
            
            # Find all navigation links
            nav_links = self.find_navigation_links(soup)
            
            # Try common blog/news URLs
            potential_blog_urls = [
                '/blog',
                '/news', 
                '/articles',
                '/posts',
                '/blog/',
                '/news/',
                '/research',
                '/updates'
            ]
            
            working_urls = []
            
            for path in potential_blog_urls:
                test_url = urljoin(self.base_url, path)
                if self.test_url(test_url):
                    working_urls.append(test_url)
            
            print(f"\nWorking blog/news URLs found: {len(working_urls)}")
            for url in working_urls:
                print(f"  - {url}")
            
            # Check navigation links for blog-like pages
            blog_nav_links = []
            for link in nav_links:
                if any(keyword in link['text'].lower() for keyword in ['blog', 'news', 'article', 'post', 'research', 'update']):
                    blog_nav_links.append(link)
            
            print(f"\nBlog-related navigation links: {len(blog_nav_links)}")
            for link in blog_nav_links:
                print(f"  - {link['text']}: {link['url']}")
            
            return {
                'main_page': {
                    'title': soup.title.string if soup.title else 'No title',
                    'url': response.url
                },
                'working_blog_urls': working_urls,
                'blog_nav_links': blog_nav_links,
                'all_nav_links': nav_links[:20]  # First 20 nav links
            }
            
        except Exception as e:
            print(f"Error discovering site structure: {e}")
            return None
    
    def find_navigation_links(self, soup):
        """Find all navigation links"""
        links = []
        
        # Look in navigation elements
        nav_selectors = ['nav a', '.nav a', '.navigation a', 'header a', '.menu a']
        
        for selector in nav_selectors:
            elements = soup.select(selector)
            for elem in elements:
                href = elem.get('href', '')
                text = elem.get_text(strip=True)
                
                if href and text:
                    full_url = urljoin(self.base_url, href)
                    links.append({
                        'url': full_url,
                        'text': text,
                        'selector': selector
                    })
        
        # Remove duplicates
        unique_links = []
        seen = set()
        for link in links:
            key = (link['url'], link['text'])
            if key not in seen:
                unique_links.append(link)
                seen.add(key)
        
        return unique_links
    
    def test_url(self, url):
        """Test if a URL is accessible"""
        try:
            response = self.session.head(url, timeout=10)
            return response.status_code == 200
        except:
            return False
    
    def analyze_specific_page(self, url):
        """Analyze a specific page for content"""
        print(f"\nAnalyzing page: {url}")
        
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for article-like content
            article_links = []
            link_selectors = [
                'a[href*="article"]',
                'a[href*="post"]', 
                'a[href*="blog"]',
                'a[href*="news"]',
                'article a',
                '.post a',
                '.article a'
            ]
            
            for selector in link_selectors:
                elements = soup.select(selector)
                if elements:
                    print(f"  Found {len(elements)} links with selector: {selector}")
                    
                    for elem in elements[:5]:  # First 5
                        href = elem.get('href', '')
                        text = elem.get_text(strip=True)[:50]
                        
                        if href:
                            full_url = urljoin(url, href)
                            article_links.append({
                                'url': full_url,
                                'text': text,
                                'selector': selector
                            })
            
            # Look for content structure
            content_elements = {
                'articles': len(soup.select('article')),
                'posts': len(soup.select('.post, .blog-post')),
                'cards': len(soup.select('.card')),
                'items': len(soup.select('.item')),
                'entries': len(soup.select('.entry'))
            }
            
            print(f"  Content elements found: {content_elements}")
            
            return {
                'url': url,
                'title': soup.title.string if soup.title else 'No title',
                'article_links': article_links[:10],
                'content_elements': content_elements
            }
            
        except Exception as e:
            print(f"  Error analyzing {url}: {e}")
            return None

def main():
    discovery = StabilityDiscovery()
    
    # Discover site structure
    structure = discovery.discover_site_structure()
    
    if structure:
        # Analyze any working blog URLs we found
        page_analyses = []
        
        for url in structure.get('working_blog_urls', []):
            analysis = discovery.analyze_specific_page(url)
            if analysis:
                page_analyses.append(analysis)
        
        # Also analyze nav link pages that might be blogs
        for link in structure.get('blog_nav_links', [])[:3]:  # First 3
            analysis = discovery.analyze_specific_page(link['url'])
            if analysis:
                page_analyses.append(analysis)
        
        # Save results
        results = {
            'discovery': structure,
            'page_analyses': page_analyses
        }
        
        with open('stability_discovery.json', 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"\n" + "="*60)
        print("DISCOVERY SUMMARY")
        print("="*60)
        
        print(f"Main site: {structure['main_page']['url']}")
        print(f"Working blog URLs: {len(structure['working_blog_urls'])}")
        print(f"Blog navigation links: {len(structure['blog_nav_links'])}")
        
        for analysis in page_analyses:
            if analysis['article_links']:
                print(f"\nPage: {analysis['url']}")
                print(f"  Title: {analysis['title']}")
                print(f"  Article links found: {len(analysis['article_links'])}")
                
                for link in analysis['article_links'][:3]:
                    print(f"    - {link['text']}")
        
        print(f"\nResults saved to: stability_discovery.json")
    
    else:
        print("Failed to discover site structure")

if __name__ == "__main__":
    main()