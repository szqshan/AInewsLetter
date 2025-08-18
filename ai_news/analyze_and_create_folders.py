#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分析HTML文件中的40个网站链接，与已有爬虫项目对比，为新网站创建文件夹
"""

import os
import re
import json
from urllib.parse import urlparse
from pathlib import Path

# HTML文件中的40个网站数据
sources_data = [
    {"name": "Google DeepMind", "link": "https://deepmind.google/"},
    {"name": "Meta AI", "link": "https://ai.meta.com/blog/"},
    {"name": "OpenAI", "link": "https://openai.com/news/"},
    {"name": "Anthropic", "link": "https://www.anthropic.com/news"},
    {"name": "Mistral AI", "link": "https://mistral.ai/news/"},
    {"name": "Cohere", "link": "https://cohere.com/blog"},
    {"name": "Perplexity AI", "link": "https://blog.perplexity.ai/"},
    {"name": "Stability AI", "link": "https://stability.ai/news"},
    {"name": "Hugging Face", "link": "https://huggingface.co/blog"},
    {"name": "Runway", "link": "https://runwayml.com/blog/"},
    {"name": "Midjourney", "link": "https://docs.midjourney.com/blog"},
    {"name": "Character.AI", "link": "https://blog.character.ai/"},
    {"name": "Replicate", "link": "https://replicate.com/blog"},
    {"name": "Together AI", "link": "https://www.together.ai/blog"},
    {"name": "Fireworks AI", "link": "https://fireworks.ai/blog"},
    {"name": "Groq", "link": "https://groq.com/news/"},
    {"name": "Cerebras", "link": "https://www.cerebras.net/blog/"},
    {"name": "SambaNova", "link": "https://sambanova.ai/blog/"},
    {"name": "Scale AI", "link": "https://scale.com/blog"},
    {"name": "Weights & Biases", "link": "https://wandb.ai/site/articles"},
    {"name": "LangChain", "link": "https://blog.langchain.dev/"},
    {"name": "LlamaIndex", "link": "https://blog.llamaindex.ai/"},
    {"name": "Pinecone", "link": "https://www.pinecone.io/blog/"},
    {"name": "Weaviate", "link": "https://weaviate.io/blog"},
    {"name": "Chroma", "link": "https://blog.trychroma.com/"},
    {"name": "Qdrant", "link": "https://qdrant.tech/blog/"},
    {"name": "Milvus", "link": "https://milvus.io/blog"},
    {"name": "Google AI Blog", "link": "https://ai.googleblog.com/"},
    {"name": "Microsoft AI Blog", "link": "https://blogs.microsoft.com/ai/"},
    {"name": "NVIDIA AI Blog", "link": "https://blogs.nvidia.com/blog/category/deep-learning/"},
    {"name": "AWS AI Blog", "link": "https://aws.amazon.com/blogs/machine-learning/"},
    {"name": "IBM AI Blog", "link": "https://www.ibm.com/blog/category/artificial-intelligence/"},
    {"name": "Intel AI Blog", "link": "https://www.intel.com/content/www/us/en/artificial-intelligence/posts.html"},
    {"name": "Qualcomm AI Blog", "link": "https://www.qualcomm.com/news/onq/tag/artificial-intelligence"},
    {"name": "AMD AI Blog", "link": "https://www.amd.com/en/technologies/infinity-hub/ai.html"},
    {"name": "Papers with Code", "link": "https://paperswithcode.com/"},
    {"name": "Towards Data Science", "link": "https://towardsdatascience.com/"},
    {"name": "The Gradient", "link": "https://thegradient.pub/"},
    {"name": "Distill", "link": "https://distill.pub/"},
    {"name": "AI Research Blog", "link": "https://ai.facebook.com/blog/"}
]

# 已有的爬虫项目
existing_crawlers = {
    'Claude_newsroom': ['anthropic.com'],
    'Huggingface_blog': ['huggingface.co'],
    'OpenAI_newsroom': ['openai.com'],
    'Stability': ['stability.ai'],
    'X': ['x.com', 'twitter.com'],
    'chinese_media': [],  # 中文媒体
    'google_ai_blog': ['ai.googleblog.com'],
    'nlpSp1der': []  # 通用爬虫
}

def extract_domain(url):
    """提取URL的域名"""
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        # 移除www前缀
        if domain.startswith('www.'):
            domain = domain[4:]
        return domain
    except:
        return None

def is_duplicate(source, existing_crawlers):
    """检查是否已有对应的爬虫"""
    domain = extract_domain(source['link'])
    if not domain:
        return False
    
    for crawler_name, domains in existing_crawlers.items():
        for existing_domain in domains:
            if existing_domain in domain or domain in existing_domain:
                return True, crawler_name
    return False, None

def create_folder_name(source_name):
    """根据网站名称创建文件夹名"""
    # 移除特殊字符，替换空格为下划线
    folder_name = re.sub(r'[^\w\s-]', '', source_name)
    folder_name = re.sub(r'\s+', '_', folder_name)
    return folder_name

def main():
    base_dir = Path('d:/ThinkAI/newletter/spider/ai_news')
    
    print("分析40个网站链接...")
    print("=" * 50)
    
    duplicates = []
    new_sites = []
    
    for source in sources_data:
        is_dup, crawler_name = is_duplicate(source, existing_crawlers)
        if is_dup:
            duplicates.append({
                'name': source['name'],
                'link': source['link'],
                'existing_crawler': crawler_name
            })
        else:
            new_sites.append(source)
    
    print(f"发现重复网站 ({len(duplicates)} 个):")
    for dup in duplicates:
        print(f"  - {dup['name']} ({dup['link']}) -> 已有爬虫: {dup['existing_crawler']}")
    
    print(f"\n需要新建爬虫的网站 ({len(new_sites)} 个):")
    for site in new_sites:
        print(f"  - {site['name']} ({site['link']})")
    
    print(f"\n开始为 {len(new_sites)} 个新网站创建文件夹...")
    print("=" * 50)
    
    created_folders = []
    
    for site in new_sites:
        folder_name = create_folder_name(site['name'])
        folder_path = base_dir / folder_name
        
        try:
            # 创建文件夹
            folder_path.mkdir(exist_ok=True)
            
            # 创建README.md文件
            readme_content = f"""# {site['name']} 爬虫项目

## 网站信息
- **网站名称**: {site['name']}
- **网站链接**: {site['link']}
- **域名**: {extract_domain(site['link'])}

## 项目结构
```
{folder_name}/
├── README.md          # 项目说明文档
├── requirements.txt   # Python依赖包
├── spider.py         # 主爬虫脚本
├── run_crawler.py    # 爬虫运行脚本
└── uploader.py       # 数据上传脚本
```

## 开发计划
- [ ] 分析网站结构
- [ ] 开发爬虫脚本
- [ ] 测试数据抓取
- [ ] 集成数据上传
- [ ] 部署定时任务

## 使用说明
待开发完成后补充使用说明。
"""
            
            readme_path = folder_path / 'README.md'
            with open(readme_path, 'w', encoding='utf-8') as f:
                f.write(readme_content)
            
            created_folders.append({
                'name': site['name'],
                'folder': folder_name,
                'path': str(folder_path),
                'link': site['link']
            })
            
            print(f"✓ 创建文件夹: {folder_name}")
            
        except Exception as e:
            print(f"✗ 创建文件夹失败 {folder_name}: {e}")
    
    print(f"\n任务完成!")
    print(f"- 重复网站: {len(duplicates)} 个")
    print(f"- 新建文件夹: {len(created_folders)} 个")
    print(f"- 总计处理: {len(sources_data)} 个网站")
    
    # 保存结果到JSON文件
    result = {
        'duplicates': duplicates,
        'new_sites': created_folders,
        'summary': {
            'total_sites': len(sources_data),
            'duplicate_count': len(duplicates),
            'new_folders_count': len(created_folders)
        }
    }
    
    result_path = base_dir / 'folder_creation_result.json'
    with open(result_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"\n结果已保存到: {result_path}")

if __name__ == '__main__':
    main()