import os
import sys
import platform
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# Global model cache to avoid re-loading
_model_cache = {}

def is_apple_silicon():
    """检测是否为 Apple Silicon (Mac M1/M2/M3)"""
    return sys.platform == "darwin" and platform.machine() == "arm64"

def get_faster_whisper_model(model_size="base"):
    from faster_whisper import WhisperModel
    if f"faster_{model_size}" not in _model_cache:
        print(f"--- Loading faster-whisper model ({model_size}) on CPU... ---")
        _model_cache[f"faster_{model_size}"] = WhisperModel(model_size, device="cpu", compute_type="int8")
        print(f"--- faster-whisper {model_size} loaded successfully! ---")
    return _model_cache[f"faster_{model_size}"]

def transcribe_local(file_path: str):
    model_size = "base"
    
    # 1. 尝试使用 mlx-whisper (仅限 Mac Apple Silicon)
    if is_apple_silicon():
        try:
            import mlx_whisper
            print(f"--- [GPU 加速] 使用 mlx-whisper 为 {file_path} 进行转录 ---")
            # mlx-whisper 的模型加载是内置的，这里我们可以指定路径或大小
            # 默认返回 verbose 格式，包含 segments 和 word_timestamps
            output = mlx_whisper.transcribe(file_path, path_or_hf_repo=f"mlx-community/whisper-{model_size}-mlx", word_timestamps=True)
            
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
    model = get_faster_whisper_model(model_size)
    print(f"--- [CPU 模式] 使用 faster-whisper 为 {file_path} 进行转录 ---")
    segments, info = model.transcribe(file_path, beam_size=5, word_timestamps=True)
    
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

def transcribe_cloud(file_path: str):
    file_size = os.path.getsize(file_path)
    if file_size > 25 * 1024 * 1024:
        raise Exception(f"音频文件过大 ({file_size / 1024 / 1024:.2f}MB)，超过限额。")

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    with open(file_path, "rb") as audio_file:
        transcript = client.audio.transcriptions.create(
            model="whisper-1", 
            file=audio_file,
            response_format="verbose_json",
            timestamp_granularities=["word", "segment"]
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

def transcribe_audio(file_path: str, mode: str = "cloud"):
    if mode == "local":
        return transcribe_local(file_path)
    else:
        return transcribe_cloud(file_path)
