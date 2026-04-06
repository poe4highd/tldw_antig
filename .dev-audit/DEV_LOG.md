# 2026-04-06 开发日志

### [Eval] Gemma 4 e4b 字幕矫正评测 — 对比 e2b / qwen3:8b / gpt-4o-mini

- **需求**：上次 gemma4:e2b 评测 CER 37%，主因是 2B 激活参数对中文指令跟随能力不足、JSON 输出不稳定。下载 gemma4:e4b（4B 激活，9.6GB）测试更大版本能否改善。

- **计划**：
  1. 确认 gemma4:e4b 已拉取到 Ollama（192.168.1.182）
  2. 修改 `evaluate_accuracy.py`：已有结果复用缓存，只新跑 e4b
  3. 用 venv Python 跑 compare_subs.py 计算 CER（此前全局 Python 缺 zhconv）

- **实际改动**：
  1. `backend/scripts/evaluate_accuracy.py`：`main()` 改为对已有 JSON 结果复用缓存跳过重跑，只执行 gemma4:e4b 新推理，统一评估所有模型 CER；新增 gemma4:e4b 评测轮次

- **评测结果**（测试集：QVBpiuph3rM，基准字数 7496）：

  | 模型 | CER | 准确率 | 输出字数 |
  |------|-----|--------|----------|
  | gpt-4o-mini | **12.26%** | **87.74%** | 8015 |
  | gemma4:e4b | **13.43%** | **86.57%** | 7859 |
  | qwen3:8b | 28.52% | 71.48% | 6447 |
  | gemma4:e2b | 37.05% | 62.95% | 5675 |

- **问题发现**：
  - e4b 在 chunk 5 仍出现 JSON 错误（模型用了 `text_content` 而非 `text`，且 JSON 提前截断），但 15 个 chunk 中仅 1 个失败，影响有限
  - 输出字数 7859 接近基准，丢字问题在 e4b 上基本消失

- **经验**：
  - gemma4:e4b（4B 激活参数）CER 13.43%，与 gpt-4o-mini（12.26%）差距仅 1.17 个百分点，可作为本地主力离线方案
  - e4b 体量（9.6GB）超出 RTX 4060（8GB VRAM），实际能跑说明 Ollama 在该机器上有足够系统内存做卸载
  - 模型激活参数从 2B→4B 对中文指令跟随有显著提升，后续若要再优化可考虑 gemma4:e12b 等更大版本
  - 运行评测脚本需明确使用 `backend/venv` 环境，全局 Python 缺 zhconv

# 2026-04-04 开发日志

### [Eval] Gemma 4 本地字幕矫正评测 — gemma4:e2b vs qwen3:8b vs gpt-4o-mini

- **需求**：Google 新发布 Gemma 4，探索 RTX 4060（8GB VRAM）能流畅运行的最大版本，集成到本地 Ollama，测试其在字幕矫正步骤（`split_into_paragraphs`）中的表现是否可替代现有 qwen3:8b。

- **计划**：
  1. 确认 4060 适配版本（gemma4:e2b，7.2GB）
  2. 升级 Ollama 至 ≥0.20.0（原版本 0.15.5 不支持 Gemma 4）
  3. 在测试视频 QVBpiuph3rM 上生成 Whisper 转录缓存
  4. 修改 `evaluate_accuracy.py` 增加 Gemma 4 对比轮次
  5. 跑三模型 CER 对比（gemma4:e2b / qwen3:8b / gpt-4o-mini）

- **实际改动**：
  1. `backend/scripts/evaluate_accuracy.py`：输出文件名改为含模型名（`eval_{model_name}_{video_id}.json`，避免覆盖）；`main()` 新增 `gemma4:e2b` 评测轮次
  2. `backend/requirements.txt`：补充遗漏依赖 `zhconv`（`compare_subs.py` 需要，之前只在系统 Python 存在）
  3. Ollama 服务器（192.168.1.182）升级：0.15.5 → 0.20.2，拉取 `gemma4:e2b`（7.2GB）

- **评测结果**（测试集：QVBpiuph3rM，基准字数 7496）：

  | 模型 | CER | 准确率 | 输出字数 |
  |------|-----|--------|----------|
  | gpt-4o-mini | **12.26%** | **87.74%** | 8015 |
  | qwen3:8b | 28.52% | 71.48% | 6447 |
  | gemma4:e2b | 37.05% | 62.95% | 5675 |

- **问题发现**：
  - Gemma 4 e2b 存在明显 JSON 输出不稳定（chunk 1 空段落、chunk 2 截断），导致部分分块内容丢失
  - 输出字数比基准少 24%（丢字严重），是 CER 高的主要原因
  - Ollama 对 JSON mode 的支持在小模型上不稳定，现有正则容错（processor.py:219-226）有一定缓解但不足以保证质量

- **经验**：
  - gemma4:e2b（2B 激活参数 MoE）对复杂中文指令跟随能力不足，不建议用于字幕矫正任务
  - 若要用 Gemma 4，需要 gemma4:e4b（9.6GB）或以上，但超出 8GB VRAM；可以考虑量化版本
  - 本地 Ollama 矫正整体质量与 gpt-4o-mini 差距仍大，可作为离线降级方案但不建议作为主力
  - Ollama 版本需与模型要求匹配，升级前务必确认 `api/version`
