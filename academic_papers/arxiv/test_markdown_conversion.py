# test_markdown_conversion.py
import json

def convert_paper_to_markdown(paper):
    """将论文数据转换为Markdown格式"""
    title = paper.get("title", "").strip()
    abstract = paper.get("abstract", "").strip()
    authors = paper.get("authors", [])
    arxiv_id = paper.get("arxiv_id", "")
    url = paper.get("url", "")
    pdf_url = paper.get("pdf_url", "")
    published = paper.get("published", "")
    categories = paper.get("categories", [])
    primary_category = paper.get("primary_category", "")
    
    # 生成Markdown内容
    markdown_content = f"""# {title}

## 基本信息

- **arXiv ID**: {arxiv_id}
- **发布日期**: {published}
- **主要分类**: {primary_category}
- **所有分类**: {', '.join(categories)}
- **作者**: {', '.join(authors)}

## 链接

- **arXiv页面**: {url}
- **PDF下载**: {pdf_url}

## 摘要

{abstract}
"""
    
    return markdown_content

# 测试转换
if __name__ == "__main__":
    # 读取JSON数据
    with open("crawled_data/category/all_papers.json", "r", encoding="utf-8") as f:
        papers = json.load(f)
    
    # 取前3篇论文测试
    for i, paper in enumerate(papers[:3]):
        print(f"\n{'='*80}")
        print(f"论文 {i+1}: {paper.get('title', '')[:50]}...")
        print('='*80)
        
        markdown = convert_paper_to_markdown(paper)
        print(markdown)
        
        # 保存为测试文件
        with open(f"test_paper_{i+1}.md", "w", encoding="utf-8") as f:
            f.write(markdown)
        
        print(f"\n✅ 已保存为: test_paper_{i+1}.md")