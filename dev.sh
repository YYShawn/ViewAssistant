#!/bin/bash
# ViewAssistant 开发服务器启动脚本

cd "$(dirname "$0")"

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "📦 虚拟环境不存在，正在创建..."
    python3 -m venv venv
    echo "✅ 虚拟环境已创建"
fi

# 激活虚拟环境
source venv/bin/activate

# 检查依赖
if ! python -c "import fastapi" 2>/dev/null; then
    echo "📦 正在安装依赖..."
    pip install -r requirements.txt -q
    echo "✅ 依赖已安装"
fi

# 启动服务器
echo "🚀 启动 ViewAssistant 配置服务器..."
echo "📍 访问地址: http://127.0.0.1:8000"
echo "⏹  按 Ctrl+C 停止服务器"
echo ""

python src/server.py
