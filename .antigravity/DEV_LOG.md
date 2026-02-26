# 2026-02-26 开发日志

## [08:35] | 调研 | 重新处理最近 5 个错误任务
### 需求背景
`results` 目录下存在 15 个 `_error.json` 错误文件。需要挑选最近的 5 个进行重新处理，排查是否依然报错。

### 当前现状
- 错误任务总数：正在确认 (预期 15)
- 最近 5 个任务：
  1. `results/P78fylSwdpw_error.json` (2026-02-26 08:27)
  2. `results/G-7HWsOROfs_error.json` (2026-02-25 12:09)
  3. `results/NIbPEW0alBg_error.json` (2026-02-25 12:09)
  4. `results/uwVgVVHyXqo_error.json` (2026-02-25 11:41)
  5. `results/pqPw7xCZVaw_error.json` (2026-02-25 11:40)

### 待办事项
- [x] 确定重新处理的执行命令
- [x] 输出实施计划并获批
- [x] 修正 Worker 调用架构 (确保使用 sys.executable)
- [x] 执行并验证重新处理 (已完成)


# 开发日志 (2026-02-26) - 任务：修复 Worker 错误 traceback 被覆盖

## 1. 需求 (Requirement)
- **背景**: `results/_error.json` 中所有错误信息都只有 `"Worker 进程失败 (exit code: 1)"`，看不到真实堆栈，无法定位失败原因。
- **根本原因**: `process_task.py` 外层 `except` 块（L339）无条件 `json.dump` 覆盖了 `worker.py` 已写好的 `{"error", "traceback"}`。
- **目标**: 保留 worker 写的 traceback；若 worker 崩溃前未写错误文件，用父进程捕获的 stderr 兜底。

## 2. 计划 (Plan)
- `process_task.py` L236：subprocess exit != 0 时，若 `_error.json` 不存在则用 stderr 写入兜底
- `process_task.py` L339：外层 except 先检查 `_error.json` 是否有 `traceback` 字段，有则跳过写入

## 3. 回顾 (Review)
- 修改文件：`backend/process_task.py`，共 2 处改动
- L236 新增：`if not os.path.exists(error_file)` 保护，用 stderr 兜底写 `{"error", "traceback"}`
- L339 修改：外层 except 先读取现有文件检查 traceback，`existing_has_traceback` 为 False 才覆盖

## 4. 经验 (Lessons)
- **子进程错误文件不能无条件覆盖**：父进程捕获的异常信息通常比子进程写的堆栈信息粗糙
- **两级兜底设计**：子进程自写（最详细） → 父进程 stderr 兜底（OOM/segfault 场景） → 父进程 except 兜底（极端情况）

---

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
