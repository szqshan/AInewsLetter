#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json

# 读取原始数据
with open('crawled_data/daily/2025-08-10/daily_papers_all.json', 'r', encoding='utf-8') as f:
    papers = json.load(f)

print(f"原始论文数: {len(papers)}")

# 选择前5篇有效论文
test_papers = []
for paper in papers:
    if paper.get('title') and paper.get('abstract') and paper.get('arxiv_id'):
        test_papers.append(paper)
        if len(test_papers) >= 5:
            break

print(f"选择了 {len(test_papers)} 篇有效论文进行测试")

# 保存测试数据
with open('test_papers.json', 'w', encoding='utf-8') as f:
    json.dump(test_papers, f, indent=2, ensure_ascii=False)

print("测试数据已保存到 test_papers.json")

# 显示选择的论文
for i, paper in enumerate(test_papers, 1):
    print(f"{i}. {paper.get('title', 'Unknown')[:60]}... (ID: {paper.get('arxiv_id', 'Unknown')})")
