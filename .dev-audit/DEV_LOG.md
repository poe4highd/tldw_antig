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
