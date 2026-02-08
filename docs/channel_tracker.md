# Channel Tracker 使用指南

频道追踪脚本，自动检查已关注频道的最新视频并加入处理队列。

## 自动调度（推荐）

启动 `main.py` 后会自动在后台运行：
- **检查频率**：每小时检查一次
- **处理限制**：每小时最多 5 个视频，每天最多 50 个
- **首次延迟**：服务启动后 5 分钟开始

无需额外配置。

## 手动运行

```bash
cd backend
PYTHONPATH=. python3 scripts/channel_tracker.py
```

## 日志

- 运行日志：`backend/tracker.log`
- 调度器日志：查看 `main.py` 输出中的 `[Scheduler]` 前缀

## 注意

- 会员专属视频会被跳过
- 每次检查约需 1-2 分钟
