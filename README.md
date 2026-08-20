# ViewAssistant

AI 内容总结助手。自动抓取邮箱中的资讯邮件，通过 DeepSeek AI 生成结构化中文周报，保存到本地或发送到指定邮箱。

## 核心功能

- **邮件采集** — 通过 IMAP 读取 QQ 邮箱（支持发件人/主题关键词过滤，支持自定义日期范围）
- **AI 总结** — 调用 DeepSeek API，按自定义 Prompt 分类整理，生成 Markdown 周报
- **本地保存** — 周报以 Markdown 文件保存到指定目录
- **邮件推送** — 自动将生成的周报以 HTML 邮件（含附件）发送到指定邮箱
- **Web 配置** — 本地浏览器界面管理所有配置，无需编辑文件
- **定时调度** — 支持每周自动运行（crontab），支持开机补跑检测
- **Docker 部署** — 可选 Docker 容器化运行，完全隔离

## 快速开始

### 环境要求

- Python 3.9+
- macOS / Windows / Linux

### 1. 克隆项目

```bash
git clone https://github.com/YYShawn/ViewAssistant.git
cd ViewAssistant
```

### 2. 准备配置

创建 `.env` 文件（密钥）：

```
EMAIL_PASSWORD=你的QQ邮箱IMAP授权码
DEEPSEEK_API_KEY=你的DeepSeek_API_Key
```

参考 `config.example.json` 创建 `config.json`：

```json
{
  "email": "你的QQ号@qq.com",
  "imap_host": "imap.qq.com",
  "sender_filter": "hello@agidaily.cc",
  "subject_keyword": "",
  "output_dir": "~/Documents/AI_Reports",
  "prompt": "你是一位AI研究助理...",
  "date_range_type": "1week",
  "schedule_day": 5,
  "schedule_time": "09:00",
  "notify_email": ""
}
```

### 3. 启动

**macOS** — 双击 `启动ViewAssistant.command`

**Windows** — 双击 `启动ViewAssistant.bat`

**Linux** — 双击 `启动ViewAssistant.sh`

浏览器会自动打开配置页面 `http://127.0.0.1:8000`，点击「运行一次」即可测试。

### 4. 手动运行

```bash
# 创建虚拟环境并安装依赖
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 直接生成周报
python src/weekly_report.py
```

## 工作流程

```
IMAP 邮箱 → 抓取邮件 → DeepSeek AI 总结 → Markdown 保存 → 邮件发送
```

## 目录结构

```
ViewAssistant/
├── src/
│   ├── weekly_report.py           # 主脚本：读邮件→生成周报→保存→发邮件
│   ├── check_missed_run.py        # 开机补跑检测
│   └── server.py                  # Web 配置后端（FastAPI）
├── scripts/
│   ├── check_env.py               # 环境检测
│   ├── dev.sh                     # 开发服务器启动
│   └── docker-entrypoint.sh       # Docker 启动脚本
├── docs/
│   └── DEPLOY.md                  # 详细部署指南
├── templates/
│   └── index.html                 # Web 配置页面
├── 启动ViewAssistant.command      # macOS 双击启动
├── 启动ViewAssistant.bat          # Windows 双击启动
├── 启动ViewAssistant.sh           # Linux 双击启动
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── config.example.json            # 配置模板
```

## Docker 部署（可选）

```bash
# 确保 .env 和 config.json 已配置
docker-compose up -d
```

容器内运行 cron 守护进程，按配置的调度自动执行。周报输出到宿主机的 `./output/` 目录。

## 技术栈

- **语言** — Python 3.9+
- **Web 框架** — FastAPI + Uvicorn
- **AI 接口** — OpenAI SDK（兼容 DeepSeek API）
- **邮件处理** — imap-tools（IMAP）、smtplib（SMTP）
- **Markdown 转 HTML** — markdown
- **HTML 转纯文本** — html2text

## 获取授权码

- **QQ 邮箱 IMAP** — 登录 [mail.qq.com](https://mail.qq.com) → 设置 → 账户 → POP3/IMAP/SMTP → 开启 IMAP → 获取授权码
- **DeepSeek API Key** — 登录 [platform.deepseek.com](https://platform.deepseek.com) → API Keys → 创建

## License

MIT