#!/bin/bash
# title2doi v3 — 生产模式启动脚本 (Linux/Mac)

set -e
cd "$(dirname "$0")"

echo "============================================"
echo "  title2doi v3 — 生产模式启动"
echo "  中国科学技术大学图书馆"
echo "============================================"
echo ""

# 检查 .env
if [ ! -f ".env" ]; then
    echo "[WARNING] 未找到 .env 文件。"
    echo "  请复制 .env.example 为 .env 并配置 API Key。"
    echo "  LLM 智能解析将无法使用，但不影响基础功能。"
    echo ""
fi

# 选择 WSGI 服务器
if python -c "import waitress" 2>/dev/null; then
    echo "[INFO] 使用 waitress 生产服务器"
    python -c "from app import app; from waitress import serve; serve(app, host='0.0.0.0', port=5000)"
elif python -c "import gunicorn" 2>/dev/null; then
    echo "[INFO] 使用 gunicorn 生产服务器"
    gunicorn -b 0.0.0.0:5000 -w 2 app:app
else
    echo "[INFO] 使用 Flask 开发服务器（建议安装 waitress）"
    python run.py
fi
