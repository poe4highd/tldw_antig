
import json
import sys
import os
from dotenv import load_dotenv

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from processor import split_into_paragraphs

load_dotenv(os.path.join(os.path.dirname(__file__), '../.env'))

def reprocess(file_path):
    print(f"Reading {file_path}...")
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    if "raw_subtitles" not in data:
        print("Error: 'raw_subtitles' not found in the file.")
        return

    raw_subtitles = data["raw_subtitles"]
    title = data.get("title", "")
    
    print(f"Found {len(raw_subtitles)} raw segments. Reprocessing with LLM...")
    
    # Call the updated function
    paragraphs, usage = split_into_paragraphs(raw_subtitles, title=title)
    
    # Update data
    data["paragraphs"] = paragraphs
    if "usage" in data:
        data["usage"]["llm_tokens"] = usage
        # simplistic cost update logic if needed, or just leave as is since we are just fixing text
    
    print("Saving updated result...")
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        
    print("Done!")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python reprocess_result.py <path_to_json>")
    else:
        reprocess(sys.argv[1])
