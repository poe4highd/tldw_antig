import os
import requests
import subprocess
import time
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY")
DOWNLOADS_DIR = "downloads"

if not os.path.exists(DOWNLOADS_DIR):
    os.makedirs(DOWNLOADS_DIR)

def download_and_convert(url, local_path):
    """下载并使用 ffmpeg 转换图片"""
    temp_path = f"{local_path}.temp"
    try:
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            with open(temp_path, "wb") as f:
                f.write(response.content)
            
            # 使用 ffmpeg 转换为标准 jpg
            subprocess.run(
                ["ffmpeg", "-i", temp_path, "-vframes", "1", local_path, "-y"],
                check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
            
            if os.path.exists(temp_path):
                os.remove(temp_path)
            return True
        else:
            print(f"  [ERROR] HTTP {response.status_code} for {url}")
    except Exception as e:
        print(f"  [ERROR] {e}")
        if os.path.exists(temp_path):
            os.remove(temp_path)
    return False

def fix_thumbnails():
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("Error: Supabase credentials not found.")
        return

    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    # 查找所有已完成的视频
    res = supabase.table("videos").select("id, thumbnail, status").eq("status", "completed").execute()
    vids = res.data
    print(f"Found {len(vids)} completed videos to check.")

    fixed_count = 0
    missing_count = 0

    for v in vids:
        video_id = v['id']
        thumb = v.get('thumbnail')
        
        if not thumb:
            print(f"Skipping {video_id}: No thumbnail value")
            continue
            
        if thumb.startswith("#"):
            print(f"Skipping {video_id}: Hex color placeholder ({thumb})")
            continue

        local_filename = f"{video_id}.jpg" if not thumb.endswith(".jpg") else thumb
        local_path = os.path.join(DOWNLOADS_DIR, local_filename)
        
        needs_fix = False
        source_url = None

        if thumb.startswith("http"):
            print(f"Checking {video_id}: Remote URL found ({thumb})")
            needs_fix = True
            source_url = thumb
        elif not os.path.exists(local_path):
            print(f"Checking {video_id}: Local file missing ({local_path})")
            needs_fix = True
            # Build YT thumbnail URL as fallback
            if len(video_id) == 11:
                source_url = f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"
            else:
                print(f"  [CANNOT FIX] Missing local file for non-youtube ID: {video_id}")
                continue

        if needs_fix and source_url:
            print(f"  Fixing {video_id} using {source_url}...")
            # Try maxresdefault, then mqdefault
            success = download_and_convert(source_url, local_path)
            if not success and "maxresdefault" in source_url:
                alt_url = source_url.replace("maxresdefault", "mqdefault")
                print(f"  Trying fallback: {alt_url}")
                success = download_and_convert(alt_url, local_path)
            
            if success:
                # 更新数据库
                supabase.table("videos").update({"thumbnail": local_filename}).eq("id", video_id).execute()
                print(f"  [SUCCESS] {video_id} fixed.")
                fixed_count += 1
            else:
                print(f"  [FAILED] {video_id} could not be fixed.")
                missing_count += 1
            
            # Rate limiting
            time.sleep(0.5)

    print(f"\nFinished. Fixed: {fixed_count}, Remaining Missing: {missing_count}")

if __name__ == "__main__":
    fix_thumbnails()
