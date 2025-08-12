#!/bin/bash
# 启动前端服务脚本

echo "🚀 启动前端服务..."

# 获取脚本所在目录的父目录（项目根目录）
PROJECT_ROOT="$(dirname "$(dirname "$0")")"
FRONTEND_DIR="$PROJECT_ROOT/minio-file-manager/frontend"

# 切换到前端目录
cd "$FRONTEND_DIR" || exit 1

echo "📂 工作目录: $FRONTEND_DIR"

# 检查是否有进程占用9010端口
if lsof -Pi :9010 -sTCP:LISTEN -t >/dev/null ; then
    echo "⚠️  端口9010已被占用，正在停止原有服务..."
    lsof -Pi :9010 -sTCP:LISTEN -t | xargs kill -9
    sleep 2
fi

# 检查node_modules是否存在
if [ ! -d "node_modules" ]; then
    echo "📦 首次运行，安装依赖包..."
    npm install
fi

# 确保.env.local存在
if [ ! -f ".env.local" ]; then
    echo "📝 创建.env.local配置文件..."
    echo "NEXT_PUBLIC_API_URL=http://localhost:9011/api/v1" > .env.local
fi

# 启动前端服务
echo "✅ 在端口9010启动前端服务..."
echo "🔗 访问地址: http://localhost:9010"
echo "📝 按 Ctrl+C 停止服务"
echo "-" * 60

npm run dev

# 如果需要后台运行，取消下面的注释并注释上面的行
# nohup npm run dev > "$PROJECT_ROOT/logs/frontend.log" 2>&1 &
# echo "✅ 前端服务已在后台启动"
# echo "📝 查看日志: tail -f $PROJECT_ROOT/logs/frontend.log"