
import json
import sys
import os
from dotenv import load_dotenv

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from processor import split_into_paragraphs

load_dotenv(os.path.join(os.path.dirname(__file__), '../.env'))

CACHE_FILE = os.path.join(os.path.dirname(__file__), '../cache/UBE4vkQrSb8_local_raw.json')
TITLE = "川普强买格陵兰真相：不是为了地盘，是为马斯克的1.5吉瓦“北极算力局”"

def verify():
    if not os.path.exists(CACHE_FILE):
        print(f"Cache file not found: {CACHE_FILE}")
        return

    with open(CACHE_FILE, "r", encoding="utf-8") as f:
        raw_subtitles = json.load(f)

    # Take first 100 segments. "智席" is at 27.6s, should be within first 100.
    subset = raw_subtitles[:100]
    
    print(f"--- Testing with {len(subset)} segments ---")
    print(f"Title: {TITLE}")
    
    # Run processor
    paragraphs, usage = split_into_paragraphs(subset, title=TITLE, description="")
    
    print("\n--- Result Paragraphs ---")
    print(json.dumps(paragraphs, ensure_ascii=False, indent=2))
    
    # Validation checks
    text_content = json.dumps(paragraphs, ensure_ascii=False)
    
    # Check 1: Language (Simplified?)
    # Check for "这种" vs "那種" (Trad: 種)
    # Check for "智席" vs "窒息"
    
    if "窒息" in text_content:
        print("\n✅ SUCCESS: '窒息' found! Homophone correction worked.")
    elif "智席" in text_content:
        print("\n❌ FAILED: '智席' still present.")
    else:
        print("\n⚠️ UNCERTAIN: Neither '窒息' nor '智席' found (maybe phrasing changed?)")

    # Check for Traditional characters
    import re
    trad_patterns = r'[這國個來們裏時後得會愛兒幾開萬鳥運龍門義專學聽實體禮觀]'
    if re.search(trad_patterns, text_content):
        print("❌ FAILED: Traditional characters detected.")
    else:
        print("✅ SUCCESS: No common traditional characters detected (Simplified confirmed).")

if __name__ == "__main__":
    verify()
