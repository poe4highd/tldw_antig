
import sys
import os
import json
from dotenv import load_dotenv

# Add backend directory to sys.path so we can import processor
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from processor import split_into_paragraphs

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), '../.env'))

def test_punctuation():
    # Sample raw subtitles (fragmented, no punctuation)
    raw_subtitles = [
        {"start": 0.0, "text": "大家好我是老李"},
        {"start": 1.5, "text": "最近有两支暴跌的科技股"},
        {"start": 3.5, "text": "进入到了我的视野当中"},
        {"start": 5.5, "text": "我觉得这开仓买入的机会"},
        {"start": 8.0, "text": "有点浮现出来了"}
    ]
    
    print("--- Input Raw Subtitles ---")
    print(json.dumps(raw_subtitles, ensure_ascii=False, indent=2))
    
    print("\n--- Processing with LLM ---")
    paragraphs, usage = split_into_paragraphs(raw_subtitles, title="测试视频", model="gpt-4o-mini")
    
    print("\n--- Result ---")
    print(json.dumps(paragraphs, ensure_ascii=False, indent=2))
    
    # Simple assertion
    text_content = ""
    for p in paragraphs:
        for s in p["sentences"]:
            text_content += s["text"]
            
    print(f"\nFinal Combined Text: {text_content}")
    
    if "，" in text_content or "。" in text_content:
        print("\nSUCCESS: Punctuation detected!")
    else:
        print("\nFAILURE: No punctuation found.")

if __name__ == "__main__":
    test_punctuation()
