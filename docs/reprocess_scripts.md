# 字幕重处理脚本

本目录包含用于重新处理已转录视频的LLM校正的脚本。

## 脚本说明

### 1. `reprocess_from_cache.py` （推荐）

从缓存的原始转录重新处理LLM校正，支持自动从数据库获取标题，并可选启用**双模型幻觉校验**。

**适用场景**：
- 更新了LLM提示词后，需要重新校正已转录的视频
- 发现原始转录中存在严重的“单字循环”或“乱码”幻觉（Hallucination）
- 原始转录已存在于 `cache/` 目录且本地 `downloads/` 包含对应的音频文件

**用法**：
```bash
cd backend
source venv/bin/activate
python tests/reprocess_from_cache.py <video_id> [title] [--detect-hallucination]
```

**幻觉处理逻辑**：
1. **自动检测**：正则扫描重复乱码模式。
2. **二次转录**：使用 `whisper base` 模型对幻觉区域及其前后上下文进行针对性重转录。
3. **备选比对**：将主模型（如 large-v3-turbo）和备选模型（base）的结果同时提供给 LLM 进行决策。
4. **智能修复**：LLM 根据语义逻辑选择更通顺的版本，修复“罗布”->“萝卜”等字义断层。

**示例**：
```bash
python tests/reprocess_from_cache.py 0_zgry0AGqU "灵修与明白神的旨意" --detect-hallucination
```

**输出**：
- 更新数据库中的 `paragraphs` 字段
- 保存备份到 `results/<video_id>_reprocessed.json`

---

### 2. `reprocess_result.py`

从本地结果JSON文件重新处理，需要文件中包含 `raw_subtitles` 字段。

**适用场景**：
- 处理本地保存的完整结果文件
- 文件已包含原始字幕数据

**用法**：
```bash
cd backend
source venv/bin/activate
python tests/reprocess_result.py <path_to_json>
```

**示例**：
```bash
python tests/reprocess_result.py results/abc123.json
```

---

### 3. `batch_reprocess.py`

批量重处理最近N个视频。

**用法**：
```bash
python tests/batch_reprocess.py [count]  # 默认 count=1
```

## 文件结构

- `cache/` - 存储原始转录的缓存文件（`{video_id}_*_raw.json`）
- `results/` - 存储处理后的结果文件
