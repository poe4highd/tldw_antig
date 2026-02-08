# Channel Tracker 使用指南

频道追踪脚本，自动检查已关注频道的最新视频并加入处理队列。

## 运行方式

```bash
cd backend
PYTHONPATH=. python3 scripts/channel_tracker.py
```

## 功能说明

1. 从数据库获取所有已处理视频的 `channel_id`
2. 检查每个频道的最新视频
3. 如果是新视频，获取元数据（标题、缩略图等）后加入队列
4. 创建 `results/{video_id}_status.json` 供 UI 显示

## 日志位置

运行日志保存在 `backend/tracker.log`

## 注意事项

- 会员专属视频会被跳过（无法获取）
- 每次运行约需 1-2 分钟（取决于频道数量）
- 建议每小时运行一次以获取最新视频
