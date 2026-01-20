#!/bin/bash

# 定义颜色 (使用 printf 保证 macOS 兼容性)
BLUE=$(printf '\033[0;34m')
GREEN=$(printf '\033[0;32m')
YELLOW=$(printf '\033[0;33m')
RED=$(printf '\033[0;31m')
NC=$(printf '\033[0m') # No Color

# 打印带有前缀的日志函数
log_backend() {
    sed "s/^/${BLUE}[BACKEND]${NC} /"
}

log_frontend() {
    sed "s/^/${GREEN}[FRONTEND]${NC} /"
}

# 停止所有进程的函数
cleanup() {
    printf "\n${NC}正在停止开发服务...${NC}\n"
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    exit
}

# 检查并清理端口函数
check_and_kill_port() {
    local port=$1
    local name=$2
    local pid=$(lsof -ti :$port)
    if [ ! -z "$pid" ]; then
        printf "${NC}检测到端口 $port ($name) 被占用，正在清理进程 (PID: $pid)...${NC}\n"
        kill -9 $pid 2>/dev/null
    fi
}

# 捕获 Ctrl+C (SIGINT)
trap cleanup SIGINT

printf "${NC}开始启动自动开发环境...${NC}\n"

# 0. 检查并清理冲突
check_and_kill_port 8000 "BACKEND"
check_and_kill_port 3000 "FRONTEND"

# 0.5 检查 Cloudflare 隧道状态
if ! pgrep -x "cloudflared" > /dev/null; then
    printf "${YELLOW}[WARN] 未检测到 Cloudflare 隧道进程 (cloudflared)。${NC}\n"
    printf "${YELLOW}建议运行: ${NC}nohup cloudflared tunnel run mac-read-tube > .cloudflared/tunnel.log 2>&1 &\n"
else
    # 检查是否是正确的隧道在运行 (可选增加更多检查)
    printf "${GREEN}[INFO] Cloudflare 隧道进程运行中。${NC}\n"
fi

# 1. 启动后端
printf "${BLUE}启动后端服务 (FastAPI)...${NC}\n"
export KMP_DUPLICATE_LIB_OK=TRUE
export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1
export KMP_BLOCKTIME=0
if [ -d "backend/venv" ]; then
    (cd backend && source venv/bin/activate && python3 main.py) 2>&1 | log_backend &
else
    (cd backend && python3 main.py) 2>&1 | log_backend &
fi
BACKEND_PID=$!

# 2. 启动前端
printf "${GREEN}启动前端服务 (Next.js)...${NC}\n"
(cd frontend && npm run dev) 2>&1 | log_frontend &
FRONTEND_PID=$!

# 等待所有后台进程
wait
