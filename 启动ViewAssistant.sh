#!/bin/bash
DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"

# 释放 8000 端口（如已被占用）
if command -v lsof > /dev/null; then
    lsof -ti:8000 | xargs kill -9 2>/dev/null
elif command -v fuser > /dev/null; then
    fuser -k 8000/tcp 2>/dev/null
fi

echo "🚀 正在启动 ViewAssistant..."
python3 "$DIR/src/server.py" &
SERVER_PID=$!

# 等待服务器就绪（最多 10 秒）
for i in {1..20}; do
    if curl -s http://127.0.0.1:8000 > /dev/null 2>&1; then
        break
    fi
    sleep 0.5
done

if ! curl -s http://127.0.0.1:8000 > /dev/null 2>&1; then
    echo "❌ 服务器启动失败，请确认已安装依赖：pip3 install -r requirements.txt"
    exit 1
fi

echo "✅ 服务器已启动，正在打开配置页面..."

# 兼容不同 Linux 桌面环境
if command -v xdg-open > /dev/null; then
    xdg-open http://127.0.0.1:8000
elif command -v gnome-open > /dev/null; then
    gnome-open http://127.0.0.1:8000
else
    echo "请手动打开浏览器访问：http://127.0.0.1:8000"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  ViewAssistant 运行中"
echo "  配置页面：http://127.0.0.1:8000"
echo "  关闭此窗口将停止服务器"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

wait $SERVER_PID
