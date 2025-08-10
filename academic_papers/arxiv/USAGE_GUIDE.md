# 📖 增强版 arXiv 爬虫使用指南

## 🚀 快速开始（5分钟）

### 第一步：安装依赖
```bash
cd academic_papers/arxiv
pip install -r requirements.txt
```

### 第二步：查看系统信息
```bash
# 查看支持的所有AI分类
python main_enhanced_simple.py info --categories

# 查看默认热门关键词
python main_enhanced_simple.py info --keywords
```

### 第三步：测试爬取功能
```bash
# 小规模测试：爬取cs.AI分类最近3天的论文
python main_enhanced_simple.py daily --days 3 --categories cs.AI
```

### 第四步：查看结果
```bash
# 查看生成的文件
ls crawled_data/daily/*/

# 查看统计信息
cat crawled_data/daily/*/daily_stats.json
```

## 🎯 常用使用场景

### 场景1：每日AI新闻获取
```bash
# 获取昨天的所有AI新论文
python main_enhanced_simple.py daily --days 1

# 获取最近一周的AI论文
python main_enhanced_simple.py daily --days 7
```

### 场景2：专业方向研究
```bash
# 专注计算机视觉
python main_enhanced_simple.py category --categories cs.CV --max-per-category 500

# 专注自然语言处理
python main_enhanced_simple.py category --categories cs.CL cs.AI --max-per-category 300

# 专注机器学习理论
python main_enhanced_simple.py category --categories cs.LG stat.ML --max-per-category 400
```

### 场景3：热点技术追踪
```bash
# 追踪Transformer技术发展
python main_enhanced_simple.py keyword --keywords "transformer" "attention" --days 14

# 追踪大语言模型进展
python main_enhanced_simple.py keyword --keywords "LLM" "large language model" --days 7

# 追踪扩散模型研究
python main_enhanced_simple.py keyword --keywords "diffusion" "stable diffusion" --days 10
```

### 场景4：全面数据收集
```bash
# 收集所有AI相关分类的论文（大量数据）
python main_enhanced_simple.py category --max-per-category 1000

# 收集所有热门关键词的论文
python main_enhanced_simple.py keyword --days 14
```

## 📊 输出数据说明

### 每日爬取输出
```
crawled_data/daily/2025-08-10/
├── daily_papers_all.json          # 所有论文的完整信息
├── daily_papers_by_category.json  # 按分类组织的论文
└── daily_stats.json               # 爬取统计信息
```

### 关键词爬取输出
```
crawled_data/weekly/2025-W32/
├── weekly_papers_by_keyword.json      # 按关键词组织的论文
├── weekly_papers_deduplicated.json    # 去重后的论文集合
└── weekly_stats.json                  # 爬取统计信息
```

### 分类爬取输出
```
crawled_data/category/
├── papers_by_category.json    # 按分类组织的论文
├── all_papers.json           # 所有论文合集
└── category_stats.json       # 分类统计信息
```

## 🔧 配置优化

### 调整爬取数量
编辑 `config_enhanced.json`:
```json
{
  "crawl_strategies": {
    "daily_new": {
      "max_results": 1000,  // 每日最大爬取数量
      "concurrent": 5       // 并发数量
    }
  }
}
```

### 添加自定义关键词
```json
{
  "crawler": {
    "trending_keywords": [
      "你的关键词1",
      "你的关键词2",
      "transformer",
      "diffusion"
    ]
  }
}
```

### 自定义分类组合
```json
{
  "crawler": {
    "ai_categories": {
      "my_focus": ["cs.AI", "cs.LG"],
      "nlp_research": ["cs.CL"],
      "vision_research": ["cs.CV"]
    }
  }
}
```

## 💡 最佳实践

### 1. 控制爬取频率
```bash
# 小量测试（适合日常使用）
python main_enhanced_simple.py daily --days 1 --categories cs.AI

# 中量爬取（适合周度更新）
python main_enhanced_simple.py daily --days 7

# 大量爬取（适合初始化数据）
python main_enhanced_simple.py category --max-per-category 1000
```

### 2. 合理设置时间范围
- **每日爬取**: 1-3天回溯（获取最新论文）
- **关键词爬取**: 7-14天回溯（获取足够样本）
- **分类爬取**: 不限时间（获取全量数据）

### 3. 分批处理大量数据
```bash
# 分别爬取不同分类，避免一次请求过多
python main_enhanced_simple.py category --categories cs.AI --max-per-category 500
python main_enhanced_simple.py category --categories cs.LG --max-per-category 500
python main_enhanced_simple.py category --categories cs.CL --max-per-category 500
```

### 4. 定期清理旧数据
```bash
# 手动清理30天前的数据
find crawled_data/daily -type d -mtime +30 -exec rm -rf {} \;
```

## ⚠️ 常见问题

### Q1: 爬取结果为0篇论文？
**A**: 可能是时间范围太小，尝试增加 `--days` 参数：
```bash
# 从1天增加到7天
python main_enhanced_simple.py daily --days 7 --categories cs.AI
```

### Q2: 爬取速度慢？
**A**: 可以调整并发参数（在配置文件中）：
```json
{
  "crawler": {
    "max_concurrent_papers": 5,  // 增加并发数
    "request_delay": 1           // 减少延迟（小心使用）
  }
}
```

### Q3: 内存占用高？
**A**: 减少单次爬取数量：
```bash
# 从1000减少到200
python main_enhanced_simple.py category --max-per-category 200
```

### Q4: 网络连接失败？
**A**: 检查网络连接，或增加重试次数：
```json
{
  "crawler": {
    "max_retries": 5,  // 增加重试次数
    "timeout": 60      // 增加超时时间
  }
}
```

## 📈 数据分析示例

### 使用Python分析爬取数据
```python
import json
from collections import Counter

# 读取每日爬取数据
with open('crawled_data/daily/2025-08-10/daily_papers_all.json', 'r') as f:
    papers = json.load(f)

# 分析作者分布
authors = []
for paper in papers:
    authors.extend(paper.get('authors', []))

author_counts = Counter(authors)
print("高产作者Top 10:")
for author, count in author_counts.most_common(10):
    print(f"{author}: {count}篇")

# 分析分类分布
categories = []
for paper in papers:
    categories.extend(paper.get('categories', []))

category_counts = Counter(categories)
print("\n热门分类Top 10:")
for category, count in category_counts.most_common(10):
    print(f"{category}: {count}篇")
```

### 生成简单报告
```python
import json
from datetime import datetime

def generate_daily_report(date_str):
    """生成每日爬取报告"""
    stats_file = f'crawled_data/daily/{date_str}/daily_stats.json'
    
    with open(stats_file, 'r') as f:
        stats = json.load(f)
    
    print(f"📊 {date_str} AI论文爬取报告")
    print("=" * 40)
    print(f"总论文数: {stats['total_papers']}")
    print(f"时间范围: {stats['date_range']['earliest']} - {stats['date_range']['latest']}")
    print(f"爬取时间: {stats['crawl_date']}")
    
    if 'categories_stats' in stats:
        print("\n分类统计:")
        for category, count in stats['categories_stats'].items():
            print(f"  {category}: {count}篇")

# 使用示例
generate_daily_report('2025-08-10')
```

## 🎯 进阶用法

### 1. 批量爬取脚本
```bash
#!/bin/bash
# batch_crawl.sh - 批量爬取脚本

echo "开始批量爬取AI论文..."

# 每日更新
python main_enhanced_simple.py daily --days 1

# 关键词追踪
python main_enhanced_simple.py keyword --keywords "transformer" "LLM" --days 3

# 分类更新（仅核心分类）
python main_enhanced_simple.py category --categories cs.AI cs.LG cs.CL --max-per-category 100

echo "批量爬取完成！"
```

### 2. 数据合并脚本
```python
# merge_data.py - 合并多次爬取的数据
import json
import glob
from pathlib import Path

def merge_daily_data():
    """合并所有每日爬取数据"""
    all_papers = []
    
    # 获取所有每日数据文件
    daily_files = glob.glob('crawled_data/daily/*/daily_papers_all.json')
    
    for file_path in daily_files:
        with open(file_path, 'r') as f:
            papers = json.load(f)
            all_papers.extend(papers)
    
    # 去重（基于arXiv ID）
    seen_ids = set()
    unique_papers = []
    
    for paper in all_papers:
        arxiv_id = paper.get('arxiv_id')
        if arxiv_id and arxiv_id not in seen_ids:
            unique_papers.append(paper)
            seen_ids.add(arxiv_id)
    
    # 保存合并结果
    output_file = 'crawled_data/merged_papers.json'
    with open(output_file, 'w') as f:
        json.dump(unique_papers, f, indent=2, ensure_ascii=False)
    
    print(f"✅ 合并完成: {len(unique_papers)} 篇论文 → {output_file}")

if __name__ == "__main__":
    merge_daily_data()
```

---

## 🎉 开始使用

选择适合你需求的命令，开始体验增强版arXiv爬虫的强大功能：

```bash
# 🔥 推荐：每日AI论文获取
python main_enhanced_simple.py daily --days 3

# 🎯 精准：特定方向深入研究  
python main_enhanced_simple.py category --categories cs.AI --max-per-category 500

# 🚀 热点：追踪前沿技术发展
python main_enhanced_simple.py keyword --keywords "transformer" "LLM" --days 7
```

**让AI论文获取变得简单高效！** 📚✨
