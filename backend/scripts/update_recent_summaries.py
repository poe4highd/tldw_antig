#!/usr/bin/env python3
import os
import json
import sys
# Add parent dir to path to import backend modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from supabase import create_client, Client
from dotenv import load_dotenv
from processor import summarize_text

load_dotenv()

supabase_url = os.environ.get("SUPABASE_URL")
supabase_key = os.environ.get("SUPABASE_SERVICE_KEY")
supabase: Client = create_client(supabase_url, supabase_key)

RESULTS_DIR = os.path.join(os.path.dirname(__file__), '..', 'results')

def update_recent_10():
    print("Fetching top 10 most recently completed tasks...")
    # Fetch top 10 recently completed tasks
    response = supabase.table("videos").select("*").eq("status", "completed").order("created_at", desc=True).limit(10).execute()
    tasks = response.data
    
    if not tasks:
        print("No completed tasks found.")
        return

    print(f"Found {len(tasks)} tasks to update.")

    for i, task in enumerate(tasks):
        task_id = task["id"]
        result_file = os.path.join(RESULTS_DIR, f"{task_id}.json")
        
        if not os.path.exists(result_file):
            print(f"[{i+1}/10] Task {task_id}: Result JSON not found, skipping.")
            continue
            
        print(f"[{i+1}/10] Processing Task {task_id} (Title: {task.get('title')})...")
        
        with open(result_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        paragraphs = data.get("paragraphs", [])
        if not paragraphs:
            print(f"[{i+1}/10] Task {task_id}: No paragraphs found, skipping.")
            continue
            
        # Build full_text with timestamps
        full_text = ""
        for p in paragraphs:
            for s in p.get("sentences", []):
                start_sec = int(s.get("start", 0))
                h, r = divmod(start_sec, 3600)
                m, s_v = divmod(r, 60)
                ts = f"[{h:02d}:{m:02d}:{s_v:02d}]" if h > 0 else f"[{m:02d}:{s_v:02d}]"
                full_text += f"{ts} {s.get('text', '')}\n"
                
        # Call summarize_text
        summary_data, summary_usage = summarize_text(
            full_text,
            title=data.get("title", ""),
            description=data.get("description", "")
        )
        
        new_summary = summary_data.get("summary", "")
        new_keywords = summary_data.get("keywords", [])
        
        if not new_summary:
            print(f"[{i+1}/10] Task {task_id}: Failed to generate new summary.")
            continue
            
        # Update local JSON
        data["summary"] = new_summary
        data["keywords"] = new_keywords
        
        # We optionally add usage back if needed, but not strictly required since it's just backfilling
        
        with open(result_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            
        # Update supabase if we store summary/keywords there, though currently the frontend fetches JSON directly from /result/<id> which pulls from RESULTS_DIR.
        # Check if tasks table has summary/keywords column. Usually `report_data` has it if video exists, but /result/<id> API reads from results dir.
        # If there's a submissions table, it might need updating. Let's do it via the JSON first.
        
        print(f"[{i+1}/10] Task {task_id}: Successfully updated summary.")

if __name__ == "__main__":
    update_recent_10()
