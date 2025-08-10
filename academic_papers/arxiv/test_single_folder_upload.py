#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试单个文件夹上传，验证文件夹结构
"""

import os
import sys
from pathlib import Path

# 添加src目录到Python路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

from upload_folder_structure import FolderStructureUploader

def test_single_folder():
    """测试单个文件夹上传"""
    articles_dir = "crawled_data/articles"
    
    # 初始化上传器
    uploader = FolderStructureUploader()
    
    # 查找第一个论文文件夹
    paper_folders = uploader.find_paper_folders(articles_dir)
    
    if not paper_folders:
        print("❌ 没有找到论文文件夹")
        return
    
    # 只测试第一个文件夹
    test_folder = paper_folders[0]
    folder_name = os.path.basename(test_folder)
    
    print(f"🧪 测试上传文件夹: {folder_name}")
    print(f"📁 文件夹路径: {test_folder}")
    
    # 显示文件夹内容
    print("\n📋 文件夹内容:")
    for root, dirs, files in os.walk(test_folder):
        level = root.replace(test_folder, '').count(os.sep)
        indent = ' ' * 2 * level
        print(f"{indent}{os.path.basename(root)}/")
        sub_indent = ' ' * 2 * (level + 1)
        for file in files:
            print(f"{sub_indent}{file}")
    
    # 创建存储桶
    if not uploader.create_bucket_if_not_exists():
        print("❌ 存储桶创建失败")
        return
    
    # 上传测试
    print(f"\n🚀 开始上传测试...")
    result = uploader.upload_paper_folder_complete(test_folder)
    
    print(f"\n📊 上传结果:")
    print(f"   成功: {result['success']}")
    print(f"   论文ID: {result['arxiv_id']}")
    print(f"   文件夹名: {result['folder_name']}")
    print(f"   总文件数: {result['total_files']}")
    print(f"   成功上传: {result['successful_uploads']}")
    
    if result['success']:
        print("\n✅ 上传成功的文件:")
        for upload_result in result['upload_results']:
            if upload_result['success']:
                print(f"   ✅ {upload_result['object_name']}")
            else:
                print(f"   ❌ {upload_result['relative_path']}: {upload_result.get('error', 'Unknown')}")
    
    return result['success']

if __name__ == "__main__":
    success = test_single_folder()
    if success:
        print("\n🎉 测试成功！现在可以检查MinIO中的文件夹结构")
    else:
        print("\n❌ 测试失败")

