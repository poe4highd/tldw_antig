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

所有部署配置都纳入仓库 `deploy/` 目录，这是唯一的源头：

| 仓库文件 | 内容 |
|---------|------|
| `deploy/systemd/tldw-backend.service` | FastAPI 后端 (uvicorn --reload, port 8000) |
| `deploy/systemd/tldw-frontend.service` | 本地 Next.js 开发服务器 (port 3000，生产前端在 Vercel) |
| `deploy/systemd/tldw-scheduler.service` | 任务调度器 (scheduler.py) |
| `deploy/systemd/cloudflared-tldw.service` | Cloudflare 隧道 (ubuntu-read-tube，api.read-tube.com → 8000) |
| `deploy/systemd/tldw.target` | 统一控制以上所有服务的 target |
| `deploy/systemd/tldw-ytdlp-upgrade.{service,timer}` | 每周一 04:00 自动升级 yt-dlp（失败发邮件告警） |
| `deploy/bin/run-*.sh` | 各服务的启动逻辑（按脚本位置解析仓库路径） |
| `deploy/bin/rt` | 快捷管理命令 |
| `deploy/install.sh` | 把单元与 `rt` 软链接到 `~/.config/systemd/user/`、`~/bin/` |

> systemd 只从固定目录加载单元，因此 `~/.config/systemd/user/` 下保留的是由 `install.sh` 生成的软链接，**不要手工编辑**。
> 单元文件中的唯一绝对锚点是 `%h/projects/tldw_antig`，软链接必须指向这个生产主仓库，而不是 worktree（`install.sh` 会校验）。
>
> **注意**：`loginctl enable-linger xs` 已启用，确保无登录会话时服务也持续运行。

**新机器 / 首次安装**：
```bash
git clone git@github.com:poe4highd/tldw_antig.git ~/projects/tldw_antig
cd ~/projects/tldw_antig && ./deploy/install.sh
systemctl --user enable tldw.target tldw-backend tldw-frontend tldw-scheduler cloudflared-tldw
```

**改动生效规则**（合并到 main 即上线）：

| 改动 | 生效方式 |
|------|---------|
| `backend/**/*.py` | uvicorn `--reload` 自动重载；scheduler 需 `rt restart tldw-scheduler` |
| `deploy/bin/run-*.sh` | `rt restart <服务>` |
| `deploy/systemd/*` | `systemctl --user daemon-reload` 后 `rt restart <服务>` |
| 新增单元文件 | 重新执行 `./deploy/install.sh` |

**运维告警**：scheduler 连续 5 个任务失败时发邮件（恢复后再发一封），yt-dlp 自动升级失败也会发邮件。
需在 `backend/.env` 配置 `ALERT_SMTP_USER` / `ALERT_SMTP_PASSWORD`（Gmail 应用专用密码），见 `backend/.env.example`；
配置后可用 `cd backend && venv/bin/python alerting.py` 发送测试邮件。未配置时只写日志。

**批量重新入队失败任务**：`cd backend && venv/bin/python scripts/requeue_failed.py --limit 40 [--dry-run]`

### 5.2 快捷命令 `rt`

`deploy/bin/rt`（经 `install.sh` 链接为 `~/bin/rt`）封装了常用的 systemd 操作：

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
