@echo off
chcp 65001 >nul
echo ============================================
echo   title2doi - 标题DOI批量检索工具 v1
echo   中国科学技术大学图书馆
echo ============================================
echo.
echo 正在启动服务...
echo 浏览器会自动打开 http://localhost:5000
echo 按 Ctrl+C 停止服务
echo.

start http://localhost:5000

cd /d "%~dp0"
python run.py

pause
