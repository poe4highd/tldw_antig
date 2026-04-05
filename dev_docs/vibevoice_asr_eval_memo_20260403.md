# VibeVoice-ASR 评估备忘录

**日期**：2026-04-03  
**结论**：暂不测试，条件不成熟，留档备查

---

## 模型信息

- **模型**：`microsoft/VibeVoice-ASR-HF`（7B 参数）
- **来源**：Microsoft 开源，2026-01-21 发布，已集成进 HuggingFace Transformers
- **特点**：
  - 单次处理最长 60 分钟连续音频（64K token）
  - 同时输出 ASR + 说话人分离 + 时间戳
  - 支持 50+ 语言，无需显式指定语言
  - 支持自定义热词（Hotwords）
- **接入方式**：`pip install "transformers>=5.3.0"`，然后：
  ```python
  from transformers import AutoProcessor, VibeVoiceAsrForConditionalGeneration
  model_id = "microsoft/VibeVoice-ASR-HF"
  processor = AutoProcessor.from_pretrained(model_id)
  model = VibeVoiceAsrForConditionalGeneration.from_pretrained(model_id, device_map="auto")
  inputs = processor.apply_transcription_request(audio_path).to(model.device, model.dtype)
  output_ids = model.generate(**inputs)
  generated_ids = output_ids[:, inputs["input_ids"].shape[1]:]
  # return_format: "raw" | "parsed" | "transcription_only"
  transcription = processor.decode(generated_ids, return_format="transcription_only")[0]
  ```

---

## 取消测试的原因

| 障碍 | 详情 |
|------|------|
| transformers 版本冲突 | 需要 >=5.3.0，当前项目使用 4.55.0，升级有 breaking change 风险 |
| 显存不足 | RTX 4060 仅 8GB，bfloat16 需 ~14GB；需要 4-bit 量化或 CPU offload |
| 与现有方案重叠 | faster-whisper large-v3-turbo 已满足需求，SenseVoice 补充中文场景 |
| 模型体积 | 首次下载约 14GB |

---

## 如果未来要测试

### 前置条件
1. 在独立 venv 中升级：`pip install "transformers>=5.3.0"` 并验证现有功能不受影响
2. 确认 bitsandbytes 已安装（4-bit 量化用）：`pip install bitsandbytes`
3. 下载测试音频：`yt-dlp -x --audio-format mp3 -o "backend/downloads/%(id)s.%(ext)s" "https://www.youtube.com/watch?v=QVBpiuph3rM"`

### 评估流程
```bash
# 1. 运行转录（需要先写 test_vibevoice_asr.py）
python backend/scripts/test_vibevoice_asr.py

# 2. 与 ground truth 对比（工具已有）
python backend/scripts/compare_subs.py \
  --gt backend/tests/data/QVBpiuph3rM.zh-CN.srv1 \
  --pred backend/cache/QVBpiuph3rM_local_vibevoice-asr_raw.json
```

### 输出格式转换
VibeVoice 的 `parsed` 格式需要映射到项目统一缓存格式：
```python
# VibeVoice 输出
[{"Start": 0.43, "End": 3.09, "Speaker": 0, "Content": "..."}]

# 项目缓存格式
[{"start": 0.43, "end": 3.09, "text": "..."}]
```

### 参考对比基准（其他模型历史 CER）
- faster-whisper large-v3-turbo：参见 `backend/validation/` 下历史报告
- SenseVoice ONNX：参见同目录报告
- 目标：准确率 > 88%（当前最优约 88.87%）
