import os
import json
import sys
from dotenv import load_dotenv

# Ensure we are in the backend directory context for imports
sys.path.append(os.path.join(os.getcwd(), 'backend'))

load_dotenv(os.path.join(os.getcwd(), 'backend', '.env'))

from transcriber import transcribe_audio

VIDEO_ID = "QVBpiuph3rM"
AUDIO_PATH = f"backend/downloads/{VIDEO_ID}.m4a"
TITLE = "灵修与明白神的旨意" # QVBpiuph3rM 的大致标题
CACHE_PATH = f"backend/cache/{VIDEO_ID}_local_large-v3_raw.json"

def main():
    if not os.path.exists(AUDIO_PATH):
        print(f"Error: {AUDIO_PATH} not found.")
        return

    print(f"--- Running Step 1 Transcription for {VIDEO_ID} ---")
    print(f"Prompt: {TITLE}")
    
    # Run transcription
    raw_subtitles = transcribe_audio(AUDIO_PATH, mode="local", initial_prompt=TITLE)
    
    # Save to cache
    os.makedirs(os.path.dirname(CACHE_PATH), exist_ok=True)
    with open(CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(raw_subtitles, f, ensure_ascii=False, indent=2)
    
    print(f"--- Transcription saved to {CACHE_PATH} ---")

if __name__ == "__main__":
    main()
