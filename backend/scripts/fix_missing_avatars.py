import os
import json
import subprocess
from db import get_db

supabase = get_db()

def get_channel_avatar(channel_id):
    """Use yt-dlp to get the channel avatar URL."""
    if not channel_id:
        return None
    
    # Construct channel URL
    if channel_id.startswith('UC'):
        url = f"https://www.youtube.com/channel/{channel_id}"
    else:
        url = f"https://www.youtube.com/{channel_id}"
        
    cmd = ["yt-dlp", "--quiet", "--extract-flat", "--dump-json", url]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            data = json.loads(result.stdout)
            thumbnails = data.get('thumbnails', [])
            if thumbnails:
                # Return the highest quality one
                return thumbnails[-1]['url']
    except Exception as e:
        print(f"Error fetching avatar for {channel_id}: {e}")
    
    return None

def main():
    if not supabase:
        print("Supabase not connected.")
        return

    print("Fetching completed videos with missing avatars...")
    res = supabase.table("videos").select("id, report_data").eq("status", "completed").execute()
    
    videos_to_fix = [v for v in res.data if not (v.get("report_data") or {}).get("channel_avatar")]
    print(f"Found {len(videos_to_fix)} videos to fix.")

    for i, video in enumerate(videos_to_fix):
        vid_id = video["id"]
        rd = video.get("report_data") or {}
        channel_id = rd.get("channel_id")
        
        # If channel_id is missing but it's a YouTube ID, try to fetch metadata first
        if not channel_id and len(vid_id) == 11:
            print(f"[{i+1}/{len(videos_to_fix)}] fetching missing channel_id for video {vid_id}...")
            cmd_meta = ["yt-dlp", "--quiet", "--dump-json", "--no-download", f"https://www.youtube.com/watch?v={vid_id}"]
            try:
                res_meta = subprocess.run(cmd_meta, capture_output=True, text=True, timeout=30)
                if res_meta.returncode == 0:
                    meta_data = json.loads(res_meta.stdout)
                    channel_id = meta_data.get('channel_id') or meta_data.get('uploader_id')
                    if channel_id:
                        rd['channel_id'] = channel_id
                        print(f"Found channel_id: {channel_id}")
            except Exception as e:
                print(f"Metadata fetch failed for {vid_id}: {e}")

        if not channel_id:
            print(f"[{i+1}/{len(videos_to_fix)}] Skipping {vid_id}: No channel_id found.")
            continue
            
        print(f"[{i+1}/{len(videos_to_fix)}] Fixing avatar for video {vid_id} (Channel: {channel_id})...")
        avatar_url = get_channel_avatar(channel_id)
        
        if avatar_url:
            rd["channel_avatar"] = avatar_url
            try:
                supabase.table("videos").update({"report_data": rd}).eq("id", vid_id).execute()
                print(f"Successfully updated avatar for {vid_id}")
            except Exception as e:
                print(f"Failed to update database for {vid_id}: {e}")
        else:
            print(f"Could not retrieve avatar for channel {channel_id}")

if __name__ == "__main__":
    main()
