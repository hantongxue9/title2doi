@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ============================================
echo   title2doi v3 — 生产模式启动
echo   中国科学技术大学图书馆
echo ============================================
echo.

:: 检查 .env 文件
if not exist ".env" (
    echo [WARNING] 未找到 .env 文件。
    echo 请复制 .env.example 为 .env 并配置 API Key。
    echo LLM 智能解析将无法使用，但不影响基础解析和 DOI 查询。
    echo.
)

:: 尝试用 waitress，不可用则回退到 Flask
python -c "import waitress" 2>nul
if %errorlevel% equ 0 (
    echo [INFO] 使用 waitress 生产服务器启动
    echo [INFO] 访问 http://localhost:5000
    echo [INFO] 按 Ctrl+C 停止
    echo.
    python -c "from app import app; from waitress import serve; print('服务已启动'); serve(app, host='0.0.0.0', port=5000)"
) else (
    echo [INFO] waitress 未安装，使用 Flask 开发服务器
    echo [INFO] 访问 http://localhost:5000
    echo [INFO] 按 Ctrl+C 停止
    echo.
    python run.py
)

pause
