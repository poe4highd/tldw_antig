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

log_scheduler() {
    sed "s/^/${YELLOW}[SCHEDULER]${NC} /"
}

# 停止所有进程的函数
cleanup() {
    printf "\n${NC}正在停止开发服务...${NC}\n"
    kill $BACKEND_PID $FRONTEND_PID $SCHEDULER_PID 2>/dev/null
    exit
}

# 检查并清理端口函数
check_and_kill_port() {
    local port=$1
    local name=$2
    # 使用 lsof 获取所有占用该端口的 PID
    local pids=$(lsof -ti :$port)
    if [ ! -z "$pids" ]; then
        printf "${RED}[CLEANUP]${NC} 检测到端口 $port ($name) 被占用，正在强制清理进程: $pids\n"
        echo "$pids" | xargs kill -9 2>/dev/null
        sleep 1
    fi
}

# 额外清理函数：针对性清理本项目的残留进程名
cleanup_stale_processes() {
    printf "${BLUE}[CLEANUP]${NC} 正在清理残留的后端和调度器进程...\n"
    # 清理 uvicorn 和相关的 python 进程
    pgrep -f "uvicorn main:app" | xargs kill -9 2>/dev/null
    pgrep -f "scheduler.py" | xargs kill -9 2>/dev/null
    pgrep -f "process_task.py" | xargs kill -9 2>/dev/null
}

# 捕获 Ctrl+C (SIGINT)
trap cleanup SIGINT

printf "${NC}开始启动自动开发环境...${NC}\n"

# 0. 检查并清理冲突
cleanup_stale_processes
check_and_kill_port 8000 "BACKEND"
check_and_kill_port 3000 "FRONTEND"

# 0.5 检查 Cloudflare 隧道状态
if ! pgrep -x "cloudflared" > /dev/null; then
    printf "${YELLOW}[WARN] 未检测到 Cloudflare 隧道进程 (cloudflared)。${NC}\n"
    printf "${YELLOW}建议运行: ${NC}systemctl --user start cloudflared-tldw  (或 rt start)\n"
else
    # 检查是否是正确的隧道在运行 (可选增加更多检查)
    printf "${GREEN}[INFO] Cloudflare 隧道进程运行中。${NC}\n"
fi

# 1. 启动后端 (使用 uvicorn --reload 支持热重载)
printf "${BLUE}启动后端服务 (FastAPI + 热重载)...${NC}\n"
export KMP_DUPLICATE_LIB_OK=TRUE
export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1
export KMP_BLOCKTIME=0
if [ -d "backend/venv" ]; then
    (cd backend && source venv/bin/activate && uvicorn main:app --host 0.0.0.0 --port 8000 --reload) 2>&1 | log_backend &
else
    (cd backend && uvicorn main:app --host 0.0.0.0 --port 8000 --reload) 2>&1 | log_backend &
fi
BACKEND_PID=$!

# 2. 启动前端
printf "${GREEN}启动前端服务 (Next.js)...${NC}\n"
(cd frontend && npm run dev) 2>&1 | log_frontend &
FRONTEND_PID=$!

# 3. 启动任务调度器 (顺序处理)
printf "${YELLOW}启动任务调度器 (Scheduler)...${NC}\n"
if [ -d "backend/venv" ]; then
    (cd backend && source venv/bin/activate && python3 -u scheduler.py) 2>&1 | log_scheduler &
else
    (cd backend && python3 -u scheduler.py) 2>&1 | log_scheduler &
fi
SCHEDULER_PID=$!

# 等待所有后台进程
wait
