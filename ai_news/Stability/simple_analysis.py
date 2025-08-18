#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
from bs4 import BeautifulSoup
import json
import time
from urllib.parse import urljoin, urlparse

class StabilityAnalyzer:
    def __init__(self):
        self.base_url = "https://stability.ai"
        self.blog_url = "https://stability.ai/blog"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.results = {}
    
    def analyze_blog_page(self):
        """Analyze blog listing page"""
        print("Analyzing Stability AI blog page...")
        
        try:
            response = self.session.get(self.blog_url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Basic page info
            self.results['page_info'] = {
                'title': soup.title.string if soup.title else 'No title',
                'url': response.url,
                'status_code': response.status_code
            }
            
            print(f"Page title: {self.results['page_info']['title']}")
            print(f"Status code: {response.status_code}")
            
            # Find article links
            article_links = self.find_article_links(soup)
            self.results['article_links'] = article_links
            
            # Analyze page structure
            structure = self.analyze_structure(soup)
            self.results['page_structure'] = structure
            
            return True
            
        except Exception as e:
            print(f"Error analyzing blog page: {e}")
            return False
    
    def find_article_links(self, soup):
        """Find article links on the page"""
        links = []
        
        # Try different selectors for article links
        selectors = [
            'a[href*="/blog/"]',
            'a[href*="/news/"]', 
            'a[href*="/article/"]',
            'article a',
            '.blog-post a',
            '.post a'
        ]
        
        for selector in selectors:
            elements = soup.select(selector)
            if elements:
                print(f"Found {len(elements)} links with selector: {selector}")
                
                for elem in elements[:10]:  # First 10 links
                    href = elem.get('href', '')
                    if href:
                        full_url = urljoin(self.base_url, href)
                        text = elem.get_text(strip=True)[:100]
                        
                        links.append({
                            'url': full_url,
                            'text': text,
                            'selector': selector,
                            'classes': elem.get('class', [])
                        })
        
        # Remove duplicates
        unique_links = []
        seen_urls = set()
        for link in links:
            if link['url'] not in seen_urls:
                unique_links.append(link)
                seen_urls.add(link['url'])
        
        print(f"Found {len(unique_links)} unique article links")
        return unique_links[:10]  # Return first 10
    
    def analyze_structure(self, soup):
        """Analyze page structure"""
        structure = {}
        
        # Check for main containers
        containers = ['main', 'article', '.content', '#content', '.blog', '.posts']
        for container in containers:
            elem = soup.select_one(container)
            if elem:
                structure[container] = {
                    'found': True,
                    'class': elem.get('class', []),
                    'id': elem.get('id', ''),
                    'children_count': len(elem.find_all())
                }
        
        # Look for common blog elements
        blog_elements = {
            'nav': soup.select_one('nav'),
            'header': soup.select_one('header'),
            'footer': soup.select_one('footer'),
            'sidebar': soup.select_one('aside, .sidebar'),
            'articles': soup.select('article'),
            'blog_posts': soup.select('.blog-post, .post')
        }
        
        for name, elem in blog_elements.items():
            if elem:
                if isinstance(elem, list):
                    structure[name] = {'count': len(elem)}
                else:
                    structure[name] = {
                        'found': True,
                        'class': elem.get('class', []),
                        'id': elem.get('id', '')
                    }
        
        return structure
    
    def analyze_article_page(self, article_url):
        """Analyze a single article page"""
        print(f"Analyzing article: {article_url}")
        
        try:
            response = self.session.get(article_url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            article_data = {
                'url': article_url,
                'title': self.extract_title(soup),
                'content_info': self.analyze_content(soup),
                'images': self.find_images(soup),
                'meta_info': self.extract_meta_info(soup)
            }
            
            return article_data
            
        except Exception as e:
            print(f"Error analyzing article {article_url}: {e}")
            return None
    
    def extract_title(self, soup):
        """Extract article title"""
        title_selectors = [
            'h1',
            '.title',
            '.article-title',
            '.post-title',
            '[class*="title"]'
        ]
        
        for selector in title_selectors:
            elem = soup.select_one(selector)
            if elem and elem.get_text(strip=True):
                return {
                    'text': elem.get_text(strip=True),
                    'selector': selector,
                    'class': elem.get('class', [])
                }
        
        return {'text': soup.title.string if soup.title else 'No title found'}
    
    def analyze_content(self, soup):
        """Analyze content structure"""
        content_selectors = [
            '.content',
            '.article-content', 
            '.post-content',
            'article',
            'main',
            '.entry-content'
        ]
        
        content_info = {}
        
        for selector in content_selectors:
            elem = soup.select_one(selector)
            if elem:
                text = elem.get_text(strip=True)
                content_info[selector] = {
                    'text_length': len(text),
                    'paragraph_count': len(elem.find_all('p')),
                    'image_count': len(elem.find_all('img')),
                    'link_count': len(elem.find_all('a')),
                    'class': elem.get('class', [])
                }
        
        return content_info
    
    def find_images(self, soup):
        """Find images in the article"""
        images = []
        img_elements = soup.find_all('img')
        
        for img in img_elements[:10]:  # First 10 images
            src = img.get('src', '')
            if src:
                images.append({
                    'src': urljoin(self.base_url, src),
                    'alt': img.get('alt', ''),
                    'class': img.get('class', []),
                    'parent_tag': img.parent.name if img.parent else ''
                })
        
        return images
    
    def extract_meta_info(self, soup):
        """Extract meta information like date, author, etc."""
        meta_info = {}
        
        # Look for date information
        date_selectors = [
            '.date',
            '.published',
            '.post-date',
            '[datetime]',
            'time'
        ]
        
        for selector in date_selectors:
            elem = soup.select_one(selector)
            if elem:
                meta_info['date'] = {
                    'text': elem.get_text(strip=True),
                    'datetime': elem.get('datetime', ''),
                    'selector': selector
                }
                break
        
        # Look for author
        author_selectors = [
            '.author',
            '.by-author',
            '[rel="author"]'
        ]
        
        for selector in author_selectors:
            elem = soup.select_one(selector)
            if elem:
                meta_info['author'] = {
                    'text': elem.get_text(strip=True),
                    'selector': selector
                }
                break
        
        return meta_info
    
    def save_results(self):
        """Save analysis results to JSON file"""
        with open('stability_analysis.json', 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        print("Analysis results saved to: stability_analysis.json")
    
    def print_summary(self):
        """Print analysis summary"""
        print("\n" + "="*60)
        print("STABILITY AI WEBSITE ANALYSIS SUMMARY")
        print("="*60)
        
        if 'page_info' in self.results:
            print(f"Page Title: {self.results['page_info']['title']}")
            print(f"Page URL: {self.results['page_info']['url']}")
        
        if 'article_links' in self.results:
            links = self.results['article_links']
            print(f"\nFound {len(links)} article links:")
            for i, link in enumerate(links[:5], 1):
                print(f"  {i}. {link['text'][:50]}...")
                print(f"     URL: {link['url']}")
        
        if 'page_structure' in self.results:
            structure = self.results['page_structure']
            print(f"\nPage Structure:")
            for element, info in structure.items():
                if isinstance(info, dict) and info.get('found'):
                    print(f"  - {element}: Found")
                elif isinstance(info, dict) and 'count' in info:
                    print(f"  - {element}: {info['count']} elements")
        
        if 'sample_article' in self.results:
            article = self.results['sample_article']
            print(f"\nSample Article Analysis:")
            print(f"  Title: {article.get('title', {}).get('text', 'N/A')}")
            print(f"  Images: {len(article.get('images', []))}")
            if 'content_info' in article:
                for selector, info in article['content_info'].items():
                    print(f"  Content ({selector}): {info['text_length']} chars, {info['paragraph_count']} paragraphs")
                    break

def main():
    analyzer = StabilityAnalyzer()
    
    # Analyze blog page
    if analyzer.analyze_blog_page():
        
        # If we found articles, analyze the first one
        if analyzer.results.get('article_links'):
            first_article_url = analyzer.results['article_links'][0]['url']
            sample_article = analyzer.analyze_article_page(first_article_url)
            if sample_article:
                analyzer.results['sample_article'] = sample_article
        
        # Save and print results
        analyzer.save_results()
        analyzer.print_summary()
    else:
        print("Failed to analyze the blog page")

if __name__ == "__main__":
    main()