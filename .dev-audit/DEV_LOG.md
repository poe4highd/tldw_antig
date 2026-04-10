# 2026-04-09 开发日志

### [Perf] 182 本机 Ollama 启用 RTX 4060 GPU 推理，速度提升 2.1x

- **背景**：评测发现 182 本机 Ollama 跑 gemma4:e4b V2 耗时 73 min，而 176 MacStudio 仅 34 min。怀疑本机未使用 GPU。

- **排查过程**：
  1. `nvidia-smi` 确认 RTX 4060（8GB 显存）存在且驱动正常
  2. `ollama ps` 显示 `66%/34% CPU/GPU`，推理时 GPU 显存仅 ~3.4GB
  3. `journalctl -u ollama` 关键日志：`allocating 9086.21 MiB on device 0: cudaMalloc failed: out of memory` → 降级 CPU
  4. num_gpu 层数逐步测试：num_gpu=42 成功（3752MB），num_gpu=43 失败（模型只有 42 层）
  5. `ollama ps` 的 `66%/34%` 是**内存占比**而非层数比：42/43 层在 GPU，output layer 在 CPU，权重文件 6.6GB 在系统内存

- **根因**：`OLLAMA_GPU_LAYERS` 未配置，Ollama 默认尝试全量 43 层（需 9.1GB 显存），超出 8GB 后整体降级 CPU，**不自动做部分 offload**。

- **修复**：`/etc/systemd/system/ollama.service.d/override.conf` 新增 `Environment="OLLAMA_GPU_LAYERS=42"`，重启服务。

- **额外发现**：`processor.py` 通过 OpenAI SDK 的 `extra_body={"options": {"num_gpu": 42}}` 传参，**对 Ollama OpenAI 兼容接口无效**，服务端环境变量才是正确做法。

- **速度测试结果**：

  | 配置 | tokens/s | 全程耗时（19 chunks） |
  |------|---------|---------------------|
  | 182 纯 CPU（修复前） | 17.9 | 73 min |
  | 182 GPU num_gpu=42（修复后） | 37.8 | 预计 ~33 min |
  | 176 MacStudio | ~40 | 34 min |

- **代码改动**：
  - `backend/processor.py`：加 `extra_body` 传 `num_gpu`（服务端兜底，无实际效果但留作文档）
  - `backend/scripts/evaluate_accuracy.py`：加计时输出、e4b V2 / 26b V2 加缓存检查、删除 26b 评测块（OOM）

- **经验**：
  - Ollama 显存不足时**不会自动降层数**，直接全量降级 CPU，必须显式配置 `OLLAMA_GPU_LAYERS`
  - `ollama ps` 的 CPU/GPU 比例显示的是**显存占比**，不是层数比例，容易误判
  - 8GB 显存装 8B Q4_K_M 模型（~4.7GB 权重 + KV cache + runtime）刚好够，42/43 层可全 GPU

# 2026-04-07 开发日志

### [Improve] PROMPT_V2 句子保留模式 — gemma4:e4b 首次超越 gpt-4o-mini

- **需求**：LLM 矫正在 CER 上无正收益（raw 11.90%，gpt-4o-mini 12.26%，e4b V1 12.98%）。根因是 LLM 合并分段引入字词漂移。目标：改 prompt 策略，只做同音纠错+句末标点，保留原始句子边界，不改字数，期望 CER 追平 raw。

- **实际改动**：
  1. `backend/processor.py`：新增 `PROMPT_V2`（句子保留模式）— 核心规则：输入几行→输出几个 sentence，1:1 对应，只做同音字原位替换+句末标点，禁止合并/拆分/插词
  2. `backend/processor.py`：`split_into_paragraphs()` 新增 `prompt_mode` 参数（`"v1"`/`"v2"`）；V2 下 CHUNK_SIZE 60（防漏行）、system message 换为校对员角色
  3. `backend/scripts/evaluate_accuracy.py`：修复 `evaluate_cer` / `evaluate_raw_baseline` 使用系统 python3 问题，改为自动检测并优先使用 `backend/venv/bin/python`
  4. `backend/scripts/evaluate_accuracy.py`：新增 gemma4:e4b V2 评测轮次，结果独立保存
  5. `backend/scripts/gen_comparison_table.py`：扩展为五列对比表（GT / raw / gpt-4o-mini / e4b V1 / e4b V2）

- **评测结果**（测试集：QVBpiuph3rM，基准字数 7496）：

  | 模型 | CER | 准确率 | 输出字数 | 结果文件 |
  |------|-----|--------|----------|----------|
  | **gemma4:e4b V2（本次）** | **11.89%** | **88.11%** | 8103 | `backend/results/eval_gemma4_e4b-v2_QVBpiuph3rM.json` |
  | raw Whisper（无矫正）| 11.90% | 88.10% | 8100 | `backend/cache/QVBpiuph3rM_local_large-v3-turbo_raw.json` |
  | gpt-4o-mini | 12.26% | 87.74% | 8015 | `backend/results/eval_gpt-4o-mini_QVBpiuph3rM.json` |
  | gemma4:e4b V1 | 12.98% | 87.02% | 7971 | `backend/results/eval_gemma4_e4b_QVBpiuph3rM.json` |
  | qwen3:8b | 28.52% | 71.48% | 6447 | `backend/results/eval_qwen3_8b_QVBpiuph3rM.json` |

  五列逐行对比表：`backend/validation/QVBpiuph3rM_5way_comparison.md`

- **关键发现**：
  - **V2 CER 11.89%，首次超越 gpt-4o-mini（12.26%），成为所有方案最佳**
  - V2 sentence 数与 raw 完全对齐（1123/1123），句子边界完整保留
  - 3 个 chunk（1/2/12）返回空响应，fallback 到 group_by_time，反而维持了 raw 质量
  - 插词问题（"是"31次、"那"30次）来自 Whisper 本身，V2 未引入新问题

- **空响应问题排查与修复**：
  - 诊断：用完整 prompt 手动测试 chunk 1 和 chunk 10，finish_reason 均为 stop，确认是 **Ollama 服务偶发性空响应**，与内容无关（非安全过滤）
  - 修复①：`processor.py` 加入指数退避重试（最多 3 次，间隔 1s/2s/4s）
  - 重跑验证：19 个 chunk 中，6 个遇到空响应，5 个一次重试成功，1 个（chunk 10）三次全失败 fallback
  - chunk 10 单独测试：第 3 次调用（等 2s 后）成功 → 原重试代码第 3 次失败后直接退出，未给第 4 次机会
  - 修复②：重试次数从 3 提升至 **5**（间隔 1/2/4/8/16s），覆盖 Ollama 较长抖动窗口
  - 结果：V2 CER 11.90%，与 raw Whisper 完全持平

- **经验**：
  - 对本地小模型（Gemma4 4B），"保留句子边界 + 只做最小改动"比"合并分段"策略 CER 更低，且更可控
  - CHUNK_SIZE 从 80 降到 60 可减少长上下文导致的格式漂移，但同时增加了 Ollama 调用次数（19 vs 15）
  - Ollama 远程服务存在偶发性空响应（约 6/19 次），必须加重试机制才能用于生产
  - **V2 策略结论：gemma4:e4b + PROMPT_V2 + 重试机制，CER = raw Whisper，可作为本地零成本矫正方案**

# 2026-04-06 开发日志

### [Improve] Gemma4 矫正质量提升 + raw Whisper baseline 评测

- **需求**：在 e4b CER 13.43% 基础上，进一步优化矫正质量；同时补充 raw Whisper（无 LLM 矫正）的 baseline，厘清 LLM 矫正步骤的实际增益。

- **实际改动**：
  1. `backend/scripts/evaluate_accuracy.py`：新增 `evaluate_raw_baseline()` 函数，在 LLM 评测前先对 raw Whisper cache 直接计算 CER，作为 baseline 对照
  2. `backend/processor.py`：JSON key 归一化（`text_content`/`content` → `text`），消除 chunk 5 丢失问题
  3. `backend/processor.py`：Ollama 调用加 `temperature=0.1`（原默认 ~0.8），减少 JSON 格式随机性
  4. `backend/processor.py`：prompt 输出示例注明"字段名不得使用 text_content、content 或其他变体"

- **评测结果**（测试集：QVBpiuph3rM，基准字数 7496）：

  | 模型 | CER | 准确率 | 输出字数 | 结果文件 |
  |------|-----|--------|----------|----------|
  | **raw Whisper（无矫正）** | **11.90%** | **88.10%** | 8100 | `backend/cache/QVBpiuph3rM_local_large-v3-turbo_raw.json` |
  | gpt-4o-mini | 12.26% | 87.74% | 8015 | `backend/results/eval_gpt-4o-mini_QVBpiuph3rM.json` |
  | gemma4:e4b（本次） | 12.98% | 87.02% | 7971 | `backend/results/eval_gemma4_e4b_QVBpiuph3rM.json` |
  | gemma4:e4b（上次） | 13.43% | 86.57% | 7859 | （已覆盖） |
  | qwen3:8b | 28.52% | 71.48% | 6447 | `backend/results/eval_qwen3_8b_QVBpiuph3rM.json` |
  | gemma4:e2b | 37.05% | 62.95% | 5675 | `backend/results/eval_gemma4_e2b_QVBpiuph3rM.json` |

  详细报告：`backend/validation/QVBpiuph3rM_raw_*.txt`、`backend/validation/QVBpiuph3rM_llm_*.txt`

- **关键发现（反直觉）**：
  - **raw Whisper 本身 CER 11.90%，比任何 LLM 矫正结果都低**
  - LLM 矫正未能消除 Whisper 的虚词插入问题（"是" 31次、"那" 30次），反而引入新的字词替换错误（`的→地` 7次等）
  - e4b 本次输出字数 7971 > 上次 7859，JSON fallback 修复有效，chunk 5 不再丢失
  - CER 从 13.43% → 12.98%，temperature 降低 + fallback 修复带来 0.45pp 改善

- **经验与待决策**：
  - LLM 矫正在 CER 指标上无正收益，但对可读性、标点、段落结构有价值（CER 不测这些）
  - 若目标是降低 CER，应改 prompt 策略：**只做分段+标点，明确禁止字词替换**
  - 另一选项：关掉矫正，直接用 raw Whisper 分段，省去 LLM 调用成本

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
