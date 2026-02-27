#!/usr/bin/env python3
"""重新处理最近5个失败任务 —— 将 Supabase 状态改回 queued，触发 scheduler 重试"""

import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from db import get_db

TASK_IDS = [
    "P78fylSwdpw",
    "Le2QwIuAR2g",
    "sdSusCDZcDg",
    "IijbvUP-J5g",
    "9J_o779xb5k",
]

RESULTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "results")

def main():
    supabase = get_db()
    if not supabase:
        print("❌ Supabase 连接失败，请检查 .env")
        sys.exit(1)

    for task_id in TASK_IDS:
        # 1. 查询当前状态和 report_data
        res = supabase.table("videos").select("status,report_data,title").eq("id", task_id).execute()
        if not res.data:
            print(f"⚠️  {task_id}: Supabase 中不存在，跳过")
            continue
        video = res.data[0]
        rd = video.get("report_data") or {}
        url = rd.get("url", "(无 URL)")
        title = video.get("title", "?")
        print(f"\n📋 {task_id} | {title[:40]} | {url[:60]}")
        print(f"   当前状态: {video['status']}")

        # 2. 补全 URL（task_id 即 YouTube video_id），确保 process_task.py 能重新下载
        if not rd.get("url"):
            rd["url"] = f"https://www.youtube.com/watch?v={task_id}"
            rd["mode"] = rd.get("mode") or "cloud"
            print(f"   ⚠️  无 URL，自动补全: {rd['url']}")

        # 3. 更新 Supabase 状态为 queued，source=manual（最高优先级），重置 retry_count
        rd["source"] = "manual"
        rd["retry_count"] = 0
        supabase.table("videos").update({
            "status": "queued",
            "report_data": rd
        }).eq("id", task_id).execute()

        # 3. 删除本地 _error.json（清理旧错误），更新 _status.json 为 queued
        error_file = os.path.join(RESULTS_DIR, f"{task_id}_error.json")
        status_file = os.path.join(RESULTS_DIR, f"{task_id}_status.json")
        if os.path.exists(error_file):
            os.remove(error_file)
        with open(status_file, "w") as f:
            json.dump({"status": "queued", "progress": 0, "eta": None}, f)

        print(f"   ✅ 已重新入队 → scheduler 将自动处理")

    print(f"\n✅ 共重新入队 {len(TASK_IDS)} 个任务，等待 scheduler 处理（最多10秒轮询间隔）")

if __name__ == "__main__":
    main()
