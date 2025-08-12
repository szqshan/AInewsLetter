# 📚 项目脚本说明

这个文件夹包含了项目的所有管理脚本，可以从项目根目录的scripts文件夹中直接运行。

## 🚀 启动脚本

### 1. 启动后端服务
```bash
./scripts/start_backend.sh
```
- 自动检查并清理9011端口
- 启动FastAPI后端服务
- API文档: http://localhost:9011/docs

### 2. 启动前端服务
```bash
./scripts/start_frontend.sh
```
- 自动检查并清理9010端口
- 自动安装依赖（首次运行）
- 自动创建配置文件
- 访问地址: http://localhost:9010

## 📊 查询脚本

### 3. 显示ES索引详情
```bash
# 显示默认索引
python3 scripts/show_es_details.py

# 显示特定索引
python3 scripts/show_es_details.py minio_files

# 显示所有索引
python3 scripts/show_es_details.py --all
```
显示信息包括：
- 文档数量和存储大小
- 字段结构和数据类型
- 索引设置（分片、副本）
- 最新文档样本
- 按存储桶和文件类型的分布统计

## 🧹 清理脚本

### 4. 清空Elasticsearch
```bash
# 交互式确认
python3 scripts/clear_es.py

# 直接清空（无需确认）
python3 scripts/clear_es.py -y
```
清空的索引：
- minio_files
- minio_documents
- minio_articles
- newsletter_articles

### 5. 清空MinIO存储桶
```bash
# 清理默认存储桶（交互式）
python3 scripts/clear_minio.py

# 清理默认存储桶（直接执行）
python3 scripts/clear_minio.py -y

# 清理所有存储桶（需确认）
python3 scripts/clear_minio.py --all

# 清理所有存储桶（直接执行）
python3 scripts/clear_minio.py --all -y

# 清理指定存储桶
python3 scripts/clear_minio.py bucket1 bucket2
```

默认存储桶：
- test-bucket
- test-articles
- test-documents
- newsletter-articles
- newsletter-articles-nlp

## 💡 快速启动指南

1. **首次启动**
```bash
# 在项目根目录执行
./scripts/start_backend.sh    # 终端1
./scripts/start_frontend.sh   # 终端2
```

2. **清理数据**
```bash
# 在项目根目录执行
python3 scripts/clear_es.py -y      # 清空ES
python3 scripts/clear_minio.py -y   # 清空MinIO
```

3. **后台运行**
如需后台运行，编辑脚本文件，取消后台运行部分的注释。

## 📝 注意事项

- 所有脚本都应该从项目根目录运行
- 脚本会自动找到正确的工作目录
- 清理脚本有安全确认机制，使用 `-y` 参数可跳过确认
- 日志文件默认输出到控制台，可修改脚本实现文件输出

## 🔧 环境要求

- Python 3.x
- Node.js & npm
- 正确配置的 `.env` 文件（后端）
- 网络连接（访问远程ES和MinIO）