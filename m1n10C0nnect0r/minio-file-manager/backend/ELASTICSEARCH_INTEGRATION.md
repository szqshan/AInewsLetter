# Elasticsearch集成说明

## 配置信息

已成功集成远程Elasticsearch服务器：
- **服务地址**: http://60.205.160.74:9200
- **用户名**: elastic
- **密码**: 已配置在.env文件中
- **索引名称**: minio_files

## 功能特性

### 1. 自动索引
- 文件上传时自动创建Elasticsearch索引
- 支持元数据索引（标签、作者、描述等）
- 文件删除时自动同步删除索引

### 2. 强大搜索
- 全文检索支持
- 模糊匹配与拼写纠错
- 搜索结果高亮显示
- 按存储桶、文件类型过滤
- 相关度评分排序

### 3. 统计分析
- 文件总数统计
- 按存储桶分布统计
- 按文件类型分布统计

## API端点

### 搜索文件
```
GET /api/v1/search/files?query=关键词&bucket=桶名&file_type=.pdf&page=1&size=20
POST /api/v1/search/files (高级搜索)
```

### 文件统计
```
GET /api/v1/search/stats
```

### 索引管理
```
DELETE /api/v1/search/index/{bucket_name}/{object_name}
POST /api/v1/search/reindex/{bucket_name}
```

## 测试验证

运行测试脚本验证所有功能：
```bash
cd backend
python3 test_elasticsearch.py
```

测试结果：
- ✅ 文件上传自动索引
- ✅ 多维度搜索功能
- ✅ 搜索结果高亮
- ✅ 文件删除同步索引
- ✅ 统计信息准确

## 使用示例

### 1. 上传文件（自动索引）
```python
import requests

files = {'file': ('报告.pdf', content, 'application/pdf')}
data = {'metadata': '{"tags":"重要,2024","author":"管理员"}'}

response = requests.post(
    'http://localhost:9011/api/v1/objects/bucket-name/upload',
    files=files,
    data=data
)
```

### 2. 搜索文件
```python
# 简单搜索
response = requests.get('http://localhost:9011/api/v1/search/files?query=2024')

# 高级搜索
response = requests.post(
    'http://localhost:9011/api/v1/search/files',
    json={
        "query": "报告 AND 2024",
        "bucket": "documents",
        "file_type": ".pdf",
        "page": 1,
        "size": 20
    }
)
```

### 3. 获取统计
```python
response = requests.get('http://localhost:9011/api/v1/search/stats')
stats = response.json()
print(f"总文件数: {stats['total_files']}")
```

## 注意事项

1. 确保Elasticsearch服务可访问
2. 首次运行会自动创建索引
3. 索引更新有轻微延迟（通常<1秒）
4. ES索引失败不会影响文件上传操作

## 故障排查

如果搜索功能不工作：
1. 检查ES服务状态
2. 验证.env中的配置
3. 查看backend.log日志
4. 确认网络连接正常