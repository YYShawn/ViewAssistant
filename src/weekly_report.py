#!/usr/bin/env python3
import os
import json
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime, timedelta
from imap_tools import MailBox, AND
from openai import OpenAI
import html2text
from dotenv import dotenv_values

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(SCRIPT_DIR)
env = dotenv_values(os.path.join(BASE_DIR, ".env"))

with open(os.path.join(BASE_DIR, "config.json")) as f:
    cfg = json.load(f)

EMAIL = cfg["email"]
IMAP_HOST = cfg["imap_host"]
PASSWORD = env["EMAIL_PASSWORD"]
OUTPUT_DIR = os.path.expanduser(cfg["output_dir"])
PROMPT = cfg["prompt"]


def fetch_weekly_emails():
    since = datetime.now() - timedelta(days=7)
    emails = []

    criteria = {"date_gte": since.date()}
    if cfg.get("sender_filter"):
        criteria["from_"] = cfg["sender_filter"]

    h = html2text.HTML2Text()
    h.ignore_images = True
    h.body_width = 0

    with MailBox(IMAP_HOST).login(EMAIL, PASSWORD) as mb:
        for msg in mb.fetch(AND(**criteria)):
            keyword = cfg.get("subject_keyword", "")
            if keyword and keyword.lower() not in msg.subject.lower():
                continue
            if msg.html:
                body = h.handle(msg.html)
            else:
                body = msg.text or ""
            emails.append(
                f"### {msg.date.strftime('%Y-%m-%d')} | {msg.subject}\n{body[:5000]}"
            )

    return emails


def generate_report(emails):
    client = OpenAI(
        api_key=env["DEEPSEEK_API_KEY"],
        base_url="https://api.deepseek.com"
    )
    content = "\n\n---\n\n".join(emails)
    response = client.chat.completions.create(
        model="deepseek-chat",
        max_tokens=4096,
        messages=[{
            "role": "user",
            "content": f"{PROMPT}\n\n以下是本周邮件内容：\n\n{content}"
        }]
    )
    return response.choices[0].message.content


LAST_RUN_FILE = os.path.join(BASE_DIR, "logs", ".last_run")
LOG_DIR = os.path.join(BASE_DIR, "logs")


def save_report(report):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    filename = f"AI周报_{datetime.now().strftime('%Y-%m-%d')}.md"
    path = os.path.join(OUTPUT_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"# AI 前沿资讯周报（{datetime.now().strftime('%Y年第%W周')}）\n\n")
        f.write(report)
    print(f"[完成] 报告已保存：{path}")
    return path


def send_report_email(report: str, filepath: str):
    notify_email = cfg.get("notify_email", "").strip()
    if not notify_email:
        return

    week_label = datetime.now().strftime("%Y年第%W周")
    msg = MIMEMultipart()
    msg["From"] = EMAIL
    msg["To"] = notify_email
    msg["Subject"] = f"AI 前沿资讯周报 · {week_label}"
    msg.attach(MIMEText(report, "plain", "utf-8"))

    with open(filepath, "rb") as f:
        part = MIMEBase("application", "octet-stream")
        part.set_payload(f.read())
        encoders.encode_base64(part)
        part.add_header("Content-Disposition", f'attachment; filename="{os.path.basename(filepath)}"')
        msg.attach(part)

    try:
        with smtplib.SMTP_SSL("smtp.qq.com", 465) as server:
            server.login(EMAIL, PASSWORD)
            server.sendmail(EMAIL, notify_email, msg.as_string())
        print(f"[邮件] 周报已发送至 {notify_email}")
    except Exception as e:
        print(f"[邮件] 发送失败：{e}")


def record_last_run():
    os.makedirs(LOG_DIR, exist_ok=True)
    with open(LAST_RUN_FILE, "w") as f:
        f.write(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))


if __name__ == "__main__":
    print("正在读取本周邮件...")
    emails = fetch_weekly_emails()
    print(f"找到 {len(emails)} 封资讯邮件")
    if emails:
        print("正在生成周报...")
        report = generate_report(emails)
        path = save_report(report)
        send_report_email(report, path)
        record_last_run()
    else:
        print("本周未找到符合条件的邮件，请检查 config.json 中的过滤条件")
