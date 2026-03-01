# 2026-03-01 开发日志

### [回顾] 修复 yt-dlp 下载失败：过期 Cookies + systemd ffmpeg 路径缺失
- **需求**：视频 w1IksuH1k-Q 在 scheduler 修复后仍然失败。需要深层排查。
- **Error Stack**：
  1. `yt_dlp.utils.ExtractorError: Requested format is not available` — 过期 cookies 导致 YouTube 返回受限格式列表
  2. `DownloadError: Unable to download video subtitles: HTTP Error 429` — 字幕下载 429 限流被当作致命错误
  3. `DownloadError: Preprocessing: ffmpeg not found` — systemd 服务 PATH 不含 anaconda
- **根因分析**：
  1. **过期 cookies**：`.env` 中 `YOUTUBE_COOKIES_PATH` 指向过期 cookies 文件，YouTube 返回不同的格式列表导致 `bestaudio/best` 无法匹配
  2. **字幕 429 致命**：yt-dlp 默认将字幕下载失败视为致命错误
  3. **ffmpeg 路径**：systemd user service 的 PATH 不含 `/home/xs/anaconda3/bin`，yt-dlp 和 subprocess 调用找不到 ffmpeg
- **修复**：
  1. `downloader.py`：添加 3 层重试策略（cookies+字幕 → cookies无字幕 → 无cookies无字幕），添加 `_find_ffmpeg()` 动态查找并配置 `ffmpeg_location`
  2. `process_task.py`：启动时自动检测并补全 ffmpeg PATH，去除 metadata 提取中不必要的 cookies 和 extractor_args
- **验证**：w1IksuH1k-Q 全链路处理成功（下载 → 转录 → LLM → 完成），结果文件 363KB

### [经验] 关键教训
- **Cookies 是双刃剑**：过期 cookies 比无 cookies 更糟糕——会导致 YouTube 返回受限的格式列表。应永远有无 cookies 降级路径。
- **systemd 环境隔离**：从交互式 shell 测试通过 ≠ 从 systemd service 运行通过。PATH、env vars 完全不同。
- **`extractor_args: player_client`**：`android` client 需要 GVS PO Token，缺失时格式被跳过。不应作为默认配置。

---

### [前置] 修复 Scheduler 使用错误 Python 解释器导致所有任务立刻失败
- **需求**：继续排查视频提交立刻失败的根因。上一轮修复了竞态条件和错误兜底，但任务仍然快速失败。
- **Error Stack**：系统 `python3` 指向 anaconda（`/home/xs/anaconda3/bin/python3`），缺少 `supabase` 包导致 `ImportError: cannot import name 'create_client'`。Scheduler 自身用 venv 运行但子进程用硬编码的 `python3`。
- **计划**：
  1. 修复 scheduler.py 的 Python 解释器（`sys.executable` 替代 `python3`）
  2. 修复 /history 端点的同类竞态条件（活动任务列表显示 PROCESSING 100%）
  3. 重启 scheduler 使修复生效

### [回顾] 实际改动
1. **根因修复** (`scheduler.py:158`): `["python3", ...]` → `[sys.executable, ...]`，确保子进程使用与 scheduler 相同的 venv Python
2. **活动任务竞态修复** (`main.py:643-668`): /history 端点的 processing 分支增加本地 failed/completed 状态检测，与 GET /result 保持一致

### [经验] 关键根因
- **隐式解释器假设**: `python3` 在不同环境指向不同解释器。Scheduler 被 venv python 启动，但 subprocess 调用系统 python3，包环境完全不同。应始终用 `sys.executable` 确保一致性。
- **错误被多层吞没**: process_task.py 在 import 阶段就崩溃 → 没走到异常处理 → 无 _error.json → scheduler 旧代码也不补写 → Supabase 更新也失败 → 信息全部丢失

# 2026-02-28 开发日志

### [前置] 修复视频处理失败后"立刻显示错误+100%进度"的竞态条件（yirGNdXQxkE）
- **需求**：用户提交视频 yirGNdXQxkE 后立刻显示失败，进度100%。无 `_error.json` 导致无法诊断失败原因。上次 commit `4e1ed19` 的修复不完整。
- **Error Stack**：`results/yirGNdXQxkE_status.json` = `{"status": "failed", "progress": 100}`，Supabase 状态卡在 `processing`（未同步失败），无 `_error.json`。
- **计划**：
  1. 修复 GET `/result` 竞态：Supabase 说 processing 但本地文件已 failed 时，直接透传了 progress=100
  2. Scheduler 失败路径补写 `_error.json`，捕获 stderr 保留诊断信息
  3. process_task.py 早期退出路径补写 `_error.json`
  4. 手动运行 process_task.py 诊断实际失败原因

### [回顾] 实际改动
1. **BUG 1 - GET /result 竞态修复** (`main.py:541-555`): 当 Supabase 为 queued/processing 但本地 _status.json 为 failed 时，不再直接透传本地文件内容，而是走 failed 分支逻辑（返回 progress=0 + 错误详情）
2. **BUG 2 - Scheduler 错误兜底** (`scheduler.py:164-196`): 将 `capture_output=False` 改为捕获 stderr；在 `returncode != 0` 和 `except` 分支中，如果 process_task.py 未创建 `_error.json`，由 scheduler 补写（含 exit code 和 stderr）
3. **BUG 3 - 早期退出兜底** (`process_task.py:77-85`): "无 URL/本地文件" 的早期退出路径增加 `_error.json` 创建
4. **诊断结果**: 手动运行 `process_task.py yirGNdXQxkE` 全流程成功（下载→转录→LLM→Supabase），确认之前的失败为间歇性问题（可能是网络抖动或 GPU 资源冲突）

### [经验] 关键根因与设计教训
- **竞态条件的本质**: 双层状态系统（Supabase + 本地文件）在任务快速失败时（<8秒），Supabase 更新可能被 `except: pass` 吞掉，导致 GET /result 在 "processing" 分支下直接透传本地的 `{"status": "failed", "progress": 100}`——完美绕过了 failed 分支的 progress=0 修复
- **错误诊断链断裂**: Scheduler → process_task.py → worker.py 三层中，只有 worker.py 和 process_task.py 的 except 分支会写 `_error.json`，scheduler 的失败处理和 process_task 的早期退出都不写，导致崩溃时无法诊断
- **防御性原则**: 任何写 `save_status("failed", ...)` 的地方都应同时确保 `_error.json` 存在
