import os
import json
import sys
from dotenv import load_dotenv

# Ensure we are in the backend directory context for imports
backend_dir = os.path.join(os.getcwd(), 'backend')
sys.path.append(backend_dir)

load_dotenv(os.path.join(backend_dir, '.env'))

from processor import split_into_paragraphs

VIDEO_ID = "QVBpiuph3rM"
TITLE = "灵修与明白神的旨意"
DESCRIPTION = "本视频分享关于灵修的意义和如何明白神的旨意。"
CACHE_PATH = f"backend/cache/{VIDEO_ID}_local_large-v3_raw.json"
OUTPUT_PATH = f"backend/results/{VIDEO_ID}_step3.json"

def main():
    if not os.path.exists(CACHE_PATH):
        print(f"Error: {CACHE_PATH} not found. Please run Step 1 first.")
        return

    with open(CACHE_PATH, "r", encoding="utf-8") as f:
        raw_subtitles = json.load(f)

    print(f"--- Running Step 3 Contextual LLM Correction for {VIDEO_ID} ---")
    
    # Run paragraph splitting and correction (with context support in the new processor.py)
    paragraphs, usage = split_into_paragraphs(raw_subtitles, title=TITLE, description=DESCRIPTION)
    
    # Save final result
    result = {
        "paragraphs": paragraphs,
        "usage": usage,
        "title": TITLE
    }
    
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"--- Step 3 result saved to {OUTPUT_PATH} ---")
    print(f"Tokens used: {usage}")

if __name__ == "__main__":
    main()
