import os
import sys
import platform
from dotenv import load_dotenv

load_dotenv()

def is_apple_silicon():
    """检测是否为 Apple Silicon (Mac M1/M2/M3)"""
    return sys.platform == "darwin" and platform.machine() == "arm64"

def get_faster_whisper_model(model_size="large-v3-turbo"):
    from faster_whisper import WhisperModel
    if f"faster_{model_size}" not in _model_cache:
        print(f"--- Loading faster-whisper model ({model_size}) on CPU... ---")
        _model_cache[f"faster_{model_size}"] = WhisperModel(model_size, device="cpu", compute_type="int8")
        print(f"--- faster-whisper {model_size} loaded successfully! ---")
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
        model_dir = "backend/models/sensevoice-onnx"
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
    vad_model_path = "backend/models/silero_vad/silero_vad.onnx"
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
    Robust for long files and provides incremental progress.
    """
    import sherpa_onnx
    import time
    from sherpa_utils import load_audio_for_sherpa
    recognizer = get_sensevoice_onnx_model()
    # Create a fresh VAD instance for each file to ensure clean state
    vad_config = get_silero_vad_config()
    vad = sherpa_onnx.VoiceActivityDetector(vad_config, buffer_size_in_seconds=30)
    
    print(f"--- [Sherpa-VAD] Processing {file_path} ---")
    samples = load_audio_for_sherpa(file_path)
    sample_rate = 16000
    
    results = []
    chunk_size = int(0.1 * sample_rate) # 100ms
    
    start_time = time.time()
    for i in range(0, len(samples), chunk_size):
        chunk = samples[i : i + chunk_size]
        vad.accept_waveform(chunk)
        
        while not vad.empty():
            segment = vad.front
            # Transcribe segment
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
                # Progress logging for long files
                if len(results) % 10 == 0:
                     print(f"--- [Progress] Transcribed {start_s:.1f}s... ---")
            
            vad.pop()
    
    print(f"--- SenseVoice ONNX (VAD) finished in {time.time() - start_time:.2f}s ---")
    return results

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
    # Global cache is maintained, but we can trigger collection
    if torch.backends.mps.is_available():
        torch.mps.empty_cache()
    gc.collect()
    
    return results

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
            output = mlx_whisper.transcribe(
                file_path, 
                path_or_hf_repo=hf_repo, 
                word_timestamps=True,
                initial_prompt=initial_prompt
            )
            
            results = []
            for segment in output.get("segments", []):
                results.append({
                    "start": segment["start"],
                    "end": segment["end"],
                    "text": segment["text"].strip(),
                    "words": segment.get("words", [])
                })
            print(f"--- GPU 转录完成: {len(results)} segments found ---")
            return results
        except ImportError:
            print("--- mlx-whisper 未安装，回退至 CPU 模式 ---")
        except Exception as e:
            print(f"--- mlx-whisper 运行失败: {e}，正在尝试回退至 CPU 模式 ---")

    # 2. 回退到 faster-whisper (CPU 模式)
    # Note: large-v3 on CPU might be very slow
    model = get_faster_whisper_model(model_size)
    print(f"--- [CPU 模式] 使用 faster-whisper 为 {file_path} 进行转录 ---")
    segments, info = model.transcribe(file_path, beam_size=5, word_timestamps=True, initial_prompt=initial_prompt)
    
    results = []
    for segment in segments:
        results.append({
            "start": segment.start,
            "end": segment.end,
            "text": segment.text.strip(),
            "words": [{"start": w.start, "end": w.end, "text": w.word} for w in segment.words] if segment.words else []
        })
    print(f"--- CPU 转录完成: {len(results)} segments found ---")
    return results

def transcribe_cloud(file_path: str, initial_prompt: str = None):
    file_size = os.path.getsize(file_path)
    if file_size > 25 * 1024 * 1024:
        raise Exception(f"音频文件过大 ({file_size / 1024 / 1024:.2f}MB)，超过限额。")

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

def transcribe_audio(file_path: str, mode: str = "cloud", initial_prompt: str = None, model_size: str = "large-v3-turbo"):
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
