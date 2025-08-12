# MinIO File Manager

一个基于 FastAPI 和 Next.js 的全栈 MinIO 文件管理系统，提供完整的文件操作功能。

## 功能特性

### 后端功能
- **桶管理**：创建、删除、列出桶
- **文件操作**：上传、下载、删除、复制文件
- **预授权 URL**：生成临时访问链接
- **桶策略**：设置和获取桶访问策略
- **Swagger 文档**：自动生成的 API 文档
- **模块化设计**：易于集成到其他项目

### 前端功能
- **现代 UI**：基于 Next.js 15 + React 19 + Tailwind CSS
- **拖拽上传**：支持拖拽和多文件上传
- **实时预览**：文件列表实时更新
- **状态管理**：使用 Zustand 进行状态管理

## 技术栈

### 后端
- FastAPI
- Python 3.8+
- MinIO Python SDK
- Pydantic
- uvicorn

### 前端
- Next.js 15
- React 19
- TypeScript
- Tailwind CSS 3
- shadcn/ui
- Zustand
- Lucide Icons

## 快速开始

### 环境要求
- Python 3.8+
- Node.js 18+
- MinIO 服务器

### 后端安装和运行

1. 进入后端目录
```bash
cd backend
```

2. 创建虚拟环境
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows
```

3. 安装依赖
```bash
pip install -r requirements.txt
```

4. 配置环境变量
编辑 `.env` 文件，设置你的 MinIO 连接信息：
```env
MINIO_ENDPOINT=your-minio-endpoint:9000
MINIO_ACCESS_KEY=your-access-key
MINIO_SECRET_KEY=your-secret-key
MINIO_USE_SSL=false
API_PORT=9011
API_HOST=0.0.0.0
```

5. 运行后端服务
```bash
python -m uvicorn app.main:app --reload --port 9011
```

6. 访问 API 文档
- Swagger UI: http://localhost:9011/docs
- ReDoc: http://localhost:9011/redoc

### 前端安装和运行

1. 进入前端目录
```bash
cd frontend
```

2. 安装依赖
```bash
npm install
```

3. 运行开发服务器
```bash
npm run dev
```

4. 访问应用
打开浏览器访问 http://localhost:9010

## API 端点

### 桶管理
- `GET /api/v1/buckets` - 列出所有桶
- `POST /api/v1/buckets` - 创建新桶
- `DELETE /api/v1/buckets/{bucket_name}` - 删除桶
- `GET /api/v1/buckets/{bucket_name}/policy` - 获取桶策略
- `PUT /api/v1/buckets/{bucket_name}/policy` - 设置桶策略
- `PUT /api/v1/buckets/{bucket_name}/make-public` - 设置桶为公开访问
- `PUT /api/v1/buckets/{bucket_name}/make-private` - 设置桶为私有访问

### 文件操作
- `GET /api/v1/objects/{bucket_name}` - 列出桶中的对象
- `POST /api/v1/objects/{bucket_name}/upload` - 上传文件
- `GET /api/v1/objects/{bucket_name}/{object_name}/download` - 下载文件
- `GET /api/v1/objects/{bucket_name}/{object_name}/info` - 获取文件信息
- `GET /api/v1/objects/{bucket_name}/{object_name}/public-url` - 获取文件公开访问URL
- `DELETE /api/v1/objects/{bucket_name}/{object_name}` - 删除文件
- `POST /api/v1/objects/copy` - 复制文件
- `POST /api/v1/objects/presigned-url` - 生成预授权 URL

## 项目结构

```
minio-file-manager/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── endpoints/
│   │   │       ├── buckets.py    # 桶管理端点
│   │   │       └── objects.py    # 文件操作端点
│   │   ├── core/
│   │   │   └── config.py         # 配置管理
│   │   ├── schemas/
│   │   │   └── minio_schemas.py  # Pydantic 模型
│   │   ├── services/
│   │   │   └── minio_service.py  # MinIO 服务层
│   │   └── main.py               # FastAPI 应用入口
│   ├── requirements.txt
│   └── .env
├── frontend/
│   ├── app/
│   │   ├── layout.tsx
│   │   ├── page.tsx
│   │   └── globals.css
│   ├── components/
│   │   ├── ui/                   # UI 组件
│   │   └── minio/                # MinIO 相关组件
│   ├── lib/
│   │   ├── api.ts                # API 客户端
│   │   └── utils.ts
│   ├── store/
│   │   └── minio-store.ts        # Zustand 状态管理
│   └── package.json
└── README.md
```

## 模块化集成

后端服务设计为模块化架构，可以轻松集成到其他项目中：

1. **独立的服务层**：`minio_service.py` 可以单独使用
2. **标准的 FastAPI 路由**：易于集成到现有的 FastAPI 应用
3. **清晰的 API 设计**：RESTful 风格，易于理解和使用

### 集成示例

```python
from app.services.minio_service import MinioService

# 创建服务实例
minio = MinioService()

# 使用服务
buckets = await minio.list_buckets()
```

## 公开访问功能

### 设置桶为公开访问

系统提供了便捷的API来设置桶的访问权限：

```bash
# 设置桶为公开访问
curl -X PUT http://localhost:9011/api/v1/buckets/my-bucket/make-public

# 设置桶为私有访问
curl -X PUT http://localhost:9011/api/v1/buckets/my-bucket/make-private
```

设置为公开后，桶中的文件可以通过以下URL直接访问：
```
http://your-minio-server:9000/bucket-name/object-name
```

### 获取文件公开访问URL

系统提供了专门的API来获取文件的公开访问地址：

```bash
# 获取文件的公开访问URL
curl http://localhost:9011/api/v1/objects/my-bucket/document.pdf/public-url
```

返回结果示例：
```json
{
  "public_url": "http://60.205.160.74:9000/my-bucket/document.pdf",
  "is_public": true,
  "bucket": "my-bucket",
  "object": "document.pdf",
  "note": "此URL可以直接访问"
}
```

### 公开URL vs 预签名URL

| 特性 | 公开URL | 预签名URL |
|------|---------|-----------|
| 有效期 | 永久有效 | 临时有效（可设置） |
| 桶要求 | 必须是公开桶 | 适用于私有桶 |
| 安全性 | 任何人可访问 | 时限控制访问 |
| 使用场景 | 静态资源、公开文档 | 临时分享、付费内容 |

### 自定义访问策略

也可以通过策略API设置更精细的访问控制：

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {"AWS": "*"},
      "Action": ["s3:GetObject"],
      "Resource": ["arn:aws:s3:::my-bucket/public/*"]
    }
  ]
}
```

## 安全建议

1. **生产环境配置**
   - 使用 HTTPS 连接 MinIO
   - 设置强密码
   - 限制 CORS 来源

2. **访问控制**
   - 实现用户认证
   - 添加 API 密钥验证
   - 设置合适的桶策略
   - 谨慎使用公开访问功能

3. **公开访问注意事项**
   - 仅对不包含敏感信息的桶设置公开访问
   - 定期审查公开桶的内容
   - 使用自定义策略限制公开访问的范围

## 许可证

MIT License