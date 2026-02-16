import os
import sys
from db import get_db

def fix_missing_submissions(target_user_id=None):
    supabase = get_db()
    if not supabase:
        print("Error: Could not connect to Supabase.")
        return

    print("--- Starting Data Migration: Fix Missing Submissions ---")
    
    # 1. 查询所有已完成但可能缺失提交记录的视频
    query = supabase.table("videos").select("id, user_id, status").eq("status", "completed")
    if target_user_id:
        query = query.eq("user_id", target_user_id)
    
    v_res = query.execute()
    videos = v_res.data
    print(f"Found {len(videos)} completed videos for analysis.")

    fixed_count = 0
    skipped_count = 0
    error_count = 0

    for v in videos:
        vid = v["id"]
        uid = v.get("user_id")
        
        if not uid:
            print(f"Video {vid} has no user_id, skipping.")
            skipped_count += 1
            continue

        # 2. 检查 submissions 表中是否存在该 video_id 与 user_id 的关联
        s_res = supabase.table("submissions") \
            .select("id") \
            .eq("user_id", uid) \
            .eq("video_id", vid) \
            .execute()
        
        if not s_res.data:
            print(f"Video {vid} is missing submission for user {uid}. Fixing...")
            try:
                # 尝试插入。由于之前 task_id 存储不一致，这里我们用 video_id 作为 task_id 的回填
                # 这样即使以后加了唯一约束，这种修复也是安全的
                supabase.table("submissions").insert({
                    "user_id": uid,
                    "video_id": vid,
                    "task_id": vid
                }).execute()
                print(f"  [SUCCESS] Linked {vid} to {uid}")
                fixed_count += 1
            except Exception as e:
                print(f"  [ERROR] Failed to link {vid}: {e}")
                error_count += 1
        else:
            skipped_count += 1

    print("\n--- Migration Summary ---")
    print(f"Checked: {len(videos)}")
    print(f"Fixed:   {fixed_count}")
    print(f"Skipped: {skipped_count}")
    print(f"Errors:  {error_count}")

if __name__ == "__main__":
    # 可以指定特定用户 ID，或者补全所有
    target_id = "a00233b0-dede-4a1f-84e4-9b4439d02fe4"
    fix_missing_submissions(target_id)
