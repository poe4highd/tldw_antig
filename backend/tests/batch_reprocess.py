
import json
import sys
import os
import glob
from dotenv import load_dotenv

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from processor import split_into_paragraphs

load_dotenv(os.path.join(os.path.dirname(__file__), '../.env'))

RESULTS_DIR = os.path.join(os.path.dirname(__file__), '../results')

def get_recent_files(n=1):
    files = glob.glob(os.path.join(RESULTS_DIR, "*.json"))
    # Exclude status and error files
    files = [f for f in files if not f.endswith("_status.json") and not f.endswith("_error.json")]
    # Sort by modification time, newest first
    files.sort(key=os.path.getmtime, reverse=True)
    return files[:n]

def reprocess(file_path):
    print(f"--- Reprocessing {os.path.basename(file_path)} ---")
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"Failed to read file: {e}")
        return

    if "raw_subtitles" not in data:
        print("Error: 'raw_subtitles' not found in the file.")
        return

    raw_subtitles = data["raw_subtitles"]
    title = data.get("title", "")
    # Try to get description if available, otherwise empty string
    description = data.get("description", "")
    
    print(f"Title: {title}")
    
    # Call the updated function
    # Note: Description might be missing in old result files, but our updated split_into_paragraphs handles empty description.
    paragraphs, usage = split_into_paragraphs(raw_subtitles, title=title, description=description)
    
    # Update data
    data["paragraphs"] = paragraphs
    if "usage" in data:
        data["usage"]["llm_tokens"] = usage
    
    print("Saving updated result...")
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print("Success.")

if __name__ == "__main__":
    num_to_reprocess = 1
    if len(sys.argv) > 1:
        try:
            num_to_reprocess = int(sys.argv[1])
        except ValueError:
            print(f"Invalid argument: {sys.argv[1]}. Using default of 1.")
            print("Usage: python tests/batch_reprocess.py [number_of_files]")
    
    recent_files = get_recent_files(num_to_reprocess)
    print(f"Found {len(recent_files)} recent files to reprocess.")
    for f in recent_files:
        reprocess(f)
