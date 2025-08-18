@echo off
chcp 65001 >nul
echo Google AI Blog 定时爬虫调度器
echo ==============================

cd /d "%~dp0"

echo 检查Python环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误：未找到Python环境，请先安装Python
    pause
    exit /b 1
)

echo 安装依赖包...
pip install -r requirements.txt

echo 启动定时调度器...
echo 调度器将每6小时检查一次新文章
echo 按 Ctrl+C 停止调度器
echo.
python scheduler.py start