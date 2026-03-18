# 2026-03-17 开发日志

### [UX] 上传文件报告页自动切换到 MP3 播放器
- **需求**：上传的音频/视频没有 YouTube 链接，报告页面默认显示 YouTube 播放器导致"该视频不能观看"。应自动根据来源类型切换：YouTube → YouTube 播放器，上传文件 → MP3 播放器。同时删除手动切换按钮。
- **实际改动**：
  1. `frontend/app/result/[id]/ResultClient.tsx` L86-87：`useLocalAudio` 从 `useState(false)` 改为根据 `result.youtube_id` 自动判断（`up_` 前缀或无 youtube_id → 本地音频）
  2. 同文件：删除 "Sync Audio" / "YouTube" 手动切换按钮
- **验证**：`npx next build` ✓

### [Bugfix] /process 端点增加 URL 格式校验
- **需求**：用户反映任务 `1773761314` 处理失败。排查发现该任务通过 `/process` 端点提交，URL 值为 "Xxx"（无效），`media_path` 为 null。后端无 URL 校验直接入队，yt-dlp 下载 "Xxx" 报错。
- **根因**：`/process` 端点不校验 URL 格式，任何文本都能入队。非 YouTube ID 且非 HTTP URL 的输入会生成时间戳 task_id 并白白浪费 scheduler 资源。
- **实际改动**：
  1. `backend/main.py` `/process` 端点：新增 URL 基础校验，必须是 `http(s)://` 开头或 11 位 YouTube ID，否则返回 400
  2. `frontend/app/tasks/page.tsx` `startProcess()`：前端提交前同步校验，无效输入即时提示
- **验证**：`python3 -m py_compile main.py` ✓

# 2026-03-16 开发日志

### [Bugfix] 修复上传音频处理因 channel 变量未定义而崩溃
- **需求**：用户反映上传音频文件未被正确处理。排查发现最近两次上传（`up_da05b8c0`、`up_c033b14b`）均在 finalize 阶段报 `UnboundLocalError: cannot access local variable 'channel'`。
- **根因**：`process_task.py` 中 `channel`、`channel_id`、`channel_avatar` 三个变量只在 `if url:` 分支（YouTube 路径 L142-144）内初始化，上传文件走 `elif local_file:` 分支跳过了初始化，但 L290-292 无条件引用这三个变量。Worker 子进程（转录+摘要）实际已成功完成，但 finalize 写结果时崩溃，导致 GPU 算力白烧。
- **计划**：
  1. 将 `channel`/`channel_id`/`channel_avatar` 初始化提到 `if url:` 之前（与 `video_id`、`description` 同级）
  2. Worker 成功后清理残留的 `_error.json`，防止重试场景下状态混乱
- **实际改动**：
  1. `backend/process_task.py` L109-111：新增 `channel = None` / `channel_id = None` / `channel_avatar = None` 默认初始化
  2. `backend/process_task.py` L145：删除 `if url:` 内的重复初始化（保留 `channel_url = None`，因其仅在该分支使用）
  3. `backend/process_task.py` L276-280：Worker 成功后检查并删除残留 `_error.json`
- **验证**：`python3 -m py_compile process_task.py` ✓
- **经验**：变量作用域问题——当多个分支共享后续代码时，公共变量必须在分支之前初始化。重试场景需要清理上次失败的残留状态文件。
