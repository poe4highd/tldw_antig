# 2026-03-07 开发日志

### [前置] 修复自动追踪任务完成后丢失 `report_data.source`
- **需求**：在频道追踪健康审计中发现，自动追踪创建的视频在完成处理后，`report_data.source` 会从 `tracker` 变成 `null`，削弱来源追踪与统计能力。用户要求先修复这个问题并提交。
- **根因**：
  1. `backend/process_task.py` 完成态 upsert `videos` 时重建了整段 `report_data`。
  2. 新 `report_data` 只保留字幕、摘要、关键词、频道等生成结果字段，未合并 queued 阶段已有的 `source`、`retry_count`、`duration`、`view_count` 等元字段。
- **计划**：
  1. 修改 `process_task.py`，在完成态保存前保留原始 `report_data` 元字段，仅覆盖生成结果字段。
  2. 做语法校验并补充审计记录。
  3. 提交代码与审计文档，随后单独检查 `backend/youtube_cookie.txt` 是否可用。

### [回顾] 保留 Tracker 任务来源字段与 queued 元数据
- **实际改动**：
  1. `backend/process_task.py`：新增 `existing_report_data`，在读取任务时保存当前数据库中的 `report_data`。
  2. 完成态回写 Supabase 时，先以 `existing_report_data` 为基础，再覆盖 `paragraphs`、`raw_subtitles`、`summary`、`keywords`、`channel`、`channel_id`、`channel_avatar` 等生成结果字段。
  3. 这样可保留 `source=tracker` 以及其他 queued 阶段写入的元数据，避免完成态把来源信息冲掉。
- **验证**：
  1. 代码结构检查完成，逻辑上已从“重建 report_data”改为“合并 report_data”。
  2. 该修复不会改变现有完成态字段，只会保留此前被错误丢弃的元字段。

### [经验] 关键教训
- **完成态 upsert 不能无脑重建 JSON 字段**：对 `report_data` 这类混合字段，处理链后半段应合并更新而不是整段覆盖，否则很容易把队列阶段的来源、重试次数和辅助元数据冲掉。

### [前置] 再次审核频道追踪功能健康度
- **需求**：用户要求再次审核频道追踪功能是否健康运行，本轮重点确认 systemd 服务、Tracker 定时触发、`yt-dlp` 修复、入队结果与端到端处理链是否闭环。
- **审计范围**：
  1. `tldw-backend`、`tldw-scheduler`、`tldw-frontend` 服务状态
  2. `[Tracker]` 小时级调度日志与最近运行时间
  3. `backend/scripts/channel_tracker.py` 的 `yt-dlp` 解析与 cookies 降级路径
  4. 最新 Tracker 入队任务是否成功被 scheduler 接走并处理完成
- **计划**：
  1. 先核对 systemd 状态、进程存活和 Tracker / scheduler 日志。
  2. 再核对 `venv/bin/yt-dlp`、cookies 路径与当前代码路径解析逻辑是否一致。
  3. 最后用最新一条 Tracker 发现的视频验证“入队 -> 调度 -> 完成”的端到端闭环，并输出是否需要重启或修复。

### [回顾] 频道追踪功能健康审计（结论：健康运行，存在轻微退化与可观测性缺口）
- **运行态**：
  1. `tldw-backend.service` 处于 `active (running)`，自 `2026-03-06 21:32:37 CST` 持续运行。
  2. `tldw-scheduler.service` 处于 `active (running)`，审计时正在处理任务 `Kys6HuRNwxo`。
  3. `tldw-frontend.service` 处于 `active (running)`。
- **调度链**：
  1. Tracker 自 `2026-03-06 21:37:40 CST` 修复后按约 1 小时频率稳定触发，最近一次运行时间为 `2026-03-07 13:42:10 ~ 13:42:33 CST`。
  2. 最近一次成功新增任务时间为 `2026-03-07 13:42:33 CST`，日志显示 `Added 1 tasks to the queue (0 retries, 1 new)`。
  3. 当前配置为 5 个追踪频道：`@nicolasyounglive`、`@axtonliu`、`UC26hLZoe-haxcuLYxzWAiNg`、`@AlanChen`、`@yuegemovie`。
- **依赖链**：
  1. `backend/scripts/channel_tracker.py` 已生效使用 `_resolve_ytdlp_cmd()`，优先绑定 `venv/bin/yt-dlp`。
  2. 当前实际 `yt-dlp` 版本为 `2026.02.21`，路径 `/home/xs/projects/tldw_antig/backend/venv/bin/yt-dlp`。
  3. `YOUTUBE_COOKIES_PATH=./youtube_cookies.txt` 存在，但日志中每轮都会出现 `Cookies 请求失败 (rc=1)`，随后自动回退到无 cookies 路径继续执行。
- **处理链闭环**：
  1. 最新任务 `Kys6HuRNwxo` 于 `2026-03-07 13:42:26 CST` 创建，`13:42:31 CST` 被 scheduler 接走。
  2. 本地状态文件在处理中经历 `llm_processing`，最终 `results/Kys6HuRNwxo_status.json` 为 `{\"status\": \"completed\", \"progress\": 100, \"eta\": null}`。
  3. `journalctl --user -u tldw-scheduler` 显示该任务于 `2026-03-07 13:47:58 CST` 成功写回 Supabase，scheduler 记录 `Task Kys6HuRNwxo completed successfully`。
- **审计发现**：
  1. **轻微退化**：cookies 文件看起来已失效或不兼容，Tracker 每轮都要先失败再回退，功能仍可用，但会增加额外耗时并留下噪声日志。
  2. **轻微基础设施波动**：scheduler 日志仍偶发 `Supabase handshake timed out`，但会自动恢复，未阻断今天的自动追踪与处理。
  3. **可观测性缺口**：`backend/process_task.py` 在任务完成后重新 upsert `report_data`，仅保留字幕/摘要/频道等字段，未保留原始 `source=tracker`，导致像 `Kys6HuRNwxo` 这种自动追踪创建的视频在完成后 `report_data.source` 变成 `null`。功能不受影响，但会削弱审计、统计与来源追踪能力。

### [经验] 健康度判定与后续建议
- **当前判定**：频道追踪功能属于“健康运行”。最新自动发现、自动入队、自动处理闭环均已实证通过，因此当前**不需要重启服务**。
- **建议 1**：刷新 `youtube_cookies.txt`，减少每轮 `cookies -> fallback` 的无效重试，降低日志噪声与检查时延。
- **建议 2**：后续单独修复 `process_task.py` 对 `report_data.source` 的覆盖问题，保留 `tracker/manual/submission/like` 等来源字段，提升运营与排障可观测性。

### [前置] 排查“最近视频处理是否停滞、频道追踪是否正常”
- **需求**：用户怀疑最近一个视频处理已停了几天，并要求确认系统运行、频道追踪、最近运行时间以及是否需要重启服务。
- **关键现象**：
  1. `results/IBpkIyz43Rk.json` 时间戳为 `2026-03-06 21:11:45 CST`，说明视频处理链未停摆。
  2. `tldw-backend`、`tldw-scheduler`、`tldw-frontend` 均为 `active (running)`。
  3. `journalctl --user -u tldw-backend` 中 `[Tracker]` 日志按小时触发，但持续报错 `Unexpected error for @...: [Errno 2] No such file or directory: 'yt-dlp'`。
- **计划**：
  1. 核对 systemd 服务状态与 scheduler/Tracker 日志，确认故障边界。
  2. 修复 `backend/scripts/channel_tracker.py` 在 systemd 环境下的 `yt-dlp` 命令解析。
  3. 重启 backend 并复查 Tracker 日志，确认修复生效后再同步审计记录。

### [回顾] 修复频道追踪器在 systemd 下找不到 yt-dlp
- **根因**：
  1. `backend/scripts/channel_tracker.py` 通过 `subprocess.run()` 硬编码调用 `"yt-dlp"`，直接依赖外部 `PATH`。
  2. systemd user service 的 `PATH` 不含 venv `bin` 和 `/home/xs/anaconda3/bin`，因此交互式 shell 可执行不代表服务环境可执行。
  3. 结果是频道追踪调度器每小时都在运行，但自动抓取新视频长期处于“假活”状态。
- **实际改动**：
  1. `backend/scripts/channel_tracker.py`：新增 `_resolve_ytdlp_cmd()`，优先使用 `venv/bin/yt-dlp`，其次回退系统 `PATH`，最后回退 `sys.executable -m yt_dlp`。
  2. `get_latest_video_id()` 与 `get_video_metadata()` 改为统一使用解析后的命令前缀，消除对子进程 `PATH` 的硬依赖。
  3. 重启 `tldw-backend.service` 使修复生效；无需重启 `scheduler` 与 `frontend`。
  4. 已提交并推送代码：`7688adf Fix tracker yt-dlp resolution under systemd`。
- **验证**：
  1. `./venv/bin/python3 -m py_compile scripts/channel_tracker.py` 通过。
  2. 在精简环境 `PATH=/usr/bin` 下执行 `_resolve_ytdlp_cmd() + ["--version"]` 返回 `2026.02.21`。
  3. backend 重启后，`2026-03-06 21:37:40 CST` 首轮 Tracker 正常执行，日志中不再出现 `No such file or directory: 'yt-dlp'`。
  4. 修复前最近一次成功处理视频时间为 `2026-03-06 21:11:45 CST`（`IBpkIyz43Rk`），确认问题只影响频道追踪，不影响现有任务处理链。

### [经验] 关键教训
- **交互式 shell 与 systemd 是两套环境**：命令行里存在的可执行文件，不代表 service 进程一定能解析到。
- **后台任务“定时触发”不等于“业务正常”**：本次故障中调度器与后端服务都活着，但实际自动追踪因子进程命令解析失败而失效。
- **外部命令应优先绑定当前运行时**：若主进程已在 venv 中运行，子进程应尽量复用同一 venv 可执行文件或解释器，避免把正确性押在全局 `PATH` 上。
