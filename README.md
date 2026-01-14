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

## AI 处理逻辑
系统不仅进行语音转录，还会将结果提交给 OpenAI LLM (GPT-4o-mini) 进行二次加工。

### LLM Prompt 核心指令
为了提供极致的阅读体验，AI 遵循以下指令：
- **精准修正**：在不改变字数的前提下，根据上下文纠正多音字或同音字。
- **标点与分段**：为文本添加精准的标点符号（如，。？！“”），并根据逻辑进行自然分段。
- **简繁自适应**：自动识别标题语言。如果标题是繁体字，则转录结果也自动转换为繁体中文。
- **禁止删减**：绝对禁止删除任何词汇（包括口语词），确保转录的完整性。

## 文件存储结构
所有处理过程中产生的文件均保存在 `backend/` 目录下：
- `downloads/`: 存储下载的原始音频文件 (`.m4a`, `.mp3`等)。
- `cache/`: 存储 Whisper 输出的原始转录 JSON 数据，用于加速重复访问。
- `results/`: 存储最终生成的结构化报告 (`.json`)，包含分段文本、元数据及成本统计。

## 注意事项
- **大文件限制**: OpenAI API 限制单文件 25MB。超过此限制的视频请选择 **Local** 模式。
- **首次运行**: 本地模式首次运行时，系统会自动下载 Whisper 模型（约 1-3GB），请留意终端下载状态。
