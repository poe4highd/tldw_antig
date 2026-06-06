import os
import sys
import platform
from dotenv import load_dotenv

load_dotenv()

# Use absolute paths for models to avoid ambiguity in different execution contexts
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.environ["HF_HOME"] = os.path.join(BASE_DIR, "models/huggingface")
os.environ["MODELSCOPE_CACHE"] = os.path.join(BASE_DIR, "models/modelscope")
os.environ["TEMP_DIR"] = os.path.join(BASE_DIR, "data/temp")

def is_apple_silicon():
    """检测是否为 Apple Silicon (Mac M1/M2/M3)"""
    return sys.platform == "darwin" and platform.machine() == "arm64"

def get_faster_whisper_model(model_size="large-v3-turbo"):
    from faster_whisper import WhisperModel
    if f"faster_{model_size}" not in _model_cache:
        print(f"--- Loading faster-whisper model ({model_size}) on CUDA (compute_type: float16)... ---")
        try:
            _model_cache[f"faster_{model_size}"] = WhisperModel(model_size, device="cuda", compute_type="float16")
            print(f"--- faster-whisper {model_size} loaded successfully on CUDA! ---")
        except Exception as e:
            print(f"--- Failed to load on CUDA, falling back to CPU (compute_type: int8). Error: {e} ---")
            _model_cache[f"faster_{model_size}"] = WhisperModel(model_size, device="cpu", compute_type="int8")
            print(f"--- faster-whisper {model_size} loaded successfully on CPU! ---")
    return _model_cache[f"faster_{model_size}"]

# Global model cache to avoid re-loading
_model_cache = {}
_funasr_cache = {}
_sherpa_cache = {}

def get_funasr_model(model_name="iic/SenseVoiceSmall"):
    import torch
    import gc
    
    # 零驻留策略：加载新模型前清空所有模型缓存（包括 Whisper）
    if len(_funasr_cache) > 0 or len(_model_cache) > 0:
        print("--- [Memory Flush] 清理所有模型缓存 (Whisper & FunASR) ---")
        _funasr_cache.clear()
        _model_cache.clear()
        gc.collect()
        if torch.backends.mps.is_available():
            torch.mps.empty_cache()

    if model_name not in _funasr_cache:
        print(f"--- Loading FunASR model ({model_name})... ---")
        # Use MPS for Mac GPU acceleration, fallback to CPU
        device = "mps" if torch.backends.mps.is_available() else "cpu"
            
        _funasr_cache[model_name] = AutoModel(
            model=model_name,
            trust_remote_code=True, # Enabled remote code to fix "No module named model"
            device=device,
            disable_update=True, # Prevent auto-update check hanging
            # ncpu=1 # Removed limit to use all cores
        )
    return _funasr_cache[model_name]

def get_sensevoice_onnx_model():
    """
    Load SenseVoice ONNX model using sherpa-onnx.
    Optimized for Mac (MPS/Apple Silicon).
    """
    import sherpa_onnx
    if "sensevoice_onnx" not in _sherpa_cache:
        print("--- Loading SenseVoice ONNX model (sherpa-onnx)... ---")
        model_dir = os.path.join(BASE_DIR, "models/sensevoice-onnx")
        model_path = os.path.join(model_dir, "model.int8.onnx")
        tokens_path = os.path.join(model_dir, "tokens.txt")
        
        if not os.path.exists(model_path):
            # Fallback to non-int8 if int8 is missing for some reason
            model_path = os.path.join(model_dir, "model.onnx")
            
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"SenseVoice ONNX model not found in {model_dir}")

        _sherpa_cache["sensevoice_onnx"] = sherpa_onnx.OfflineRecognizer.from_sense_voice(
            model=model_path,
            tokens=tokens_path,
            num_threads=os.cpu_count(),
            use_itn=True,
            debug=False
        )
        print("--- SenseVoice ONNX loaded successfully! ---")
    return _sherpa_cache["sensevoice_onnx"]

def get_silero_vad_config():
    """Load Silero VAD model config for segmenting long audio."""
    vad_model_path = os.path.join(BASE_DIR, "models/silero_vad/silero_vad.onnx")
    if not os.path.exists(vad_model_path):
         raise FileNotFoundError(f"VAD model not found at {vad_model_path}. Please ensure it is downloaded.")
         
    import sherpa_onnx
    silero_config = sherpa_onnx.SileroVadModelConfig(
        model=vad_model_path,
        min_silence_duration=0.5,
        min_speech_duration=0.25,
        threshold=0.5,
        window_size=512,
    )
    vad_config = sherpa_onnx.VadModelConfig()
    vad_config.silero_vad = silero_config
    vad_config.sample_rate = 16000
    return vad_config

def transcribe_sensevoice_onnx(file_path: str):
    """
    Transcribe audio using SenseVoice ONNX via sherpa-onnx + Silero VAD.
    Uses streaming chunks to avoid OOM on long files.
    """
    import sherpa_onnx
    import time
    from sherpa_utils import iter_audio_chunks
    recognizer = get_sensevoice_onnx_model()
    vad_config = get_silero_vad_config()
    vad = sherpa_onnx.VoiceActivityDetector(vad_config, buffer_size_in_seconds=30)
    sample_rate = 16000
    chunk_size = int(0.1 * sample_rate)  # 100ms mini-chunks for VAD

    def _drain_vad():
        while not vad.empty():
            segment = vad.front
            stream = recognizer.create_stream()
            stream.accept_waveform(sample_rate, segment.samples)
            recognizer.decode_stream(stream)
            start_s = segment.start / sample_rate
            duration_s = len(segment.samples) / sample_rate
            text = stream.result.text.strip()
            if text:
                results.append({
                    "start": start_s,
                    "end": start_s + duration_s,
                    "text": text,
                    "words": []
                })
                if len(results) % 10 == 0:
                    print(f"--- [Progress] Transcribed {start_s:.1f}s... ---")
            vad.pop()

    print(f"--- [Sherpa-VAD] Processing {file_path} (streaming chunks) ---")
    results = []
    start_time = time.time()

    # 外层：流式 30s 大块；内层：100ms 小块喂 VAD，峰值内存 ~2MB/chunk
    for big_chunk in iter_audio_chunks(file_path, chunk_seconds=30):
        for i in range(0, len(big_chunk), chunk_size):
            vad.accept_waveform(big_chunk[i: i + chunk_size])
            _drain_vad()

    # flush 尾部残留
    vad.flush()
    _drain_vad()

    print(f"--- SenseVoice ONNX (VAD) finished in {time.time() - start_time:.2f}s ---")
    return results, None  # SenseVoice ONNX 无单一语言码输出

def _get_silence_cut_points(file_path: str, target_points: list) -> list:
    """
    用 ffmpeg silencedetect 找最靠近 target_points 的静音结束点作为实际切割点。
    在静音处切割可避免 Whisper 在边界截断句子。
    """
    import re, subprocess
    result = subprocess.run([
        "ffmpeg", "-i", file_path,
        "-af", "silencedetect=noise=-40dB:d=0.3",
        "-f", "null", "-"
    ], capture_output=True, text=True)

    silence_ends = []
    for line in result.stderr.split('\n'):
        m = re.search(r'silence_end: ([\d.]+)', line)
        if m:
            silence_ends.append(float(m.group(1)))

    if not silence_ends:
        return target_points  # 没有静音点，回退到按时间切割

    adjusted = []
    for t in target_points:
        # 在目标点前后 60s 范围内寻找最近的静音结束点
        candidates = [s for s in silence_ends if abs(s - t) < 60]
        if candidates:
            adjusted.append(min(candidates, key=lambda s: abs(s - t)))
        else:
            adjusted.append(t)
    return adjusted


def _transcribe_mlx_chunked(file_path: str, hf_repo: str, initial_prompt: str,
                             chunk_minutes: int = 20, overlap_seconds: int = 30) -> dict:
    """
    对超长文件分块调用 mlx_whisper：
    - 在静音处切割，避免截断句子
    - 加 overlap 防止边界词丢失，合并时丢弃 overlap 区段避免重复
    - 每个 segment 加绝对时间戳 offset
    """
    import mlx_whisper, json, subprocess, tempfile

    # 探测总时长
    probe = subprocess.run([
        "ffprobe", "-v", "quiet", "-print_format", "json", "-show_streams", file_path
    ], capture_output=True, text=True)
    streams = json.loads(probe.stdout).get("streams", [{}])
    duration = max((float(s.get("duration", 0)) for s in streams), default=0.0)

    chunk_sec = chunk_minutes * 60
    if duration <= chunk_sec:
        # 短文件直接处理，不分块
        return mlx_whisper.transcribe(
            file_path, path_or_hf_repo=hf_repo,
            word_timestamps=True, initial_prompt=initial_prompt
        )

    # 计算目标切割点并调整到静音处
    target_cuts = list(range(chunk_sec, int(duration), chunk_sec))
    actual_cuts = _get_silence_cut_points(file_path, target_cuts)
    boundaries = [0.0] + actual_cuts + [duration]

    results_all = {"segments": [], "language": None}
    with tempfile.TemporaryDirectory() as tmpdir:
        for idx in range(len(boundaries) - 1):
            seg_start = boundaries[idx]
            seg_end = boundaries[idx + 1]
            extract_duration = min(seg_end + overlap_seconds, duration) - seg_start

            seg_path = os.path.join(tmpdir, f"seg_{idx:03d}.mp3")
            subprocess.run([
                "ffmpeg", "-ss", str(seg_start), "-i", file_path,
                "-t", str(extract_duration),
                "-q:a", "2", "-y", seg_path
            ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            print(f"--- [Chunked] 转录分段 {idx + 1}/{len(boundaries) - 1}: "
                  f"{seg_start:.1f}s - {seg_end:.1f}s ---")
            out = mlx_whisper.transcribe(
                seg_path, path_or_hf_repo=hf_repo,
                word_timestamps=True, initial_prompt=initial_prompt
            )

            if results_all["language"] is None:
                results_all["language"] = out.get("language")

            for seg in out.get("segments", []):
                abs_start = seg["start"] + seg_start
                abs_end = seg["end"] + seg_start

                # 跳过超出本段有效范围的 segment（overlap 区域的重复内容）
                if abs_start >= seg_end:
                    continue
                abs_end = min(abs_end, seg_end + 1.0)  # clamp，防止越界

                seg["start"] = abs_start
                seg["end"] = abs_end
                for w in seg.get("words", []):
                    w["start"] += seg_start
                    w["end"] += seg_start
                results_all["segments"].append(seg)

    return results_all


def transcribe_funasr(file_path: str, model_name="iic/SenseVoiceSmall"):
    model = get_funasr_model(model_name)
    print(f"--- [FunASR] 使用 {model_name} 为 {file_path} 进行转录 ---")
    
    # SenseVoiceSmall and Paraformer-zh specific logic
    res = model.generate(
        input=file_path,
        cache={},
        language="auto", # for SenseVoice
        use_itn=True,
        batch_size_s=60, # Reduced to 60s to prevent swap/OOM
        merge_vad=True,
        merge_length_s=15,
    )
    
    results = []
    # FunASR result format normalization
    if isinstance(res, list) and len(res) > 0:
        # Standard FunASR output is a list of dicts with 'text' and 'timestamp'
        for item in res:
            text = item.get("text", "")
            # Some models might return timestamps in ms, some in s
            # Format: [[start, end], [start, end], ...]
            timestamps = item.get("timestamp", [])
            
            # If no timestamps, we treat the whole thing as one segment
            if not timestamps:
                results.append({"start": 0.0, "end": 0.0, "text": text, "words": []})
            else:
                # Handle cases where FunASR returns a single string but multiple timestamps
                # Paraformer-zh often returns a long string and a list of word timestamps
                # For our purposes, we'll try to break it down or keep it as one large chunk if necessary
                results.append({
                    "start": timestamps[0][0] / 1000.0 if timestamps[0][0] > 100 else timestamps[0][0], 
                    "end": timestamps[-1][1] / 1000.0 if timestamps[-1][1] > 100 else timestamps[-1][1], 
                    "text": text,
                    "words": []
                })
    
    print(f"--- FunASR 转录完成 ---")

    import torch
    import gc
    # Resource Cleanup (especially for Mac/MPS)
    if torch.backends.mps.is_available():
        torch.mps.empty_cache()
    gc.collect()

    return results, None  # FunASR 无可靠单一语言码输出

def _transcribe_faster_whisper_chunked(file_path: str, model, initial_prompt: str,
                                        chunk_minutes: int = 20, overlap_seconds: int = 30):
    """
    对超长文件分块调用 faster-whisper，避免全量加载 OOM。
    ≤ chunk_minutes 的短文件直接整文件处理。
    """
    import json, subprocess, tempfile, gc

    probe = subprocess.run([
        "ffprobe", "-v", "quiet", "-print_format", "json", "-show_streams", file_path
    ], capture_output=True, text=True)
    streams = json.loads(probe.stdout).get("streams", [{}])
    duration = max((float(s.get("duration", 0)) for s in streams), default=0.0)

    chunk_sec = chunk_minutes * 60

    def _run_transcribe(path, prompt):
        segs, info = model.transcribe(
            path, beam_size=5, word_timestamps=True,
            initial_prompt=prompt,
            vad_filter=True,
            vad_parameters={"min_silence_duration_ms": 500}
        )
        results = []
        for seg in segs:
            results.append({
                "start": seg.start,
                "end": seg.end,
                "text": seg.text.strip(),
                "words": [{"start": w.start, "end": w.end, "text": w.word} for w in seg.words] if seg.words else []
            })
        lang = getattr(info, "language", None)
        return results, lang

    if duration <= chunk_sec:
        return _run_transcribe(file_path, initial_prompt)

    target_cuts = list(range(chunk_sec, int(duration), chunk_sec))
    actual_cuts = _get_silence_cut_points(file_path, target_cuts)
    boundaries = [0.0] + actual_cuts + [duration]

    all_segments = []
    detected_lang = None
    with tempfile.TemporaryDirectory() as tmpdir:
        for idx in range(len(boundaries) - 1):
            seg_start = boundaries[idx]
            seg_end = boundaries[idx + 1]
            extract_duration = min(seg_end + overlap_seconds, duration) - seg_start

            seg_path = os.path.join(tmpdir, f"seg_{idx:03d}.mp3")
            subprocess.run([
                "ffmpeg", "-ss", str(seg_start), "-i", file_path,
                "-t", str(extract_duration),
                "-q:a", "2", "-y", seg_path
            ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            print(f"--- [FW-Chunked] 转录分段 {idx + 1}/{len(boundaries) - 1}: "
                  f"{seg_start:.1f}s - {seg_end:.1f}s ---")
            chunk_segs, lang = _run_transcribe(seg_path, initial_prompt)
            if detected_lang is None:
                detected_lang = lang

            for seg in chunk_segs:
                abs_start = seg["start"] + seg_start
                abs_end = seg["end"] + seg_start
                if abs_start >= seg_end:
                    continue
                seg["start"] = abs_start
                seg["end"] = min(abs_end, seg_end + 1.0)
                for w in seg.get("words", []):
                    w["start"] += seg_start
                    w["end"] += seg_start
                all_segments.append(seg)

            gc.collect()

    print(f"--- [FW-Chunked] 完成: {len(all_segments)} segments, language={detected_lang} ---")
    return all_segments, detected_lang


def transcribe_local(file_path: str, initial_prompt: str = None, model_size: str = "large-v3-turbo"):
    # Map friendly names to actual model paths
    model_mapping = {
        "large-v3-turbo": "large-v3-turbo", # mlx-whisper uses direct names
        "turbo": "large-v3-turbo",
        "medium": "large-v3-turbo",
        "large-v3": "large-v3-turbo"
    }
    
    actual_model = model_mapping.get(model_size, model_size)
    
    # 1. 尝试使用 mlx-whisper (仅限 Mac Apple Silicon)
    if is_apple_silicon():
        # [Memory Flush] 只有当其他模型已加载时才清理,避免无谓导入 torch
        if len(_funasr_cache) > 0 or len(_model_cache) > 0 or len(_sherpa_cache) > 0:
            import torch
            import gc
            print("--- [Memory Flush] 清理模型缓存 (Torch/Sherpa) 以释放 GPU 给 MLX ---")
            _funasr_cache.clear()
            _model_cache.clear()
            _sherpa_cache.clear()
            gc.collect()
            if torch.backends.mps.is_available():
                torch.mps.empty_cache()

        try:
            import mlx_whisper
            # large-v3-turbo typically doesn't have -mlx in the repo name on mlx-community
            if "turbo" in actual_model:
                hf_repo = f"mlx-community/whisper-{actual_model}"
            else:
                hf_repo = f"mlx-community/whisper-{actual_model}-mlx"

            print(f"--- [GPU 加速] 使用 mlx-whisper ({actual_model}) 为 {file_path} 进行转录 ---")
            output = _transcribe_mlx_chunked(file_path, hf_repo, initial_prompt)

            results = []
            for segment in output.get("segments", []):
                results.append({
                    "start": segment["start"],
                    "end": segment["end"],
                    "text": segment["text"].strip(),
                    "words": segment.get("words", [])
                })
            detected_lang = output.get("language", None)
            print(f"--- GPU 转录完成: {len(results)} segments, language={detected_lang} ---")
            return results, detected_lang
        except ImportError:
            print("--- mlx-whisper 未安装，回退至 CPU 模式 ---")
        except Exception as e:
            print(f"--- mlx-whisper 运行失败: {e}，正在尝试回退至 CPU 模式 ---")

    # 2. 回退到 faster-whisper，分块处理防止超长音频 OOM
    model = get_faster_whisper_model(model_size)
    print(f"--- [FW 分块模式] 使用 faster-whisper 为 {file_path} 进行转录 ---")
    return _transcribe_faster_whisper_chunked(file_path, model, initial_prompt)

def transcribe_cloud(file_path: str, initial_prompt: str = None):
    # 灰度锁定：强制路由到本地处理，锁定 OpenAI 云端调用
    print(f"--- [Cloud Lock] 正在拦截云端请求并强制路由至本地处理 ({os.path.basename(file_path)}) ---")
    return transcribe_local(file_path, initial_prompt=initial_prompt, model_size="large-v3-turbo")  # 返回元组，透传

    # 原逻辑已屏蔽
    # file_size = os.path.getsize(file_path)

    from openai import OpenAI
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    with open(file_path, "rb") as audio_file:
        transcript = client.audio.transcriptions.create(
            model="whisper-1", 
            file=audio_file,
            response_format="verbose_json",
            timestamp_granularities=["word", "segment"],
            prompt=initial_prompt # OpenAI specifies 'prompt' instead of 'initial_prompt' for transcriptions.create
        )
    
    results = []
    # 兼容 verbose_json 格式
    segments = getattr(transcript, 'segments', [])
    for segment in segments:
        results.append({
            "start": segment["start"] if isinstance(segment, dict) else segment.start,
            "end": segment["end"] if isinstance(segment, dict) else segment.end,
            "text": (segment["text"] if isinstance(segment, dict) else segment.text).strip(),
            "words": segment.get("words", []) if isinstance(segment, dict) else getattr(segment, 'words', [])
        })
    return results

def transcribe_audio(file_path: str, mode: str = "local", initial_prompt: str = None, model_size: str = "large-v3-turbo"):
    if mode == "local":
        # Check if it's a FunASR model
        if model_size in ["paraformer", "sensevoice", "Paraformer-zh", "SenseVoiceSmall"]:
            if "sense" in model_size.lower() and is_apple_silicon():
                try:
                    return transcribe_sensevoice_onnx(file_path)
                except Exception as e:
                    print(f"--- [Warning] SenseVoice ONNX failed, falling back to FunASR: {e} ---")
            
            model_name = "iic/SenseVoiceSmall" if "sense" in model_size.lower() else "iic/speech_paraformer-large_asr_nat-zh-cn-16k-common-vocab8404-pytorch"
            return transcribe_funasr(file_path, model_name=model_name)
        return transcribe_local(file_path, initial_prompt=initial_prompt, model_size=model_size)
    else:
        return transcribe_cloud(file_path, initial_prompt=initial_prompt)
