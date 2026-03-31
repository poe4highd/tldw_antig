# 2026-03-30 开发日志

### [Perf] 降低 Supabase Egress 超量 — 轮询瘦身 + SELECT 精简

- **需求**：Supabase Free Plan egress 限额 5GB，本计费周期已用 9.74GB（超量 4.74GB）。分析原因并优化数据传输量。
- **根因分析**：
  1. `tasks/page.tsx` 进度轮询每 2 秒拉一次 `/result/{taskId}`（含 report_data ~85KB 大字段），5 分钟任务产生 ~12.5MB 出流量
  2. `tasks/page.tsx` 历史记录每 15 秒无条件轮询，历史数据变化频率极低
  3. `pending/page.tsx` 队列页每 5 秒无条件轮询，队列为空时完全无意义
  4. `main.py` `/bookshelf` 使用 `videos(*)` 拉全量 video 记录（含 paragraphs/raw_subtitles 大字段）
- **计划**：
  1. 进度轮询降频：2000ms → 30000ms
  2. 历史记录改为事件驱动：任务完成时触发一次，移除定时器
  3. 队列轮询改为条件触发：`active_tasks.length > 0` 时才轮询
  4. `videos(*)` 改为精确字段选择，通过 PostgREST JSON path 仅拉 summary/keywords
- **实际改动**：
  1. `frontend/app/tasks/page.tsx:186` 轮询间隔 2000 → 30000
  2. `frontend/app/tasks/page.tsx` 移除 `setInterval(() => fetchHistory(), 15000)`，在任务 completed 分支加 `fetchHistory()` 触发一次
  3. `frontend/app/pending/page.tsx` 拆分 useEffect：初始加载独立，轮询条件依赖 `tasks.length > 0`
  4. `backend/main.py:1022/1030` `videos(*)` → `videos(id, title, thumbnail, status, is_public, report_data->summary, report_data->keywords)`
  5. 同步修改后端取值：`video.get("report_data", {}).get("summary")` → `video.get("summary")`
- **验证**：
  1. 代码层面逻辑验证通过，字段对齐
  2. PostgREST JSON path 选择器（`report_data->summary`）需上线后在 Supabase Dashboard → API Logs 验证字段提升是否生效；如异常可 fallback 到 `report_data` 整列
  3. 预计每日 egress 从 300-500MB 降至 100-150MB
- **经验**：轮询场景要区分"用户主动在看的动态数据"与"变化频率低的静态列表"——前者可以轮询但要瘦身载荷，后者应改为事件驱动或手动触发。SELECT * 在 JOIN 场景代价尤其高，report_data 大字段（paragraphs/raw_subtitles）应通过 JSON path 选择器按需提取。
