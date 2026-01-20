# 字幕重处理脚本

本目录包含用于重新处理已转录视频的LLM校正的脚本。

## 脚本说明

### 1. `reprocess_from_cache.py` （推荐）

从缓存的原始转录重新处理LLM校正，支持自动从数据库获取标题。

**适用场景**：
- 更新了LLM提示词后，需要重新校正已转录的视频
- 原始转录已存在于 `cache/` 目录

**用法**：
```bash
cd backend
source venv/bin/activate
python tests/reprocess_from_cache.py <video_id> [title]
```

**示例**：
```bash
python tests/reprocess_from_cache.py 0_zgry0AGqU "灵修与明白神的旨意"
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
