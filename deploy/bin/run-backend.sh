#!/bin/bash
# FastAPI 后端启动脚本（由 tldw-backend.service 调用）
# --reload：合并到 main 即上线，改 .py 自动重载
set -euo pipefail
cd "$(dirname "$(readlink -f "$0")")/../../backend"
fuser -k 8000/tcp 2>/dev/null || true
exec venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000 --reload
