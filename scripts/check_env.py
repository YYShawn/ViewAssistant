#!/usr/bin/env python3
"""
ViewAssistant 环境检测脚本
运行此脚本以检查所有必需的依赖和系统配置
"""

import sys
import subprocess
import platform
import shutil

def print_section(title):
    print(f"\n{'='*60}")
    print(f" {title}")
    print('='*60)

def check_python_version():
    print_section("Python 版本检查")
    version = sys.version_info
    print(f"当前 Python 版本: {version.major}.{version.minor}.{version.micro}")

    if version.major < 3 or (version.major == 3 and version.minor < 9):
        print("❌ Python 版本过低，需要 Python 3.9 或更高版本")
        return False
    else:
        print("✅ Python 版本符合要求 (>= 3.9)")
        return True

def check_dependencies():
    print_section("依赖包检查")
    required_packages = [
        'imap_tools',
        'openai',
        'html2text',
        'dotenv'
    ]

    all_installed = True
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package} 已安装")
        except ImportError:
            print(f"❌ {package} 未安装")
            all_installed = False

    if not all_installed:
        print("\n修复方法:")
        print("  pip install imap-tools openai html2text python-dotenv")

    return all_installed

def check_system_commands():
    print_section("系统命令检查")
    system = platform.system()

    if system == 'Darwin':
        # macOS
        print("检测到 macOS 系统")
        commands = {
            'osascript': '文件夹选择器需要',
            'crontab': '定时任务需要'
        }
    elif system == 'Windows':
        # Windows
        print("检测到 Windows 系统")
        commands = {
            'powershell': '文件夹选择器需要'
        }
    elif system == 'Linux':
        # Linux
        print("检测到 Linux 系统")
        commands = {
            'zenity': '文件夹选择器需要（可选）',
            'crontab': '定时任务需要'
        }
    else:
        print(f"⚠️  未识别的系统: {system}")
        return True

    all_available = True
    for cmd, purpose in commands.items():
        if shutil.which(cmd):
            print(f"✅ {cmd} 可用 ({purpose})")
        else:
            print(f"❌ {cmd} 不可用 ({purpose})")
            all_available = False

    return all_available

def check_config_files():
    print_section("配置文件检查")
    import os

    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    files_to_check = {
        '.env': '存储敏感信息（邮箱授权码、API Key）',
        'config.json': '存储配置信息（邮箱、提示词等）'
    }

    all_exist = True
    for filename, purpose in files_to_check.items():
        filepath = os.path.join(project_root, filename)
        if os.path.exists(filepath):
            print(f"✅ {filename} 存在 ({purpose})")
        else:
            print(f"❌ {filename} 不存在 ({purpose})")
            all_exist = False

    if not all_exist:
        print("\n修复方法:")
        print("  参考 DEPLOY.md 中的「前置准备」章节创建这些文件")

    return all_exist

def check_permissions():
    print_section("权限检查")
    system = platform.system()

    if system == 'Darwin':
        print("macOS 需要以下权限:")
        print("  • 系统设置 → 隐私与安全性 → 完全磁盘访问 → 开启「终端」")
        print("  （如果定时任务无法写入文件，需要此权限）")
    elif system == 'Linux':
        print("Linux 可能需要以下权限:")
        print("  • systemd 服务配置需要 sudo 权限")

    return True

def main():
    print("""
╔══════════════════════════════════════════════════════════════╗
║         ViewAssistant 环境检测工具                           ║
║         确保所有依赖和配置正确安装                           ║
╚══════════════════════════════════════════════════════════════╝
""")

    checks = [
        check_python_version(),
        check_dependencies(),
        check_system_commands(),
        check_config_files(),
        check_permissions()
    ]

    print_section("检测结果汇总")

    if all(checks):
        print("✅ 所有检查通过！环境配置正确。")
        print("\n下一步:")
        print("  python src/weekly_report.py  # 运行一次测试")
        return 0
    else:
        print("❌ 部分检查未通过，请根据上述提示修复问题。")
        print("\n常见问题:")
        print("  1. Python 版本过低 → 从 python.org 下载最新版本")
        print("  2. 依赖未安装 → pip install -r requirements.txt")
        print("  3. 配置文件缺失 → 参考 DEPLOY.md 创建")
        return 1

if __name__ == '__main__':
    sys.exit(main())
