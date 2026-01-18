#!/bin/bash

# 定义颜色
BLUE='\033[0;34m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

# 打印带有前缀的日志函数
log_backend() {
    sed "s/^/${BLUE}[BACKEND]${NC} /"
}

log_frontend() {
    sed "s/^/${GREEN}[FRONTEND]${NC} /"
}

# 停止所有进程的函数
cleanup() {
    echo -e "\n${NC}正在停止开发服务...${NC}"
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    exit
}

# 捕获 Ctrl+C (SIGINT)
trap cleanup SIGINT

echo -e "${NC}开始启动自动开发环境...${NC}"

# 1. 启动后端
echo -e "${BLUE}启动后端服务 (FastAPI)...${NC}"
if [ -d "backend/venv" ]; then
    (cd backend && source venv/bin/activate && python3 main.py) 2>&1 | log_backend &
else
    (cd backend && python3 main.py) 2>&1 | log_backend &
fi
BACKEND_PID=$!

# 2. 启动前端
echo -e "${GREEN}启动前端服务 (Next.js)...${NC}"
(cd frontend && npm run dev) 2>&1 | log_frontend &
FRONTEND_PID=$!

# 等待所有后台进程
wait
