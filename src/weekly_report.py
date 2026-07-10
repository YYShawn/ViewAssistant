#!/usr/bin/env python3
import os
import json
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import markdown
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
    range_type = cfg.get("date_range_type", "1week")
    if range_type == "custom":
        date_from = cfg.get("date_from", "")
        date_to = cfg.get("date_to", "")
        since = datetime.strptime(date_from, "%Y-%m-%d") if date_from else datetime.now() - timedelta(days=7)
        until = datetime.strptime(date_to, "%Y-%m-%d") + timedelta(days=1) if date_to else None
    else:
        presets = {"1week": 7, "2weeks": 14, "1month": 30, "3months": 90}
        days = presets.get(range_type, 7)
        since = datetime.now() - timedelta(days=days)
        until = None
    emails = []

    criteria = {"date_gte": since.date()}
    if until:
        criteria["date_lt"] = until.date()
    if cfg.get("sender_filter"):
        criteria["from_"] = cfg["sender_filter"]

    h = html2text.HTML2Text()
    h.ignore_images = True
    h.body_width = 0

    with MailBox(IMAP_HOST).login(EMAIL, PASSWORD) as mb:
        for msg in mb.fetch(AND(**criteria)):
            if msg.date.date() < since.date():
                continue
            if until and msg.date.date() >= until.date():
                continue
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


EMAIL_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head><meta charset="utf-8"><style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
         background: #f0f2f5; margin: 0; padding: 24px; color: #1a1a2e; }}
  .wrap {{ max-width: 680px; margin: 0 auto; background: white;
           border-radius: 12px; padding: 36px;
           box-shadow: 0 1px 4px rgba(0,0,0,0.08); }}
  h1 {{ font-size: 22px; color: #1a1a2e;
        border-bottom: 2px solid #3b82f6; padding-bottom: 12px; margin-top: 0; }}
  h2 {{ font-size: 16px; color: #1a1a2e;
        border-left: 4px solid #3b82f6; padding-left: 12px; margin-top: 32px; }}
  h3 {{ font-size: 14px; color: #374151; margin-top: 20px; }}
  p  {{ color: #374151; line-height: 1.8; margin: 8px 0; }}
  a  {{ color: #3b82f6; text-decoration: none; }}
  a:hover {{ text-decoration: underline; }}
  ul {{ padding-left: 20px; }}
  li {{ color: #374151; line-height: 1.8; margin: 6px 0; }}
  strong {{ color: #1a1a2e; }}
  hr {{ border: none; border-top: 1px solid #f3f4f6; margin: 24px 0; }}
  .footer {{ margin-top: 32px; padding-top: 16px; border-top: 1px solid #f3f4f6;
             font-size: 12px; color: #9ca3af; }}
</style></head>
<body><div class="wrap">
{content}
<div class="footer">由 ViewAssistant 自动生成 · {date}</div>
</div></body></html>"""


def send_report_email(report: str, filepath: str):
    notify_email = cfg.get("notify_email", "").strip()
    if not notify_email:
        return

    week_label = datetime.now().strftime("%Y年第%W周")
    html_body = markdown.markdown(report, extensions=["extra", "nl2br"])
    html_content = EMAIL_HTML_TEMPLATE.format(
        content=html_body,
        date=datetime.now().strftime("%Y-%m-%d")
    )

    msg = MIMEMultipart("alternative")
    msg["From"] = EMAIL
    msg["To"] = notify_email
    msg["Subject"] = f"AI 前沿资讯周报 · {week_label}"
    msg.attach(MIMEText(report, "plain", "utf-8"))
    msg.attach(MIMEText(html_content, "html", "utf-8"))

    # 附件（用 ASCII 文件名避免乱码）
    ascii_filename = f"AI_Weekly_{datetime.now().strftime('%Y-W%W')}.md"
    outer = MIMEMultipart("mixed")
    outer["From"] = EMAIL
    outer["To"] = notify_email
    outer["Subject"] = msg["Subject"]
    outer.attach(msg)

    with open(filepath, "rb") as f:
        part = MIMEBase("application", "octet-stream")
        part.set_payload(f.read())
        encoders.encode_base64(part)
        part.add_header("Content-Disposition", f'attachment; filename="{ascii_filename}"')
        outer.attach(part)

    try:
        with smtplib.SMTP_SSL("smtp.qq.com", 465) as server:
            server.login(EMAIL, PASSWORD)
            server.sendmail(EMAIL, notify_email, outer.as_string())
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
