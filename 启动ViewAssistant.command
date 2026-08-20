#!/bin/bash
DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"

# 检查虚拟环境，不存在则创建
if [ ! -d "venv" ]; then
    echo "📦 正在创建虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
source venv/bin/activate

# 检查依赖
if ! python -c "import fastapi" 2>/dev/null; then
    echo "📦 正在安装依赖（首次运行需要几分钟）..."
    pip install -r requirements.txt -q
fi

# 如果 8000 端口已被占用则先释放
lsof -ti:8000 | xargs kill -9 2>/dev/null

echo "🚀 正在启动 ViewAssistant..."
python "$DIR/src/server.py" &
SERVER_PID=$!

# 等待服务器就绪（最多 10 秒）
for i in {1..20}; do
    if curl -s http://127.0.0.1:8000 > /dev/null 2>&1; then
        break
    fi
    sleep 0.5
done

echo "✅ 服务器已启动，正在打开配置页面..."
open http://127.0.0.1:8000

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  ViewAssistant 运行中"
echo "  配置页面：http://127.0.0.1:8000"
echo "  关闭此窗口将停止服务器"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

wait $SERVER_PID
