import os
import json
import sys
import argparse
from pathlib import Path

# Add parent directory to path to import db
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db import get_db

def sync_result(task_id, supabase, results_dir):
    result_file = os.path.join(results_dir, f"{task_id}.json")
    if not os.path.exists(result_file):
        print(f"Error: Result file not found: {result_file}")
        return False
    
    try:
        with open(result_file, "r", encoding="utf-8") as f:
            result = json.load(f)
        
        # Determine video_id
        video_id = result.get("youtube_id") or result.get("id") or task_id
        
        video_data = {
            "id": video_id,
            "title": result.get("title", "Unknown"),
            "thumbnail": result.get("thumbnail"),
            "media_path": result.get("media_path"),
            "report_data": {
                "paragraphs": result.get("paragraphs", []),
                "raw_subtitles": result.get("raw_subtitles", []),
                "summary": result.get("summary"),
                "keywords": result.get("keywords", []),
                "channel": result.get("channel"),
                "channel_id": result.get("channel_id"),
                "channel_avatar": result.get("channel_avatar")
            },
            "usage": result.get("usage", {}),
            "user_id": result.get("user_id"),
            "is_public": result.get("is_public", True),
            "status": "completed"
        }
        
        print(f"Syncing {video_id} to Supabase...")
        res = supabase.table("videos").upsert(video_data).execute()
        
        if res.data:
            print(f"Successfully synced: {video_id}")
            
            # Sync keywords if any
            keywords = result.get("keywords", [])
            for kw in keywords:
                kw_clean = kw.strip()
                if not kw_clean: continue
                try:
                    kw_res = supabase.table("keywords").select("id, count").eq("name", kw_clean).execute()
                    if kw_res.data:
                        kw_id = kw_res.data[0]["id"]
                        new_count = (kw_res.data[0]["count"] or 0) + 1
                        supabase.table("keywords").update({"count": new_count}).eq("id", kw_id).execute()
                    else:
                        new_kw = supabase.table("keywords").insert({"name": kw_clean, "count": 1}).execute()
                        if new_kw.data: kw_id = new_kw.data[0]["id"]
                        else: continue
                    supabase.table("video_keywords").upsert({"video_id": video_id, "keyword_id": kw_id}).execute()
                except Exception as kw_e:
                    print(f"Error syncing keyword '{kw_clean}': {kw_e}")
            
            return True
        else:
            print(f"Sync failed for {video_id}: No data returned from upsert")
            return False
            
    except Exception as e:
        print(f"Error syncing {task_id}: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    parser = argparse.ArgumentParser(description="Sync local results to Supabase")
    parser.add_argument("--id", help="Specific task/video ID to sync")
    parser.add_argument("--all", action="store_true", help="Sync all results in the directory")
    args = parser.parse_args()
    
    supabase = get_db()
    if not supabase:
        print("Error: Supabase not connected")
        sys.exit(1)
    
    backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    results_dir = os.path.join(backend_dir, "results")
    
    if args.id:
        sync_result(args.id, supabase, results_dir)
    elif args.all:
        for f in os.listdir(results_dir):
            if f.endswith(".json") and not f.endswith("_status.json") and not f.endswith("_error.json"):
                task_id = f.replace(".json", "")
                sync_result(task_id, supabase, results_dir)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
