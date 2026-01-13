import os
from openai import OpenAI
from faster_whisper import WhisperModel
from dotenv import load_dotenv

load_dotenv()

# Global model cache to avoid re-loading
_model_cache = {}

def get_model(model_size="base"):
    if model_size not in _model_cache:
        print(f"--- Loading Whisper model ({model_size})... This may take a while if downloading... ---")
        _model_cache[model_size] = WhisperModel(model_size, device="cpu", compute_type="int8")
        print(f"--- Model {model_size} loaded successfully! ---")
    return _model_cache[model_size]

def transcribe_local(file_path: str):
    model_size = "base"
    model = get_model(model_size)
    
    print(f"--- Starting local transcription for: {file_path} ---")
    # 启用 word_timestamps
    segments, info = model.transcribe(file_path, beam_size=5, word_timestamps=True)
    
    results = []
    for segment in segments:
        results.append({
            "start": segment.start,
            "end": segment.end,
            "text": segment.text.strip(),
            "words": [{"start": w.start, "end": w.end, "text": w.word} for w in segment.words] if segment.words else []
        })
    print(f"--- Transcription completed: {len(results)} segments found ---")
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
