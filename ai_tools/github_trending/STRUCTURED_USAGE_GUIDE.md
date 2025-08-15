# 📚 GitHub Trending 结构化爬虫使用指南

> 按时间维度分类，结构化存储，智能去重的GitHub AI工具爬虫

## 🎯 核心特性

### ✨ 主要功能
- **📅 三时间维度**: daily、weekly、monthly 热度排行榜
- **🔄 智能去重**: 自动跳过已爬取的重复项目
- **📁 单独目录**: 每个AI工具创建独立存储文件夹
- **🏗️ arXiv架构**: 参考arXiv爬虫的企业级存储架构
- **🤖 AI识别**: 智能识别AI相关项目
- **📊 质量评分**: 多维度项目质量评估
- **🏆 排行榜**: 自动生成各时间维度排行榜

### 🛠️ 技术特点
- **异步爬取**: 高性能并发处理
- **API增强**: GitHub API获取详细信息
- **结构化存储**: 标准化数据格式
- **存储集成**: 支持MinIO+PostgreSQL+Elasticsearch三层存储

## 📋 快速开始

### 1. 环境准备
```bash
# 安装依赖
pip install aiohttp aiofiles beautifulsoup4 python-dateutil

# 检查GitHub Token配置
ls github_config.py
```

### 2. 基础使用
```bash
# 完整爬取所有时间维度
python run_structured_crawler.py

# 只爬取每日trending
python run_structured_crawler.py --time-range daily

# 自定义输出目录
python run_structured_crawler.py --output my_github_data
```

### 3. 查看结果
```bash
# 显示目录结构
python run_structured_crawler.py --show-structure

# 查看排行榜
cat crawled_data/rankings/daily/ranking_daily_*.md
```

## 📁 输出目录结构

```
crawled_data/
├── 📂 tools/                    # 每个工具的单独目录
│   ├── 📂 daily/               # 每日trending工具
│   │   ├── 📁 microsoft_vscode_vscode/
│   │   │   ├── content.md      # 工具详细信息
│   │   │   └── metadata.json   # 元数据
│   │   └── 📁 facebook_react_react/
│   │       ├── content.md
│   │       └── metadata.json
│   ├── 📂 weekly/              # 每周trending工具  
│   └── 📂 monthly/             # 每月trending工具
├── 📂 data/                    # 聚合数据JSON
│   ├── 📂 daily/
│   ├── 📂 weekly/
│   └── 📂 monthly/
├── 📂 rankings/                # 热度排行榜
│   ├── 📂 daily/
│   ├── 📂 weekly/
│   └── 📂 monthly/
├── 📂 metadata/                # 去重记录
│   └── processed_repos.json
└── comprehensive_report_*.md    # 综合报告
```

## 🔍 详细功能说明

### 📅 时间维度爬取

#### 支持的时间范围
- **daily**: 每日trending（最新热门项目）
- **weekly**: 每周trending（一周内热门项目）
- **monthly**: 每月trending（一月内热门项目）

#### 使用示例
```bash
# 爬取所有时间维度
python run_structured_crawler.py --time-range all

# 单独爬取
python run_structured_crawler.py --time-range daily
python run_structured_crawler.py --time-range weekly  
python run_structured_crawler.py --time-range monthly
```

### 🔄 智能去重机制

#### 去重策略
1. **跨时间维度去重**: 同一项目在不同时间维度只存储一次
2. **基于仓库全名**: 使用 `owner/repo` 作为唯一标识
3. **持久化记录**: 去重信息保存在 `metadata/processed_repos.json`
4. **增量爬取**: 支持多次运行，只爬取新项目

#### 去重示例
```json
{
  "processed_repos": [
    "microsoft_vscode",
    "facebook_react", 
    "tensorflow_tensorflow"
  ],
  "last_updated": "2024-01-15T10:30:00Z",
  "total_count": 3
}
```

### 📁 单独目录存储

#### 目录命名规则
```
{owner}_{repo_name}_{simplified_name}/
```

#### 目录内容
```
microsoft_vscode_vscode/
├── content.md          # Markdown格式的完整信息
└── metadata.json       # JSON格式的元数据
```

#### content.md 格式示例
```markdown
# Visual Studio Code

## 基本信息
- **项目名称**: microsoft/vscode
- **GitHub ID**: microsoft_vscode
- **创建日期**: 2015-09-03
- **最后更新**: 2024-01-15
- **主要语言**: TypeScript
- **开源许可**: MIT

## 链接
- **GitHub链接**: https://github.com/microsoft/vscode
- **Stars数量**: 150,000
- **Forks数量**: 26,000

## 项目描述
Visual Studio Code - lightweight but powerful source code editor

## 技术标签
editor, typescript, javascript, electron

## 项目统计
- **⭐ Stars**: 150,000
- **🍴 Forks**: 26,000
- **👁️ Watchers**: 3,500
- **📂 Issues**: 5,200

## 质量评估
- **质量评分**: 95.5/100
- **活跃度**: 高
- **社区热度**: 高
```

### 🤖 AI相关性识别

#### 识别关键词库
```python
AI_KEYWORDS = [
    # 核心AI关键词
    "artificial intelligence", "machine learning", "deep learning",
    "neural network", "transformer", "llm", "large language model",
    
    # 技术框架
    "pytorch", "tensorflow", "keras", "scikit-learn", "huggingface",
    "openai", "anthropic", "langchain", "llamaindex",
    
    # 应用领域  
    "computer vision", "nlp", "natural language processing",
    "stable diffusion", "diffusion model", "generative ai",
    
    # 新兴技术
    "multimodal", "embedding", "vector database", "rag",
    "fine-tuning", "prompt engineering", "ai agent"
]
```

#### 识别规则
1. **文本检查**: 项目名称 + 描述 + GitHub标签
2. **关键词匹配**: 包含任一AI关键词即认为相关
3. **大小写不敏感**: 自动转换为小写匹配

### 📊 质量评分系统

#### 评分维度 (总分100分)
1. **Stars权重 (40%)**
   - 10,000+ stars: 40分
   - 1,000+ stars: 30分
   - 100+ stars: 20分
   - 10+ stars: 10分

2. **活跃度权重 (25%)**
   - 7天内更新: 25分
   - 30天内更新: 20分
   - 90天内更新: 15分
   - 365天内更新: 10分

3. **社区参与度权重 (20%)**
   - 基于 forks 和 watchers 数量

4. **项目完整性权重 (15%)**
   - 有开源许可证: +5分
   - 有Wiki文档: +3分
   - 有GitHub标签: +1分/标签 (最多7分)

### 🏆 排行榜生成

#### 排行榜特点
- **按质量分排序**: 综合质量评分从高到低
- **Top 20展示**: 每个时间维度显示前20名
- **详细信息**: 包含Stars、语言、质量分等信息
- **奖牌标识**: 前三名有特殊奖牌标识

#### 排行榜示例
```markdown
# GitHub Trending AI工具排行榜 - Daily

## 🏆 Top 20 AI工具排行榜

### 🥇 [tensorflow/tensorflow](https://github.com/tensorflow/tensorflow)
**描述**: An Open Source Machine Learning Framework for Everyone
**技术信息**:
- 💫 Stars: 185,000
- 💻 语言: C++
- 🎯 质量评分: 98.5/100

### 🥈 [pytorch/pytorch](https://github.com/pytorch/pytorch)  
**描述**: Tensors and Dynamic neural networks in Python
**技术信息**:
- 💫 Stars: 78,000
- 💻 语言: Python
- 🎯 质量评分: 96.2/100
```

## 🔗 存储架构集成

### 三层存储架构
参考arXiv爬虫的企业级存储架构：

```
数据流向: 本地存储 → MinIO对象存储 → PostgreSQL元数据 → Elasticsearch索引
```

### 集成步骤

#### 1. 检查存储连接
```bash
python storage_integrator.py --check
```

#### 2. 上传数据到存储架构
```bash
python storage_integrator.py --upload
```

#### 3. 查看集成指南
```bash
python storage_integrator.py --report
```

### 存储架构服务

| 服务 | 地址 | 用途 |
|------|------|------|
| MinIO对象存储 | `60.205.160.74:9000` | 文件存储 |
| PostgreSQL数据库 | `60.205.160.74:5432` | 元数据存储 |
| Elasticsearch搜索 | `60.205.160.74:9200` | 全文检索 |
| MinIO连接器API | `localhost:9011` | 数据管理接口 |

### 集成后的数据访问

#### 通过API搜索
```bash
# 搜索GitHub AI工具
curl "http://localhost:9011/api/v1/elasticsearch/search?index=minio_articles&query=github_trending&size=10"

# 搜索特定语言工具
curl "http://localhost:9011/api/v1/elasticsearch/search?index=minio_articles&query=python&size=10"
```

#### 直接访问MinIO
```bash
# 访问具体工具内容
http://60.205.160.74:9000/github-trending-tools/github_tools/[tool_name]/content.md
```

## 🧪 测试和验证

### 运行测试套件
```bash
python test_structured.py
```

### 测试内容
1. **目录结构创建**: 验证所有必要目录正确创建
2. **去重功能**: 验证重复项目识别机制
3. **AI识别功能**: 验证AI相关性判断准确性
4. **完整爬取流程**: 端到端功能测试

### 预期测试结果
```
🚀 结构化GitHub爬虫完整测试套件
==================================================

📝 执行测试: 目录结构创建
------------------------------
✅ 目录结构创建测试通过

📝 执行测试: 去重功能  
------------------------------
✅ 去重功能测试通过

📝 执行测试: AI识别功能
------------------------------
✅ AI识别功能测试通过

📝 执行测试: 完整爬取流程
------------------------------
✅ 完整爬取流程: 通过

==================================================
📊 测试结果: 4/4 通过
🎉 所有测试通过! 结构化爬虫可以正常使用
```

## 📈 使用场景

### 1. AI工具发现
- **技术调研**: 发现最新的AI工具和框架
- **趋势分析**: 了解AI领域的发展趋势
- **竞品分析**: 分析同类AI产品的受欢迎程度

### 2. 开发者工具
- **工具选型**: 基于质量评分选择合适的AI工具
- **学习资源**: 发现高质量的AI学习项目
- **技术栈决策**: 了解主流AI技术栈的使用情况

### 3. 研究用途
- **数据收集**: 为AI研究收集GitHub数据
- **社区分析**: 分析AI开源社区的活跃度
- **项目评估**: 评估AI项目的质量和影响力

## ⚠️ 注意事项

### API限制
- **GitHub API**: 每小时5000次请求（有Token）
- **请求间隔**: 默认1秒间隔，避免频率限制
- **并发控制**: 建议不超过5个并发请求

### 存储空间
- **本地存储**: 每个工具约5-10KB
- **MinIO存储**: 支持大规模数据存储
- **定期清理**: 建议定期清理测试数据

### 网络要求
- **稳定网络**: 需要稳定的网络连接
- **GitHub访问**: 确保能正常访问GitHub
- **存储架构**: 集成时需要内网访问存储服务

## 🔧 故障排除

### 常见问题

#### 1. API Token无效
```bash
❌ API请求失败 401: microsoft/vscode
```
**解决方案**: 检查 `github_config.py` 中的API Token是否正确

#### 2. 存储连接失败
```bash
❌ MinIO连接器: 连接失败 (connection refused)
```
**解决方案**: 
1. 启动MinIO连接器服务
2. 检查服务端口是否正确
3. 确认网络连接正常

#### 3. 目录权限问题
```bash
❌ 创建目录失败: Permission denied
```
**解决方案**: 确保有输出目录的写权限

#### 4. 内存不足
```bash
❌ 爬取过程出现错误: Memory error
```
**解决方案**: 
1. 减少并发数量
2. 增加系统内存
3. 分批处理数据

### 调试技巧

#### 启用详细日志
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

#### 检查网络连接
```bash
curl -I https://github.com
curl -I http://localhost:9011/api/v1/buckets
```

#### 验证数据完整性
```bash
# 检查工具目录
find crawled_data/tools -name "*.md" | wc -l
find crawled_data/tools -name "*.json" | wc -l

# 检查去重记录
cat crawled_data/metadata/processed_repos.json
```

## 🚀 进阶使用

### 自定义配置

#### 修改AI关键词
编辑 `github_config.py` 中的 `ai_keywords` 列表

#### 调整质量评分权重
修改 `structured_spider.py` 中的 `_calculate_quality_score` 方法

#### 更改输出格式
自定义 `_generate_tool_content_md` 方法

### 扩展功能

#### 添加新的时间维度
在 `time_ranges` 列表中添加新值

#### 支持更多编程语言
修改 `languages` 列表

#### 集成其他数据源
参考现有API集成模式

### 自动化部署

#### 定时任务
```bash
# 添加到crontab
0 */6 * * * cd /path/to/github_trending && python run_structured_crawler.py
```

#### Docker部署
```dockerfile
FROM python:3.9
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt
CMD ["python", "run_structured_crawler.py"]
```

## 📚 相关文档

- [arXiv爬虫存储架构参考文档](../../arXiv爬虫存储架构参考文档.md)
- [GitHub API文档](https://docs.github.com/en/rest)
- [MinIO对象存储文档](https://docs.min.io/)

---

## 🎉 总结

GitHub Trending结构化爬虫提供了一套完整的AI工具发现和管理解决方案：

✅ **时间维度分类**: 支持daily/weekly/monthly三种trending  
✅ **智能去重**: 避免重复爬取，提高效率  
✅ **结构化存储**: 每个工具单独目录，便于管理  
✅ **企业级架构**: 集成MinIO+PostgreSQL+Elasticsearch  
✅ **质量评估**: 多维度评分，筛选高质量项目  
✅ **自动排行榜**: 生成热度排行榜，发现趋势  

通过这套工具，您可以高效地发现、收集和管理GitHub上的AI相关项目，为技术决策和研究提供数据支持！🚀
