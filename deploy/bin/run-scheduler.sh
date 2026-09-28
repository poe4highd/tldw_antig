#!/bin/bash
# 任务调度器启动脚本（由 tldw-scheduler.service 调用）
set -euo pipefail
cd "$(dirname "$(readlink -f "$0")")/../../backend"
exec venv/bin/python3 -u scheduler.py
