#!/bin/bash

# 项目备份脚本
# 创建项目快照，保存当前的工作状态

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 获取当前日期时间
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="backups/backup_${TIMESTAMP}"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}项目备份工具${NC}"
echo -e "${GREEN}========================================${NC}"

# 创建备份目录
mkdir -p "$BACKUP_DIR"

echo -e "\n${YELLOW}📁 创建备份目录: $BACKUP_DIR${NC}"

# 备份后端代码
echo -e "\n${YELLOW}📦 备份后端代码...${NC}"
cp -r minio-file-manager/backend "$BACKUP_DIR/backend"
# 清理临时文件
find "$BACKUP_DIR/backend" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find "$BACKUP_DIR/backend" -name "*.pyc" -delete 2>/dev/null || true
find "$BACKUP_DIR/backend" -name "*.log" -delete 2>/dev/null || true
rm -rf "$BACKUP_DIR/backend/venv" 2>/dev/null || true

# 备份前端代码
echo -e "${YELLOW}📦 备份前端代码...${NC}"
cp -r minio-file-manager/frontend "$BACKUP_DIR/frontend"
# 清理 node_modules 和临时文件
rm -rf "$BACKUP_DIR/frontend/node_modules" 2>/dev/null || true
rm -rf "$BACKUP_DIR/frontend/.next" 2>/dev/null || true
rm -f "$BACKUP_DIR/frontend/*.log" 2>/dev/null || true

# 备份文档
echo -e "${YELLOW}📚 备份文档...${NC}"
cp -r docs "$BACKUP_DIR/docs" 2>/dev/null || true
cp *.md "$BACKUP_DIR/" 2>/dev/null || true
cp CLAUDE.md "$BACKUP_DIR/" 2>/dev/null || true

# 备份配置文件
echo -e "${YELLOW}⚙️  备份配置文件...${NC}"
cp .env.example "$BACKUP_DIR/" 2>/dev/null || true
cp .gitignore "$BACKUP_DIR/" 2>/dev/null || true

# 创建项目状态信息
echo -e "${YELLOW}📝 生成项目状态信息...${NC}"
cat > "$BACKUP_DIR/PROJECT_INFO.md" << EOF
# 项目备份信息

## 备份时间
${TIMESTAMP}

## Git 状态
\`\`\`
$(git log --oneline -n 10)
\`\`\`

## 当前分支
$(git branch --show-current)

## 项目结构
\`\`\`
$(tree -L 3 -I 'node_modules|__pycache__|venv|.git' 2>/dev/null || find . -type d -name node_modules -prune -o -type d -name __pycache__ -prune -o -type d -name venv -prune -o -type d -name .git -prune -o -type f -print | head -100)
\`\`\`

## 核心功能
- MinIO 文件管理系统
- Elasticsearch 集成
- 文档处理管道（Document Pipeline）
- Newsletter 文章管理
- 模糊搜索和推荐系统

## API 端点
- /api/v1/buckets/* - 存储桶管理
- /api/v1/objects/* - 文件对象管理
- /api/v1/search/* - 搜索功能
- /api/v1/documents/* - 文档搜索和推荐
- /api/v1/newsletter/* - Newsletter 管理

## 依赖版本
### 后端
$(cd minio-file-manager/backend && cat requirements.txt | head -15)

### 前端
$(cd minio-file-manager/frontend && grep -E '"(react|next|typescript)"' package.json | head -5 || echo "Package info not available")
EOF

# 创建压缩包
echo -e "\n${YELLOW}🗜️  创建压缩包...${NC}"
tar -czf "$BACKUP_DIR.tar.gz" "$BACKUP_DIR"

# 计算备份大小
BACKUP_SIZE=$(du -sh "$BACKUP_DIR.tar.gz" | cut -f1)

echo -e "\n${GREEN}✅ 备份完成！${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "备份位置: ${YELLOW}$BACKUP_DIR${NC}"
echo -e "压缩包: ${YELLOW}$BACKUP_DIR.tar.gz${NC}"
echo -e "大小: ${YELLOW}$BACKUP_SIZE${NC}"
echo -e "${GREEN}========================================${NC}"

# 询问是否删除未压缩的备份目录
read -p "是否删除未压缩的备份目录？(y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    rm -rf "$BACKUP_DIR"
    echo -e "${GREEN}已删除未压缩的备份目录${NC}"
fi

echo -e "\n${GREEN}💡 提示：${NC}"
echo -e "  1. 备份已保存在 backups 目录"
echo -e "  2. 可以使用 tar -xzf $BACKUP_DIR.tar.gz 解压"
echo -e "  3. 建议定期备份重要版本"