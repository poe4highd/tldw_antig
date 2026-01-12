# YouTube 转录与播放工具

这是一个全栈应用，支持从 YouTube 下载视频并将其转录为文本，支持云端 (OpenAI) 和本地 (Whisper) 两种模式。

## 系统要求
- Python 3.9+
- Node.js 18+
- **ffmpeg** (必须安装，用于音频提取)
- NVIDIA GPU (可选，用于本地模式加速)

## 快速开始

### 1. 启动后端
```bash
cd backend
source venv/bin/activate
# 在 .env 中填入 OpenAI API Key (如果使用云端模式)
uvicorn main:app --reload
```

### 2. 启动前端
```bash
cd frontend
npm install
npm run dev
```
访问 [http://localhost:3000](http://localhost:3000) 即可使用。

## 功能点
- [x] **URL 下载**: 自动使用 `yt-dlp` 提取音频。
- [x] **双模式转录**: 灵活切换 OpenAI API 或本地 `faster-whisper`。
- [x] **同步播放**: 点击字幕，视频自动跳转到对应时间点。
- [x] **实时高亮**: 视频播放时，当前朗读的字幕行会自动高亮。
