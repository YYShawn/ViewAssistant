#!/usr/bin/env python3
import asyncio
import json
import os
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


@app.get("/", response_class=HTMLResponse)
async def index():
    with open(os.path.join(BASE_DIR, "templates", "index.html"), encoding="utf-8") as f:  # noqa
        return f.read()


@app.get("/api/config")
async def get_config():
    with open(CONFIG_FILE, encoding="utf-8") as f:
        cfg = json.load(f)
    env = dotenv_values(ENV_FILE)
    return {
        **cfg,
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
    return {"status": "ok"}


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


@app.get("/api/logs")
async def get_logs():
    log_file = os.path.join(BASE_DIR, "logs", "run.log")  # noqa
    if not os.path.exists(log_file):
        return {"content": "暂无日志"}
    with open(log_file, encoding="utf-8", errors="replace") as f:
        content = f.read()
    return {"content": content[-5000:] if len(content) > 5000 else content}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
