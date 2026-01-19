import os
import sys
import json
import multiprocessing
import time

# 必须在所有 AI 相关 import 之前执行
if __name__ == "__main__":
    try:
        multiprocessing.set_start_method('fork', force=True)
    except RuntimeError:
        pass

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from transcriber import transcribe_audio

def verify_advanced():
    video_id = "QVBpiuph3rM"
    audio_path = f"backend/downloads/{video_id}.m4a"
    mode = "local"
    
    if not os.path.exists(audio_path):
        print(f"Error: {audio_path} not found.")
        return

    models = ["sensevoice"]

    # We use the video title as prompt for consistency where supported
    initial_prompt = "灵修与明白神的旨意"
    
    for model_size in models:
        cache_path = f"backend/cache/{video_id}_local_{model_size}_raw.json"
        
        # 为了验证 Step 7 优化，我们这次强制重新运行 FunASR 模型
        if "para" in model_size or "sense" in model_size:
            print(f"--- [Step 7] 强制重新运行 {model_size} 以验证 GPU/内存优化 ---")
        elif os.path.exists(cache_path):
            print(f"--- Skipping {model_size}, already exists. ---")
            continue
            
        print(f"--- Running {model_size} transcription for {video_id} ---")
        try:
            raw_subtitles = transcribe_audio(audio_path, mode=mode, initial_prompt=initial_prompt, model_size=model_size)
            
            # Save to cache
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(raw_subtitles, f, ensure_ascii=False, indent=2)
            
            print(f"--- Completed {model_size}! Saved to {cache_path} ---")
            
            # 等待 10 秒供系统回收 Swap 空间
            print("--- [Cool Down] 等待 10s 以回收资源 ---")
            time.sleep(10)
            
        except Exception as e:
            print(f"--- Failed {model_size}: {e} ---")

if __name__ == "__main__":
    verify_advanced()
