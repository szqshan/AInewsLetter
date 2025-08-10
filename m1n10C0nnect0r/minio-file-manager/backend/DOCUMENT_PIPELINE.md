# 文档处理管道（Document Pipeline）

## 概述

文档处理管道是一个智能的文件上传系统，当检测到上传的文件是 Markdown、HTML 或其他可配置的文档格式时，系统会自动：

1. **上传到 MinIO** - 存储原始文件
2. **提取内容** - 解析文档内容和元数据
3. **索引到 Elasticsearch** - 创建可搜索的索引
4. **生成公开 URL** - 提供 MinIO 的公开访问地址

## 支持的文件格式

默认支持以下格式（可配置）：
- **Markdown** (.md, .markdown)
- **HTML** (.html, .htm)
- **Text** (.txt) - 可选
- **reStructuredText** (.rst) - 可选

## 核心功能

### 1. 自动内容提取
- **Markdown 文件**：
  - 提取标题、子标题
  - 识别代码块
  - 转换为纯文本和 HTML
  - 提取链接和 URL

- **HTML 文件**：
  - 提取 title 标签
  - 解析 meta 标签（description, keywords, author）
  - 转换为纯文本
  - 保留结构信息

### 2. 智能索引
- 自动计算内容哈希（用于去重）
- 统计字数、字符数、行数
- 提取 URL 列表
- 生成多维度的搜索索引

### 3. 模糊搜索
- 自动纠正拼写错误
- 支持近似匹配
- 短语前缀匹配
- 通配符搜索
- 多字段权重搜索（标题权重更高）

### 4. 相似文档推荐
- 基于内容的相似度计算
- More Like This 算法
- 自动排除源文档
- 按相似度评分排序

## API 端点

### 上传文件（带 Pipeline）
```http
POST /api/v1/objects/{bucket_name}/upload
```

参数：
- `file`: 文件内容
- `object_name`: 自定义文件名（可选）
- `use_pipeline`: 是否使用文档处理管道（默认：true）
- `metadata`: JSON 格式的元数据（可选）

响应示例：
```json
{
  "bucket": "documents",
  "object_name": "2024/project.md",
  "etag": "d41d8cd98f00b204e9800998ecf8427e",
  "size": 2048,
  "message": "文件已成功上传到MinIO并索引到Elasticsearch",
  "public_url": "http://minio:9000/documents/2024/project.md",
  "es_indexed": true,
  "es_document_id": "abc123def456"
}
```

### 搜索文档
```http
GET /api/v1/documents/search
```

参数：
- `query`: 搜索关键词（必填）
- `fuzzy`: 是否启用模糊搜索（默认：true）
- `bucket_name`: 限定搜索的存储桶（可选）
- `document_type`: 文档类型过滤（可选）
- `size`: 返回结果数量（默认：20）

响应示例：
```json
{
  "total": 5,
  "documents": [
    {
      "_id": "abc123",
      "_score": 8.5,
      "title": "项目文档.md",
      "bucket_name": "documents",
      "object_name": "2024/project.md",
      "minio_public_url": "http://minio:9000/documents/2024/project.md",
      "document_type": "markdown",
      "statistics": {
        "word_count": 1500,
        "char_count": 9011
      },
      "_highlight": {
        "content": ["...匹配的<mark>关键词</mark>片段..."],
        "title": ["<mark>项目</mark>文档.md"]
      }
    }
  ]
}
```

### 获取相似文档
```http
GET /api/v1/documents/similar/{document_id}
```

参数：
- `document_id`: 源文档的 ID（content_hash）
- `size`: 返回结果数量（默认：10）

### 文档统计
```http
GET /api/v1/documents/stats
```

返回文档索引的统计信息，包括总数、类型分布、存储桶分布等。

## 配置选项

在 `.env` 文件中配置：

```env
# 文档管道配置
DOCUMENT_PIPELINE_ENABLED=true
DOCUMENT_PIPELINE_TYPES=["markdown", "html"]
DOCUMENT_PIPELINE_INDEX=minio_documents
DOCUMENT_PIPELINE_MAX_CONTENT_SIZE=50000
```

## 使用示例

### Python 示例
```python
import requests

# 上传 Markdown 文件
with open('README.md', 'rb') as f:
    files = {'file': ('README.md', f, 'text/markdown')}
    response = requests.post(
        'http://localhost:9011/api/v1/objects/documents/upload',
        files=files,
        params={'use_pipeline': 'true'}
    )
    result = response.json()
    print(f"文件已上传: {result['public_url']}")
    print(f"ES索引ID: {result['es_document_id']}")

# 搜索文档
search_response = requests.get(
    'http://localhost:9011/api/v1/documents/search',
    params={'query': '项目', 'fuzzy': 'true'}
)
docs = search_response.json()
for doc in docs['documents']:
    print(f"找到: {doc['title']} (评分: {doc['_score']})")
```

### JavaScript 示例
```javascript
// 上传文件
const formData = new FormData();
formData.append('file', fileInput.files[0]);

const uploadResponse = await fetch(
  `/api/v1/objects/documents/upload?use_pipeline=true`,
  {
    method: 'POST',
    body: formData
  }
);
const result = await uploadResponse.json();
console.log('公开URL:', result.public_url);

// 搜索文档
const searchResponse = await fetch(
  `/api/v1/documents/search?query=项目&fuzzy=true`
);
const docs = await searchResponse.json();
docs.documents.forEach(doc => {
  console.log(`${doc.title} - 评分: ${doc._score}`);
});
```

## 测试脚本

运行测试脚本验证功能：

```bash
python test_document_pipeline.py
```

测试脚本会：
1. 创建测试文件（MD、HTML、TXT）
2. 上传到 MinIO
3. 验证 ES 索引
4. 测试搜索功能（精确和模糊）
5. 测试相似文档推荐
6. 显示统计信息

## 性能优化

1. **批量处理**：对于大量文件，建议使用批量上传
2. **内容限制**：默认索引前 50000 字符，可配置
3. **异步处理**：所有操作都是异步的，提高并发性能
4. **缓存**：ES 自动缓存常用查询

## 注意事项

1. **去重**：系统使用内容哈希自动去重
2. **编码**：自动处理 UTF-8 编码，其他编码可能出现乱码
3. **大文件**：超大文档会被截断索引，但原文件完整保存
4. **权限**：确保 MinIO 存储桶有适当的访问权限
5. **ES 连接**：确保 Elasticsearch 服务正常运行

## 故障排除

### 文件未被索引
- 检查文件类型是否在配置的支持列表中
- 确认 `use_pipeline` 参数为 `true`
- 查看服务器日志确认 ES 连接正常

### 搜索无结果
- 等待 1-2 秒让 ES 完成索引
- 尝试使用模糊搜索
- 检查搜索关键词是否存在于文档中

### 公开 URL 无法访问
- 确认 MinIO 存储桶设置为公开访问
- 检查网络连接和防火墙设置
- 验证 MinIO 服务正常运行