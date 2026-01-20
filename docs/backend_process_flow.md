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

### 第二阶段：预处理与转录 (Pre-processing & Transcription)
- **引擎**: OpenAI Whisper (Local MLX-Whisper 或 Faster-Whisper)
- **动作**: 将音频转换为带有时间戳的初始文字序列片段。
- **产物 (中间态)**: 
  - **路径**: `backend/cache/{id}_{mode}_raw.json`
  - **内容**: 原始的、未加标点、未分段的 JSON 数组。

### 第三阶段：质量检测与双模型修复 (Quality Detection & Retranscription)
这是系统提升鲁棒性的关键环节，负责处理转录幻觉与遗漏。主要逻辑位于 `backend/hallucination_detector.py`。

1.  **缺陷扫描**:
    - **幻觉检测**: 识别重复乱码（如 `用？！用？！`）或多余标点。
    - **间隙检测 (Gap Detection)**: 识别 3 秒以上的空白期。
    - **语速密度分析**: 通过文本/时长比例识别可能的“漏词”段落。
2.  **针对性重转录**:
    - **幻觉修复**: 使用 `Whisper Base` 模型重新扫描，快速拆穿乱码。
    - **间隙补漏 (Gap Filling)**: 使用精度更高的 `Whisper Small` 模型深挖被大模型忽略的内容。
3.  **产物**: 标记了 `[HALLUCINATION]` 和 `[ALT:]` 备选建议的增强转录文本。

### 第四阶段：LLM 深度加工与语言处理 (LLM Processing)
负责逻辑校正、字数守恒处理及段落重构。代码位于 `backend/processor.py`。

#### 4.1 核心提示词规则 (Prompt Rules)
- **字数守恒 (CRITICAL)**: 转录已十分精准，禁止大段改写，字数误差必须在 5% 以内。
- **幻觉智能裁决**: 比较主模型与备选模型结果，剔除乱码，保留补漏内容。
- **字义分析修复**: 结合视频标题（Context）修复同音断层（如：罗布 -> 萝卜）。

#### 4.2 语言自动探测
系统根据视频标题自动判定：`Simplified` (默认) / `Traditional` / `English`。

### 第五阶段：结果组装与存储 (Result Persistence)
- **文件**: `backend/results/{task_id}.json` (本地最终快照)
- **数据库**: 同步写入 Supabase `videos` 表，重点更新 `report_data` 中的 `paragraphs` 字段。

---

## 2. 关键工具速查

| 脚本 | 作用 |
| :--- | :--- |
| `reprocess_from_cache.py` | 当提示词或模型更新时，通过 Cache + 音频补刷重新生成报告 |
| `test_gap_detection.py` | 诊断工具，分析特定视频的转录密度与间隙 |
| `maintenance.py` | 维护工具，清理过期媒体文件 |

## 3. 常见问题处理
如果发现视频有“卡顿”或“文字缺失”：
- 请尝试运行 `python tests/reprocess_from_cache.py {video_id} --detect-hallucination`。
- 这会触发 `Whisper Small` 对间隙进行二次增强扫描。
