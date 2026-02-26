# 开发启动与日志监控指南 (Development Guide)

本指南介绍如何在开发环境下高效启动 Read-Tube 的前后端服务，并实时监控系统运行状态。

## 1. 快速启动 (推荐)

项目根目录下提供了一个 `dev.sh` 脚本，可以一键并行启动前后端服务，并将日志合并输出。

### 使用方法：
```bash
./dev.sh
```

### 功能特点：
- **自动环境识别**：自动检测 `backend/venv` 并激活虚拟环境。
- **日志着色与前缀**：
  - `[BACKEND]` (蓝色)：后端 FastAPI 服务的输出。
  - `[FRONTEND]` (绿色)：前端 Next.js 服务的输出。
- **自动化冲突处理**：脚本启动前会检测端口 8000 和 3000。如果发现被旧进程占用，将自动清理相关进程，确保“一键启动”无需手动杀 PID。
- **进程生命周期管理**：按下 `Ctrl+C` 会自动清理并关闭前后端所有相关进程，防止端口占用。

---

## 2. 分步启动 (手动方式)

如果您需要进行更精细的调试或分别管理服务，可以采用分步启动。

### 后端 (API)
```bash
cd backend
source venv/bin/activate
# 方法 A: 直接运行脚本 (推荐，带自动重载)
python main.py

# 方法 B: 使用 uvicorn 命令
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 前端 (UI)
```bash
cd frontend
npm run dev
```

---

## 3. 日志监控 (Logging & Monitoring)

### 3.1 终端实时监控
使用 `./dev.sh` 时，您可以直接在终端看到合并后的日志流。通过前缀颜色快速定位问题所在。

### 3.2 持久化日志文件
后端运行过程中，标准的 `stdout/stderr` 会被重定向或保持在当前会话。
- **标准日志**：后端默认不直接写入文件，建议在生产环境使用 `pm2` 或 `nohup` 进行持久化：
  ```bash
  nohup python3 main.py > uvicorn_stable.log 2>&1 &
  ```
- **关键任务状态**：每个转录任务的状态保存在 `backend/results/{task_id}_status.json` 中，可通过查看此文件了解任务具体进度。

### 3.3 异常排查
- **HTTP 404/500**：检查后端终端输出，查看是否有 Python 堆栈错误。
- **CORS 跨域问题**：检查 `backend/main.py` 中的 `allow_origins` 配置。
- **LSP 崩溃**：如遇到 `downloader.py` 导致的 IDE 性能问题，请参考 `docs/ai_agent_dev_preferences_cn.md` 中的延迟导入部分。

---

## 4. 常用维护命令

- **清理空间**：`cd backend && python maintenance.py` (清理导出、原视频及临时文件)
- **重置 Prompt 效果**：修改 Prompt 后运行 `python maintenance.py` 触发全量重处理。

---

## 5. 持久化后台服务 (systemd)

对于长期运行的服务器环境，使用 **systemd user services** 代替手动执行 `dev.sh`。关闭终端、VSCode 甚至注销账户后服务依然运行，重启系统后自动恢复。

### 5.1 服务列表

| 服务文件 | 内容 |
|---------|------|
| `~/.config/systemd/user/tldw-backend.service` | FastAPI 后端 (uvicorn, port 8000) |
| `~/.config/systemd/user/tldw-frontend.service` | Next.js 前端 (npm run dev, port 3000) |
| `~/.config/systemd/user/tldw-scheduler.service` | 任务调度器 (scheduler.py) |
| `~/.config/systemd/user/cloudflared-tldw.service` | Cloudflare 隧道 (ubuntu-read-tube) |
| `~/.config/systemd/user/tldw.target` | 统一控制以上所有服务的 target |

> **注意**：`loginctl enable-linger xs` 已启用，确保无登录会话时服务也持续运行。

### 5.2 快捷命令 `rt`

项目提供了 `~/bin/rt` 脚本，封装了常用的 systemd 操作：

```bash
rt                         # 查看所有服务状态
rt start                   # 启动所有服务
rt stop                    # 停止所有服务
rt restart                 # 重启所有服务
rt restart tldw-backend    # 只重启某个服务
rt logs                    # 实时查看后端日志（Ctrl+C 退出）
rt logs tldw-frontend      # 实时查看前端日志
rt logs tldw-scheduler     # 实时查看调度器日志
rt logs cloudflared-tldw   # 实时查看隧道日志
```

### 5.3 原生 systemctl / journalctl 命令

```bash
# 服务控制
systemctl --user start tldw.target
systemctl --user stop tldw.target
systemctl --user restart tldw-backend

# 日志查看
journalctl --user -u tldw-backend -f           # 实时追踪
journalctl --user -u tldw-backend -n 100       # 最近 100 行
journalctl --user -u tldw-backend -p err       # 只看错误
journalctl --user -u tldw-backend --since "10 min ago"

# 同时查看多个服务
journalctl --user -u tldw-backend -u tldw-scheduler -f
```

### 5.4 与 dev.sh 的区别

| 对比项 | `./dev.sh` | systemd 服务 |
|--------|-----------|-------------|
| 终端依赖 | 终端关闭即停 | 完全独立 |
| 日志颜色 | 有（ANSI 彩色） | 无（journald 纯文本） |
| 自动重启 | 无 | 崩溃后自动重启 |
| 开机自启 | 无 | 有 |
| 适用场景 | 开发调试 | 后台长期运行 |
