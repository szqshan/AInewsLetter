#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化版分类批量爬取脚本
用于快速按分类爬取arXiv论文
"""

import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path


def run_command(command):
    """执行命令并返回结果"""
    print(f"🚀 执行命令: {command}")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ 命令执行成功")
            return True
        else:
            print(f"❌ 命令执行失败: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ 执行异常: {e}")
        return False


def batch_crawl_categories():
    """批量按分类爬取"""
    
    # 要爬取的分类
    categories = [
        "cs.AI",   # 人工智能
        "cs.LG",   # 机器学习
        "cs.CL",   # 计算与语言
        "cs.CV",   # 计算机视觉
        "cs.NE"    # 神经和进化计算
    ]
    
    # 爬取参数
    max_results_per_category = 200  # 每个分类最大数量
    concurrent = 3                  # 并发数
    
    print("=" * 60)
    print("🎯 arXiv分类批量爬取工具")
    print("=" * 60)
    print(f"📂 目标分类: {', '.join(categories)}")
    print(f"📊 每分类最大数量: {max_results_per_category}")
    print(f"⚡ 并发数: {concurrent}")
    print(f"⏰ 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    successful_categories = 0
    failed_categories = 0
    
    # 逐个分类爬取
    for i, category in enumerate(categories, 1):
        print(f"\n📑 [{i}/{len(categories)}] 开始爬取分类: {category}")
        print("-" * 40)
        
        # 构建爬取命令
        query = f"cat:{category}"
        output_dir = f"crawled_data/categories/{category.replace('.', '_')}"
        
        command = f'python main.py crawl --query "{query}" --max-results {max_results_per_category} --concurrent {concurrent} --output {output_dir} --download-pdf'
        
        # 执行爬取
        success = run_command(command)
        
        if success:
            successful_categories += 1
            print(f"🎉 {category} 爬取完成")
        else:
            failed_categories += 1
            print(f"💥 {category} 爬取失败")
        
        # 分类间延迟
        if i < len(categories):
            print("⏳ 等待2秒后继续下一个分类...")
            time.sleep(2)
    
    # 输出总结
    print("\n" + "=" * 60)
    print("🎊 批量爬取完成！")
    print("=" * 60)
    print(f"✅ 成功分类: {successful_categories}")
    print(f"❌ 失败分类: {failed_categories}")
    print(f"📁 数据目录: crawled_data/categories/")
    print(f"⏰ 结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 显示后续操作建议
    if successful_categories > 0:
        print("\n💡 后续操作建议:")
        print("1. 上传到存储系统:")
        print("   python main.py upload --source crawled_data/categories")
        print("2. 查看系统状态:")
        print("   python main.py status --detail")


if __name__ == "__main__":
    # 确保在正确的目录
    script_dir = Path(__file__).parent
    print(f"📍 当前工作目录: {script_dir}")
    
    # 检查必要文件
    if not (script_dir / "main.py").exists():
        print("❌ 未找到 main.py 文件，请确保在 academic_papers/arxiv 目录下运行")
        sys.exit(1)
    
    if not (script_dir / "config.json").exists():
        print("❌ 未找到 config.json 文件，请确保配置文件存在")
        sys.exit(1)
    
    # 开始批量爬取
    batch_crawl_categories()
