# Read-Tube
YouTube / Audio / Video Quick Reader


## 系统要求
- Python 3.9+
- Node.js 18+
- **ffmpeg** (必须安装，用于媒体处理)
- NVIDIA GPU (可选，用于本地模式加速)

## 📖 指南与规划
- 👉 **[功能细节与指导文档](docs/features_guide.md)**：了解系统当前的核心能力与使用技巧。
- 👉 **[混合云部署指南 (Vercel + 穿透)](docs/hybrid_deployment_guide.md)**：分步指导如何零成本将服务公开。
- 👉 **[数据存储与外接硬盘配置](docs/storage_management.md)**：磁盘空间不足时的迁移与管理方案。
- 👉 **[产品公测与路线图 (Roadmap)](docs/product_roadmap.md)**：了解未来的开发规划与商业化路径。
- 👉 **[AI 协作偏好与规范](docs/ai_agent_dev_preferences_cn.md)**：记录项目开发中的 AI 协作习惯与规范。

---

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

## 数据清理与全量重处理
如果您更新了 LLM Prompt 或者想要清理冗余的历史文件，可以使用我们提供的维护脚本：

```bash
cd backend
source venv/bin/activate
python maintenance.py
```

### 脚本功能：
1.  **去重与清理**：自动删除过期的 `_status.json`、`_error.json` 以及重复的历史报告（基于媒体 ID 去重，保留最新版）。
2.  **全量重处理**：自动读取 `cache/` 中的原始转录文本，并使用最新的 Prompt 重新调用 OpenAI API 进行校正和分段。
3.  **媒体清理**：自动删除 `downloads/` 目录中不再被任何报告引用的媒体文件（仅清理 1 小时前的文件，防止误删正在进行的任务）。

## 注意事项
- **大文件限制**: OpenAI API 限制单文件 25MB。超过此限制的视频请选择 **Local** 模式。
- **首次运行**: 本地模式首次运行时，系统会自动下载 Whisper 模型（约 1-3GB），请留意终端下载状态。

## 开发者工具 (Dev Tools)

### 单文件重处理脚本
位于 `backend/tests/reprocess_result.py`，用于针对单个结果文件重新运行 LLM 处理（例如调试 Prompt 效果时）。

**注意：该脚本会直接覆盖原 JSON 文件。**

```bash
cd backend
source venv/bin/activate
python tests/reprocess_result.py results/<filename>.json
```
