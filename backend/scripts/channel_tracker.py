#!/usr/bin/env python3
import os
import subprocess
import json
import logging
from db import get_db

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

supabase = get_db()

def get_latest_video_id(channel_handle):
    """Use yt-dlp to get the latest public, non-live video ID from a channel handle."""
    if not channel_handle:
        return None
    
    # Prefix with @ if not present
    if not channel_handle.startswith('@') and not channel_handle.startswith('UC'):
        channel_handle = '@' + channel_handle
        
    url = f"https://www.youtube.com/{channel_handle}/videos"
    
    # Use match-filter to skip live and non-public (members) videos
    # We check top 5 to find the latest valid one
    cmd = [
        "yt-dlp", 
        "--get-id", 
        "--playlist-items", "5", 
        "--match-filter", "!is_live & availability=public",
        "--max-downloads", "1",
        "--quiet",
        "--js-runtimes", "node",
        url
    ]
    
    # Add cookies if available
    cookies_path = os.environ.get("YOUTUBE_COOKIES_PATH")
    if cookies_path and os.path.exists(cookies_path):
        cmd.extend(["--cookies", cookies_path])
    elif os.path.exists("youtube_cookies.txt"):
        cmd.extend(["--cookies", "youtube_cookies.txt"])
        
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        video_id = result.stdout.strip()
        if video_id:
            # Take the first line in case of multiple IDs or extra output
            return video_id.split('\n')[0].strip()
        
        # If no video_id found, check return code
        if result.returncode != 0:
            if not result.stdout.strip():
                 logger.info(f"No matching public videos found for {channel_handle} in top 5 items.")
            else:
                logger.error(f"Error fetching latest video for {channel_handle}: {result.stderr or result.stdout}")
    except Exception as e:
        logger.error(f"Unexpected error for {channel_handle}: {e}")
    
    return None


def get_video_metadata(video_id):
    """Fetch video metadata (title, thumbnail, channel info) using yt-dlp."""
    if not video_id:
        return None
    
    url = f"https://www.youtube.com/watch?v={video_id}"
    cmd = [
        "yt-dlp", 
        "--dump-json", 
        "--no-download",
        "--no-playlist",
        "--js-runtimes", "node",
        url
    ]
    
    # Add cookies if available
    cookies_path = os.environ.get("YOUTUBE_COOKIES_PATH")
    if cookies_path and os.path.exists(cookies_path):
        cmd.extend(["--cookies", cookies_path])
    elif os.path.exists("youtube_cookies.txt"):
        cmd.extend(["--cookies", "youtube_cookies.txt"])
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(result.stdout)
        
        return {
            "title": data.get("title", "Unknown Title"),
            "thumbnail": data.get("thumbnail"),
            "channel_name": data.get("channel") or data.get("uploader"),
            "channel_id": data.get("channel_id") or data.get("uploader_id"),
            "duration": data.get("duration"),
            "view_count": data.get("view_count", 0),
        }
    except subprocess.CalledProcessError as e:
        logger.error(f"Error fetching metadata for {video_id}: {e.stderr}")
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing metadata JSON for {video_id}: {e}")
    except Exception as e:
        logger.error(f"Unexpected error fetching metadata for {video_id}: {e}")
    
    return None

def retry_failed_videos():
    """Find failed videos and re-queue them if they haven't reached the retry limit."""
    if not supabase:
        return 0
    
    logger.info("Checking for failed videos to retry...")
    retried_count = 0
    
    try:
        # Fetch failed videos. We'll check retry_count in Python as JSONB filtering can be tricky
        response = supabase.table("videos") \
            .select("id, title, report_data") \
            .eq("status", "failed") \
            .execute()
        
        for video in response.data:
            vid_id = video["id"]
            report_data = video.get("report_data") or {}
            retry_count = report_data.get("retry_count", 0)
            
            if retry_count < 3:
                logger.info(f"Retrying video {vid_id} (Attempt {retry_count + 1}/3)...")
                
                # Update status to queued and increment retry_count
                report_data["retry_count"] = retry_count + 1
                
                supabase.table("videos").update({
                    "status": "queued",
                    "report_data": report_data
                }).eq("id", vid_id).execute()
                
                # Update local status file if it exists
                results_dir = "results"
                status_file = f"{results_dir}/{vid_id}_status.json"
                if os.path.exists(status_file):
                    try:
                        with open(status_file, "w") as f:
                            json.dump({"status": "queued", "progress": 0, "retry_count": retry_count + 1}, f)
                    except Exception as e:
                        logger.warning(f"Failed to update local status file for {vid_id}: {e}")
                
                retried_count += 1
                
        if retried_count > 0:
            logger.info(f"Re-queued {retried_count} failed videos.")
            
    except Exception as e:
        logger.error(f"Error during failed videos retry: {e}")
        
    return retried_count

def main():
    if not supabase:
        logger.error("Supabase client not initialized. Exiting.")
        return

    logger.info("Starting channel tracking...")
    
    # 0. Retry previously failed videos
    retried_count = retry_failed_videos()
    
    # 0.1 获取需要跳过的频道（track_new_videos=FALSE）
    skip_channels = set()
    try:
        skip_res = supabase.table("channel_settings") \
            .select("channel_id") \
            .eq("track_new_videos", False) \
            .execute()
        skip_channels = {c["channel_id"] for c in skip_res.data}
        if skip_channels:
            logger.info(f"Skipping {len(skip_channels)} channels with tracking disabled.")
    except Exception as e:
        # channel_settings 表可能不存在
        logger.warning(f"Failed to fetch channel_settings (table may not exist): {e}")

    # 1. Fetch unique channel IDs from the videos table
    try:
        # We look into report_data->channel_id which stores the handle/id we extracted previously
        response = supabase.table("videos").select("report_data->channel_id").not_.is_("report_data->channel_id", "null").execute()
        
        channel_ids = set()
        for v in response.data:
            c_id = v.get("channel_id")
            if c_id and c_id not in skip_channels:
                channel_ids.add(c_id)
        
        logger.info(f"Found {len(channel_ids)} unique channels to track.")
    except Exception as e:
        logger.error(f"Failed to fetch channel IDs: {e}")
        return

    # 2. For each channel, find the latest video
    new_tasks_count = 0
    for channel_id in channel_ids:
        logger.info(f"Checking channel: {channel_id}")
        latest_vid = get_latest_video_id(channel_id)
        
        if not latest_vid:
            continue
            
        # 3. Check if this video already exists in our database
        try:
            check_res = supabase.table("videos").select("id").eq("id", latest_vid).execute()
            if not check_res.data:
                # 4. New video found! Fetch metadata first
                logger.info(f"New video found: {latest_vid} for channel {channel_id}. Fetching metadata...")
                
                metadata = get_video_metadata(latest_vid)
                if not metadata:
                    logger.error(f"Failed to fetch metadata for {latest_vid}. Skipping.")
                    continue
                
                logger.info(f"Got metadata: {metadata.get('title')}")
                
                # Insert with required fields
                supabase.table("videos").insert({
                    "id": latest_vid,
                    "title": metadata["title"],
                    "thumbnail": metadata.get("thumbnail"),
                    "status": "queued",
                    "report_data": {
                        "channel_id": metadata.get("channel_id"),
                        "channel": metadata.get("channel_name"),
                        "duration": metadata.get("duration"),
                        "view_count": metadata.get("view_count"),
                        "source": "tracker"
                    }
                }).execute()
                
                # Also create a status file for immediate visibility in UI
                results_dir = "results"
                if not os.path.exists(results_dir):
                    os.makedirs(results_dir)
                
                with open(f"{results_dir}/{latest_vid}_status.json", "w") as f:
                    json.dump({"status": "queued", "progress": 0}, f)
                    
                new_tasks_count += 1
                logger.info(f"Successfully queued video: {latest_vid}")
            else:
                logger.info(f"Video {latest_vid} already exists. Skipping.")
        except Exception as e:
            logger.error(f"Error checking/inserting video {latest_vid}: {e}")

    total_added = retried_count + new_tasks_count
    logger.info(f"Channel tracking finished. Added {total_added} tasks to the queue ({retried_count} retries, {new_tasks_count} new).")

if __name__ == "__main__":
    main()
