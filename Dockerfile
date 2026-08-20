# ViewAssistant Docker 镜像
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖（cron 和时区支持）
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    cron \
    tzdata && \
    rm -rf /var/lib/apt/lists/*

# 设置时区（默认 Asia/Shanghai，可通过环境变量覆盖）
ENV TZ=Asia/Shanghai
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# 复制依赖文件并安装
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目源码（保持目录结构，脚本依赖 BASE_DIR 定位 config/.env）
COPY src/ ./src/

# 创建日志和输出目录
RUN mkdir -p /app/logs /app/output

# 复制 cron 启动脚本
COPY scripts/docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

# 暴露端口（如果需要 Web 配置界面，可选）
# EXPOSE 8000

# 启动 cron 和应用
ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["cron", "-f"]
