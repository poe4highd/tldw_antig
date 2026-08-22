# 2026-06-05 开发日志

### [Perf/OOM] faster-whisper 分块转录路径落地

- **需求**：5-22 日仅对 faster-whisper 加了 `vad_filter` 防御，CPU 模式下超长音频仍会全量加载导致 OOM；同时清理 `dev_docs/assets/` 中的临时 mockup 图片。

- **受影响文件**：
  - `backend/transcriber.py`
  - `dev_docs/assets/`（删除 4 张临时 mockup 图片）

- **回顾**：
  1. 新增 `_transcribe_faster_whisper_chunked(file_path, model, initial_prompt, chunk_minutes=20, overlap_seconds=30)`：用 ffprobe 探测总时长，≤ chunk_minutes 直接整文件；超过则复用已有 `_get_silence_cut_points` 在静音处切割，ffmpeg 逐段提取 + 30s overlap，合并时 `abs_start >= seg_end` 过滤重复，`gc.collect()` 主动释放内存
  2. `transcribe_local` 的 faster-whisper 回退路径从直接 `model.transcribe` 改为调用上述分块函数
  3. 删除 4 张 `dev_docs/assets/` 临时 mockup 图片（`admin_insight_*`、`enhanced_report_discussion_*`、`login_page_*`、`unified_dashboard_*`），不影响任何代码引用

- **经验**：
  - faster-whisper 分块策略与 mlx-whisper 完全对称，复用同一套 `_get_silence_cut_points` + overlap 合并逻辑，代码复杂度增量极小
  - `gc.collect()` 在每块转录后调用，对 CPU 长音频场景内存压力有明显缓解

---

# 2026-05-22 开发日志

### [Perf/OOM] 长音频分块流式转录 — 突破 Whisper 时长 OOM 限制

- **需求**：处理 70+ 分钟长音频时（如 `up_9f2ea319.m4a`），`transcribe_sensevoice_onnx` 因 `load_audio_for_sherpa` 全量加载 WAV 导致 OOM 崩溃；mlx-whisper 路径同样整文件喂入无分块。

- **受影响文件**：
  - `backend/sherpa_utils.py`
  - `backend/transcriber.py`

- **计划**：
  1. `sherpa_utils.py`：新增 `iter_audio_chunks` 流式生成器（每块 30s，~2MB/chunk）
  2. `transcriber.py`：重写 `transcribe_sensevoice_onnx` 为双层流式（外层 30s 块 + 内层 100ms VAD 块），加 `vad.flush()` 处理尾部
  3. `transcriber.py`：新增 `_get_silence_cut_points`（用 ffmpeg silencedetect 找静音切割点）和 `_transcribe_mlx_chunked`（超 20min 才分块，overlap+去重合并），替换 mlx 路径的直接 `transcribe` 调用
  4. `transcriber.py`：faster-whisper 加 `vad_filter=True` 作为防御性措施

- **回顾**：
  1. `sherpa_utils.py` 新增 `iter_audio_chunks` 生成器，保留旧函数 `load_audio_for_sherpa` 不破坏其他引用
  2. `transcribe_sensevoice_onnx` 全函数重写：`load_audio_for_sherpa` 改为 `iter_audio_chunks`，内嵌 `_drain_vad` 辅助函数，结尾 `vad.flush()` 处理尾部残留
  3. `_get_silence_cut_points`：用 ffmpeg `silencedetect=noise=-40dB:d=0.3` 解析静音结束点，在目标切割点前后 60s 内找最近静音点，无静音点时回退到按时间切割
  4. `_transcribe_mlx_chunked`：≤ chunk_minutes(20min) 直接整文件，否则在静音处切割 + 30s overlap；合并时 `abs_start >= seg_end` 过滤 overlap 重复，`abs_end` clamp 防越界
  5. faster-whisper `model.transcribe` 加 `vad_filter=True, vad_parameters={"min_silence_duration_ms": 500}`

- **经验**：
  - SenseVoice ONNX 的 OOM 根因是 `sherpa_utils.load_audio_for_sherpa` 一次性 `readframes(num_frames)` —— 2h 音频全量 float32 numpy 数组约 460MB，不是 VAD buffer 本身的问题
  - mlx-whisper 分块合并的准确性关键：(1) 在静音处切割而非硬切时间点，(2) overlap 区域合并时必须用 `abs_start >= seg_end` 而非 `abs_start > prev_end` 做去重
  - faster-whisper 的 `vad_filter` 是免费的防御，跳过静音段同时降内存压力
  - 测试文件：`downloads/up_9f2ea319.m4a`（70.8min 长），`downloads/r_2BLtms3Jw.mp3`（15.2min 短，不应触发分块）
