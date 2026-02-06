import os
import json
import asyncio
import yt_dlp
from db import get_db

async def backfill_info(force=False):
    supabase = get_db()
    if not supabase:
        print("Supabase client not initialized.")
        return

    # Fetch all YouTube videos
    response = supabase.table("videos").select("id, title, report_data").execute()
    
    videos = response.data
    total = len(videos)
    updated = 0
    
    # Cache for channel info to avoid redundant requests
    channel_cache = {}

    print(f"Starting deep backfill for {total} records...")

    for i, video in enumerate(videos):
        video_id = video['id']
        # YouTube ID is usually 11 chars
        if len(video_id) != 11 or video_id.startswith("up_"):
            continue
            
        report_data = video.get('report_data', {}).copy()
        orig_report_data = video.get('report_data', {}).copy()
        has_channel = report_data.get('channel')
        has_avatar = report_data.get('channel_avatar')
        
        if not force and has_channel and has_avatar:
            # print(f"[{i+1}/{total}] Skipping {video_id}, already has full info.")
            continue
            
        print(f"[{i+1}/{total}] Processing {video_id} - {video['title']}...")
        
        channel_id = report_data.get('channel_id')
        channel_name = report_data.get('channel')
        channel_avatar = report_data.get('channel_avatar')
        channel_url = None
        
        # 1. Try to get basic info if missing
        if not channel_name or not channel_id:
            try:
                print(f"  Fetching video metadata for {video_id}...")
                with yt_dlp.YoutubeDL({'quiet': True, 'no_warnings': True}) as ydl:
                    info = ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=False)
                    channel_name = info.get('uploader') or info.get('channel') or info.get('uploader_id')
                    channel_id = info.get('uploader_id') or info.get('channel_id')
                    channel_url = info.get('uploader_url') or info.get('channel_url')
                    
                    report_data['channel'] = channel_name
                    report_data['channel_id'] = channel_id
            except Exception as e:
                print(f"  Error fetching video info for {video_id}: {e}")
                
        # 2. Get Avatar if missing
        if not channel_avatar or force:
            if not channel_url and channel_id:
                if channel_id.startswith('UC'): # Standard channel ID
                    channel_url = f"https://www.youtube.com/channel/{channel_id}"
                else: # Handle @ handle
                    channel_url = f"https://www.youtube.com/{channel_id}"
            
            if channel_url:
                if channel_url in channel_cache:
                    channel_avatar = channel_cache[channel_url]
                else:
                    try:
                        print(f"  Fetching channel info for {channel_url}...")
                        with yt_dlp.YoutubeDL({'quiet': True, 'extract_flat': True}) as ydl_chan:
                            chan_info = ydl_chan.extract_info(channel_url, download=False)
                            channel_avatar = chan_info['thumbnails'][-1]['url'] if chan_info and chan_info.get('thumbnails') else None
                            channel_cache[channel_url] = channel_avatar
                    except Exception as e:
                        print(f"  Error fetching channel avatar: {e}")
                
                if channel_avatar:
                    report_data['channel_avatar'] = channel_avatar

        # 3. Update Supabase if anything changed
        if report_data.get('channel') != orig_report_data.get('channel') or \
           report_data.get('channel_avatar') != orig_report_data.get('channel_avatar'):
            try:
                supabase.table("videos").update({"report_data": report_data}).eq("id", video_id).execute()
                print(f"  -> SUCCESS: Updated info for {video_id}")
                updated += 1
            except Exception as e:
                print(f"  -> FAILED: Supabase update error: {e}")
        else:
            print(f"  -> No change for {video_id}")
        
    print(f"\nDeep backfill finished.")
    print(f"Processed: {total}")
    print(f"Updated: {updated}")

if __name__ == "__main__":
    import sys
    force_update = "--force" in sys.argv
    asyncio.run(backfill_info(force=force_update))
