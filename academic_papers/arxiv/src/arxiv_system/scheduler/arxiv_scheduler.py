#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
arXiv 爬虫定时任务调度器
支持每日、每周和自定义定时任务
"""

import schedule
import time
import asyncio
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional
import threading
import signal
import sys

from ..crawler.enhanced_arxiv_crawler import EnhancedArxivCrawler
from ..oss.wrapper import OSSUploader
from ..utils.file_utils import load_config, save_json


class ArxivScheduler:
    """arXiv爬虫定时调度器"""
    
    def __init__(self, config_path: str = "config_enhanced.json"):
        """初始化调度器
        
        Args:
            config_path: 配置文件路径
        """
        self.config = load_config(config_path)
        self.crawler_config = self.config.get("crawler", {})
        self.oss_config = self.config.get("oss", {})
        
        self.logger = self._setup_logging()
        self.crawler = None
        self.running = False
        
        # 注册信号处理器用于优雅退出
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _setup_logging(self) -> logging.Logger:
        """设置日志系统"""
        logging_config = self.config.get("logging", {})
        
        logging.basicConfig(
            level=getattr(logging, logging_config.get("level", "INFO")),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(logging_config.get("file", "arxiv_scheduler.log")),
                logging.StreamHandler()
            ]
        )
        
        return logging.getLogger(__name__)
    
    def _signal_handler(self, signum, frame):
        """信号处理器，用于优雅退出"""
        self.logger.info(f"接收到信号 {signum}，准备停止调度器...")
        self.stop()
    
    def start_daily_schedule(self, immediate_run: bool = False):
        """启动每日定时任务
        
        Args:
            immediate_run: 是否立即执行一次
        """
        daily_config = self.crawler_config.get("daily_schedule", {})
        crawl_time = daily_config.get("time", "09:00")
        
        print(f"📅 设置每日定时爬取: {crawl_time}")
        self.logger.info(f"设置每日定时任务: {crawl_time}")
        
        # 设置每日任务
        schedule.every().day.at(crawl_time).do(self._run_daily_crawl)
        
        # 设置每周全量更新（周日凌晨）
        schedule.every().sunday.at("02:00").do(self._run_weekly_crawl)
        
        # 设置每月清理任务（每月1号）
        schedule.every().month.do(self._run_monthly_cleanup)
        
        self.running = True
        
        if immediate_run:
            print("🚀 立即执行一次每日爬取任务...")
            self._run_daily_crawl()
        
        print("⏰ 定时任务已启动，等待执行...")
        print("📋 任务列表:")
        print(f"   - 每日爬取: {crawl_time}")
        print(f"   - 每周全量: 周日 02:00")
        print(f"   - 每月清理: 每月1号")
        print("按 Ctrl+C 停止调度器")
        
        self._run_scheduler()
    
    def start_custom_schedule(self, daily_time: str = "09:00", 
                            weekly_time: str = "02:00",
                            immediate_run: bool = False):
        """启动自定义定时任务
        
        Args:
            daily_time: 每日执行时间
            weekly_time: 每周执行时间
            immediate_run: 是否立即执行一次
        """
        print(f"📅 设置自定义定时任务:")
        print(f"   - 每日爬取: {daily_time}")
        print(f"   - 每周全量: 周日 {weekly_time}")
        
        # 设置自定义任务
        schedule.every().day.at(daily_time).do(self._run_daily_crawl)
        schedule.every().sunday.at(weekly_time).do(self._run_weekly_crawl)
        
        self.running = True
        
        if immediate_run:
            print("🚀 立即执行一次每日爬取任务...")
            self._run_daily_crawl()
        
        print("⏰ 自定义定时任务已启动...")
        self._run_scheduler()
    
    def run_once_daily(self, days_back: int = 1):
        """执行一次每日爬取任务
        
        Args:
            days_back: 回溯天数
        """
        print(f"🌅 执行单次每日爬取任务（回溯 {days_back} 天）")
        
        try:
            result = asyncio.run(self._daily_crawl_task(days_back))
            print(f"✅ 单次每日爬取完成: {result}")
            return result
        except Exception as e:
            self.logger.error(f"单次每日爬取失败: {e}")
            print(f"❌ 单次每日爬取失败: {e}")
            return {"success": False, "error": str(e)}
    
    def run_once_weekly(self, days_back: int = 7):
        """执行一次每周爬取任务
        
        Args:
            days_back: 回溯天数
        """
        print(f"📚 执行单次每周爬取任务（回溯 {days_back} 天）")
        
        try:
            result = asyncio.run(self._weekly_crawl_task(days_back))
            print(f"✅ 单次每周爬取完成: {result}")
            return result
        except Exception as e:
            self.logger.error(f"单次每周爬取失败: {e}")
            print(f"❌ 单次每周爬取失败: {e}")
            return {"success": False, "error": str(e)}
    
    def _run_scheduler(self):
        """运行调度器主循环"""
        while self.running:
            try:
                schedule.run_pending()
                time.sleep(60)  # 每分钟检查一次
            except KeyboardInterrupt:
                self.logger.info("接收到键盘中断，停止调度器")
                break
            except Exception as e:
                self.logger.error(f"调度器运行异常: {e}")
                time.sleep(60)  # 出错后等待1分钟再继续
        
        print("📴 调度器已停止")
    
    def stop(self):
        """停止调度器"""
        self.running = False
        schedule.clear()
        print("🛑 正在停止调度器...")
    
    def _run_daily_crawl(self):
        """执行每日爬取任务"""
        try:
            print(f"\n🌅 开始执行每日爬取任务: {datetime.now()}")
            self.logger.info("开始每日爬取任务")
            
            result = asyncio.run(self._daily_crawl_task())
            
            if result.get("success"):
                print("✅ 每日爬取任务完成")
                self.logger.info(f"每日爬取任务完成: {result}")
            else:
                print(f"❌ 每日爬取任务失败: {result.get('error', '未知错误')}")
                self.logger.error(f"每日爬取任务失败: {result}")
                
        except Exception as e:
            self.logger.error(f"每日爬取任务异常: {e}")
            print(f"❌ 每日爬取任务异常: {e}")
    
    def _run_weekly_crawl(self):
        """执行每周爬取任务"""
        try:
            print(f"\n📚 开始执行每周爬取任务: {datetime.now()}")
            self.logger.info("开始每周爬取任务")
            
            result = asyncio.run(self._weekly_crawl_task())
            
            if result.get("success"):
                print("✅ 每周爬取任务完成")
                self.logger.info(f"每周爬取任务完成: {result}")
            else:
                print(f"❌ 每周爬取任务失败: {result.get('error', '未知错误')}")
                self.logger.error(f"每周爬取任务失败: {result}")
                
        except Exception as e:
            self.logger.error(f"每周爬取任务异常: {e}")
            print(f"❌ 每周爬取任务异常: {e}")
    
    def _run_monthly_cleanup(self):
        """执行每月清理任务"""
        try:
            print(f"\n🧹 开始执行每月清理任务: {datetime.now()}")
            self.logger.info("开始每月清理任务")
            
            # 清理30天前的临时文件
            self._cleanup_old_files(days=30)
            
            print("✅ 每月清理任务完成")
            self.logger.info("每月清理任务完成")
            
        except Exception as e:
            self.logger.error(f"每月清理任务异常: {e}")
            print(f"❌ 每月清理任务异常: {e}")
    
    async def _daily_crawl_task(self, days_back: int = 1) -> Dict[str, Any]:
        """每日爬取任务实现
        
        Args:
            days_back: 回溯天数
            
        Returns:
            任务结果
        """
        try:
            # 创建爬虫实例
            crawler = EnhancedArxivCrawler(self.config)
            
            async with crawler:
                # 爬取每日新论文
                result = await crawler.crawl_and_save_daily(days_back=days_back)
                
                # 如果启用了自动上传，则上传到OSS
                if self.oss_config.get("enable_auto_upload", False):
                    await self._upload_to_oss(result["output_dir"])
                
                return result
                
        except Exception as e:
            self.logger.error(f"每日爬取任务执行失败: {e}")
            return {"success": False, "error": str(e)}
    
    async def _weekly_crawl_task(self, days_back: int = 7) -> Dict[str, Any]:
        """每周爬取任务实现
        
        Args:
            days_back: 回溯天数
            
        Returns:
            任务结果
        """
        try:
            # 创建爬虫实例
            crawler = EnhancedArxivCrawler(self.config)
            
            async with crawler:
                # 爬取热门关键词论文
                result = await crawler.crawl_and_save_weekly(days_back=days_back)
                
                # 如果启用了自动上传，则上传到OSS
                if self.oss_config.get("enable_auto_upload", False):
                    await self._upload_to_oss(result["output_dir"])
                
                return result
                
        except Exception as e:
            self.logger.error(f"每周爬取任务执行失败: {e}")
            return {"success": False, "error": str(e)}
    
    async def _upload_to_oss(self, local_dir: str) -> bool:
        """上传到OSS
        
        Args:
            local_dir: 本地目录路径
            
        Returns:
            是否成功
        """
        try:
            print(f"☁️ 开始上传到OSS: {local_dir}")
            
            async with OSSUploader(self.oss_config) as uploader:
                result = await uploader.upload_all(
                    base_dir=Path(local_dir),
                    resume=True
                )
                
                if result.get('success'):
                    print(f"✅ OSS上传成功: {result.get('uploaded_files', 0)} 个文件")
                    self.logger.info(f"OSS上传成功: {result}")
                    return True
                else:
                    print(f"❌ OSS上传失败: {result.get('error', '未知错误')}")
                    self.logger.error(f"OSS上传失败: {result}")
                    return False
                    
        except Exception as e:
            self.logger.error(f"OSS上传异常: {e}")
            print(f"❌ OSS上传异常: {e}")
            return False
    
    def _cleanup_old_files(self, days: int = 30) -> None:
        """清理旧文件
        
        Args:
            days: 保留天数
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        output_dir = Path(self.crawler_config.get("output_directory", "crawled_data"))
        
        if not output_dir.exists():
            return
        
        cleaned_files = 0
        
        # 清理daily目录中的旧文件
        daily_dir = output_dir / "daily"
        if daily_dir.exists():
            for date_dir in daily_dir.iterdir():
                if date_dir.is_dir():
                    try:
                        dir_date = datetime.strptime(date_dir.name, "%Y-%m-%d")
                        if dir_date < cutoff_date:
                            import shutil
                            shutil.rmtree(date_dir)
                            cleaned_files += 1
                            print(f"🗑️ 清理旧目录: {date_dir}")
                    except ValueError:
                        # 目录名格式不正确，跳过
                        continue
        
        # 清理weekly目录中的旧文件
        weekly_dir = output_dir / "weekly"
        if weekly_dir.exists():
            for week_dir in weekly_dir.iterdir():
                if week_dir.is_dir():
                    # 简单按创建时间清理
                    dir_mtime = datetime.fromtimestamp(week_dir.stat().st_mtime)
                    if dir_mtime < cutoff_date:
                        import shutil
                        shutil.rmtree(week_dir)
                        cleaned_files += 1
                        print(f"🗑️ 清理旧目录: {week_dir}")
        
        print(f"🧹 清理完成，共清理 {cleaned_files} 个旧目录")
        self.logger.info(f"清理旧文件完成，清理了 {cleaned_files} 个目录")
    
    def get_schedule_status(self) -> Dict[str, Any]:
        """获取调度状态
        
        Returns:
            调度状态信息
        """
        jobs = schedule.get_jobs()
        
        status = {
            "running": self.running,
            "total_jobs": len(jobs),
            "jobs": []
        }
        
        for job in jobs:
            job_info = {
                "function": job.job_func.__name__,
                "interval": str(job.interval),
                "unit": job.unit,
                "at_time": str(job.at_time) if job.at_time else None,
                "next_run": job.next_run.isoformat() if job.next_run else None
            }
            status["jobs"].append(job_info)
        
        return status
