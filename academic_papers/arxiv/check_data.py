#!/usr/bin/env python3
import json

# 读取论文数据
with open('crawled_data/daily/2025-08-10/daily_papers_all.json', 'r', encoding='utf-8') as f:
    papers = json.load(f)

print(f"总论文数: {len(papers)}")

if papers:
    first_paper = papers[0]
    print("\n第一篇论文的字段:")
    for key, value in first_paper.items():
        if isinstance(value, str):
            value_preview = value[:100] + "..." if len(value) > 100 else value
        else:
            value_preview = str(value)
        print(f"  {key}: {value_preview}")
    
    # 检查有多少论文有title和summary
    valid_papers = 0
    for paper in papers:
        if paper.get('title') and paper.get('summary'):
            valid_papers += 1
    
    print(f"\n有效论文数(有title和summary): {valid_papers}")
    
    # 检查字段名称
    print(f"\n可用字段: {list(first_paper.keys())}")
