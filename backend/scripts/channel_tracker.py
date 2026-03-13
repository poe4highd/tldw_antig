#!/usr/bin/env python3
import os
import sys
import subprocess
import json
import logging
import shutil
from db import get_db

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

supabase = get_db()

def _resolve_ytdlp_cmd():
    """解析 yt-dlp 调用命令，避免 systemd 环境 PATH 缺失导致找不到可执行文件。"""
    venv_ytdlp = os.path.join(os.path.dirname(sys.executable), "yt-dlp")
    if os.path.isfile(venv_ytdlp) and os.access(venv_ytdlp, os.X_OK):
        return [venv_ytdlp]

    ytdlp_in_path = shutil.which("yt-dlp")
    if ytdlp_in_path:
        return [ytdlp_in_path]

    # 最后回退到 python -m yt_dlp，尽量不依赖 PATH。
    return [sys.executable, "-m", "yt_dlp"]

def _resolve_cookies_path():
    """查找可用的 cookies 文件路径，不存在则返回 None。"""
    cookies_path = os.environ.get("YOUTUBE_COOKIES_PATH")
    if cookies_path and os.path.exists(cookies_path):
        return cookies_path
    if os.path.exists("youtube_cookies.txt"):
        return "youtube_cookies.txt"
    return None


def _build_channel_videos_url(channel_handle):
    """根据 @handle 或 UC... 频道 ID 构造正确的 videos 页 URL。"""
    if channel_handle.startswith("UC"):
        return f"https://www.youtube.com/channel/{channel_handle}/videos"
    if not channel_handle.startswith("@"):
        channel_handle = "@" + channel_handle
    return f"https://www.youtube.com/{channel_handle}/videos"


def _run_ytdlp_get_ids(cmd, channel_handle, cookies_path):
    """执行 yt-dlp 获取视频 ID 列表，带 cookies 失败时自动降级重试。"""
    # 第一次尝试：带 cookies（如果有）
    run_cmd = cmd[:]
    if cookies_path:
        run_cmd.extend(["--cookies", cookies_path])

    result = subprocess.run(run_cmd, capture_output=True, text=True)
    ids = [l.strip() for l in result.stdout.strip().split('\n') if l.strip()]
    if ids:
        return ids

    # 带 cookies 失败且 cookies 存在时，去掉 cookies 重试
    if cookies_path and result.returncode != 0:
        logger.info(f"Cookies 请求失败 (rc={result.returncode})，去掉 cookies 重试 {channel_handle}...")
        result = subprocess.run(cmd, capture_output=True, text=True)
        ids = [l.strip() for l in result.stdout.strip().split('\n') if l.strip()]
        if ids:
            return ids

    # 仍然没有结果
    if result.returncode != 0 and not result.stdout.strip():
        logger.info(f"No matching public videos found for {channel_handle} in top 5 items.")
    elif result.returncode != 0:
        logger.error(f"Error fetching latest video for {channel_handle}: {result.stderr or result.stdout}")

    return []


def get_latest_video_ids(channel_handle):
    """Use yt-dlp to get the latest 5 public, non-live video IDs from a channel handle."""
    if not channel_handle:
        return []

    url = _build_channel_videos_url(channel_handle)

    cmd = _resolve_ytdlp_cmd() + [
        "--get-id",
        "--playlist-items", "1:5",
        "--match-filter", "!is_live & availability=public",
        "--quiet",
        url
    ]

    cookies_path = _resolve_cookies_path()

    try:
        return _run_ytdlp_get_ids(cmd, channel_handle, cookies_path)
    except Exception as e:
        logger.error(f"Unexpected error for {channel_handle}: {e}")

    return []


def get_video_metadata(video_id):
    """Fetch video metadata (title, thumbnail, channel info) using yt-dlp."""
    if not video_id:
        return None

    url = f"https://www.youtube.com/watch?v={video_id}"
    cmd = _resolve_ytdlp_cmd() + [
        "--dump-json",
        "--no-download",
        "--no-playlist",
        url
    ]

    cookies_path = _resolve_cookies_path()

    def _try_fetch(use_cookies):
        run_cmd = cmd[:]
        if use_cookies and cookies_path:
            run_cmd.extend(["--cookies", cookies_path])
        result = subprocess.run(run_cmd, capture_output=True, text=True, check=True)
        return json.loads(result.stdout)

    try:
        # 先带 cookies 尝试
        data = _try_fetch(use_cookies=True)
    except (subprocess.CalledProcessError, json.JSONDecodeError):
        if cookies_path:
            logger.info(f"Cookies 元数据请求失败，去掉 cookies 重试 {video_id}...")
            try:
                data = _try_fetch(use_cookies=False)
            except subprocess.CalledProcessError as e:
                logger.error(f"Error fetching metadata for {video_id}: {e.stderr}")
                return None
            except json.JSONDecodeError as e:
                logger.error(f"Error parsing metadata JSON for {video_id}: {e}")
                return None
        else:
            return None
    except Exception as e:
        logger.error(f"Unexpected error fetching metadata for {video_id}: {e}")
        return None

    return {
        "title": data.get("title", "Unknown Title"),
        "thumbnail": data.get("thumbnail"),
        "channel_name": data.get("channel") or data.get("uploader"),
        "channel_id": data.get("channel_id") or data.get("uploader_id"),
        "duration": data.get("duration"),
        "view_count": data.get("view_count", 0),
    }

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
        sys.exit(1)

    logger.info("Starting channel tracking...")
    
    # 0. Retry previously failed videos
    retried_count = retry_failed_videos()
    
    # 1. Fetch channels with tracking enabled (track_new_videos=TRUE)
    try:
        response = supabase.table("channel_settings") \
            .select("channel_id") \
            .eq("track_new_videos", True) \
            .execute()
        
        channel_ids = {c["channel_id"] for c in response.data}
        logger.info(f"Found {len(channel_ids)} channels with tracking enabled.")
    except Exception as e:
        logger.error(f"Failed to fetch tracked channel IDs: {e}")
        sys.exit(1)

    # 2. For each channel, find the latest videos (up to 5)
    new_tasks_count = 0
    for channel_id in channel_ids:
        logger.info(f"Checking channel: {channel_id}")
        latest_vids = get_latest_video_ids(channel_id)

        if not latest_vids:
            continue

        for latest_vid in latest_vids:
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
                            "channel_name": metadata.get("channel_name"),
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
    # 同时输出到 stdout 供 main.py 解析（logging 默认输出到 stderr）
    print(f"Added {total_added} tasks to the queue ({retried_count} retries, {new_tasks_count} new).")

if __name__ == "__main__":
    main()
