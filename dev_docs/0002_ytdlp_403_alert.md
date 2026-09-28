# 0002 yt-dlp 403 修复 + 失败告警 + 卡住判定修正

- 日期：2026-09-27
- 分支：`shad` → `main`

## 1. 现象与证据
- 首页最新视频停在 2026-08-17。频道追踪正常（每天约 24 轮），但 8/17 后入队 108 个视频中 106 个 failed。
- `results/<id>_error.json`：自 08-18 起 104 次 `ERROR: unable to download video data: HTTP Error 403: Forbidden`。
- 106 个失败任务 `retry_count` 均已达上限 3，不会再自动重试。
- 根因：生产 venv yt-dlp 为 2026.02.21（7 个月未升级）。隔离 venv 复现：同一视频完整下载，旧版 403，2026.08.19 成功。
  - `--test` 仅下载前 10KiB 时旧版也成功，403 出现在后续分片——验证下载问题必须完整下载。
- 连带 bug：`check_stuck_tasks` 以 `created_at` 判断卡住（queued>24h / processing>3h）。tracker 重试不更新 `created_at`，
  旧任务重新入队后 30 分钟内就会被再次标记 failed、甚至处理中途被打断——这是 3 次重试迅速耗尽的原因。
- 连带 bug：scheduler 失败分支 `logger.info(..., file=sys.stderr)` 抛 TypeError，落入外层 except 重复处理。
- 系统静默失败 6 周无人察觉：没有任何失败告警。

## 2. 方案
1. 生产 venv 升级 `yt-dlp[default]`（2026.08.19，含 yt-dlp-ejs）；`requirements.txt` 改为 `yt-dlp[default]`，不锁版本。
2. `downloader.py`：配置 node 为 yt-dlp JS 运行时（PATH → ~/.nvm 查找），应对 YouTube 签名挑战。
3. `scheduler.py`：
   - 卡住判定改为"最后活动时间" = max(`created_at`, `results/<id>_status.json` mtime)；`STUCK_QUEUED_HOURS` 24 → 72。
   - 连续 5 个任务失败发邮件告警（一次），恢复后发恢复通知。
   - 修复 `logger.info(file=...)` TypeError。
4. `alerting.py`：SMTP（Gmail SSL 465）发信，凭据 `ALERT_SMTP_USER`/`ALERT_SMTP_PASSWORD`，收件人 poe4high.dimension@gmail.com；未配置只写日志。
5. `deploy/`：`tldw-ytdlp-upgrade.timer` 每周一 04:00 升级 yt-dlp，失败发邮件；`install.sh` 自动启用 `*.timer`。
6. `scripts/requeue_failed.py`：补跑最近 40 个 failed（9/11~9/28），重置 retry_count、删旧 `_error.json`、刷新 `_status.json`。
   - 8 月那批不补跑（时效性低，节省 LLM 费用）。

## 3. 上线顺序（有依赖）
合并 main → **先重启 scheduler 载入新卡住判定** → `install.sh` 启用 timer → 再执行 requeue（否则旧逻辑 30 分钟内把它们打回 failed）→ push。

## 4. 待用户操作
- ✅ 已完成（2026-09-27）：`backend/.env` 已配置 `ALERT_SMTP_USER`、`ALERT_SMTP_PASSWORD`（16 位应用密码，去空格、不加引号），测试邮件发送成功。
- 原步骤：填写凭据后 `rt restart tldw-scheduler`，
  然后 `cd backend && venv/bin/python alerting.py` 发测试邮件。
