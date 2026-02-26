# 开发日志 (2026-02-26) - 任务：Scheduler 自动清理卡住的 processing 任务

## 1. 需求 (Requirement)
- **背景**: 当 `process_task.py` 子进程崩溃时（OOM、网络中断等），Supabase 中 `videos.status` 永久停留在 `processing`，前端硬编码显示 5% 进度，用户无法重新提交。今日发现用户 Poe 有 3 个任务卡死（DBNj41pCGao、O3b2Y5x_3FI、h7BAQMWQ8jM），需人工介入清理。
- **目标**: Scheduler 定期自动扫描超时任务，`processing > 3h` 或 `queued > 24h` 的任务自动标为 `failed`，用户可重新提交。

## 2. 计划 (Plan)
- 在 `backend/scheduler.py` 新增 `check_stuck_tasks()` 函数
- 查询 Supabase 中超时的 `processing`（>3h）和 `queued`（>24h）任务
- 批量更新为 `failed`，同步写入本地 `_status.json`
- 在 `run_scheduler()` 主循环开头每 30 分钟调用一次（启动时立即执行）

## 3. 回顾 (Review)
- 修改文件：`backend/scheduler.py`，新增 4 处改动
- 新增 `from datetime import datetime, timedelta`
- 新增常量：`STUCK_PROCESSING_HOURS=3`、`STUCK_QUEUED_HOURS=24`、`TIMEOUT_CHECK_INTERVAL=1800`
- 新增函数 `check_stuck_tasks()`：查询超时任务并批量更新为 `failed`
- `run_scheduler()` 主循环开头加入 30 分钟定时调用，启动时 `last_timeout_check=0` 保证立即执行
- 验证：插入 4 小时前的 `processing` 测试数据，触发检测后确认变为 `failed`，测试通过

## 4. 经验 (Lessons)
- **生产兜底**：Scheduler 宕机重启后第一个循环即执行清理，能覆盖宕机期间积累的僵死任务
- **用 created_at 替代 updated_at**：表中没有 updated_at，created_at 作为超时基准需要预留足够余量（3h 含排队等待时间）
- **原子性写入**：Supabase 更新和本地 `_status.json` 写入都在函数内完成，前端两条路径都能感知失败状态
