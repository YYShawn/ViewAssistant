# ViewAssistant 部署指南

## 目录

- [前置准备（所有系统通用）](#前置准备所有系统通用)
- [macOS 部署](#macos-部署)
- [Windows 部署](#windows-部署)
- [Linux 部署](#linux-部署)

---

命令行运行
  ./scripts/dev.sh

## 前置准备（所有系统通用）

### 0. 环境要求

- **Python 3.9+**（推荐 3.11 或更高）
- macOS / Windows / Linux

快速检测环境是否就绪：

```bash
python3 scripts/check_env.py
```

### 1. 获取 QQ 邮箱 IMAP 授权码

1. 登录 [mail.qq.com](https://mail.qq.com)
2. 点击顶部 **设置** → **账户**
3. 找到 **POP3/IMAP/SMTP 服务** → 开启 **IMAP/SMTP 服务**
4. 按提示手机验证后，复制生成的 **16 位授权码**

### 2. 获取 DeepSeek API Key

1. 登录 [platform.deepseek.com](https://platform.deepseek.com)
2. 左侧菜单 → **API Keys** → **Create Key**
3. 复制 `sk-` 开头的 Key，并确保账户有余额

### 3. 克隆项目

```bash
git clone https://github.com/YYShawn/ViewAssistant.git
cd ViewAssistant
```

### 4. 安装 Python 依赖

**推荐使用虚拟环境（避免污染系统 Python）：**

```bash
# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
# macOS/Linux:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

**或直接安装到系统（不推荐）：**

```bash
pip install imap-tools openai html2text python-dotenv
```

> 💡 使用虚拟环境后，每次运行脚本前需要先激活环境

### 5. 创建 .env 文件

在项目根目录创建 `.env` 文件，填入以下内容：

```
EMAIL_PASSWORD=你的QQ邮箱授权码
DEEPSEEK_API_KEY=你的DeepSeek_API_Key
```

### 6. 创建 config.json 文件

参考 `config.example.json`，在项目根目录创建 `config.json`：

```json
{
  "email": "你的QQ号@qq.com",
  "imap_host": "imap.qq.com",
  "sender_filter": "hello@agidaily.cc",
  "subject_keyword": "",
  "output_dir": "填写周报输出目录（见各系统说明）",
  "prompt": "你是一位AI研究助理，请将以下本周的AI前沿资讯邮件整理成一份中文周报。\n要求：\n- 按主题分类（模型进展 / 应用落地 / 行业动态 / 其他）\n- 每条保留核心要点，去除广告和无关内容\n- 每条资讯的标题后面必须附上原文链接，格式为：**标题** [原文](URL)，链接来自邮件原文，不得虚构\n- 标注你认为最值得关注的3项进展，说明理由\n- 开头写一段50字以内的本周总体概述\n- 输出格式为 Markdown"
}
```

### 7. 手动测试

```bash
python src/weekly_report.py
```

输出 `[完成] 报告已保存：...` 即表示配置正确。

---

## macOS 部署

### 启动配置页面

双击项目目录中的 **启动ViewAssistant.command**，终端窗口会自动弹出并打开浏览器。

> 首次双击若提示"无法打开"，右键 → 打开 → 允许即可。

### config.json 中的 output_dir 填写示例

```json
"output_dir": "~/Documents/AI_Reports"
```

### 设置每周五 9:00 自动运行（crontab）

```bash
crontab -e
```

在文件末尾添加：

```
0 9 * * 5 /usr/bin/python3 /完整路径/ViewAssistant/src/weekly_report.py >> /完整路径/ViewAssistant/run.log 2>&1
```

验证是否生效：

```bash
crontab -l
```

### 设置开机补跑（launchd）

在 `~/Library/LaunchAgents/` 目录下创建 `com.viewassistant.checkrun.plist`：

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.viewassistant.checkrun</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>/完整路径/ViewAssistant/src/check_missed_run.py</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/完整路径/ViewAssistant/startup_check.log</string>
    <key>StandardErrorPath</key>
    <string>/完整路径/ViewAssistant/startup_check.log</string>
</dict>
</plist>
```

加载启动项：

```bash
launchctl load ~/Library/LaunchAgents/com.viewassistant.checkrun.plist
```

### 开启终端完全磁盘访问权限

**系统设置 → 隐私与安全性 → 完全磁盘访问 → 开启「终端」**

---

## Windows 部署

### 启动配置页面

双击项目目录中的 **启动ViewAssistant.bat**，命令行窗口会自动弹出并打开浏览器。按任意键关闭窗口时服务器同步停止。

### 前置：安装 Python

从 [python.org](https://www.python.org/downloads/) 下载安装 Python 3.9+，安装时勾选 **Add Python to PATH**。

### config.json 中的 output_dir 填写示例

```json
"output_dir": "C:/Users/你的用户名/Documents/AI_Reports"
```

### 设置每周五 9:00 自动运行（任务计划程序）

1. 按 `Win + S` 搜索 **任务计划程序** 并打开
2. 右侧点击 **创建基本任务**
3. 填写名称：`ViewAssistant 周报`
4. 触发器选择 **每周**，勾选 **星期五**，时间设为 `09:00`
5. 操作选择 **启动程序**：
   - 程序：`python`
   - 参数：`C:\完整路径\ViewAssistant\src\weekly_report.py`
   - 起始于：`C:\完整路径\ViewAssistant\`
6. 完成后右键任务 → **运行** 测试是否正常

### 设置开机补跑（任务计划程序）

重复上述步骤，触发器改为 **计算机启动时**，程序参数改为 `src/check_missed_run.py`。

---

## Linux 部署

### 启动配置页面

在文件管理器中双击 **启动ViewAssistant.sh**（需在桌面环境中选择"在终端中运行"），或在终端执行：

```bash
./启动ViewAssistant.sh
```

### config.json 中的 output_dir 填写示例

```json
"output_dir": "~/Documents/AI_Reports"
```

### 设置每周五 9:00 自动运行（crontab）

```bash
crontab -e
```

添加：

```
0 9 * * 5 /usr/bin/python3 /完整路径/ViewAssistant/src/weekly_report.py >> /完整路径/ViewAssistant/run.log 2>&1
```

### 设置开机补跑（systemd）

创建 `/etc/systemd/system/viewassistant.service`：

```ini
[Unit]
Description=ViewAssistant Missed Run Check
After=network.target

[Service]
Type=oneshot
ExecStart=/usr/bin/python3 /完整路径/ViewAssistant/src/check_missed_run.py
StandardOutput=append:/完整路径/ViewAssistant/startup_check.log
StandardError=append:/完整路径/ViewAssistant/startup_check.log

[Install]
WantedBy=multi-user.target
```

启用服务：

```bash
sudo systemctl enable viewassistant.service
sudo systemctl start viewassistant.service
```

---

## 日志查看

| 日志文件 | 内容 |
|---------|------|
| `run.log` | 每周五定时任务运行记录 |
| `startup_check.log` | 开机补跑检测记录 |

## 文件结构说明

---

## Docker 部署（可选）

> 适合熟悉 Docker 的用户，提供完全隔离的运行环境

### 前置要求

- 安装 [Docker Desktop](https://www.docker.com/products/docker-desktop/)（macOS/Windows）
- 或安装 Docker Engine（Linux）

### 快速启动

1. 确保 `.env` 和 `config.json` 已配置完成
2. 构建并启动容器：

```bash
docker-compose up -d
```

### 查看日志

```bash
docker-compose logs -f
```

### 停止服务

```bash
docker-compose down
```

### 说明

- 容器内运行 cron 守护进程，按 `config.json` 中的调度配置自动执行
- `.env` 和 `config.json` 以只读方式挂载到容器，修改后需 `docker-compose restart`
- 输出目录固定为宿主机的 `./output` 目录（容器内 `OUTPUT_DIR=/app/output`），不受 `config.json` 中 `output_dir` 影响
- 日志写入宿主机的 `./logs` 目录

---

## 常见问题

### 虚拟环境相关

**Q: 每次运行都要激活虚拟环境吗？**  
A: 是的。如果使用虚拟环境，运行前需要先 `source venv/bin/activate`（或 Windows 的 `venv\Scripts\activate`）

**Q: crontab 定时任务怎么使用虚拟环境？**  
A: 在 crontab 中使用虚拟环境内的 Python：

```
0 9 * * 5 /完整路径/ViewAssistant/venv/bin/python /完整路径/ViewAssistant/src/weekly_report.py >> /完整路径/ViewAssistant/run.log 2>&1
```

### 依赖安装问题

**Q: pip install 报错怎么办？**  
A: 尝试升级 pip：`python3 -m pip install --upgrade pip`

**Q: 国内网络安装慢怎么办？**  
A: 使用国内镜像源：`pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple`

---

## 文件结构说明

```
ViewAssistant/
├── src/
│   ├── weekly_report.py           # 主脚本
│   ├── check_missed_run.py        # 开机补跑脚本
│   └── server.py                  # Web 配置后端
├── scripts/
│   ├── check_env.py               # 环境检测脚本
│   ├── dev.sh                     # 开发服务器启动脚本
│   └── docker-entrypoint.sh       # Docker 启动脚本
├── docs/
│   └── DEPLOY.md                  # 部署指南
├── templates/
│   └── index.html                 # Web 配置页面
├── 启动ViewAssistant.command     # macOS 双击启动
├── 启动ViewAssistant.bat         # Windows 双击启动
├── 启动ViewAssistant.sh          # Linux 双击启动
├── requirements.txt              # Python 依赖清单
├── Dockerfile                    # Docker 部署（可选）
├── docker-compose.yml            # Docker 编排（可选）
├── config.json                   # 本地配置（不上传 GitHub）
├── config.example.json           # 配置模板
├── .env                          # 密钥文件（不上传 GitHub）
├── .gitignore
└── logs/                         # 运行时自动生成（不上传 GitHub）
    ├── run.log                   # 定时任务日志
    ├── startup_check.log         # 补跑日志
    └── .last_run                 # 上次运行时间记录
```
