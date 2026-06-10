#!/bin/bash
set -e

# 从 config.json 读取定时任务配置
SCHEDULE=${CRON_SCHEDULE:-"0 9 * * 5"}

# 设置 cron 任务
echo "$SCHEDULE cd /app && /usr/local/bin/python weekly_report.py >> /app/logs/run.log 2>&1" > /etc/cron.d/viewassistant
echo "" >> /etc/cron.d/viewassistant
chmod 0644 /etc/cron.d/viewassistant
crontab /etc/cron.d/viewassistant

# 运行一次补跑检测
python check_missed_run.py >> /app/logs/startup_check.log 2>&1 || true

echo "[ViewAssistant] 容器已启动"
echo "[ViewAssistant] 定时任务: $SCHEDULE"
echo "[ViewAssistant] 时区: $TZ"

exec "$@"
