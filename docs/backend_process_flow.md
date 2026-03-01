# 后端处理流程与数据流转 (Backend Process Flow)

本文档说明 Read-Tube 后端从接收任务到生成最终报告的完整处理流程及产生的文件。

## 架构概览

系统采用**三层调度 + 独立 Worker 进程**架构：

```
┌─────────────────────────────────────────────────────────┐
│  频道追踪层 (main.py → channel_tracker.py)               │
│  每小时检查已订阅频道，发现新视频自动入队                    │
└────────────────────────┬────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────┐
│  任务队列层 (scheduler.py)                               │
│  优先级：手动提交 > 自动追踪，FIFO 顺序处理                │
└────────────────────────┬────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────┐
│  任务执行层 (process_task.py → worker.py)                │
│  主进程负责下载/元数据，Worker 独立进程负责转录/LLM          │
└─────────────────────────────────────────────────────────┘
```

## 核心处理流程

### 第一阶段：媒体与元数据获取 (process_task.py)

**输入**: YouTube URL 或用户上传文件

**动作**:
1. 从 Supabase 获取任务详情（URL、标题、用户信息）
2. **缓存检查**：在 `downloads/` 中查找 `{id}.m4a|mp3|mp4|webm`，已有则跳过下载
3. **文件存在性校验**：缓存或 `media_path` 指向的文件必须实际存在，否则重新下载
4. 调用 `yt-dlp` 获取元数据（标题、缩略图、频道信息、描述）
5. 若需下载：调用 `downloader.py` 的 `download_audio()` 获取音频

**下载策略** (`downloader.py`):
- 格式优先级：`bestaudio/best`（通常为 `.m4a`，也可能是 `.webm`/`.mp4`）
- 附带下载：缩略图 (`.jpg`)、字幕 (`.vtt`/`.srt`，中/英)
- 三次重试：完整下载 → 去字幕下载 → 去 cookies 下载

**音频提取**（仅视频格式 `.mp4/.webm/.mov/.avi/.mkv`）:
- 用 `ffmpeg` 提取音频为 `.mp3`，提取封面为 `.jpg`
- **自动清理**：提取成功后删除原始视频文件，仅保留音频

**产物**:
- `backend/downloads/{id}.m4a` 或 `.mp3` (音频源文件)
- `backend/downloads/{id}.jpg` (封面图)
- `backend/downloads/{id}.vtt` (字幕，如有)

### 第二阶段：转录 (worker.py → transcriber.py)

Worker 在**独立子进程**中运行，避免 MLX/Torch Metal GPU 冲突。

**转录源选择**（优先级从高到低）：
1. **转录缓存**：`cache/{id}_{mode}_{model}_raw.json`，命中则直接跳到 LLM 阶段
2. **字幕劫持**：`sub_utils.py` 查找已下载的 `.vtt`/`.srt` 字幕文件，解析为 segments
3. **Whisper 转录**：调用 `transcriber.py` 的 `transcribe_audio()`

**转录引擎**:
- **faster-whisper** (Linux/CUDA)：模型 `large-v3-turbo`，`float16` 精度
- **mlx-whisper** (Apple Silicon)：同等模型的 MLX 优化版本
- Cloud 模式实际被拦截强制走本地（Cloud Lock）

**产物**:
- `backend/cache/{id}_{mode}_{model}_raw.json`：原始 segments JSON 数组，含时间戳

### 第三阶段：LLM 深度加工 (worker.py → processor.py)

**3.1 段落重构** (`split_into_paragraphs`):
- 将碎片化 segments 合并为自然段落
- 支持超长文本分 chunk 处理
- **字数守恒**：字数误差 ≤5%，禁止大段改写
- **字义修复**：结合视频标题修复同音断层（如：罗布 → 萝卜）
- **语言探测**：根据标题自动选择简体/繁体/英文

**3.2 摘要与关键词提取** (`summarize_text`):
- 对带时间戳的全文调用 LLM 生成摘要
- 提取 5-9 个关键词

**产物**:
- `paragraphs`：结构化段落数组（含 `sentences[{text, start}]`）
- `summary`：全文摘要
- `keywords`：关键词列表

### 第四阶段：结果组装与存储 (process_task.py)

**本地存储**:
- `backend/results/{task_id}.json`：完整结果快照

**Supabase 同步**:
- `videos` 表：标题、缩略图、`media_path`（指向实际存在的音频文件）、`report_data`（paragraphs + raw_subtitles + summary + keywords + 频道信息）、`status=completed`
- `keywords` 表：关键词去重计数
- `submissions` 表：用户-视频关联

---

## 频道追踪系统

### 配置
- 管理员面板设置 `channel_settings.track_new_videos = TRUE`
- 检查间隔：每小时一次（`CHANNEL_CHECK_INTERVAL_HOURS = 1`）
- 配额限制：每小时最多 5 个、每天最多 50 个新视频

### 检查流程 (`scripts/channel_tracker.py`)
1. **重试失败任务**：`status=failed` 且 `retry_count < 3` 的视频重新入队
2. **检查新视频**：`yt-dlp --get-id --playlist-items 5` 获取频道最新视频
3. **去重**：检查视频是否已在 `videos` 表中
4. **入队**：获取元数据后插入 `videos` 表，`status=queued, source=tracker`

### 任务队列 (`scheduler.py`)
- 优先级：`source=manual`（用户提交）> `source=tracker`（自动追踪）
- 按 `created_at` 升序，FIFO 处理
- 单任务串行执行

---

## 文件生命周期

| 文件 | 创建时机 | 删除时机 |
|------|---------|---------|
| `downloads/{id}.m4a` | yt-dlp 下载 | 3 天过期清理 |
| `downloads/{id}.mp4/.webm` | yt-dlp 下载（视频格式） | 音频提取后**立即删除** |
| `downloads/{id}.mp3` | ffmpeg 音频提取 | 3 天过期清理 |
| `downloads/{id}.jpg` | yt-dlp/ffmpeg 提取 | 3 天过期清理 |
| `downloads/{id}.vtt` | yt-dlp 下载字幕 | 3 天过期清理 |
| `cache/{key}_raw.json` | 转录完成后 | 手动清理 |
| `results/{id}.json` | 任务完成 | 手动清理 |
| `results/{id}_status.json` | 任务全程 | 覆盖更新 |

---

## 关键代码位置

| 模块 | 文件 | 核心函数 |
|------|------|---------|
| API 入口 | `main.py` | `/process` 路由 |
| 频道追踪调度 | `main.py` | `run_channel_tracker()`, `scheduler_loop()` |
| 频道追踪执行 | `scripts/channel_tracker.py` | `main()`, `retry_failed_videos()` |
| 任务队列 | `scheduler.py` | `get_next_task()`, `run_scheduler()` |
| 任务处理主进程 | `process_task.py` | `process_video_task()` |
| Worker 进程 | `worker.py` | `main()` |
| 下载器 | `downloader.py` | `download_audio()` |
| 转录引擎 | `transcriber.py` | `transcribe_audio()`, `transcribe_local()` |
| LLM 处理 | `processor.py` | `split_into_paragraphs()`, `summarize_text()` |
| 字幕工具 | `sub_utils.py` | `find_downloaded_subtitles()`, `parse_vtt_srt()` |
| 质量检测 | `hallucination_detector.py` | `detect_hallucinations()` (未集成到主流程) |
| 过期清理 | `cleanup_downloads.py` | 3 天过期文件清理 |

## 辅助工具

| 脚本 | 作用 |
|------|------|
| `reprocess_from_cache.py` | 利用缓存重新生成报告（提示词/模型更新后使用） |
| `test_gap_detection.py` | 诊断转录密度与间隙问题 |
| `cleanup_downloads.py` | 清理 3 天以上的下载文件 |

## 待集成功能

以下模块已实现但尚未集成到主处理流程：

- **质量检测** (`hallucination_detector.py`)：幻觉检测、间隙检测、语速密度分析
- **双模型修复**：用 Whisper Base 修复幻觉、Whisper Small 补漏间隙
- 可通过 `reprocess_from_cache.py --detect-hallucination` 手动触发
