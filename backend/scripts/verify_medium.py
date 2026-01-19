import os
import sys
import json

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from transcriber import transcribe_audio

def verify_medium():
    video_id = "QVBpiuph3rM"
    audio_path = f"backend/downloads/{video_id}.m4a"
    mode = "local"
    model_size = "medium"
    
    if not os.path.exists(audio_path):
        print(f"Error: {audio_path} not found.")
        return

    print(f"--- Running Medium model transcription for {video_id} ---")
    
    # We use the video title as prompt for consistency with other steps
    initial_prompt = "灵修与明白神的旨意"
    
    raw_subtitles = transcribe_audio(audio_path, mode=mode, initial_prompt=initial_prompt, model_size=model_size)
    
    # Save to cache
    cache_path = f"backend/cache/{video_id}_{mode}_{model_size}_raw.json"
    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(raw_subtitles, f, ensure_ascii=False, indent=2)
    
    print(f"--- Completed! Saved to {cache_path} ---")

if __name__ == "__main__":
    verify_medium()
