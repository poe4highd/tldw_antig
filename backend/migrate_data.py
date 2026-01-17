import os
import json
import asyncio
from db import get_db

RESULTS_DIR = "results"

async def migrate_to_supabase():
    supabase = get_db()
    if not supabase:
        print("Supabase client not initialized. Check your credentials.")
        return

    if not os.path.exists(RESULTS_DIR):
        print(f"Results directory {RESULTS_DIR} not found.")
        return

    files = [f for f in os.listdir(RESULTS_DIR) if f.endswith(".json") and not f.endswith("_error.json") and not f.endswith("_status.json")]
    
    for f_name in files:
        file_path = os.path.join(RESULTS_DIR, f_name)
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                
                # Prepare data for 'videos' table
                video_data = {
                    "id": data.get("youtube_id") or f_name.replace(".json", ""),
                    "title": data.get("title"),
                    "thumbnail": data.get("thumbnail"),
                    "media_path": data.get("media_path"),
                    "report_data": {
                        "paragraphs": data.get("paragraphs"),
                        "raw_subtitles": data.get("raw_subtitles")
                    },
                    "usage": data.get("usage"),
                    "status": "completed"
                }
                
                # Upsert into videos table
                print(f"Migrating {video_data['title']} ({video_data['id']})...")
                response = supabase.table("videos").upsert(video_data).execute()
                
        except Exception as e:
            print(f"Failed to migrate {f_name}: {e}")

if __name__ == "__main__":
    asyncio.run(migrate_to_supabase())
