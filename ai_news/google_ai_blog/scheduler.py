#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Google AI Blog 定时爬虫调度器
使用schedule库实现定时任务
"""

import schedule
import time
import json
import os
import logging
from datetime import datetime, timedelta
from google_ai_spider import GoogleAIBlogSpider

class GoogleAIScheduler:
    def __init__(self, config_file: str = 'config.json'):
        """
        初始化调度器
        Args:
            config_file: 配置文件路径
        """
        self.config_file = config_file
        self.load_config()
        self.setup_logging()
        self.spider = GoogleAIBlogSpider()
        self.last_run_file = 'data/metadata/last_run.json'
    
    def load_config(self):
        """加载配置文件"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
        except Exception as e:
            print(f"加载配置文件失败: {e}")
            # 使用默认配置
            self.config = {
                "spider_config": {
                    "max_articles_per_run": 20,
                    "request_delay_seconds": 2
                },
                "schedule_config": {
                    "check_interval_hours": 6,
                    "daily_run_time": "09:00"
                }
            }
    
    def setup_logging(self):
        """设置日志"""
        log_dir = 'logs'
        os.makedirs(log_dir, exist_ok=True)
        
        log_file = os.path.join(log_dir, f'scheduler_{datetime.now().strftime("%Y%m%d")}.log')
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        
        self.logger = logging.getLogger("GoogleAIScheduler")
    
    def load_last_run_info(self) -> dict:
        """加载上次运行信息"""
        if os.path.exists(self.last_run_file):
            try:
                with open(self.last_run_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        
        return {
            'last_run_time': None,
            'last_article_count': 0,
            'total_runs': 0
        }
    
    def save_last_run_info(self, article_count: int):
        """保存本次运行信息"""
        last_run_info = self.load_last_run_info()
        
        run_info = {
            'last_run_time': datetime.now().isoformat(),
            'last_article_count': article_count,
            'total_runs': last_run_info.get('total_runs', 0) + 1
        }
        
        os.makedirs(os.path.dirname(self.last_run_file), exist_ok=True)
        
        try:
            with open(self.last_run_file, 'w', encoding='utf-8') as f:
                json.dump(run_info, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"保存运行信息失败: {e}")
    
    def should_run_now(self) -> bool:
        """检查是否应该运行爬虫"""
        last_run_info = self.load_last_run_info()
        last_run_time = last_run_info.get('last_run_time')
        
        if not last_run_time:
            return True
        
        try:
            last_run = datetime.fromisoformat(last_run_time)
            check_interval = self.config['schedule_config'].get('check_interval_hours', 6)
            
            if datetime.now() - last_run >= timedelta(hours=check_interval):
                return True
        except:
            return True
        
        return False
    
    def run_spider(self):
        """运行爬虫任务"""
        try:
            self.logger.info("开始执行爬虫任务")
            
            max_articles = self.config['spider_config'].get('max_articles_per_run', 20)
            articles = self.spider.crawl_latest_articles(max_articles=max_articles)
            
            article_count = len(articles)
            self.logger.info(f"爬取完成，获得 {article_count} 篇新文章")
            
            # 保存运行信息
            self.save_last_run_info(article_count)
            
            # 发送通知（如果配置了）
            if self.config.get('notification_config', {}).get('enable_notifications', False):
                self.send_notification(f"Google AI Blog爬虫完成：获得 {article_count} 篇新文章")
            
            return article_count
            
        except Exception as e:
            self.logger.error(f"爬虫任务执行失败: {e}")
            
            # 发送错误通知
            if self.config.get('notification_config', {}).get('notify_on_errors', False):
                self.send_notification(f"Google AI Blog爬虫执行失败: {str(e)}")
            
            return 0
    
    def send_notification(self, message: str):
        """发送通知（预留接口）"""
        # 这里可以实现发送通知的逻辑
        # 比如发送到webhook、邮件等
        webhook_url = self.config.get('notification_config', {}).get('webhook_url')
        if webhook_url:
            try:
                import requests
                requests.post(webhook_url, json={'text': message}, timeout=10)
            except:
                pass
        
        self.logger.info(f"通知: {message}")
    
    def scheduled_run(self):
        """定时运行任务"""
        if self.should_run_now():
            return self.run_spider()
        else:
            self.logger.info("距离上次运行时间不足，跳过本次执行")
            return 0
    
    def force_run(self):
        """强制运行任务"""
        return self.run_spider()
    
    def setup_schedule(self):
        """设置定时任务"""
        # 每日定时运行
        daily_run_time = self.config['schedule_config'].get('daily_run_time', '09:00')
        schedule.every().day.at(daily_run_time).do(self.scheduled_run)
        
        # 每隔几小时检查一次
        check_interval = self.config['schedule_config'].get('check_interval_hours', 6)
        schedule.every(check_interval).hours.do(self.scheduled_run)
        
        self.logger.info(f"定时任务已设置：每日{daily_run_time}运行，每{check_interval}小时检查一次")
    
    def run_scheduler(self):
        """运行调度器"""
        self.logger.info("Google AI Blog 爬虫调度器启动")
        
        # 设置定时任务
        self.setup_schedule()
        
        # 启动时运行一次
        self.logger.info("启动时执行一次爬虫任务")
        self.force_run()
        
        # 主循环
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # 每分钟检查一次
        except KeyboardInterrupt:
            self.logger.info("调度器已停止")
    
    def run_once(self):
        """运行一次爬虫任务"""
        return self.force_run()
    
    def show_status(self):
        """显示状态信息"""
        last_run_info = self.load_last_run_info()
        
        print("\\n=== Google AI Blog 爬虫状态 ===")
        print(f"上次运行时间: {last_run_info.get('last_run_time', '从未运行')}")
        print(f"上次获取文章: {last_run_info.get('last_article_count', 0)} 篇")
        print(f"总运行次数: {last_run_info.get('total_runs', 0)} 次")
        
        # 显示索引统计
        try:
            with open('data/metadata/article_index.json', 'r', encoding='utf-8') as f:
                index = json.load(f)
            
            print(f"\\n总文章数: {index.get('total_articles', 0)} 篇")
            print(f"索引更新时间: {index.get('last_update', 'N/A')}")
            
            categories = index.get('categories', {})
            if categories:
                print("\\n分类统计:")
                for category, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
                    print(f"  {category}: {count} 篇")
        except:
            print("\\n无法加载文章索引信息")

def main():
    """主函数"""
    import sys
    
    scheduler = GoogleAIScheduler()
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == 'run':
            # 运行一次
            count = scheduler.run_once()
            print(f"爬取完成，获得 {count} 篇新文章")
            
        elif command == 'start':
            # 启动定时调度器
            scheduler.run_scheduler()
            
        elif command == 'status':
            # 显示状态
            scheduler.show_status()
            
        else:
            print("用法:")
            print("  python scheduler.py run     # 运行一次爬虫")
            print("  python scheduler.py start   # 启动定时调度器")
            print("  python scheduler.py status  # 显示状态信息")
    else:
        # 默认运行一次
        count = scheduler.run_once()
        print(f"爬取完成，获得 {count} 篇新文章")

if __name__ == "__main__":
    main()