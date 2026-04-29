#!/usr/bin/env python3
"""开机时检查是否错过了周五的周报，若错过则立即补跑。"""
import os
import subprocess
from datetime import datetime, timedelta

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LAST_RUN_FILE = os.path.join(BASE_DIR, ".last_run")
MAIN_SCRIPT = os.path.join(BASE_DIR, "weekly_report.py")


def get_last_scheduled_friday():
    """返回最近一次应该触发的周五 9:00。"""
    now = datetime.now()
    days_since_friday = (now.weekday() - 4) % 7
    last_friday = now.date() - timedelta(days=days_since_friday)
    scheduled = datetime(last_friday.year, last_friday.month, last_friday.day, 9, 0)
    if scheduled > now:
        scheduled -= timedelta(weeks=1)
    return scheduled


def get_last_run():
    if not os.path.exists(LAST_RUN_FILE):
        return None
    with open(LAST_RUN_FILE) as f:
        try:
            return datetime.strptime(f.read().strip(), "%Y-%m-%d %H:%M:%S")
        except ValueError:
            return None


if __name__ == "__main__":
    last_scheduled = get_last_scheduled_friday()
    last_run = get_last_run()

    if last_run is None or last_run < last_scheduled:
        print(f"[补跑] 检测到 {last_scheduled.strftime('%Y-%m-%d')} 周五的周报未生成，开始补跑...")
        subprocess.run(["/usr/bin/python3", MAIN_SCRIPT], env=os.environ)
    else:
        print(f"[跳过] 本周周报已于 {last_run.strftime('%Y-%m-%d %H:%M')} 生成，无需补跑")
