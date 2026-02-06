import os
import json
import asyncio
import yt_dlp
from db import get_db

async def backfill_avatars():
    supabase = get_db()
    if not supabase:
        print("Supabase client not initialized.")
        return

    # Fetch all YouTube videos
    response = supabase.table("videos").select("id, title, report_data").execute()
    
    videos = response.data
    total = len(videos)
    updated = 0
    
    # We want to keep channel info to avoid redundant requests
    channel_cache = {}

    for i, video in enumerate(videos):
        video_id = video['id']
        # YouTube ID is usually 11 chars
        if len(video_id) != 11 or video_id.startswith("up_"):
            continue
            
        report_data = video.get('report_data', {})
        if report_data.get('channel_avatar'):
            print(f"[{i+1}/{total}] Skipping {video_id}, already has avatar.")
            continue
            
        print(f"[{i+1}/{total}] Processing {video_id} - {video['title']}...")
        
        # We need the channel_url. If not in report_data, we might need to fetch video info first
        channel_id = report_data.get('channel_id')
        channel_url = None
        
        if channel_id:
            channel_url = f"https://www.youtube.com/channel/{channel_id}"
        else:
            # Fetch video info to get channel_url
            try:
                with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
                    info = ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=False)
                    channel_url = info.get('uploader_url') or info.get('channel_url')
                    if not report_data.get('channel'):
                        report_data['channel'] = info.get('uploader') or info.get('channel')
                    if not report_data.get('channel_id'):
                        report_data['channel_id'] = info.get('uploader_id') or info.get('channel_id')
            except Exception as e:
                print(f"  Error fetching video info: {e}")
                continue

        if not channel_url:
            print(f"  Could not find channel URL for {video_id}")
            continue

        # Get avatar from cache or fetch
        if channel_url in channel_cache:
            avatar = channel_cache[channel_url]
        else:
            try:
                with yt_dlp.YoutubeDL({'quiet': True, 'extract_flat': True}) as ydl:
                    chan_info = ydl.extract_info(channel_url, download=False)
                    avatar = chan_info['thumbnails'][-1]['url'] if chan_info.get('thumbnails') else None
                    channel_cache[channel_url] = avatar
            except Exception as e:
                print(f"  Error fetching channel info: {e}")
                avatar = None

        if avatar:
            report_data['channel_avatar'] = avatar
            # Update Supabase
            try:
                supabase.table("videos").update({"report_data": report_data}).eq("id", video_id).execute()
                print(f"  Updated avatar for {video['title']}")
                updated += 1
            except Exception as e:
                print(f"  Failed to update Supabase: {e}")
        
    print(f"Finished backfill. Total YouTube videos processed: {total}, Updated: {updated}")

if __name__ == "__main__":
    asyncio.run(backfill_avatars())
