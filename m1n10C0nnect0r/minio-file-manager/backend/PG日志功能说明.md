# PostgreSQL 存储日志功能说明

## 功能概述
成功实现了PostgreSQL存储的前后输入输出日志记录功能，可以详细记录文档处理管道中的PostgreSQL操作。

## 实现要点

### 1. 数据库配置修正
- **数据库**: `ai_newsletters` (原配置错误使用了不存在的newsletters数据库)
- **用户**: `ruanchuhao` (原配置错误使用了不存在的postgres用户)
- **表名**: `articles` (原代码错误使用了不存在的newsletters表)

### 2. 日志记录位置

#### article_processing_service.py
在PostgreSQL操作前后记录详细日志：

**输入日志** (操作前):
- 文件名
- 标题
- 摘要
- 分类
- 标签
- 作者
- 阅读时间
- 内容哈希
- 字数统计
- MinIO路径

**输出日志** (操作后):
- 操作成功状态
- 记录ID (UUID)
- 是否重复
- 创建时间
- 错误信息(如果有)

#### postgresql_service.py
内部操作日志：
- 连接池初始化
- UUID生成
- 重复检查
- SQL执行
- 错误详情

### 3. 测试验证

运行测试脚本：
```bash
python3 test_complete_pipeline.py
```

成功输出示例：
```
PostgreSQL存储 - 输入数据:
文件名: ai_newsletter_20250808_235442.md
标题: AI Newsletter测试文档
分类: agent
...
PostgreSQL存储 - 输出结果:
操作成功: True
记录ID: 3dc6ce4d-9122-4c71-8675-9322b130ee26
创建时间: 2025-08-08T23:54:42.746909
```

### 4. 数据清理工具

提供了两个清理工具：

#### clean_all_data.py
一键清理所有数据：
```bash
python3 clean_all_data.py
```

#### selective_clean.py
选择性清理：
```bash
# 查看统计
python3 selective_clean.py --stats

# 清理PostgreSQL
python3 selective_clean.py --pg

# 清理所有
python3 selective_clean.py --all -y
```

## 注意事项

1. **时区问题**: PostgreSQL的timestamp字段使用无时区格式，已修正为使用`datetime.now()`而非`datetime.now(timezone.utc)`

2. **枚举类型**: categoryenum 包含: agent, news, papers, coding, tools

3. **元数据字段**: 已为articles表添加metadata JSON字段用于存储额外信息

4. **日志级别**: 设置为INFO级别显示主要操作，DEBUG级别显示详细信息

## 环境变量配置 (.env)
```env
# PostgreSQL Settings
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DATABASE=ai_newsletters
POSTGRES_USER=ruanchuhao
POSTGRES_PASSWORD=
```

## 验证方法

查询数据库验证插入：
```sql
SELECT id, title, category, author, created_at 
FROM articles 
ORDER BY created_at DESC 
LIMIT 5;
```