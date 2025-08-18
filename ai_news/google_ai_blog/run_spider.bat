@echo off
chcp 65001 >nul
echo Google AI Blog RSS 爬虫
echo =====================

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

echo 开始爬取Google AI Blog文章...
python scheduler.py run

echo.
echo 爬取完成！查看 data/articles 目录获取文章内容
echo 查看 logs 目录获取详细日志
pause