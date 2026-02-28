import os
import time
import json
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from db import get_db

RESULTS_DIR = "results"
STUCK_PROCESSING_HOURS = 3
STUCK_QUEUED_HOURS = 24
TIMEOUT_CHECK_INTERVAL = 30 * 60  # 秒
supabase = get_db()

def save_status(task_id, status, progress, eta=None):
    if not os.path.exists(RESULTS_DIR):
        os.makedirs(RESULTS_DIR)
    with open(f"{RESULTS_DIR}/{task_id}_status.json", "w") as f:
        json.dump({"status": status, "progress": progress, "eta": eta}, f)

def check_stuck_tasks():
    """将超时卡住的任务自动标记为 failed"""
    if not supabase:
        return
    try:
        processing_cutoff = (datetime.now(timezone.utc) - timedelta(hours=STUCK_PROCESSING_HOURS)).isoformat()
        queued_cutoff = (datetime.now(timezone.utc) - timedelta(hours=STUCK_QUEUED_HOURS)).isoformat()

        for status, cutoff in [("processing", processing_cutoff), ("queued", queued_cutoff)]:
            res = supabase.table("videos") \
                .select("id") \
                .eq("status", status) \
                .lt("created_at", cutoff) \
                .execute()
            for v in res.data:
                supabase.table("videos").update({"status": "failed"}).eq("id", v["id"]).execute()
                save_status(v["id"], "failed", 100)
                print(f"[Scheduler] Auto-failed stuck {status} task: {v['id']}")
    except Exception as e:
        print(f"[Scheduler] Error in check_stuck_tasks: {e}")


def get_next_task():
    if not supabase:
        # Fallback to local status files if no Supabase
        if not os.path.exists(RESULTS_DIR):
            return None
        
        queued_tasks = []
        for f in os.listdir(RESULTS_DIR):
            if f.endswith("_status.json"):
                with open(os.path.join(RESULTS_DIR, f), "r") as rf:
                    try:
                        data = json.load(rf)
                        if data.get("status") == "queued":
                            tid = f.replace("_status.json", "")
                            mtime = os.path.getmtime(os.path.join(RESULTS_DIR, f))
                            queued_tasks.append((tid, mtime))
                    except:
                        continue
        if not queued_tasks:
            return None
        
        # Sort by mtime ascending (oldest first)
        queued_tasks.sort(key=lambda x: x[1])
        return {"id": queued_tasks[0][0], "is_local": True}
    
    try:
        if supabase:
            # 1. First, try to fetch 'manual' tasks (highest priority)
            # Use ->> to query the source field inside report_data JSONB
            # Note: We order by created_at ASC to keep FIFO within the same priority level
            response = supabase.table("videos") \
                .select("id") \
                .eq("status", "queued") \
                .filter("report_data->>source", "eq", "manual") \
                .order("created_at", desc=False) \
                .limit(1) \
                .execute()
            
            if response.data:
                return {"id": response.data[0]["id"], "is_local": False}
                
            # 2. If no manual tasks, fetch 'tracker' tasks (or those without a specific source)
            # This ensures backward compatibility with tasks that didn't have a source yet
            response = supabase.table("videos") \
                .select("id") \
                .eq("status", "queued") \
                .or_("report_data->>source.eq.tracker,report_data->>source.is.null") \
                .order("created_at", desc=False) \
                .limit(1) \
                .execute()
                
            if response.data:
                return {"id": response.data[0]["id"], "is_local": False}
    except Exception as e:
        print(f"[Scheduler] Error fetching from Supabase: {e}")
    
    # Fallback to local status files if Supabase is unavailable or returns nothing
    # (Existing local logic remains as fallback)
    if not os.path.exists(RESULTS_DIR):
        return None
    
    queued_tasks = []
    for f in os.listdir(RESULTS_DIR):
        if f.endswith("_status.json"):
            tid = f.replace("_status.json", "")
            if os.path.exists(f"{RESULTS_DIR}/{tid}.json") or os.path.exists(f"{RESULTS_DIR}/{tid}_error.json"):
                continue
                
            with open(os.path.join(RESULTS_DIR, f), "r") as rf:
                try:
                    data = json.load(rf)
                    if data.get("status") == "queued":
                        mtime = os.path.getmtime(os.path.join(RESULTS_DIR, f))
                        # For local fallback, we don't differentiate priority yet as it's a rare case
                        queued_tasks.append((tid, mtime))
                except: continue
                
    if not queued_tasks:
        return None
    
    queued_tasks.sort(key=lambda x: x[1])
    return {"id": queued_tasks[0][0], "is_local": True}

def run_scheduler():
    print("--- [Scheduler] Started and monitoring queue... ---")
    last_timeout_check = 0
    while True:
        if time.time() - last_timeout_check > TIMEOUT_CHECK_INTERVAL:
            check_stuck_tasks()
            last_timeout_check = time.time()

        task = get_next_task()
        if task:
            task_id = task["id"]
            print(f"--- [Scheduler] Found queued task: {task_id} ---")
            
            # Update status to processing
            save_status(task_id, "processing", 5)
            if supabase:
                try:
                    supabase.table("videos").update({"status": "processing"}).eq("id", task_id).execute()
                except: pass

            # Trigger processing
            # For simplicity and backward compatibility, we'll call a modified version of the processing logic
            # OR we can just trigger the existing worker logic if it's already set up.
            
            # Actually, main.py's background_process is what we want, 
            # but it's an async function inside main.py.
            # It's better to have a CLI-driven processing entry point.
            
            # For now, let's assume we can call main.py's background_process logic via a script
            # OR refactor main.py to expose it.
            
            # Let's create a small wrapper script 'process_task.py' that imports and runs the logic.
            cmd = ["python3", "process_task.py", task_id]
            # Use 'nice -n 15' on Unix/Mac to lower priority
            if sys.platform != "win32":
                cmd = ["nice", "-n", "15"] + cmd
            
            print(f"--- [Scheduler] Executing: {' '.join(cmd)} ---")
            try:
                # Use subprocess.run to wait for completion (sequential)
                result = subprocess.run(cmd, capture_output=False)
                if result.returncode == 0:
                    print(f"--- [Scheduler] Task {task_id} completed successfully ---")
                else:
                    print(f"--- [Scheduler] Task {task_id} failed with exit code {result.returncode} ---")
                    save_status(task_id, "failed", 100)
                    if supabase:
                        try:
                            supabase.table("videos").update({"status": "failed"}).eq("id", task_id).execute()
                        except Exception as up_e:
                            print(f"[Scheduler] Failed to update Supabase status: {up_e}")
            except Exception as e:
                print(f"--- [Scheduler] Exception running task {task_id}: {e} ---")
                save_status(task_id, "failed", 100)
                if supabase:
                    try:
                        supabase.table("videos").update({"status": "failed"}).eq("id", task_id).execute()
                    except Exception as up_e:
                        print(f"[Scheduler] Failed to update Supabase status: {up_e}")
            
        else:
            time.sleep(10)

if __name__ == "__main__":
    run_scheduler()
