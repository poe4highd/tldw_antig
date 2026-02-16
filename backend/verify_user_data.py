from db import get_db
import sys

def verify_data(user_id):
    supabase = get_db()
    if not supabase:
        print("Error: Could not connect to Supabase.")
        return

    print(f"=== 查询用户 {user_id} 的 submissions ===")
    subs = supabase.table('submissions').select('video_id, task_id, created_at').eq('user_id', user_id).order('created_at', desc=True).limit(20).execute()
    
    if not subs.data:
        print("没有找到该用户的 submissions 记录。")
        return

    for s in subs.data:
        vid = s.get('video_id')
        tid = s.get('task_id')
        
        # Check if video exists by video_id
        v_res = supabase.table('videos').select('id, title, status').eq('id', vid).execute()
        v_exists = len(v_res.data) > 0
        v_title = v_res.data[0]['title'] if v_exists else 'NOT FOUND'
        v_status = v_res.data[0]['status'] if v_exists else 'NOT FOUND'
        
        # Check if video exists by task_id
        t_v_res = supabase.table('videos').select('id, title, status').eq('id', tid).execute()
        t_v_exists = len(t_v_res.data) > 0
        t_v_title = t_v_res.data[0]['title'] if t_v_exists else 'NOT FOUND'
        t_v_status = t_v_res.data[0]['status'] if t_v_exists else 'NOT FOUND'
        
        print(f"Submissions Data: video_id={vid}, task_id={tid}, created_at={s.get('created_at')}")
        print(f"  -> By video_id: Exists={v_exists}, Status={v_status}, Title={v_title[:40]}")
        print(f"  -> By task_id:  Exists={t_v_exists}, Status={t_v_status}, Title={t_v_title[:40]}")
        
        if v_exists and tid != vid:
            print("  [!] 警告: task_id 与 video_id 不一致。")
        if not v_exists and t_v_exists:
            print("  [!!] 关键错误: submission.video_id 对应的 video 不存在，但 submission.task_id 对应的 video 存在！")
        print("-" * 40)

if __name__ == "__main__":
    uid = "a00233b0-dede-4a1f-84e4-9b4439d02fe4"
    verify_data(uid)
