# 2026-06-06 开发日志

### [Feature] YouTube Playlist 批量提交任务

- **需求**：用户希望提供 YouTube playlist URL 后，系统能提取列表中的所有视频 URL，并逐个提交到现有视频分析队列；测试链接为 `https://www.youtube.com/watch?v=0WEGa2iaDm8&list=PLmAJn2vsW0CCm6bx3y1aIEBI-qTaWRwLf`。该功能仅允许 `poe4high.dimension@gmail.com` 使用。

- **受影响文件（计划）**：
  - `backend/main.py`
  - `frontend/app/tasks/page.tsx`
  - `frontend/translations/zh.json`
  - `frontend/translations/en.json`
  - `.dev-audit/DEV_LOG.md`
  - `.dev-audit/PROJECT_HISTORY.md`

- **计划**：
  1. 后端新增 playlist 请求模型、白名单邮箱常量、用户 email 校验 helper、playlist URL 校验与 `yt-dlp` 扁平提取 helper。
  2. 后端新增受限批量入队端点：只允许 `poe4high.dimension@gmail.com` 对 playlist URL 调用；提取视频 ID 后逐条写入 `videos` 的 `queued` 记录与 `submissions` 关联，复用现有 scheduler 处理链路。
  3. 前端任务页识别当前登录用户 email：仅目标账号显示 playlist 批量提交入口；提交后展示已入队数量并刷新活动任务。
  4. 补齐中英文文案，并用给定 playlist URL 验证提取逻辑；在无网络或缺少 yt-dlp 环境时记录验证限制。

- **回顾**：
  1. `backend/main.py` 新增 `PlaylistProcessRequest`、`PLAYLIST_ALLOWED_EMAIL`、Bearer token 解析和 `_ensure_playlist_access()`，后端通过 Supabase `auth.get_user(access_token)` 校验真实登录用户 email，只允许 `poe4high.dimension@gmail.com` 调用。
  2. 新增 `_extract_playlist_videos()`：使用 `yt-dlp` flat playlist 模式读取 playlist 条目，去重生成标准 `https://www.youtube.com/watch?v={id}` URL，并过滤 `[Private video]` / `[Deleted video]` 这类不可分析条目。
  3. 新增 `/process-playlist`：将 playlist 内可分析视频逐个写入 `videos.status=queued` 与 `submissions`，保留 `report_data.source=manual` 以复用 scheduler 优先级，同时增加 `batch_source=playlist`、`playlist_url`、`playlist_index` 方便追踪。
  4. `frontend/app/tasks/page.tsx` 仅在当前登录 email 为 `poe4high.dimension@gmail.com` 时显示“批量处理列表”按钮；提交时附带 Supabase access token 给后端做真实鉴权，成功后展示入队数量并刷新活动任务。
  5. `frontend/translations/zh.json`、`frontend/translations/en.json` 补齐 playlist 入口、校验、提取中、入队成功文案。
  6. 验证：`backend ./venv/bin/python -m py_compile main.py` 通过；翻译 JSON 解析通过；`frontend npx tsc --noEmit` 通过；`frontend npx eslint app/tasks/page.tsx` 0 error / 7 warning（均为既有 unused/img warning）；全仓 `npm run lint` 仍失败于既有 admin/result/settings/context lint error。
  7. 使用测试链接实测 `yt-dlp --flat-playlist` 可提取 16 条，其中 1 条为 `[Private video]`，后端过滤后会入队 15 条可分析视频。
  8. 按 README 指引使用 `rt restart tldw-backend` 与 `rt restart tldw-frontend` 重启服务；后端启动时间刷新至 2026-06-06 20:15:20 CDT，前端刷新至 2026-06-06 20:15:28 CDT。`rt restart` target 本身不会刷新子服务，调度器正在处理任务所以未重启，避免中断分析。

- **经验**：
  - 仅前端隐藏入口不够安全；批量任务这种高成本操作必须以后端 token 校验作为准入边界。
  - playlist URL 带 `watch?v=...&list=...` 时，提取阶段应生成不带 `list` 参数的单视频 URL，避免后续下载流程误走 playlist。
  - YouTube playlist 可能包含私有/删除视频；flat playlist 仍可能返回占位 ID，入队前过滤能避免制造必失败任务。

---
