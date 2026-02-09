import os
import requests
import subprocess
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY")
DOWNLOADS_DIR = "downloads"

if not os.path.exists(DOWNLOADS_DIR):
    os.makedirs(DOWNLOADS_DIR)

def fix_thumbnails():
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("Error: Supabase credentials not found.")
        return

    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    # 查找所有缩略图为外部 URL 的已完成视频
    res = supabase.table("videos").select("id, thumbnail") \
        .eq("status", "completed") \
        .ilike("thumbnail", "http%") \
        .execute()
    
    vids = res.data
    print(f"Found {len(vids)} videos to fix.")

    for v in vids:
        video_id = v['id']
        url = v['thumbnail']
        local_filename = f"{video_id}.jpg"
        local_path = os.path.join(DOWNLOADS_DIR, local_filename)
        
        print(f"Fixing {video_id}...")
        
        try:
            # 下载图片
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                temp_path = os.path.join(DOWNLOADS_DIR, f"temp_{video_id}")
                with open(temp_path, "wb") as f:
                    f.write(response.content)
                
                # 使用 ffmpeg 转换为标准 jpg
                subprocess.run(
                    ["ffmpeg", "-i", temp_path, "-vframes", "1", local_path, "-y"],
                    check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                )
                
                os.remove(temp_path)
                
                # 更新数据库
                supabase.table("videos").update({"thumbnail": local_filename}).eq("id", video_id).execute()
                print(f"Successfully fixed {video_id}")
            else:
                print(f"Failed to download thumbnail for {video_id}: {response.status_code}")
        except Exception as e:
            print(f"Error fixing {video_id}: {e}")

if __name__ == "__main__":
    fix_thumbnails()
