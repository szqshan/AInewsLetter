#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Google Research Blog 一键运行脚本
提供简单的命令行界面来运行爬虫
"""

import sys
import json
import time
import logging
from pathlib import Path
from datetime import datetime
from spider import GoogleResearchSpider

class CrawlerRunner:
    def __init__(self):
        self.spider = None
        self.setup_logging()
    
    def setup_logging(self):
        """设置日志"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def check_dependencies(self):
        """检查依赖包"""
        required_packages = ['feedparser', 'requests', 'beautifulsoup4']
        missing_packages = []
        
        for package in required_packages:
            try:
                __import__(package)
            except ImportError:
                missing_packages.append(package)
        
        if missing_packages:
            print("❌ 缺少必要的依赖包:")
            for package in missing_packages:
                print(f"   - {package}")
            print("\\n请运行以下命令安装:")
            print("pip install -r requirements.txt")
            return False
        
        print("✅ 所有依赖包已安装")
        return True
    
    def show_welcome(self):
        """显示欢迎信息"""
        print("=" * 60)
        print("🤖 Google Research Blog RSS 爬虫")
        print("=" * 60)
        print("📖 自动爬取最新的AI研究文章")
        print("💾 按文章分别保存内容和媒体文件")
        print("🔧 支持自定义配置和过滤")
        print("=" * 60)
    
    def show_config_info(self):
        """显示配置信息"""
        try:
            spider = GoogleResearchSpider()
            config = spider.config
            
            print("\\n📋 当前配置:")
            print(f"   RSS源: {config['rss']['url']}")
            print(f"   数据目录: {config['storage']['data_directory']}")
            print(f"   最大文章数: {config['crawler']['max_articles_per_run']}")
            print(f"   下载媒体: {'是' if config['media']['download_enabled'] else '否'}")
            print(f"   请求延迟: {config['crawler']['request_delay']} 秒")
            
        except Exception as e:
            print(f"❌ 读取配置失败: {e}")
    
    def run_crawler(self):
        """运行爬虫"""
        try:
            print("\\n🚀 开始爬取...")
            start_time = time.time()
            
            # 创建爬虫实例
            spider = GoogleResearchSpider()
            
            # 执行爬取
            articles = spider.crawl()
            
            end_time = time.time()
            duration = end_time - start_time
            
            # 显示结果
            print("\\n" + "=" * 60)
            print("📊 爬取结果")
            print("=" * 60)
            print(f"⏱️  耗时: {duration:.2f} 秒")
            print(f"📄 新增文章: {len(articles)} 篇")
            print(f"📁 保存目录: {spider.data_dir}")
            
            if articles:
                print("\\n📚 文章列表:")
                for i, article in enumerate(articles, 1):
                    print(f"   {i}. {article['title']}")
                    print(f"      📅 {article.get('published_date', 'N/A')}")
                    print(f"      📝 {article['word_count']} 字")
                    if article.get('images'):
                        print(f"      🖼️  {len(article['images'])} 张图片")
                    print()
            else:
                print("\\n💡 没有发现新文章")
            
            return True
            
        except KeyboardInterrupt:
            print("\\n⏹️  用户中断爬取")
            return False
        except Exception as e:
            print(f"\\n❌ 爬取失败: {e}")
            self.logger.exception("爬取过程中发生异常")
            return False
    
    def show_data_summary(self):
        """显示数据统计"""
        try:
            data_dir = Path("crawled_data")
            if not data_dir.exists():
                print("\\n💡 暂无爬取数据")
                return
            
            article_dirs = [d for d in data_dir.iterdir() if d.is_dir() and d.name.startswith('article_')]
            
            if not article_dirs:
                print("\\n💡 暂无爬取数据")
                return
            
            print("\\n📊 数据统计:")
            print(f"   📁 总文章数: {len(article_dirs)}")
            
            # 统计文件类型
            total_md = 0
            total_json = 0
            total_media = 0
            
            for article_dir in article_dirs:
                if (article_dir / "content.md").exists():
                    total_md += 1
                if (article_dir / "metadata.json").exists():
                    total_json += 1
                
                media_dir = article_dir / "media"
                if media_dir.exists():
                    media_files = list(media_dir.iterdir())
                    total_media += len(media_files)
            
            print(f"   📝 Markdown文件: {total_md}")
            print(f"   📋 元数据文件: {total_json}")
            print(f"   🖼️  媒体文件: {total_media}")
            
            # 最新文章
            if article_dirs:
                latest_dir = max(article_dirs, key=lambda x: x.stat().st_mtime)
                metadata_file = latest_dir / "metadata.json"
                if metadata_file.exists():
                    try:
                        with open(metadata_file, 'r', encoding='utf-8') as f:
                            metadata = json.load(f)
                        print(f"   🆕 最新文章: {metadata.get('title', 'N/A')}")
                    except:
                        pass
            
        except Exception as e:
            print(f"❌ 读取数据统计失败: {e}")
    
    def interactive_mode(self):
        """交互模式"""
        while True:
            print("\\n" + "=" * 40)
            print("🤖 Google Research Blog 爬虫")
            print("=" * 40)
            print("1. 🚀 开始爬取")
            print("2. 📊 查看数据统计")
            print("3. ⚙️  查看配置")
            print("4. 🔧 检查依赖")
            print("5. ❌ 退出")
            print("=" * 40)
            
            try:
                choice = input("请选择操作 (1-5): ").strip()
                
                if choice == '1':
                    self.run_crawler()
                elif choice == '2':
                    self.show_data_summary()
                elif choice == '3':
                    self.show_config_info()
                elif choice == '4':
                    self.check_dependencies()
                elif choice == '5':
                    print("👋 再见！")
                    break
                else:
                    print("❌ 无效选择，请重试")
                    
            except KeyboardInterrupt:
                print("\\n👋 再见！")
                break
            except EOFError:
                print("\\n👋 再见！")
                break
    
    def run(self):
        """主运行方法"""
        self.show_welcome()
        
        # 检查依赖
        if not self.check_dependencies():
            return False
        
        # 根据命令行参数决定运行模式
        if len(sys.argv) > 1:
            command = sys.argv[1].lower()
            
            if command in ['run', 'crawl', 'start']:
                self.show_config_info()
                return self.run_crawler()
            elif command in ['status', 'stats', 'summary']:
                self.show_data_summary()
                return True
            elif command in ['config', 'conf']:
                self.show_config_info()
                return True
            elif command in ['check', 'deps']:
                return self.check_dependencies()
            elif command in ['help', '-h', '--help']:
                self.show_help()
                return True
            else:
                print(f"❌ 未知命令: {command}")
                self.show_help()
                return False
        else:
            # 交互模式
            self.interactive_mode()
            return True
    
    def show_help(self):
        """显示帮助信息"""
        print("\\n📖 使用说明:")
        print("   python run_crawler.py          # 交互模式")
        print("   python run_crawler.py run      # 直接运行爬虫")
        print("   python run_crawler.py status   # 查看数据统计")
        print("   python run_crawler.py config   # 查看配置")
        print("   python run_crawler.py check    # 检查依赖")
        print("   python run_crawler.py help     # 显示帮助")

def main():
    """主函数"""
    runner = CrawlerRunner()
    success = runner.run()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()