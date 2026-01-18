# 后端处理流程与数据流转 (Backend Process Flow)

本文档详细说明 Read-Tube 后端从接收任务到生成最终报告的完整处理流程及产生的文件及其位置。主要逻辑位于 `backend/main.py` 的 `background_process` 函数中。

## 1. 核心流程概览

### 第一阶段：媒体与元数据获取 (Media Retrieval)
- **输入**: YouTube URL 或 用户上传文件
- **动作**: 
  - 若为 URL：调用 `yt-dlp` 下载最佳音频流。
  - 若为文件：计算文件 Hash 并保存。
- **产物**:
  - `backend/downloads/{id}.mp3` (音频源文件)
  - `backend/downloads/{id}.jpg` (封面图)

### 第二阶段：音频提取与预处理 (Audio Extraction)
- **动作**: 确保输入源为纯音频格式（MP3）。如果上传的是视频文件，使用 `ffmpeg` 提取音频轨道。
- **目的**: 减小文件体积，适配 Whisper 接口要求。
- **产物**: 
  - 生成 `.mp3` 文件（如果原文件不是）。
  - 清理原始上传的视频大文件（可选）。

### 第三阶段：语音转录 (Transcription)
- **引擎**: OpenAI Whisper (Local Mode) 或 OpenAI API (Cloud Mode)
- **动作**: 将音频转换为带有时间戳的文字序列。
- **产物 (中间态)**: 
  - **路径**: `backend/cache/{id}_{mode}_raw.json`
  - **内容**: 原始的、未加标点、未分段的 JSON 数组。
  - **作用**:作为缓存层，避免重复消耗 GPU/API 资源。

### 第四阶段：LLM 深度加工与语言处理 (LLM Processing)
本阶段是核心智能处理环节，负责语言识别、标点添加及段落重组。代码位于 `backend/processor.py`。

#### 4.1 语言自动探测 (Language Detection)
系统会根据**视频标题**和**前 10 个转录片段**自动判断目标语言偏好。逻辑位于 `detect_language_preference` 函数：

1.  **英文判定**: 
    - 标题中包含连续 5 个以上英文字母，且不包含任何中文字符。
    - **结果**: `english`

2.  **繁体中文判定**:
    - 标题或前文样本中包含特定的繁体特征字（如：`這國個來們裏時後得會愛兒幾開萬鳥運龍門義專學聽實體禮觀`）。
    - **结果**: `traditional`

3.  **默认判定**:
    - 其他情况默认为简体中文。
    - **结果**: `simplified`

#### 4.2 动态提示词构建 (Dynamic Prompting)
系统会根据探测结果动态拼接 System Prompt。

**基础 Prompt (定义角色与任务)**:
```text
你是一位极致专业的视频文本编辑。我会给你一段带有时间戳的原始语音转录。
你的任务是：
1. 【忠实原文（MUST）】：绝对禁止删除任何有意义的词汇...
2. 【标点符号（CRITICAL）】：必须为所有文本添加正确的标点符号...
3. 【合并与分段】：将碎片化的文本合并为通顺的句子...
```

**语言指令注入**:
- **English**: `【目标语言】：英文。请使用英文校正，并添加半角标点。严禁翻译为中文。`
- **Traditional**: `【目标语言】：繁体中文。请使用繁体输出，并添加全角标点。`
- **Simplified**: `【目标语言】：简体中文。请使用简体输出，并添加全角标点。`

#### 4.3 产物
- **内存对象**: 结构化段落数据 (`paragraphs`)，直接用于 API 响应。

### 第五阶段：结果组装与存储 (Result Persistence)
- **动作**: 将元数据、成本统计、原始字幕 (`raw_subtitles`) 和 润色后的段落 (`paragraphs`) 组装。
- **产物 (最终态)**:
  - **文件**: `backend/results/{task_id}.json`
  - **数据库**: 同步写入 Supabase `videos` 表。
- **状态文件**: `backend/results/{task_id}_status.json` (记录进度百分比，任务完成后可能被清理)。

---

## 2. 关键文件位置速查

| 文件类型 | 目录 | 文件名示例 | 说明 |
| :--- | :--- | :--- | :--- |
| **原始音频** | `backend/downloads/` | `UBE4vkQrSb8.mp3` | 原始媒体素材 |
| **原始转录** | `backend/cache/` | `UBE4vkQrSb8_local_raw.json` | Whisper 直出，无标点，用于调试或重跑 |
| **最终报告** | `backend/results/` | `1737233856.json` | 包含最终段落、元数据，前端读取此文件 |
| **语言逻辑** | `backend/processor.py` | `detect_language_preference` | 包含正则判断与 Prompt 拼接逻辑 |

## 3. 维护与清理
使用 `backend/maintenance.py` 脚本可以：
- 清理过期的 MP3 文件（保留最近1小时）。
- 基于 Cache 重新运行 LLM 流程（当 Prompt 更新时）。
