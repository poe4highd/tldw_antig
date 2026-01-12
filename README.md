# YouTube 转录与交互播放工具

这是一个全栈应用，支持从 YouTube 下载视频并将其转录为文本，支持云端 (OpenAI) 和本地 (Whisper) 两种模式。

## 系统要求
- Python 3.9+
- Node.js 18+
- **ffmpeg** (必须安装，用于媒体处理)
- NVIDIA GPU (可选，用于本地模式加速)

## 快速开始

### 1. 配置环境
在 `backend/.env` 中填入您的 API Key（如果使用云端模式）：
```bash
OPENAI_API_KEY=sk-xxxx
```

### 2. 启动后端 (API)
为了支持局域网访问（如 192.168.x.x），**必须**指定 host 为 `0.0.0.0`：
```bash
cd backend
source venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. 启动前端 (UI)
```bash
cd frontend
npm install
npm run dev
```
访问 `http://localhost:3000` 或您的局域网 IP 即可。

## 核心功能
- [x] **双模式转录**: 灵活切换 OpenAI API 或本地 `faster-whisper`。
- [x] **局域网适配**: 前后端自动识别 IP，支持多设备远程访问。
- [x] **任务持久化**: 进度信息存入磁盘，服务器重启后任务不丢失。
- [x] **智能缓存**: 同一视频不重复下载，节省流量与时间。
- [x] **自动清理**: 音频文件保存 48 小时后自动删除，节省磁盘空间。
- [x] **交互式播放**: 字幕随视频高亮，点击字幕可精确跳转进度。
- [x] **实时进度条**: 20% 下载, 60% 转录, 90% 处理完成。

## 注意事项
- **大文件限制**: OpenAI API 限制单文件 25MB。超过此限制的视频请选择 **Local** 模式。
- **首次运行**: 本地模式首次运行时，系统会自动下载 Whisper 模型（约 1-3GB），请留意终端下载状态。
