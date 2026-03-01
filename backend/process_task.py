import os
import sys
import json
import re
import hashlib
import time
import subprocess
import shutil

# 确保 ffmpeg 可用（systemd 环境 PATH 可能不含 anaconda）
if not shutil.which('ffmpeg'):
    for candidate in ['/home/xs/anaconda3/bin', '/usr/local/bin']:
        if os.path.isfile(os.path.join(candidate, 'ffmpeg')):
            os.environ['PATH'] = candidate + ':' + os.environ.get('PATH', '')
            break

from downloader import download_audio
from processor import split_into_paragraphs, get_youtube_thumbnail_url
from db import get_db

supabase = get_db()
RESULTS_DIR = "results"
DOWNLOADS_DIR = "downloads"

def save_status(task_id, status, progress, eta=None):
    if not os.path.exists(RESULTS_DIR):
        os.makedirs(RESULTS_DIR)
    with open(f"{RESULTS_DIR}/{task_id}_status.json", "w") as f:
        json.dump({"status": status, "progress": progress, "eta": eta}, f)

def process_video_task(task_id):
    print(f"--- [Process Task] Starting task: {task_id} ---")
    
    # 1. Fetch task details from Supabase or local status
    url = None
    local_file = None
    title = "Unknown Title"
    thumbnail = None
    mode = "local"
    user_id = None
    is_public = True
    
    if supabase:
        try:
            res = supabase.table("videos").select("*").eq("id", task_id).execute()
            if res.data:
                video = res.data[0]
                # We'll store temporary info in report_data during queued state if needed
                temp_data = video.get("report_data", {}) or {}
                url = temp_data.get("url")
                local_file = video.get("media_path")
                # Handle cases where media_path is just a filename
                if local_file and not os.path.isabs(local_file) and not local_file.startswith(DOWNLOADS_DIR):
                    local_file = os.path.join(DOWNLOADS_DIR, local_file)
                
                title = video.get("title", title)
                mode = temp_data.get("mode", "cloud")
                user_id = video.get("user_id") or temp_data.get("user_id")
                is_public = video.get("is_public", temp_data.get("is_public", True))
        except Exception as e:
            print(f"[Process Task] Error fetching from Supabase: {e}")

    # Fallback to local status if Supabase didn't have it or failed
    if not url and not local_file:
        status_file = f"{RESULTS_DIR}/{task_id}_status.json"
        if os.path.exists(status_file):
            with open(status_file, "r") as f:
                data = json.load(f)
                url = data.get("url")
                local_file = data.get("local_file")
                title = data.get("title", title)
                mode = data.get("mode", "cloud")
                user_id = data.get("user_id")
                is_public = data.get("is_public", True)

    # If the URL is from our own domain, it's likely a mis-submitted result page.
    # We should fallback to a standard YouTube URL if the task_id looks like a YouTube ID.
    if url and "read-tube.com" in url and len(task_id) == 11:
        print(f"--- [Process Task] URL {url} is local result page. Falling back to YouTube for ID {task_id} ---")
        url = f"https://www.youtube.com/watch?v={task_id}"

    if not url and not local_file and len(task_id) == 11:
        # Heuristic: if it's 11 chars, it's likely a YouTube ID
        url = f"https://www.youtube.com/watch?v={task_id}"

    if not url and not local_file:
        error_msg = f"无法找到任务 {task_id} 的 URL 或本地文件"
        print(f"--- [Process Task] Error: {error_msg} ---")
        # 写入错误文件以便前端展示和调试
        with open(f"{RESULTS_DIR}/{task_id}_error.json", "w") as ef:
            json.dump({"error": error_msg}, ef, ensure_ascii=False)
        save_status(task_id, "failed", 100)
        if supabase:
            try:
                supabase.table("videos").update({"status": "failed"}).eq("id", task_id).execute()
            except Exception as e:
                print(f"[Process Task] Failed to update Supabase on abort: {e}")
        return False

    try:
        video_id = ""
        description = ""
        if url:
            id_match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11})", url)
            if id_match:
                video_id = id_match.group(1)
            else:
                video_id = hashlib.md5(url.encode()).hexdigest()[:11]
        elif local_file:
            video_id = os.path.splitext(os.path.basename(local_file))[0]

        # 1. Media Retrieval
        file_path = local_file
        if url:
            # Check cache
            possible_exts = ["m4a", "mp3", "mp4", "webm"]
            for ext in possible_exts:
                p = f"{DOWNLOADS_DIR}/{video_id}.{ext}"
                if os.path.exists(p):
                    file_path = p
                    break
            
            # Metadata Retrieval
            import yt_dlp
            ydl_opts_meta = {
                'quiet': True,
                'no_warnings': True,
                'nocheckcertificate': True,
            }
            
            channel = None
            channel_id = None
            channel_avatar = None
            channel_url = None

            try:
                with yt_dlp.YoutubeDL(ydl_opts_meta) as ydl:
                    info = ydl.extract_info(url, download=False)
                    title = info.get('title', title or 'Unknown Title')
                    thumbnail = info.get('thumbnail', thumbnail)
                    description = info.get('description', '')
                    channel = info.get('uploader') or info.get('channel') or info.get('uploader_id')
                    channel_id = info.get('uploader_id') or info.get('channel_id')
                    channel_url = info.get('uploader_url') or info.get('channel_url')
                    
                    if not channel:
                        # Avoid falling back to ID if name extraction failed
                        pass

                # Avatar block
                if channel_url:
                    try:
                        with yt_dlp.YoutubeDL({'quiet': True, 'extract_flat': True}) as ydl_chan:
                            chan_info = ydl_chan.extract_info(channel_url, download=False)
                            if chan_info and chan_info.get('thumbnails'):
                                channel_avatar = chan_info['thumbnails'][-1]['url']
                    except Exception as ce:
                        print(f"Failed to fetch channel avatar for {channel_url}: {ce}")
            except Exception as e:
                print(f"Metadata extraction failed for {url}: {e}")
                title = title or "Unknown Title"
                thumbnail = thumbnail or get_youtube_thumbnail_url(url)

            if not file_path:
                def on_download_progress(p):
                    current_p = 20 + (p * 0.2)
                    save_status(task_id, "downloading", int(current_p), eta=35)

                save_status(task_id, "scheduling_download", 20, eta=40)
                file_path, _, _ = download_audio(url, output_path=DOWNLOADS_DIR, progress_callback=on_download_progress)
        
        # 1.5 Audio Extraction (for uploaded videos)
        transcription_source_path = file_path
        ext = os.path.splitext(file_path)[1].lower()
        if ext in [".mp4", ".mov", ".avi", ".webm", ".mkv"]:
            base_path = os.path.splitext(file_path)[0]
            extracted_audio_path = base_path + ".mp3"
            extracted_thumb_path = base_path + ".jpg"

            # Audio extraction
            if not os.path.exists(extracted_audio_path):
                save_status(task_id, "extracting_audio", 45, eta=10)
                print(f"--- Extracting audio from {file_path} to {extracted_audio_path} ---")
                try:
                    subprocess.run(
                        ["ffmpeg", "-i", file_path, "-q:a", "0", "-map", "a", extracted_audio_path, "-y"],
                        check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                    )
                    transcription_source_path = extracted_audio_path
                except Exception as e:
                    print(f"Audio extraction failed: {e}. Trying to transcribe video directly...")
            else:
                transcription_source_path = extracted_audio_path
            
            # Thumbnail extraction
            if not os.path.exists(extracted_thumb_path):
                print(f"--- Extracting thumbnail from {file_path} to {extracted_thumb_path} ---")
                try:
                    subprocess.run(
                        ["ffmpeg", "-i", file_path, "-ss", "00:00:01", "-vframes", "1", extracted_thumb_path, "-y"],
                        check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                    )
                    thumbnail = os.path.basename(extracted_thumb_path)
                except Exception as e:
                    print(f"Thumbnail extraction failed: {e}")
            else:
                thumbnail = os.path.basename(extracted_thumb_path)

            # Cleanup original video
            if os.path.exists(extracted_audio_path) and file_path != extracted_audio_path:
                try:
                    print(f"--- Automatic Cleanup: Removing original video file: {file_path} ---")
                    os.remove(file_path)
                except Exception as e:
                    print(f"Failed to remove original video: {e}")

        # 2. Start Worker Process
        worker_script = os.path.join(os.path.dirname(__file__), "worker.py")
        
        cmd = [
            sys.executable, worker_script,
            task_id, mode,
            "--file", transcription_source_path,
            "--title", title or "Unknown",
            "--description", description,
            "--model", "large-v3-turbo"
        ]
        
        if video_id:
            cmd.extend(["--video-id", video_id])
        
        print(f"--- 启动 Worker 进程: {' '.join(cmd)} ---")
        
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=os.path.dirname(__file__)
        )
        
        for line in process.stdout:
            print(f"[Worker] {line.rstrip()}")
        
        return_code = process.wait()
        
        if return_code != 0:
            stderr_output = process.stderr.read()
            print(f"[Worker] 错误输出:\n{stderr_output}", file=sys.stderr)
            # 若 worker 崩溃前未写 _error.json（OOM/import error），用 stderr 兜底
            error_file = f"{RESULTS_DIR}/{task_id}_error.json"
            if not os.path.exists(error_file):
                with open(error_file, "w") as f:
                    json.dump({
                        "error": f"Worker 进程失败 (exit code: {return_code})",
                        "traceback": stderr_output
                    }, f, ensure_ascii=False)
            raise Exception(f"Worker 进程失败 (exit code: {return_code})")
        
        print(f"--- Worker 进程成功完成 ---")
        
        # 3. Finalize results
        result_file = f"{RESULTS_DIR}/{task_id}.json"
        with open(result_file, "r", encoding="utf-8") as f:
            result = json.load(f)
        
        result["url"] = url or "Uploaded File"
        result["thumbnail"] = thumbnail
        result["media_path"] = os.path.basename(file_path)
        result["user_id"] = user_id
        result["channel"] = channel
        result["channel_id"] = channel_id
        result["channel_avatar"] = channel_avatar
        
        with open(result_file, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
            
        # 4. Save to Supabase
        if supabase:
            try:
                video_data = {
                    "id": video_id if url else task_id,
                    "title": result["title"],
                    "thumbnail": thumbnail,
                    "media_path": os.path.basename(file_path),
                    "report_data": {
                        "paragraphs": result["paragraphs"],
                        "raw_subtitles": result["raw_subtitles"],
                        "summary": result.get("summary"),
                        "keywords": result.get("keywords"),
                        "channel": result.get("channel"),
                        "channel_id": result.get("channel_id"),
                        "channel_avatar": result.get("channel_avatar")
                    },
                    "usage": result["usage"],
                    "user_id": user_id,
                    "is_public": is_public,
                    "status": "completed"
                }
                print(f"--- [Process Task] Saving results to Supabase for video {video_data['id']} ---")
                res = supabase.table("videos").upsert(video_data).execute()
                if not res.data:
                    print(f"[Process Task] Warning: Upsert returned empty data for {video_data['id']}")
                else:
                    print(f"Successfully saved to Supabase: {video_data['id']}")
                
                # Keywords sync
                keywords = result.get("keywords", [])
                if keywords:
                    print(f"--- [Process Task] Syncing {len(keywords)} keywords ---")
                    for kw in keywords:
                        kw_clean = kw.strip()
                        if not kw_clean: continue
                        try:
                            kw_res = supabase.table("keywords").select("id, count").eq("name", kw_clean).execute()
                            if kw_res.data:
                                kw_id = kw_res.data[0]["id"]
                                new_count = (kw_res.data[0]["count"] or 0) + 1
                                supabase.table("keywords").update({"count": new_count}).eq("id", kw_id).execute()
                            else:
                                new_kw = supabase.table("keywords").insert({"name": kw_clean, "count": 1}).execute()
                                if new_kw.data: kw_id = new_kw.data[0]["id"]
                                else: continue
                            supabase.table("video_keywords").upsert({"video_id": video_data["id"], "keyword_id": kw_id}).execute()
                        except Exception as kw_e:
                            print(f"[Process Task] Error syncing keyword '{kw_clean}': {kw_e}")

                if user_id:
                    # submissions table should already have a link if it was created during /process
                    # but we'll try to ensure it exists
                    print(f"--- [Process Task] Syncing submission for user {user_id} ---")
                    try:
                        supabase.table("submissions").insert({
                            "user_id": user_id,
                            "video_id": video_data["id"],
                            "task_id": task_id
                        }).execute()
                    except Exception as sub_e:
                        print(f"Submission sync from task failed (expected if already exists): {sub_e}")
                        # Ensure the correct video_id is linked to the task_id
                        try:
                            supabase.table("submissions").update({
                                "video_id": video_data["id"]
                            }).eq("task_id", task_id).execute()
                        except Exception as up_e:
                             print(f"Failed to update submission: {up_e}")

            except Exception as e:
                print(f"CRITICAL: Failed to save to Supabase: {e}")
                import traceback
                traceback.print_exc()
                # If Supabase sync fails, we DO NOT mark it as completed in the results file if we want to retry,
                # but here the task is physically "done", so we keep it completed locally but log the failure.
        
        save_status(task_id, "completed", 100)
        return True

    except Exception as e:
        import traceback
        traceback.print_exc()
        error_file = f"{RESULTS_DIR}/{task_id}_error.json"
        # 检查 worker 是否已写入含 traceback 的错误文件，避免覆盖
        existing_has_traceback = False
        try:
            with open(error_file) as f:
                existing_has_traceback = "traceback" in json.load(f)
        except Exception:
            pass
        if not existing_has_traceback:
            with open(error_file, "w") as f:
                json.dump({"error": str(e), "traceback": traceback.format_exc()}, f, ensure_ascii=False)
        save_status(task_id, "failed", 100)
        if supabase:
            try:
                supabase.table("videos").update({"status": "failed"}).eq("id", task_id).execute()
            except: pass
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 process_task.py <task_id>")
        sys.exit(1)
    
    tid = sys.argv[1]
    success = process_video_task(tid)
    sys.exit(0 if success else 1)
