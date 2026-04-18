import os
import time
import json
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from db import get_db
from app_logger import get_logger
logger = get_logger(__name__)

RESULTS_DIR = "results"
STUCK_PROCESSING_HOURS = 3
STUCK_QUEUED_HOURS = 24
TIMEOUT_CHECK_INTERVAL = 30 * 60  # 秒
CONSECUTIVE_ERRORS_BEFORE_RECONNECT = 3  # 连续失败次数触发重连
supabase = get_db()
_consecutive_db_errors = 0

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
                logger.info(f"[Scheduler] Auto-failed stuck {status} task: {v['id']}")
    except Exception as e:
        logger.info(f"[Scheduler] Error in check_stuck_tasks: {e}")


def get_next_task():
    global supabase, _consecutive_db_errors

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
            response = supabase.table("videos") \
                .select("id") \
                .eq("status", "queued") \
                .filter("report_data->>source", "eq", "manual") \
                .order("created_at", desc=False) \
                .limit(1) \
                .execute()

            if response.data:
                _consecutive_db_errors = 0
                return {"id": response.data[0]["id"], "is_local": False}

            # 2. If no manual tasks, fetch 'tracker' tasks (or those without a specific source)
            response = supabase.table("videos") \
                .select("id") \
                .eq("status", "queued") \
                .or_("report_data->>source.eq.tracker,report_data->>source.is.null") \
                .order("created_at", desc=False) \
                .limit(1) \
                .execute()

            if response.data:
                _consecutive_db_errors = 0
                return {"id": response.data[0]["id"], "is_local": False}

            # 查询成功但无任务
            _consecutive_db_errors = 0
    except Exception as e:
        _consecutive_db_errors += 1
        logger.info(f"[Scheduler] Error fetching from Supabase ({_consecutive_db_errors}x): {e}")

        # 连续失败多次后尝试重建连接
        if _consecutive_db_errors >= CONSECUTIVE_ERRORS_BEFORE_RECONNECT:
            logger.info(f"[Scheduler] 连续 {_consecutive_db_errors} 次失败，重建 Supabase 连接...")
            supabase = get_db(force_new=True)
            _consecutive_db_errors = 0
    
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
    logger.info("--- [Scheduler] Started and monitoring queue... ---")
    last_timeout_check = 0
    while True:
        if time.time() - last_timeout_check > TIMEOUT_CHECK_INTERVAL:
            check_stuck_tasks()
            last_timeout_check = time.time()

        task = get_next_task()
        if task:
            task_id = task["id"]
            logger.info(f"--- [Scheduler] Found queued task: {task_id} ---")
            
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
            cmd = [sys.executable, "process_task.py", task_id]
            # Use 'nice -n 15' on Unix/Mac to lower priority
            if sys.platform != "win32":
                cmd = ["nice", "-n", "15"] + cmd
            
            logger.info(f"--- [Scheduler] Executing: {' '.join(cmd)} ---")
            try:
                # Use subprocess.run to wait for completion (sequential)
                # 捕获 stderr 以便在崩溃时保留诊断信息
                result = subprocess.run(cmd, stderr=subprocess.PIPE, text=True)
                if result.returncode == 0:
                    logger.info(f"--- [Scheduler] Task {task_id} completed successfully ---")
                else:
                    logger.info(f"--- [Scheduler] Task {task_id} failed with exit code {result.returncode} ---")
                    if result.stderr:
                        logger.info(f"[Scheduler] stderr:\n{result.stderr}", file=sys.stderr)
                    # 兜底：如果 process_task.py 崩溃前未写 _error.json，由 scheduler 补写
                    error_file = f"{RESULTS_DIR}/{task_id}_error.json"
                    if not os.path.exists(error_file):
                        with open(error_file, "w") as ef:
                            json.dump({
                                "error": f"任务进程异常退出 (exit code: {result.returncode})",
                                "traceback": result.stderr or "No stderr captured"
                            }, ef, ensure_ascii=False)
                    save_status(task_id, "failed", 100)
                    if supabase:
                        try:
                            supabase.table("videos").update({"status": "failed"}).eq("id", task_id).execute()
                        except Exception as up_e:
                            logger.info(f"[Scheduler] Failed to update Supabase status: {up_e}")
            except Exception as e:
                logger.info(f"--- [Scheduler] Exception running task {task_id}: {e} ---")
                # 补写 _error.json
                error_file = f"{RESULTS_DIR}/{task_id}_error.json"
                if not os.path.exists(error_file):
                    with open(error_file, "w") as ef:
                        json.dump({
                            "error": f"Scheduler 启动任务失败: {e}",
                            "traceback": str(e)
                        }, ef, ensure_ascii=False)
                save_status(task_id, "failed", 100)
                if supabase:
                    try:
                        supabase.table("videos").update({"status": "failed"}).eq("id", task_id).execute()
                    except Exception as up_e:
                        logger.info(f"[Scheduler] Failed to update Supabase status: {up_e}")
            
        else:
            time.sleep(10)

if __name__ == "__main__":
    run_scheduler()
