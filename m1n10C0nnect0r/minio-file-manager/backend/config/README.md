# Elasticsearch 索引配置说明

## 配置文件位置
`config/elasticsearch_mappings.json`

## 配置结构

配置文件包含 Elasticsearch 索引的映射和设置定义。索引配置包括：

- `mappings`: 字段映射定义
- `settings`: 索引设置（分片数、副本数、分析器等）

## minio_articles - 文章内容索引

用于存储和搜索文章内容，支持中文分词。

**主要字段：**
- `id`: 文章唯一标识符
- `title`: 标题（支持IK分词）
- `summary`: 摘要
- `content`: 正文内容
- `category`: 分类
- `tags`: 标签
- `author`: 作者
- `publish_date`: 发布时间
- `read_time`: 阅读时间（分钟）
- `view_count`: 浏览次数
- `like_count`: 点赞次数
- `featured`: 是否推荐
- `member_only`: 是否会员专享

**分词器配置：**
- 使用 `ik_max_word` 进行索引
- 使用 `ik_smart` 进行搜索

**索引设置：**
- 分片数：1
- 副本数：0

## 修改配置

1. 编辑 `elasticsearch_mappings.json` 文件
2. 重启应用程序
3. 新的配置将在启动时自动应用

## 注意事项

1. **IK分词器依赖：** 如果使用中文分词，需要在Elasticsearch中安装 `elasticsearch-analysis-ik` 插件
2. **字段类型：** 修改已有字段类型需要重建索引
3. **分片设置：** 分片数量在索引创建后无法修改
4. **向后兼容：** 代码包含默认配置以确保向后兼容性

## 配置示例

```json
{
  "索引名称": {
    "mappings": {
      "properties": {
        "字段名": {
          "type": "字段类型",
          "analyzer": "分析器名称"
        }
      }
    },
    "settings": {
      "number_of_shards": 1,
      "number_of_replicas": 0
    }
  }
}
```
