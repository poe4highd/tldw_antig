# 事故复盘：音频处理链路多点故障（2026-04-19）

涉及任务：`up_9f2ea319`（2769句）、`up_820a8fef`（708句）

---

## 问题一：后半段字幕缺标点

**现象**：生产页面后半段字幕无任何标点符号，前半段正常。

**根因**：`_validate_chunk_quality()` 只有4项质检，没有检查标点密度。后半段 chunks 被 Ollama 返回了无标点的结果，质检未拦截直接入库。

**修复**（`processor.py`）：新增第5项质检 `punct_density`，v2 模式下每句平均标点数 < 0.5 时触发重试。

```python
if prompt_mode == "v2":
    sentences = [s for p in chunk_paras for s in p.get("sentences", [])]
    punct_count = sum(1 for s in sentences for c in s.get("text","") if c in "，。？！,.")
    if len(sentences) > 0 and punct_count / len(sentences) < 0.5:
        return False, f"punct_density:{punct_count/len(sentences):.2f}"
```

---

## 问题二：生产页面刷新仍显示旧数据

**现象**：重新处理后生产页面中文翻译仍然是旧的无标点版本。

**根因**：Supabase `report_data.translations` 字段缓存了旧的翻译结果，`rerun_llm.py` 更新时用 `{**existing_report, ...}` 展开，保留了旧 `translations`。

**修复**（`rerun_llm.py`）：Supabase 更新时显式清空翻译缓存：

```python
report_data = {
    **existing_report,
    "paragraphs": paragraphs,
    "summary": result["summary"],
    "keywords": result["keywords"],
    "translations": {},  # 清除旧翻译缓存
}
```

---

## 问题三：语言检测误判中文视频为英文

**现象**：`detected_language=en`，生成了英文摘要。

**根因链**：
1. 视频标题是文件名（`audio1915849011.m4a`），无 CJK 字符
2. `detect_language_preference(title, description)` 没有传字幕样本，兜底返回 `"english"`
3. `rerun_llm.py` 行72没有传 `subtitle_sample` 参数（`worker.py` 已修复，`rerun_llm.py` 遗漏）

**修复**（`rerun_llm.py`）：

```python
subtitle_sample = " ".join(s.get("text", "") for s in raw_subtitles[:30])
title_lang = detect_language_preference(title, description, subtitle_sample)
```

---

## 问题四：段落矫正走 Ollama 而非 Gemini

**现象**：本机 GPU 风扇狂转，`split_into_paragraphs` 一直走 Ollama，即使 `llm_config.yaml` 首位是 Gemini。

**根因**：`split_into_paragraphs` 内部直接硬写 `pool = ServerPool()`，完全绕过了 `get_llm_client()` 返回的 Gemini client。`client` 变量拿到了 Gemini，但后续代码从未使用它，只有 Ollama 全挂时才会作为极端兜底。

**修复**（`processor.py`）：当 primary provider 不是 `ollama` 时，跳过 ServerPool，直接用 primary client 串行处理：

```python
if provider != "ollama":
    all_paragraphs, total_usage = _process_chunks_sequential(
        chunks, chunk_contexts, client, provider, chunk_params)
else:
    pool = ServerPool()
    # ... 原有并行/串行逻辑
```

---

## 问题五：繁简误判（简体视频被判为繁体）

**现象**：`title_lang=traditional → detected_language=zh-TW`，生成繁体中文摘要。

**根因**：`detect_language_preference` 的繁简判断正则 `trad_patterns` 同时匹配了 `content + sample_text`。Whisper 转录普通话时偶尔输出繁体字形（如「這」「國」），导致字幕 sample 触发繁体判断。

**修复**（`processor.py`）：繁简判断只看 `title+description`，排除 Whisper 字幕 sample：

```python
# 只用 title+description 判断繁简，字幕内容 Whisper 可能混入繁体字形
return "traditional" if re.search(trad_patterns, content) else "simplified"
```

---

## 问题六：摘要时间戳堆在末尾，前端显示全为 00:00

**现象**：摘要7行内容显示正常，但点击全部跳到 00:00。

**根因**：Gemini 有时返回如下格式——7行文字 + 7个时间戳单独成行：

```
1. 文字内容A
2. 文字内容B
...
[00:29]
[01:46]
...
```

`_postprocess()` 的逻辑是找「含时间戳的行」，文字行和时间戳行分离时无法配对，所有行的时间戳都缺失，前端默认显示 00:00。

**修复**（`processor.py`）：检测纯时间戳行数 == 纯文字行数时，按顺序配对：

```python
ts_only = [l for l in lines if re.match(r'^\[\d{2}:\d{2}(?::\d{2})?\]$', l.strip())]
text_only = [l for l in lines if not re.match(r'^\[\d{2}:\d{2}(?::\d{2})?\]$', l.strip())]
if ts_only and len(ts_only) == len(text_only):
    lines = [f"{t.strip()}{ts}" for t, ts in zip(text_only, ts_only)]
```

---

## 问题七：摘要质检只记录日志，不触发重试

**现象**：摘要生成后质量差（无 CJK、行数不足、无时间戳），但直接入库没有自动修复。

**修复**（`rerun_llm.py`）：新增 `_check_summary_quality()` + 最多3次重试闭环：

```python
def _check_summary_quality(summary, detected_language):
    lines = [l for l in summary.split('\n') if l.strip()]
    has_cjk = bool(re.search(r'[\u4e00-\u9fa5\uac00-\ud7a3]', summary))
    has_timestamps = any(re.search(r'\[\d{2}:\d{2}', l) for l in lines)
    if detected_language in ("zh", "zh-TW", "ko", "ja") and not has_cjk:
        return False, f"lang_mismatch: detected={detected_language} but no CJK"
    if len(lines) < 5:
        return False, f"too_few_lines: {len(lines)}"
    if not has_timestamps:
        return False, "no_timestamps"
    return True, "ok"
```

---

## 附：调试过程中发现的其他问题

| 问题 | 说明 |
|------|------|
| Gemini API 偶发 404 | `models/gemini-2.5-flash` 短暂不可用，自动 fallback 到 Ollama，风扇狂转 |
| `LLM_NO_FALLBACK=1` | 本机 `.env` 加入此变量，Gemini 失败时直接报错，不静默降级到 Ollama，便于调试 |
| `rerun_llm.py` 无 logger | print() 输出不进 `app.log`，调试时需直接看进程 stdout |
| Ollama 176 无 qwen3:8b | 176 服务器没有该模型，并行处理时发给176的 chunk 全部失败 |

---

## 涉及文件

- `backend/processor.py` — 标点质检、Gemini 主力路径、繁简判断、摘要后处理
- `backend/rerun_llm.py` — 语言检测传参、摘要质检重试、翻译缓存清除
- `backend/.env` — `LLM_NO_FALLBACK=1`（本机调试用，不提交）
