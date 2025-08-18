#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
from bs4 import BeautifulSoup
import json
from urllib.parse import urljoin

class DetailedStabilityAnalyzer:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def analyze_news_page(self):
        """Analyze the news listing page in detail"""
        url = "https://stability.ai/news"
        print(f"Analyzing news page: {url}")
        
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Analyze article list structure
            articles = soup.find_all('article')
            print(f"Found {len(articles)} article elements")
            
            article_data = []
            
            for i, article in enumerate(articles[:5]):  # First 5 articles
                data = self.extract_article_preview(article, i)
                if data:
                    article_data.append(data)
            
            return {
                'url': url,
                'total_articles': len(articles),
                'sample_articles': article_data,
                'page_structure': self.analyze_page_structure(soup)
            }
            
        except Exception as e:
            print(f"Error analyzing news page: {e}")
            return None
    
    def extract_article_preview(self, article, index):
        """Extract data from article preview element"""
        try:
            data = {'index': index}
            
            # Find title
            title_selectors = ['h1', 'h2', 'h3', '.title', '[class*="title"]']
            for selector in title_selectors:
                title_elem = article.select_one(selector)
                if title_elem and title_elem.get_text(strip=True):
                    data['title'] = {
                        'text': title_elem.get_text(strip=True),
                        'selector': selector,
                        'tag': title_elem.name,
                        'classes': title_elem.get('class', [])
                    }
                    break
            
            # Find link
            link_elem = article.find('a', href=True)
            if link_elem:
                data['link'] = {
                    'href': urljoin("https://stability.ai", link_elem['href']),
                    'text': link_elem.get_text(strip=True)[:50],
                    'classes': link_elem.get('class', [])
                }
            
            # Find date/time
            date_selectors = ['time', '.date', '.published', '[datetime]']
            for selector in date_selectors:
                date_elem = article.select_one(selector)
                if date_elem:
                    data['date'] = {
                        'text': date_elem.get_text(strip=True),
                        'datetime': date_elem.get('datetime', ''),
                        'selector': selector
                    }
                    break
            
            # Find summary/excerpt
            text_elements = article.find_all('p')
            if text_elements:
                summary_text = ' '.join([p.get_text(strip=True) for p in text_elements])
                data['summary'] = summary_text[:200] + "..." if len(summary_text) > 200 else summary_text
            
            # Find images
            images = article.find_all('img')
            if images:
                data['images'] = []
                for img in images[:3]:  # First 3 images
                    data['images'].append({
                        'src': urljoin("https://stability.ai", img.get('src', '')),
                        'alt': img.get('alt', ''),
                        'classes': img.get('class', [])
                    })
            
            # Article element structure
            data['element_info'] = {
                'classes': article.get('class', []),
                'id': article.get('id', ''),
                'children_count': len(article.find_all()),
                'text_length': len(article.get_text(strip=True))
            }
            
            return data
            
        except Exception as e:
            print(f"Error extracting article {index}: {e}")
            return None
    
    def analyze_page_structure(self, soup):
        """Analyze overall page structure"""
        structure = {}
        
        # Main containers
        main_containers = ['main', '.main', '#main', '.content', '.container']
        for container in main_containers:
            elem = soup.select_one(container)
            if elem:
                structure[container] = {
                    'found': True,
                    'classes': elem.get('class', []),
                    'children': len(elem.find_all())
                }
        
        # Navigation structure
        nav = soup.find('nav')
        if nav:
            nav_links = nav.find_all('a')
            structure['navigation'] = {
                'total_links': len(nav_links),
                'classes': nav.get('class', [])
            }
        
        # Check for pagination
        pagination_selectors = ['.pagination', '.pager', '[class*="page"]', 'nav[aria-label*="page"]']
        for selector in pagination_selectors:
            elem = soup.select_one(selector)
            if elem:
                structure['pagination'] = {
                    'selector': selector,
                    'classes': elem.get('class', []),
                    'links': len(elem.find_all('a'))
                }
                break
        
        return structure
    
    def analyze_single_article(self, article_url):
        """Analyze a single article page in detail"""
        print(f"Analyzing single article: {article_url}")
        
        try:
            response = self.session.get(article_url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            article_data = {
                'url': article_url,
                'title': self.extract_article_title(soup),
                'content': self.analyze_article_content(soup),
                'metadata': self.extract_article_metadata(soup),
                'images': self.extract_article_images(soup),
                'structure': self.analyze_article_structure(soup)
            }
            
            return article_data
            
        except Exception as e:
            print(f"Error analyzing article {article_url}: {e}")
            return None
    
    def extract_article_title(self, soup):
        """Extract article title with multiple fallbacks"""
        title_methods = [
            lambda: soup.select_one('h1'),
            lambda: soup.select_one('[class*="title"] h1'),
            lambda: soup.select_one('[class*="title"] h2'),
            lambda: soup.select_one('article h1'),
            lambda: soup.select_one('article h2'),
            lambda: soup.find('title')
        ]
        
        for method in title_methods:
            try:
                elem = method()
                if elem and elem.get_text(strip=True):
                    return {
                        'text': elem.get_text(strip=True),
                        'tag': elem.name,
                        'classes': elem.get('class', []),
                        'method': method.__name__ if hasattr(method, '__name__') else 'lambda'
                    }
            except:
                continue
        
        return {'text': 'Title not found'}
    
    def analyze_article_content(self, soup):
        """Analyze article content structure"""
        content_selectors = [
            '.content',
            '.article-content',
            '.post-content', 
            'article .content',
            'main article',
            '[class*="content"]'
        ]
        
        content_analysis = {}
        
        for selector in content_selectors:
            elem = soup.select_one(selector)
            if elem:
                text = elem.get_text(strip=True)
                content_analysis[selector] = {
                    'text_length': len(text),
                    'paragraphs': len(elem.find_all('p')),
                    'headings': len(elem.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])),
                    'lists': len(elem.find_all(['ul', 'ol'])),
                    'images': len(elem.find_all('img')),
                    'links': len(elem.find_all('a')),
                    'classes': elem.get('class', [])
                }
        
        return content_analysis
    
    def extract_article_metadata(self, soup):
        """Extract article metadata like date, author, tags"""
        metadata = {}
        
        # Date extraction
        date_selectors = [
            'time[datetime]',
            '.date',
            '.published',
            '.post-date',
            '[class*="date"]'
        ]
        
        for selector in date_selectors:
            elem = soup.select_one(selector)
            if elem:
                metadata['date'] = {
                    'text': elem.get_text(strip=True),
                    'datetime': elem.get('datetime', ''),
                    'selector': selector
                }
                break
        
        # Author extraction  
        author_selectors = [
            '.author',
            '.by-author',
            '[rel="author"]',
            '[class*="author"]'
        ]
        
        for selector in author_selectors:
            elem = soup.select_one(selector)
            if elem:
                metadata['author'] = {
                    'text': elem.get_text(strip=True),
                    'selector': selector
                }
                break
        
        # Tags/categories
        tag_selectors = [
            '.tags',
            '.categories',
            '.tag',
            '[class*="tag"]',
            '[class*="category"]'
        ]
        
        for selector in tag_selectors:
            elements = soup.select(selector)
            if elements:
                metadata['tags'] = [elem.get_text(strip=True) for elem in elements]
                break
        
        return metadata
    
    def extract_article_images(self, soup):
        """Extract all images from article"""
        images = []
        
        # Look for images in content areas
        content_areas = [
            soup.select_one('.content'),
            soup.select_one('article'),
            soup.select_one('main'),
            soup
        ]
        
        for area in content_areas:
            if area:
                img_elements = area.find_all('img')
                for img in img_elements:
                    src = img.get('src', '')
                    if src and not any(existing['src'] == src for existing in images):
                        images.append({
                            'src': urljoin("https://stability.ai", src),
                            'alt': img.get('alt', ''),
                            'title': img.get('title', ''),
                            'classes': img.get('class', []),
                            'parent_tag': img.parent.name if img.parent else '',
                            'parent_classes': img.parent.get('class', []) if img.parent else []
                        })
                break  # Use first valid content area
        
        return images[:10]  # Return first 10 images
    
    def analyze_article_structure(self, soup):
        """Analyze article page structure"""
        structure = {}
        
        # Check for main article container
        article_elem = soup.find('article')
        if article_elem:
            structure['article_element'] = {
                'classes': article_elem.get('class', []),
                'id': article_elem.get('id', ''),
                'children_count': len(article_elem.find_all())
            }
        
        # Check for sidebar
        sidebar_selectors = ['aside', '.sidebar', '.side-content']
        for selector in sidebar_selectors:
            elem = soup.select_one(selector)
            if elem:
                structure['sidebar'] = {
                    'selector': selector,
                    'classes': elem.get('class', [])
                }
                break
        
        # Check for comments section
        comment_selectors = ['.comments', '#comments', '[class*="comment"]']
        for selector in comment_selectors:
            elem = soup.select_one(selector)
            if elem:
                structure['comments'] = {
                    'selector': selector,
                    'classes': elem.get('class', [])
                }
                break
        
        return structure

def main():
    analyzer = DetailedStabilityAnalyzer()
    
    results = {}
    
    # Analyze news listing page
    print("1. Analyzing news listing page...")
    news_analysis = analyzer.analyze_news_page()
    if news_analysis:
        results['news_page'] = news_analysis
        
        # Pick first article for detailed analysis
        if news_analysis['sample_articles']:
            first_article = news_analysis['sample_articles'][0]
            if 'link' in first_article and 'href' in first_article['link']:
                print(f"\n2. Analyzing first article in detail...")
                article_analysis = analyzer.analyze_single_article(first_article['link']['href'])
                if article_analysis:
                    results['sample_article_detail'] = article_analysis
    
    # Save results
    with open('detailed_stability_analysis.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    # Print summary
    print(f"\n" + "="*60)
    print("DETAILED ANALYSIS SUMMARY")
    print("="*60)
    
    if 'news_page' in results:
        news = results['news_page']
        print(f"News page: {news['url']}")
        print(f"Total articles found: {news['total_articles']}")
        print(f"Sample articles analyzed: {len(news['sample_articles'])}")
        
        for i, article in enumerate(news['sample_articles'][:3]):
            print(f"\nArticle {i+1}:")
            if 'title' in article:
                print(f"  Title: {article['title']['text'][:50]}...")
            if 'link' in article:
                print(f"  URL: {article['link']['href']}")
            if 'date' in article:
                print(f"  Date: {article['date']['text']}")
    
    if 'sample_article_detail' in results:
        article = results['sample_article_detail']
        print(f"\nDetailed article analysis:")
        print(f"  URL: {article['url']}")
        print(f"  Title: {article['title']['text']}")
        print(f"  Images found: {len(article['images'])}")
        
        if article['content']:
            best_content = max(article['content'].items(), key=lambda x: x[1]['text_length'])
            print(f"  Best content selector: {best_content[0]}")
            print(f"  Content length: {best_content[1]['text_length']} chars")
            print(f"  Paragraphs: {best_content[1]['paragraphs']}")
    
    print(f"\nDetailed results saved to: detailed_stability_analysis.json")

if __name__ == "__main__":
    main()