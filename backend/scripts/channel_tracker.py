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
    """Use yt-dlp to get the latest video ID from a channel handle."""
    if not channel_handle:
        return None
    
    # Prefix with @ if not present
    if not channel_handle.startswith('@') and not channel_handle.startswith('UC'):
        channel_handle = '@' + channel_handle
        
    url = f"https://www.youtube.com/{channel_handle}/videos"
    cmd = ["yt-dlp", "--get-id", "--playlist-items", "1", url]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        video_id = result.stdout.strip()
        # Handle cases where multiple IDs might be returned or output has trash
        if video_id:
            # Take the first line in case of multiple IDs or extra output
            video_id = video_id.split('\n')[0].strip()
            return video_id
    except subprocess.CalledProcessError as e:
        logger.error(f"Error fetching latest video for {channel_handle}: {e.stderr}")
    except Exception as e:
        logger.error(f"Unexpected error for {channel_handle}: {e}")
    
    return None

def main():
    if not supabase:
        logger.error("Supabase client not initialized. Exiting.")
        return

    logger.info("Starting channel tracking...")

    # 1. Fetch unique channel IDs from the videos table
    try:
        # We look into report_data->channel_id which stores the handle/id we extracted previously
        response = supabase.table("videos").select("report_data->channel_id").not_.is_("report_data->channel_id", "null").execute()
        
        channel_ids = set()
        for v in response.data:
            c_id = v.get("channel_id")
            if c_id:
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
                # 4. New video found! Add to queue
                logger.info(f"New video found: {latest_vid} for channel {channel_id}. Adding to queue.")
                
                # Insert minimal record, scheduler will pick it up
                supabase.table("videos").insert({
                    "id": latest_vid,
                    "status": "queued"
                }).execute()
                
                # Also create a status file for immediate visibility in UI
                results_dir = "results"
                if not os.path.exists(results_dir):
                    os.makedirs(results_dir)
                
                with open(f"{results_dir}/{latest_vid}_status.json", "w") as f:
                    json.dump({"status": "queued", "progress": 0}, f)
                    
                new_tasks_count += 1
            else:
                logger.info(f"Video {latest_vid} already exists. Skipping.")
        except Exception as e:
            logger.error(f"Error checking/inserting video {latest_vid}: {e}")

    logger.info(f"Channel tracking finished. Added {new_tasks_count} new tasks to the queue.")

if __name__ == "__main__":
    main()
