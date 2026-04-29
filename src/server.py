#!/usr/bin/env python3
import asyncio
import json
import os
import platform
import subprocess
import sys

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, StreamingResponse
from pydantic import BaseModel
from dotenv import dotenv_values

app = FastAPI()

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(SCRIPT_DIR)
CONFIG_FILE = os.path.join(BASE_DIR, "config.json")
ENV_FILE = os.path.join(BASE_DIR, ".env")


def update_crontab(day: int, hour: int, minute: int):
    if platform.system() == "Windows":
        return {"updated": False, "note": "Windows 请手动在任务计划程序中更新执行时间"}

    script_path = os.path.join(SCRIPT_DIR, "weekly_report.py")
    log_path = os.path.join(BASE_DIR, "logs", "run.log")
    new_line = f"{minute} {hour} * * {day} {sys.executable} {script_path} >> {log_path} 2>&1"

    result = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
    lines = [l for l in result.stdout.splitlines() if "weekly_report.py" not in l]
    lines.append(new_line)
    subprocess.run(["crontab", "-"], input="\n".join(lines) + "\n", text=True)
    return {"updated": True}


@app.get("/", response_class=HTMLResponse)
async def index():
    with open(os.path.join(BASE_DIR, "templates", "index.html"), encoding="utf-8") as f:
        return f.read()


@app.get("/api/config")
async def get_config():
    with open(CONFIG_FILE, encoding="utf-8") as f:
        cfg = json.load(f)
    env = dotenv_values(ENV_FILE)
    return {
        **cfg,
        "schedule_day": cfg.get("schedule_day", 5),
        "schedule_time": cfg.get("schedule_time", "09:00"),
        "email_password": env.get("EMAIL_PASSWORD", ""),
        "deepseek_api_key": env.get("DEEPSEEK_API_KEY", ""),
    }


class ConfigModel(BaseModel):
    email: str
    imap_host: str
    sender_filter: str
    subject_keyword: str
    output_dir: str
    prompt: str
    schedule_day: int = 5
    schedule_time: str = "09:00"
    email_password: str
    deepseek_api_key: str


@app.post("/api/config")
async def save_config(config: ConfigModel):
    cfg = config.model_dump(exclude={"email_password", "deepseek_api_key"})
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)
    with open(ENV_FILE, "w") as f:
        f.write(f"EMAIL_PASSWORD={config.email_password}\n")
        f.write(f"DEEPSEEK_API_KEY={config.deepseek_api_key}\n")

    hour, minute = map(int, config.schedule_time.split(":"))
    cron_result = update_crontab(config.schedule_day, hour, minute)
    return {"status": "ok", **cron_result}


@app.post("/api/run")
async def run_report():
    async def generate():
        proc = await asyncio.create_subprocess_exec(
            sys.executable,
            os.path.join(SCRIPT_DIR, "weekly_report.py"),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
        async for line in proc.stdout:
            yield f"data: {line.decode('utf-8', errors='replace').rstrip()}\n\n"
        await proc.wait()
        if proc.returncode == 0:
            yield "data: ✅ 周报生成成功\n\n"
        else:
            yield f"data: ❌ 运行失败（退出码 {proc.returncode}）\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


def _pick_folder_sync() -> str:
    system = platform.system()
    try:
        if system == "Darwin":
            result = subprocess.run(
                ["osascript", "-e", 'POSIX path of (choose folder with prompt "选择周报保存目录")'],
                capture_output=True, text=True, timeout=60
            )
            return result.stdout.strip().rstrip("/")
        elif system == "Windows":
            script = (
                "Add-Type -AssemblyName System.Windows.Forms;"
                "$d = New-Object System.Windows.Forms.FolderBrowserDialog;"
                "$d.Description = '选择周报保存目录';"
                "$d.ShowDialog() | Out-Null;"
                "Write-Output $d.SelectedPath"
            )
            result = subprocess.run(
                ["powershell", "-Command", script],
                capture_output=True, text=True, timeout=60
            )
            return result.stdout.strip()
        else:  # Linux
            for cmd in [
                ["zenity", "--file-selection", "--directory", "--title=选择周报保存目录"],
                ["kdialog", "--getexistingdirectory", os.path.expanduser("~")],
            ]:
                try:
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
                    if result.returncode == 0:
                        return result.stdout.strip()
                except FileNotFoundError:
                    continue
    except Exception:
        pass
    return ""


@app.get("/api/pick-folder")
async def pick_folder():
    loop = asyncio.get_event_loop()
    path = await loop.run_in_executor(None, _pick_folder_sync)
    return {"path": path}


@app.get("/api/logs")
async def get_logs():
    log_file = os.path.join(BASE_DIR, "logs", "run.log")
    if not os.path.exists(log_file):
        return {"content": "暂无日志"}
    with open(log_file, encoding="utf-8", errors="replace") as f:
        content = f.read()
    return {"content": content[-5000:] if len(content) > 5000 else content}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
