# -*- coding: utf-8 -*-
"""
OSS上传模块
"""

from .wrapper import OSSUploader
from .oss_uploader import ArxivOSSUploader, MinIOUploader

__all__ = ["OSSUploader", "ArxivOSSUploader", "MinIOUploader"]