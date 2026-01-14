import os
import json
import time
import sys
from processor import split_into_paragraphs

RESULTS_DIR = "results"
CACHE_DIR = "cache"
DOWNLOADS_DIR = "downloads"

def run_maintenance():
    print("--- Starting Maintenance & Global LLM Reprocessing ---")
    
    if not os.path.exists(RESULTS_DIR):
        print("No results found.")
        return

    # 1. Deduplication & Cleanup of Status/Error files
    print("\n[1/3] Cleaning up temporary files and deduplicating results...")
    all_files = os.listdir(RESULTS_DIR)
    
    # Remove status and error files
    for f in all_files:
        if f.endswith("_status.json") or f.endswith("_error.json"):
            os.remove(os.path.join(RESULTS_DIR, f))
            print(f" - Deleted temporary file: {f}")

    # Re-list to get only report files
    report_files = [f for f in os.listdir(RESULTS_DIR) if f.endswith(".json")]
    unique_reports = {} # Key: unique media id, Value: (filename, mtime)
    
    for rf in report_files:
        path = os.path.join(RESULTS_DIR, rf)
        mtime = os.path.getmtime(path)
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                yt_id = data.get("youtube_id")
                media_path = data.get("media_path")
                # Unique key: YouTube ID or the basename of the media file
                ukey = yt_id if yt_id else media_path
                
                if not ukey:
                    print(f" - Skipping {rf}: No unique key found.")
                    continue

                if ukey not in unique_reports or mtime > unique_reports[ukey][1]:
                    # If we already had a version, delete the old one
                    if ukey in unique_reports:
                        old_file = unique_reports[ukey][0]
                        os.remove(os.path.join(RESULTS_DIR, old_file))
                        print(f" - Removed duplicate/older version: {old_file}")
                    
                    unique_reports[ukey] = (rf, mtime)
                else:
                    # Current file is older or same, delete it
                    os.remove(path)
                    print(f" - Removed duplicate/older version: {rf}")
        except Exception as e:
            print(f" - Error processing {rf}: {e}")

    # 2. Global Reprocessing
    print("\n[2/3] Reprocessing all reports with latest LLM prompts...")
    reprocessed_count = 0
    for ukey, (rf, _) in unique_reports.items():
        path = os.path.join(RESULTS_DIR, rf)
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            title = data.get("title", "Unknown")
            # Try to find raw cache
            raw_data = None
            for mode in ["local", "cloud"]:
                cache_path = os.path.join(CACHE_DIR, f"{ukey}_{mode}_raw.json")
                if os.path.exists(cache_path):
                    with open(cache_path, "r", encoding="utf-8") as cf:
                        raw_data = json.load(cf)
                    break
            
            if raw_data:
                print(f" - Reprocessing: {title} ({rf})")
                paragraphs, llm_usage = split_into_paragraphs(raw_data, title=title)
                
                # Ensure usage structure exists
                if "usage" not in data:
                    data["usage"] = {}
                
                data["paragraphs"] = paragraphs
                data["usage"]["llm_tokens"] = llm_usage
                # Re-calculate costs
                duration = data["usage"].get("duration", 0)
                whisper_cost = data["usage"].get("whisper_cost", 0)
                llm_cost = (llm_usage["prompt_tokens"] / 1000000.0 * 0.15) + (llm_usage["completion_tokens"] / 1000000.0 * 0.6)
                data["usage"]["llm_cost"] = round(llm_cost, 6)
                data["usage"]["total_cost"] = round(whisper_cost + llm_cost, 6)
                
                # Save back
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                reprocessed_count += 1
            else:
                print(f" - Warning: No raw cache found for {title}, skipping reprocessing.")
                
        except Exception as e:
            print(f" - Error reprocessing {rf}: {e}")

    # 3. Media Cleanup
    print("\n[3/3] Checking for orphaned media files...")
    referenced_media = set()
    for f in os.listdir(RESULTS_DIR):
        if f.endswith(".json"):
            try:
                with open(os.path.join(RESULTS_DIR, f), "r", encoding="utf-8") as rf:
                    d = json.load(rf)
                    if d.get("media_path"):
                        referenced_media.add(d.get("media_path"))
            except: pass

    for mf in os.listdir(DOWNLOADS_DIR):
        if mf not in referenced_media:
            # Avoid deleting meta files
            if mf.endswith((".mp3", ".m4a", ".mp4", ".webm", ".wav")):
                path = os.path.join(DOWNLOADS_DIR, mf)
                # Only delete if older than 1 hour to avoid deleting active downloads
                if time.time() - os.path.getmtime(path) > 3600:
                    os.remove(path)
                    print(f" - Deleted orphaned media: {mf}")

    print(f"\nDONE! Reprocessed {reprocessed_count} files.")

if __name__ == "__main__":
    run_maintenance()
