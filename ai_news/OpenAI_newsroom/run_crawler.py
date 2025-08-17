#!/usr/bin/env python3
"""
OpenAI Newsroom 爬虫运行脚本
整合整个爬虫流程，包括爬取、处理和上传
"""

import argparse
import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from loguru import logger

from spider import OpenAINewsroomSpider, ArticleDetail
from uploader import DataUploader


class CrawlerRunner:
    """爬虫运行管理器"""
    
    def __init__(self, config_path: str = "config.json"):
        self.config_path = config_path
        self.config = self._load_config()
        self.setup_logging()
    
    def _load_config(self) -> Dict:
        """加载配置文件"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"配置文件不存在: {self.config_path}")
            sys.exit(1)
        except json.JSONDecodeError as e:
            logger.error(f"配置文件格式错误: {str(e)}")
            sys.exit(1)
    
    def setup_logging(self):
        """设置日志"""
        log_dir = Path("./logs")
        log_dir.mkdir(exist_ok=True)
        
        logger.remove()
        logger.add(
            log_dir / f"crawler_{datetime.now().strftime('%Y%m%d')}.log",
            rotation="10 MB",
            retention="30 days",
            level=self.config.get('logging', {}).get('level', 'INFO'),
            encoding='utf-8'
        )
        logger.add(
            sys.stdout,
            level=self.config.get('logging', {}).get('level', 'INFO')
        )
    
    async def run_single_crawl(self, max_articles: int = None, output_dir: str = "./crawled_data") -> List[ArticleDetail]:
        """运行单次爬取任务"""
        logger.info("开始单次爬取任务")
        
        async with OpenAINewsroomSpider(self.config.get('crawler', {})) as spider:
            articles = await spider.crawl_all_articles(max_articles=max_articles, output_dir=output_dir)
            
            if not articles:
                logger.warning("未爬取到任何文章")
                return []
            
            logger.info(f"成功爬取 {len(articles)} 篇文章")
            return articles
    
    async def process_and_save(self, articles: List[ArticleDetail]) -> Dict:
        """处理并保存文章到本地"""
        if not articles:
            return {"total": 0, "local_saved": 0}
        
        uploader = DataUploader(self.config)
        
        logger.info(f"开始处理 {len(articles)} 篇文章")
        
        # 处理文章，只保存到本地
        results = uploader.process_articles(articles)
        
        logger.info(f"处理完成: {results}")
        return results
    
    def save_crawl_report(self, articles: List[ArticleDetail], results: Dict):
        """保存爬取报告"""
        report = {
            "crawl_time": datetime.now().isoformat(),
            "total_articles": len(articles),
            "results": results,
            "articles_summary": [
                {
                    "title": article.title,
                    "url": article.url,
                    "publish_date": article.publish_date,
                    "author": article.author,
                    "word_count": article.word_count,
                    "tags": article.tags
                }
                for article in articles
            ]
        }
        
        report_path = Path("./data") / f"crawl_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        logger.info(f"爬取报告已保存: {report_path}")
    
    async def run_continuous_crawl(self, interval_hours: int = 6):
        """运行持续爬取任务"""
        logger.info(f"开始持续爬取任务，间隔时间: {interval_hours}小时")
        
        while True:
            try:
                articles = await self.run_single_crawl()
                
                if articles:
                    results = await self.process_and_save(articles)
                    
                    self.save_crawl_report(articles, results)
                
                logger.info(f"等待 {interval_hours} 小时后进行下一次爬取...")
                await asyncio.sleep(interval_hours * 3600)
                
            except KeyboardInterrupt:
                logger.info("用户中断爬取任务")
                break
            except Exception as e:
                logger.error(f"爬取任务异常: {str(e)}")
                await asyncio.sleep(300)  # 5分钟后重试
    
    async def run_with_config(self, config_file: str = None):
        """根据配置文件运行"""
        if config_file and os.path.exists(config_file):
            with open(config_file, 'r', encoding='utf-8') as f:
                run_config = json.load(f)
        else:
            run_config = {
                "max_articles": 10,
                "continuous": False,
                "interval_hours": 6
            }
        
        if run_config.get('continuous', False):
            await self.run_continuous_crawl(run_config.get('interval_hours', 6))
        else:
            articles = await self.run_single_crawl(
                max_articles=run_config.get('max_articles')
            )
            
            if articles:
                results = await self.process_and_save(articles)
                
                self.save_crawl_report(articles, results)


def create_sample_config():
    """创建示例配置文件"""
    sample_config = {
        "max_articles": 5,
        "continuous": False,
        "interval_hours": 6
    }
    
    config_path = Path("./run_config.json")
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(sample_config, f, ensure_ascii=False, indent=2)
    
    print(f"示例配置文件已创建: {config_path}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="OpenAI Newsroom 爬虫")
    parser.add_argument("--config", "-c", help="配置文件路径")
    parser.add_argument("--max-articles", "-m", type=int, help="最大文章数量")
    parser.add_argument("--output-dir", "-o", default="./crawled_data", help="输出目录")
    parser.add_argument("--continuous", action="store_true", help="持续运行模式")
    parser.add_argument("--interval", type=int, default=6, help="持续运行间隔(小时)")
    # 注意：现在只支持本地保存，上传功能已移除
    parser.add_argument("--init-config", action="store_true", help="创建示例配置文件")
    
    args = parser.parse_args()
    
    if args.init_config:
        create_sample_config()
        return
    
    # 创建运行器
    runner = CrawlerRunner()
    
    # 根据参数设置运行配置
    if args.config:
        asyncio.run(runner.run_with_config(args.config))
    elif args.continuous:
        asyncio.run(runner.run_continuous_crawl(args.interval))
    else:
        # 命令行参数模式
        async def run_with_args():
            articles = await runner.run_single_crawl(max_articles=args.max_articles, output_dir=args.output_dir)
            if articles:
                results = await runner.process_and_save(articles)
                runner.save_crawl_report(articles, results)
        
        asyncio.run(run_with_args())


if __name__ == "__main__":
    main()