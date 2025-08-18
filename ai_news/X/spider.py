#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
X (Twitter) 爬虫主脚本
基于Playwright的推文爬取工具
"""

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
import hashlib
import re
import requests
from urllib.parse import urlparse

class XSpider:
    def __init__(self):
        """初始化X爬虫"""
        self.base_dir = Path(__file__).parent
        self.setup_directories()
        
    def setup_directories(self):
        """创建必要目录"""
        data_dir = self.base_dir / "crawled_data"
        data_dir.mkdir(parents=True, exist_ok=True)
        print(f"📁 数据目录已创建: {data_dir}")
        
    def generate_tweet_id(self, tweet_data):
        """生成推文唯一标识符"""
        if 'id' in tweet_data:
            return tweet_data['id']
        # 如果没有ID，使用内容哈希
        content = tweet_data.get('text', '') + tweet_data.get('url', '')
        return hashlib.md5(content.encode()).hexdigest()[:16]
        
    def is_tweet_exists(self, tweet_id):
        """检查推文是否已存在"""
        tweet_dir = self.base_dir / "crawled_data" / tweet_id
        return tweet_dir.exists()
        
    def save_tweet(self, tweet_data, tweet_id):
        """保存推文数据"""
        tweet_dir = self.base_dir / "crawled_data" / tweet_id
        tweet_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建media文件夹
        media_dir = tweet_dir / "media"
        media_dir.mkdir(exist_ok=True)
        
        # 下载图片到media文件夹
        downloaded_images = []
        images = tweet_data.get('images', [])
        if images:
            print(f"📸 开始下载 {len(images)} 张图片...")
            for i, img in enumerate(images, 1):
                try:
                    img_url = img.get('url', '')
                    if img_url:
                        # 获取文件扩展名
                        parsed_url = urlparse(img_url)
                        ext = '.jpg'  # 默认扩展名
                        if '.' in parsed_url.path:
                            ext = '.' + parsed_url.path.split('.')[-1].lower()
                        elif 'format=' in img_url:
                            format_match = re.search(r'format=([a-zA-Z]+)', img_url)
                            if format_match:
                                ext = '.' + format_match.group(1).lower()
                        
                        filename = f"image_{i}{ext}"
                        filepath = media_dir / filename
                        
                        # 下载图片
                        response = requests.get(img_url, timeout=30)
                        response.raise_for_status()
                        
                        with open(filepath, 'wb') as f:
                            f.write(response.content)
                        
                        downloaded_images.append({
                            'url': img_url,
                            'filename': filename,
                            'alt': img.get('alt', f'推文图片 {i}'),
                            'local_path': str(filepath)
                        })
                        
                        print(f"✅ 图片下载成功: {filename}")
                        
                except Exception as e:
                    print(f"❌ 图片下载失败 {img_url}: {e}")
                    downloaded_images.append({
                        'url': img_url,
                        'filename': '',
                        'alt': img.get('alt', f'推文图片 {i}'),
                        'local_path': '',
                        'error': str(e)
                    })
        
        # 保存metadata.json
        metadata_file = tweet_dir / "metadata.json"
        metadata = {
            "url": tweet_data.get('url', ''),
            "text": tweet_data.get('text', ''),
            "author": tweet_data.get('author', ''),
            "timestamp": tweet_data.get('timestamp', ''),
            "images": downloaded_images,
            "links": tweet_data.get('links', []),
            "crawl_time": datetime.now().isoformat(),
            "tweet_id": tweet_id,
            "content_hash": hashlib.md5(tweet_data.get('text', '').encode()).hexdigest()
        }
        
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
            
        # 保存content.md
        content_file = tweet_dir / "content.md"
        markdown_content = self.generate_markdown(tweet_data, downloaded_images)
        
        with open(content_file, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
            
        print(f"💾 推文已保存: {tweet_id}")
        return tweet_dir
        
    def generate_markdown(self, tweet_data, downloaded_images):
        """生成Markdown格式内容"""
        author_name = tweet_data.get('author', '未知用户')
        display_time = tweet_data.get('display_time', '未知时间')
        timestamp = tweet_data.get('timestamp', '')
        crawl_time = datetime.now().isoformat()
        
        content = f"""# {author_name} 的推文

**作者**: {author_name}  
**发布时间**: {display_time}  
**时间戳**: {timestamp}  
**来源**: {tweet_data.get('url', '')}  
**爬取时间**: {crawl_time}  

---

{tweet_data.get('text', '')}

"""
        
        # 添加本地图片
        if downloaded_images:
            content += "## 🖼️ 图片\n\n"
            for img in downloaded_images:
                if img.get('filename'):  # 只显示成功下载的图片
                    alt_text = img.get('alt', '推文图片')
                    filename = img.get('filename')
                    content += f"![{alt_text}](media/{filename})\n\n"
            
        # 添加链接
        links = tweet_data.get('links', [])
        if links:
            content += "## 🔗 相关链接\n\n"
            for link in links:
                content += f"- [{link.get('text', '链接')}]({link.get('url', '')})\n"
            content += "\n"
                
        return content
        
    def run_js_scraper(self, script_name, target_url=None):
        """运行JavaScript爬虫脚本"""
        script_path = self.base_dir / "src" / script_name
        
        if not script_path.exists():
            print(f"❌ 脚本文件不存在: {script_path}")
            return None
            
        try:
            print(f"🚀 正在运行脚本: {script_name}")
            
            # 构建命令
            cmd = ["node", str(script_path)]
            if target_url:
                cmd.append(target_url)
                
            # 运行脚本
            result = subprocess.run(
                cmd,
                cwd=str(self.base_dir),
                capture_output=True,
                text=True,
                encoding='utf-8'
            )
            
            if result.returncode == 0:
                print(f"✅ 脚本执行成功: {script_name}")
                return result.stdout
            else:
                print(f"❌ 脚本执行失败: {script_name}")
                print(f"错误信息: {result.stderr}")
                return None
                
        except Exception as e:
            print(f"❌ 运行脚本时出错: {e}")
            return None
            
    def parse_js_output(self, output):
        """解析JS脚本输出的JSON数据"""
        try:
            # 查找JSON数据标记
            start_marker = "TWEET_DATA_START"
            end_marker = "TWEET_DATA_END"
            
            start_idx = output.find(start_marker)
            end_idx = output.find(end_marker)
            
            if start_idx == -1 or end_idx == -1:
                print("❌ 未找到JSON数据标记")
                return None
                
            # 提取JSON字符串
            json_start = start_idx + len(start_marker)
            json_str = output[json_start:end_idx].strip()
            
            # 解析JSON
            tweet_data = json.loads(json_str)
            return tweet_data
            
        except json.JSONDecodeError as e:
            print(f"❌ JSON解析失败: {e}")
            return None
        except Exception as e:
            print(f"❌ 解析输出时出错: {e}")
            return None
            
    def crawl_following(self, max_tweets=None):
        """爬取Following页面推文"""
        if max_tweets is None:
            max_tweets = 20  # 默认爬取20条
            
        print(f"🎯 开始爬取Following页面推文 (最多 {max_tweets} 条)")
        
        # 运行对应的JS脚本
        result = self.run_js_scraper("scrape_following_tweets.js")
            
        if result:
            print(f"✅ Following页面推文爬取完成")
        else:
            print("❌ JS脚本执行失败")
            
        return result
        
    def run(self, target="following", max_tweets=None):
        """执行爬虫"""
        print(f"🕷️ X爬虫启动 - 目标: {target}")
        
        # 只支持following目标
        if target == "following":
            return self.crawl_following(max_tweets)
        else:
            print(f"❌ 暂不支持目标: {target}")
            return None

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='X (Twitter) 爬虫')
    parser.add_argument('--target', default='following', 
                       choices=['following'],
                       help='爬取目标')
    parser.add_argument('--max', type=int, default=None,
                       help='最大爬取数量')
    
    args = parser.parse_args()
    
    try:
        spider = XSpider()
        spider.run(target=args.target, max_tweets=args.max)
    except KeyboardInterrupt:
        print("\n⚠️ 用户中断爬虫")
    except Exception as e:
        print(f"❌ 爬虫运行出错: {e}")
        
if __name__ == "__main__":
    main()