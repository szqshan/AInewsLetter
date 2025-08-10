# -*- coding: utf-8 -*-
"""
文件工具模块
提供日志设置、配置加载、文件操作等基础功能
"""

import json
import logging
import os
import re
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional


def setup_logging(level: str = "INFO", log_file: Optional[str] = None) -> None:
    """设置日志配置
    
    Args:
        level: 日志级别 (DEBUG, INFO, WARNING, ERROR)
        log_file: 日志文件路径，如果为None则只输出到控制台
    """
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    handlers = [logging.StreamHandler()]
    if log_file:
        handlers.append(logging.FileHandler(log_file, encoding="utf-8"))
    
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format=log_format,
        handlers=handlers,
        force=True
    )


def load_config(config_path: str) -> Dict[str, Any]:
    """加载配置文件
    
    Args:
        config_path: 配置文件路径
        
    Returns:
        配置字典
        
    Raises:
        FileNotFoundError: 配置文件不存在
        json.JSONDecodeError: 配置文件格式错误
    """
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"配置文件不存在: {config_path}")
    
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)
    
    return config


def ensure_directory(path: str) -> None:
    """确保目录存在，如果不存在则创建
    
    Args:
        path: 目录路径
    """
    Path(path).mkdir(parents=True, exist_ok=True)


def safe_filename(filename: str, max_length: int = 100) -> str:
    """生成安全的文件名
    
    Args:
        filename: 原始文件名
        max_length: 最大长度
        
    Returns:
        安全的文件名
    """
    # 移除或替换不安全的字符
    safe_name = re.sub(r'[<>:"/\\|?*]', '_', filename)
    safe_name = re.sub(r'\s+', '_', safe_name)  # 替换空格
    safe_name = safe_name.strip('._')  # 移除开头和结尾的点和下划线
    
    # 限制长度
    if len(safe_name) > max_length:
        safe_name = safe_name[:max_length]
    
    return safe_name or "unnamed"


def calculate_file_hash(file_path: str, algorithm: str = "sha256") -> str:
    """计算文件哈希值
    
    Args:
        file_path: 文件路径
        algorithm: 哈希算法 (md5, sha1, sha256)
        
    Returns:
        文件哈希值
    """
    hash_obj = hashlib.new(algorithm)
    
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_obj.update(chunk)
    
    return hash_obj.hexdigest()


def save_json(data: Dict[str, Any], file_path: str, indent: int = 2) -> None:
    """保存数据为JSON文件
    
    Args:
        data: 要保存的数据
        file_path: 文件路径
        indent: JSON缩进
    """
    ensure_directory(os.path.dirname(file_path))
    
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=indent)


def load_json(file_path: str) -> Dict[str, Any]:
    """加载JSON文件
    
    Args:
        file_path: 文件路径
        
    Returns:
        JSON数据
    """
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_file_size_mb(file_path: str) -> float:
    """获取文件大小（MB）
    
    Args:
        file_path: 文件路径
        
    Returns:
        文件大小（MB）
    """
    return os.path.getsize(file_path) / (1024 * 1024)


def parse_size_string(size_str: str) -> int:
    """解析大小字符串为字节数
    
    Args:
        size_str: 大小字符串，如 "50MB", "1GB"
        
    Returns:
        字节数
    """
    size_str = size_str.upper().strip()
    
    if size_str.endswith("KB"):
        return int(float(size_str[:-2]) * 1024)
    elif size_str.endswith("MB"):
        return int(float(size_str[:-2]) * 1024 * 1024)
    elif size_str.endswith("GB"):
        return int(float(size_str[:-2]) * 1024 * 1024 * 1024)
    else:
        return int(size_str)