# 2026-03-03 开发日志

### [回顾] 修复上传视频文件无法播放的BUG
- **需求**：用户上传本地 MP4 视频后，结果页面音频无法播放（404）
- **根因**：`main.py:201-204` 提取音频后删除原始视频文件，但 `file_path` 变量未更新，导致 `media_path`（L262）仍指向已删除的 `.mp4` 文件
- **修复**：
  1. `backend/main.py:205`：删除原视频后 `file_path = extracted_audio_path`，确保 `media_path` 指向已提取的 `.mp3`
  2. `frontend/app/result/[id]/page.tsx:383`：audio src 添加 fallback，将 `.mp4/.mov/.avi/.webm/.mkv` 扩展名替换为 `.mp3`，兼容已入库的损坏数据
- **经验**：变量生命周期陷阱——`file_path` 在中间被 `os.remove()` 对应的文件删除后，下游代码仍依赖该变量构建路径。删除文件后必须同步更新引用变量。
