import os
import json
import time
import sys
from processor import split_into_paragraphs

RESULTS_DIR = "results"
CACHE_DIR = "cache"
DOWNLOADS_DIR = "downloads"

def run_maintenance():
    print("--- Starting Maintenance & Global LLM Reprocessing v2 ---")
    
    if not os.path.exists(RESULTS_DIR):
        print("No results found.")
        return

    # 1. Deduplication & Cleanup
    print("\n[1/3] Cleaning up temporary files and deduplicating results...")
    all_files = os.listdir(RESULTS_DIR)
    
    for f in all_files:
        if f.endswith("_status.json") or f.endswith("_error.json"):
            os.remove(os.path.join(RESULTS_DIR, f))

    report_files = [f for f in os.listdir(RESULTS_DIR) if f.endswith(".json")]
    unique_reports = {} # Key: title or ukey, Value: (filename, mtime)
    
    for rf in report_files:
        path = os.path.join(RESULTS_DIR, rf)
        mtime = os.path.getmtime(path)
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                title = data.get("title", "")
                yt_id = data.get("youtube_id")
                media_path = data.get("media_path")
                # Deduplicate by Title + Media Source
                ukey = f"{title}_{yt_id or media_path}"
                
                if not ukey or ukey == "_": continue

                if ukey not in unique_reports or mtime > unique_reports[ukey][1]:
                    if ukey in unique_reports:
                        os.remove(os.path.join(RESULTS_DIR, unique_reports[ukey][0]))
                        print(f" - Removed duplicate: {unique_reports[ukey][0]}")
                    unique_reports[ukey] = (rf, mtime)
                else:
                    os.remove(path)
                    print(f" - Removed duplicate: {rf}")
        except: pass

    # 2. Global Reprocessing
    print("\n[2/3] Reprocessing all reports with latest LLM prompts...")
    reprocessed_count = 0
    for ukey, (rf, _) in unique_reports.items():
        path = os.path.join(RESULTS_DIR, rf)
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            title = data.get("title", "Unknown")
            raw_data = data.get("raw_subtitles") # Use internal data if possible
            
            # If not in file, check cache
            if not raw_data:
                yt_id = data.get("youtube_id")
                media_path = data.get("media_path")
                for mid in [yt_id, media_path]:
                    if not mid: continue
                    for mode in ["local", "cloud"]:
                        cache_path = os.path.join(CACHE_DIR, f"{mid}_{mode}_raw.json")
                        if os.path.exists(cache_path):
                            with open(cache_path, "r", encoding="utf-8") as cf:
                                raw_data = json.load(cf)
                            break
                    if raw_data: break
            
            if raw_data:
                print(f" - Reprocessing: {title} ({rf})")
                paragraphs, llm_usage = split_into_paragraphs(raw_data, title=title)
                
                if "usage" not in data: data["usage"] = {}
                data["paragraphs"] = paragraphs
                data["usage"]["llm_tokens"] = llm_usage
                
                duration = data["usage"].get("duration", 0)
                if not duration and raw_data: # Try to estimate
                     duration = raw_data[-1]["end"] if raw_data else 0
                     data["usage"]["duration"] = duration

                whisper_cost = data["usage"].get("whisper_cost", 0)
                llm_cost = (llm_usage["prompt_tokens"] / 1000000.0 * 0.15) + (llm_usage["completion_tokens"] / 1000000.0 * 0.6)
                data["usage"]["llm_cost"] = round(llm_cost, 6)
                data["usage"]["total_cost"] = round(whisper_cost + llm_cost, 6)
                
                # Update raw_subtitles in file for future maintenance safety
                data["raw_subtitles"] = raw_data

                with open(path, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                reprocessed_count += 1
            else:
                print(f" - Warning: No source subtitles found for {title}, skipping.")
                
        except Exception as e:
            print(f" - Error reprocessing {rf}: {e}")

    # 3. Media Cleanup
    print("\n[3/3] Final cleanup...")
    print(f"\nDONE! Reprocessed {reprocessed_count} files.")

if __name__ == "__main__":
    run_maintenance()
