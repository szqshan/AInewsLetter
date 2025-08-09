#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通用工具函数模块
提供各个爬虫共用的工具函数
"""

import os
import json
import time
import hashlib
import requests
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def safe_request(url: str, headers: Dict = None, params: Dict = None, 
                timeout: int = 30, max_retries: int = 3) -> Optional[requests.Response]:
    """
    安全的HTTP请求函数，带重试机制
    
    Args:
        url: 请求URL
        headers: 请求头
        params: 请求参数
        timeout: 超时时间
        max_retries: 最大重试次数
    
    Returns:
        Response对象或None
    """
    if headers is None:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    
    for attempt in range(max_retries):
        try:
            response = requests.get(url, headers=headers, params=params, timeout=timeout)
            response.raise_for_status()
            return response
        except requests.RequestException as e:
            logger.warning(f"Request failed (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # 指数退避
            else:
                logger.error(f"Request finally failed: {url}")
                return None

def save_json(data: Any, filepath: str, ensure_dir: bool = True) -> bool:
    """
    保存数据为JSON格式
    
    Args:
        data: 要保存的数据
        filepath: 文件路径
        ensure_dir: 是否确保目录存在
    
    Returns:
        是否保存成功
    """
    try:
        if ensure_dir:
            Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"✅ JSON文件已保存: {filepath}")
        return True
    except Exception as e:
        logger.error(f"❌ 保存JSON文件失败: {e}")
        return False

def load_json(filepath: str) -> Optional[Any]:
    """
    加载JSON文件
    
    Args:
        filepath: 文件路径
    
    Returns:
        加载的数据或None
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"❌ 加载JSON文件失败: {e}")
        return None

def save_markdown(content: str, filepath: str, ensure_dir: bool = True) -> bool:
    """
    保存Markdown文件
    
    Args:
        content: Markdown内容
        filepath: 文件路径
        ensure_dir: 是否确保目录存在
    
    Returns:
        是否保存成功
    """
    try:
        if ensure_dir:
            Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info(f"✅ Markdown文件已保存: {filepath}")
        return True
    except Exception as e:
        logger.error(f"❌ 保存Markdown文件失败: {e}")
        return False

def generate_filename(prefix: str, extension: str = "json", 
                     timestamp: bool = True) -> str:
    """
    生成文件名
    
    Args:
        prefix: 文件名前缀
        extension: 文件扩展名
        timestamp: 是否包含时间戳
    
    Returns:
        生成的文件名
    """
    if timestamp:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{prefix}_{ts}.{extension}"
    else:
        return f"{prefix}.{extension}"

def calculate_hash(text: str) -> str:
    """
    计算文本的MD5哈希值，用于去重
    
    Args:
        text: 输入文本
    
    Returns:
        MD5哈希值
    """
    return hashlib.md5(text.encode('utf-8')).hexdigest()

def clean_text(text: str) -> str:
    """
    清理文本，移除多余的空白字符
    
    Args:
        text: 输入文本
    
    Returns:
        清理后的文本
    """
    if not text:
        return ""
    
    # 移除多余的空白字符
    text = ' '.join(text.split())
    # 移除特殊字符
    text = text.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
    return text.strip()

def format_date(date_str: str, input_format: str = None, 
               output_format: str = "%Y-%m-%d") -> str:
    """
    格式化日期字符串
    
    Args:
        date_str: 输入日期字符串
        input_format: 输入格式
        output_format: 输出格式
    
    Returns:
        格式化后的日期字符串
    """
    try:
        if input_format:
            dt = datetime.strptime(date_str, input_format)
        else:
            # Try auto parsing
            from dateutil import parser
            dt = parser.parse(date_str)
        
        return dt.strftime(output_format)
    except Exception as e:
        logger.warning(f"日期格式化失败: {e}")
        return date_str

def deduplicate_list(items: List[Dict], key: str = "id") -> List[Dict]:
    """
    根据指定键去重列表
    
    Args:
        items: 要去重的列表
        key: 用于去重的键
    
    Returns:
        去重后的列表
    """
    seen = set()
    result = []
    
    for item in items:
        if key in item and item[key] not in seen:
            seen.add(item[key])
            result.append(item)
    
    return result

def create_progress_bar(total: int, desc: str = "Processing"):
    """
    创建进度条（简单版本）
    
    Args:
        total: 总数
        desc: 描述
    
    Returns:
        进度条函数
    """
    def update(current: int):
        percent = (current / total) * 100
        bar_length = 50
        filled_length = int(bar_length * current // total)
        bar = '█' * filled_length + '-' * (bar_length - filled_length)
        print(f'\r{desc}: |{bar}| {percent:.1f}% ({current}/{total})', end='', flush=True)
        if current == total:
            print()  # 换行
    
    return update

if __name__ == "__main__":
    # 测试函数
    print("🧪 测试工具函数...")
    
    # 测试文件名生成
    filename = generate_filename("test", "json")
    print(f"生成的文件名: {filename}")
    
    # 测试文本清理
    dirty_text = "  这是一个\n\t测试文本  \r\n  "
    clean = clean_text(dirty_text)
    print(f"清理前: '{dirty_text}'")
    print(f"清理后: '{clean}'")
    
    print("✅ 工具函数测试完成")
