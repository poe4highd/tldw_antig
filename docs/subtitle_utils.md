# 字幕辅助工具集 (Subtitle Utilities)

该工具集包含用于下载 YouTube 字幕及评估 AI 转录准确率的脚本。

---

## 1. 字幕下载工具 (`download_subs.py`)

用于快速下载 YouTube 视频的真实字幕，作为基准数据。

### 放置路径
- 脚本：`backend/scripts/download_subs.py`
- 默认数据目录：`backend/tests/data/`

### 使用方法
```bash
# 使用视频 ID 下载（保存至默认目录）
python3 backend/scripts/download_subs.py dQw4w9WgXcQ

# 指定输出目录
python3 backend/scripts/download_subs.py dQw4w9WgXcQ --outdir ./mylab
```

### 核心功能
- **跳过视频下载**：仅获取字幕元数据，极致节省带宽。
- **自动备选语言**：智能尝试 `zh-Hans`, `zh`, `en` 等标引。
- **支持自动生成**：若无人工字幕，则抓取 YouTube AI 自动生成的字幕（标注为 `auto`）。

---

## 2. 字幕对比评估工具 (`compare_subs.py`)

用于量化 AI 转录结果与基准字幕之间的差异，输出 CER 字错率及错误分析。

### 放置路径
- 脚本：`backend/scripts/compare_subs.py`
- 验证报告目录：`backend/validation/` (自动创建)

### 使用方法
```bash
# 对比 AI 处理后的 JSON (LLM 修正后)
python3 backend/scripts/compare_subs.py \
  --gt backend/tests/data/QVBpiuph3rM.zh-CN.srv1 \
  --pred backend/results/1768792953.json

# 对比 Whisper 原始转录 (raw 缓存)
python3 backend/scripts/compare_subs.py \
  --gt backend/tests/data/QVBpiuph3rM.zh-CN.srv1 \
  --pred backend/cache/QVBpiuph3rM_local_raw.json
```

### 核心逻辑
- **数字归一化**：自动对齐 `2 ↔ 二` 等数字差异。
- **简繁及代词对齐**：
  - 集成 `zhconv` 实现全量简繁转换，消除繁简误报。
  - **代词归一化**：将 `祂/它` 统一映射为 `他`，使指标更关注核心语音识别。
- **报告自动持久化**：每次运行结果均会保存至 `backend/validation/`。

### 推荐工作流与输出规范
- **默认报告路径**：建议统一存储在 `backend/validation/`。脚本在未指定 `--outdir` 时会以此为默认值。
- **命名约定**：文件名格式为 `{VideoID}_{类型}_{时间戳}.txt`。
  - `raw`: 指 Whisper 原始转录阶段的评估结果。
  - `llm`: 指经过 LLM 生成/修正后的最终 JSON 结果。
  - 示例：`QVBpiuph3rM_raw_20260119_074122.txt`。

### 核心指标解读
- **CER (Character Error Rate)**：字符错误率。计算方法为 `(替换+遗漏+插入) / 基准总字数`。
- **准确率**：即 `1 - CER`。
- **Top N 错字替换**：直观展示 AI 最容易在哪些词汇上“翻车”（如同音字）。

---

## 开发者说明
该工具集主要用于“数据驱动”的 AI 优化流。在调整 Prompt 或模型后，应运行评估脚本观察 CER 是否下降，以验证改进的真实有效性。
