"""
将最近的 failed 任务重新入队（重置 retry_count、清理旧 _error.json、刷新 _status.json）。

用法（在 backend/ 下）：
  venv/bin/python scripts/requeue_failed.py --limit 40 --dry-run
  venv/bin/python scripts/requeue_failed.py --limit 40
"""
import argparse
import json
import os
import sys

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BACKEND_DIR)
from db import get_db  # noqa: E402

RESULTS_DIR = os.path.join(BACKEND_DIR, "results")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, required=True, help="按 created_at 倒序取最近 N 个 failed 任务")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    supabase = get_db()
    rows = supabase.table("videos") \
        .select("id, title, created_at") \
        .eq("status", "failed") \
        .order("created_at", desc=True) \
        .limit(args.limit) \
        .execute().data

    for v in rows:
        vid = v["id"]
        print(f"{v['created_at'][:16]}  {vid}  {(v.get('title') or '')[:50]}")
        if args.dry_run:
            continue

        # 单行读取 report_data，避免批量解 JSONB
        report_data = supabase.table("videos").select("report_data").eq("id", vid) \
            .single().execute().data.get("report_data") or {}
        report_data["retry_count"] = 0
        supabase.table("videos").update({"status": "queued", "report_data": report_data}) \
            .eq("id", vid).execute()

        error_file = os.path.join(RESULTS_DIR, f"{vid}_error.json")
        if os.path.exists(error_file):
            os.remove(error_file)
        # 刷新 mtime：scheduler 以此判断最后活动时间，避免旧任务被当作卡住
        with open(os.path.join(RESULTS_DIR, f"{vid}_status.json"), "w") as f:
            json.dump({"status": "queued", "progress": 0, "retry_count": 0}, f)

    print(f"{'[dry-run] ' if args.dry_run else ''}共 {len(rows)} 个任务{'将' if args.dry_run else '已'}重新入队")


if __name__ == "__main__":
    main()
