import os
import sys
import json
import time
import asyncio
import re
import hashlib
import random
import shutil
from fastapi import FastAPI, BackgroundTasks, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import shutil
import hashlib
import random

from downloader import download_audio
from processor import split_into_paragraphs, get_youtube_thumbnail_url
from db import get_db

supabase = get_db()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://read-tube.com",
        "https://read-tube-git-main-poe4highds-projects.vercel.app", # Adjust if Vercel preview domain needed
        "*" # Keep * as fallback but be careful
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files for audio playback
app.mount("/media", StaticFiles(directory="downloads"), name="media")

DOWNLOADS_DIR = "downloads"
RESULTS_DIR = "results"
CACHE_DIR = "cache"
DEV_DOCS_DIR = os.path.join(os.path.dirname(__file__), "..", "dev_docs")

for d in [DOWNLOADS_DIR, RESULTS_DIR, CACHE_DIR]:
    if not os.path.exists(d):
        os.makedirs(d)

class ProcessRequest(BaseModel):
    url: str
    mode: str = "cloud"
    user_id: str = None

class CommentRequest(BaseModel):
    video_id: str
    content: str
    user_id: str = None
    parent_id: str = None

def save_status(task_id, status, progress, eta=None):
    with open(f"{RESULTS_DIR}/{task_id}_status.json", "w") as f:
        json.dump({"status": status, "progress": progress, "eta": eta}, f)

def background_process(task_id, mode, url=None, local_file=None, title=None, thumbnail=None, user_id=None):
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
                'headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Referer': 'https://www.youtube.com/',
                },
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
                    
                    if not channel and channel_id:
                        channel = channel_id

                # Separate block for avatar to avoid losing channel info if this fails
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
                    save_status(task_id, f"正在下载媒体文件... {p:.1f}%", int(current_p), eta=35)
                
                save_status(task_id, "开始调度下载任务...", 20, eta=40)
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
                save_status(task_id, "正在从视频中提取音频...", 45, eta=10)
                print(f"--- Extracting audio from {file_path} to {extracted_audio_path} ---")
                import subprocess
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
                import subprocess
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

            # Cleanup original video if audio was successfully extracted
            if os.path.exists(extracted_audio_path) and file_path != extracted_audio_path:
                try:
                    print(f"--- Automatic Cleanup: Removing original video file: {file_path} ---")
                    os.remove(file_path)
                except Exception as e:
                    print(f"Failed to remove original video: {e}")

        # 2. 启动独立的 Worker 进程执行转录
        import subprocess
        worker_script = os.path.join(os.path.dirname(__file__), "worker.py")
        
        cmd = [
            "python3", worker_script,
            task_id, mode,
            "--file", transcription_source_path,
            "--title", title or "Unknown",
            "--description", description,
            "--model", "large-v3-turbo"
        ]
        
        if video_id:
            cmd.extend(["--video-id", video_id])
        
        print(f"--- 启动 Worker 进程: {' '.join(cmd)} ---")
        
        # 启动 worker 并等待完成
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=os.path.dirname(__file__)
        )
        
        # 实时输出日志
        for line in process.stdout:
            print(f"[Worker] {line.rstrip()}")
        
        # 等待进程结束
        return_code = process.wait()
        
        if return_code != 0:
            stderr_output = process.stderr.read()
            print(f"[Worker] 错误输出:\n{stderr_output}", file=sys.stderr)
            raise Exception(f"Worker 进程失败 (exit code: {return_code})")
        
        print(f"--- Worker 进程成功完成 ---")
        
        # 3. 读取 Worker 生成的结果并补充元数据
        result_file = f"{RESULTS_DIR}/{task_id}.json"
        with open(result_file, "r", encoding="utf-8") as f:
            result = json.load(f)
        
        # 补充主进程才有的信息
        result["url"] = url or "Uploaded File"
        result["thumbnail"] = thumbnail
        result["media_path"] = os.path.basename(file_path)
        result["user_id"] = user_id
        result["channel"] = channel
        result["channel_id"] = channel_id
        result["channel_avatar"] = channel_avatar
        
        # 重新保存
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
                    "status": "completed"
                }
                supabase.table("videos").upsert(video_data).execute()
                print(f"Successfully saved to Supabase: {video_data['id']}")

                # 4.5 关键词关系持久化
                keywords = result.get("keywords", [])
                if keywords:
                    for kw in keywords:
                        kw_clean = kw.strip()
                        if not kw_clean: continue
                        
                        # 获取或创建关键词记录并增加计数
                        kw_res = supabase.table("keywords").select("id, count").eq("name", kw_clean).execute()
                        if kw_res.data:
                            kw_id = kw_res.data[0]["id"]
                            new_count = (kw_res.data[0]["count"] or 0) + 1
                            supabase.table("keywords").update({"count": new_count}).eq("id", kw_id).execute()
                        else:
                            new_kw = supabase.table("keywords").insert({"name": kw_clean, "count": 1}).execute()
                            if new_kw.data:
                                kw_id = new_kw.data[0]["id"]
                            else: continue
                        
                        # 建立关联
                        supabase.table("video_keywords").upsert({
                            "video_id": video_data["id"],
                            "keyword_id": kw_id
                        }).execute()
                    print(f"Successfully synced {len(keywords)} keywords for {video_data['id']}")

                if user_id:
                    submission_data = {
                        "user_id": user_id,
                        "video_id": video_data["id"],
                        "task_id": task_id
                    }
                    supabase.table("submissions").insert(submission_data).execute()
                    print(f"Successfully saved submission for user: {user_id}")
            except Exception as e:
                print(f"Failed to save to Supabase: {e}")
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        with open(f"{RESULTS_DIR}/{task_id}_error.json", "w") as f:
            json.dump({"error": str(e)}, f)

@app.post("/process")
async def process_video(request: ProcessRequest, background_tasks: BackgroundTasks):
    # 优先使用 YouTube ID 作为 task_id
    url = request.url
    task_id = None
    
    if url:
        # 尝试提取 YouTube ID (11位字符)
        id_match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11})", url)
        if id_match:
            task_id = id_match.group(1)
    
    # 如果无法提取 YouTube ID,使用时间戳
    if not task_id:
        task_id = str(int(time.time()))
    
    save_status(task_id, "queued", 0)
    
    # 记录到 Supabase，以便 Scheduler 认领
    if supabase:
        try:
            # 尝试提取视频基本信息
            name = "YouTube Video"
            if len(task_id) == 11:
                # 简单占位，真正的信息由 process_task.py 异步获取
                name = f"YouTube: {task_id}"
            
            video_data = {
                "id": task_id,
                "title": name,
                "status": "queued",
                "report_data": {
                    "url": request.url,
                    "mode": request.mode,
                    "user_id": request.user_id
                }
            }
            supabase.table("videos").upsert(video_data).execute()
            
            if request.user_id:
                supabase.table("submissions").upsert({
                    "user_id": request.user_id,
                    "video_id": task_id,
                    "task_id": task_id
                }, on_conflict="task_id").execute()
        except Exception as e:
            print(f"Failed to create queued record in Supabase: {e}")

    # 不再直接启动 BackgroundTasks，由外部 scheduler.py 轮关注
    # background_tasks.add_task(background_process, task_id, request.mode, url=request.url, user_id=request.user_id)
    return {"task_id": task_id}

@app.post("/upload")
async def upload_audio(background_tasks: BackgroundTasks, file: UploadFile = File(...), mode: str = "local", user_id: str = None):
    # 使用文件内容 hash 生成唯一 ID
    content = await file.read()
    file_hash = hashlib.md5(content).hexdigest()[:8]
    
    # 使用 'up_' 前缀区分上传文件与 YouTube 视频
    task_id = f"up_{file_hash}"
    
    ext = os.path.splitext(file.filename)[1] or ".mp3"
    file_path = os.path.join(DOWNLOADS_DIR, f"{task_id}{ext}")
    
    with open(file_path, "wb") as f:
        f.write(content)
    
    # Generate random colored thumbnail
    colors = ["#3B82F6", "#10B981", "#F59E0B", "#EF4444", "#8B5CF6", "#EC4899"]
    random_color = random.choice(colors)
    
    save_status(task_id, "queued", 0)
    # 记录到 Supabase
    if supabase:
        try:
            video_data = {
                "id": task_id,
                "title": file.filename,
                "thumbnail": random_color,
                "media_path": os.path.basename(file_path),
                "status": "queued",
                "report_data": {
                    "mode": mode,
                    "user_id": user_id,
                    "local_file": file_path
                }
            }
            supabase.table("videos").upsert(video_data).execute()
            
            if user_id:
                supabase.table("submissions").upsert({
                    "user_id": user_id,
                    "video_id": task_id,
                    "task_id": task_id
                }, on_conflict="task_id").execute()
        except Exception as e:
            print(f"Failed to create queued record in Supabase: {e}")

    # background_tasks.add_task(background_process, mode, local_file=file_path, title=file.filename, thumbnail=random_color, user_id=user_id)
    
    return {"task_id": task_id}

@app.get("/result/{task_id}")
async def get_result(task_id: str):
    # 0. Try Supabase first
    if supabase:
        try:
            response = supabase.table("videos").select("*").eq("id", task_id).execute()
            if response.data:
                video = response.data[0]
                return {
                    "title": video["title"],
                    "url": "N/A",
                    "youtube_id": video["id"] if len(video["id"]) == 11 else None,
                    "thumbnail": video["thumbnail"],
                    "media_path": video["media_path"],
                    "paragraphs": video["report_data"].get("paragraphs"),
                    "summary": video["report_data"].get("summary"),
                    "keywords": video["report_data"].get("keywords"),
                    "usage": video["usage"],
                    "raw_subtitles": video["report_data"].get("raw_subtitles"),
                    "channel": video["report_data"].get("channel"),
                    "channel_id": video["report_data"].get("channel_id"),
                    "channel_avatar": video["report_data"].get("channel_avatar"),
                    "view_count": video.get("view_count", 0),
                    "interaction_count": video.get("interaction_count", 0),
                    "mtime": video.get("created_at"),
                    "status": "completed",
                    "progress": 100
                }
        except Exception as e:
            print(f"Supabase fetch failed: {e}")

    file_path = f"{RESULTS_DIR}/{task_id}.json"
    error_path = f"{RESULTS_DIR}/{task_id}_error.json"
    status_path = f"{RESULTS_DIR}/{task_id}_status.json"
    
    # 1. Try finding by Task ID directly
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            return {**json.load(f), "status": "completed", "progress": 100}
    
    # 2. If task_id looks like a YouTube ID (11 chars), search in results
    if len(task_id) == 11:
        for f_name in os.listdir(RESULTS_DIR):
            if f_name.endswith(".json") and not f_name.endswith("_status.json") and not f_name.endswith("_error.json"):
                try:
                    with open(f"{RESULTS_DIR}/{f_name}", "r", encoding="utf-8") as f:
                        data = json.load(f)
                        if data.get("youtube_id") == task_id:
                            return {**data, "status": "completed", "progress": 100}
                except:
                    continue

    if os.path.exists(error_path):
        with open(error_path, "r") as f:
            return {"status": "failed", "detail": json.load(f).get("error"), "progress": 100}
    elif os.path.exists(status_path):
        with open(status_path, "r") as f:
            return json.load(f)
            
    raise HTTPException(status_code=404, detail="Task not found")

@app.get("/history")
async def get_history(user_id: str = None):
    history_items = []
    total_stats = {"total_duration": 0, "total_cost": 0, "video_count": 0}
    active_tasks = []

    active_taskId_set = set()

    # 1. Fetch from Supabase if available
    if supabase:
        print(f"[DEBUG] Supabase connected, user_id: {user_id}")
        try:
            # First, fetch queued/processing videos for active_tasks
            active_vid_res = supabase.table("videos").select("id, status, created_at").order("created_at", desc=True).limit(100).execute()
            print(f"[DEBUG] Raw videos count from Supabase: {len(active_vid_res.data)}")
            for v in active_vid_res.data:
                if v["status"] in ["queued", "processing"]:
                    print(f"[DEBUG] Adding active task: {v['id']} ({v['status']})")
                    active_tasks.append({
                        "id": v["id"],
                        "status": v["status"],
                        "progress": 5 if v["status"] == "processing" else 0,
                        "mtime": v["created_at"]
                    })
                    active_taskId_set.add(v["id"])

            # Then fetch history
            query = supabase.table("submissions").select("created_at, videos(id, title, thumbnail, usage)")
            if user_id:
                # Basic UUID check to avoid Supabase error
                import re
                is_uuid = re.match(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', user_id.lower())
                if is_uuid:
                    query = query.eq("user_id", user_id)
                else:
                    # If not UUID, it won't match anyway in submissions table (usually)
                    # For now just don't add the filter if it's "1" or similar
                    pass
            
            response = query.order("created_at", desc=True).execute()
            
            seen_video_ids = set()
            for item in response.data:
                video = item.get("videos")
                if not video or video["id"] in seen_video_ids: continue
                # Skip non-completed for history main list if needed, 
                # but usually history shows everything the user did.
                # However, for consistency with the prompt, let's focus on completed for main display.
                if video.get("status") != "completed":
                    continue
                    
                seen_video_ids.add(video["id"])
                
                usage = video.get("usage", {})
                duration = usage.get("duration", 0)
                cost = usage.get("total_cost", 0)
                
                history_items.append({
                    "id": video["id"],
                    "title": video["title"],
                    "thumbnail": video["thumbnail"],
                    "url": "N/A",
                    "mtime": item["created_at"],
                    "total_cost": round(cost, 4)
                })
                total_stats["total_duration"] += duration
                total_stats["total_cost"] += cost
                total_stats["video_count"] += 1
        except Exception as e:
            print(f"Supabase history fetch failed: {e}")

    # 2. Add local results that might not be in Supabase (fallback/sync)
    # To keep code simple for now, we'll just return Supabase if it worked, 
    # or local if Supabase didn't run.
    if not history_items:
        # (Existing local logic here, I'll keep it as fallback)
        history_dict = {}
        if os.path.exists(RESULTS_DIR):
            all_files = os.listdir(RESULTS_DIR)
            files = [f for f in all_files if f.endswith(".json") and not f.endswith("_error.json") and not f.endswith("_status.json")]
            file_infos = sorted([(f, os.path.getmtime(os.path.join(RESULTS_DIR, f))) for f in files], key=lambda x: x[1], reverse=True)
            
            for f, mtime in file_infos:
                task_id = f.replace(".json", "")
                try:
                    with open(os.path.join(RESULTS_DIR, f), "r") as r:
                        data = json.load(r)
                        url = data.get("url")
                        yt_id = data.get("youtube_id")
                        unique_key = yt_id if yt_id else (url if url != "Uploaded File" else data.get("media_path"))
                        
                        usage = data.get("usage", {})
                        item_user_id = data.get("user_id")
                        
                        # Filter local history by user_id if requested
                        if user_id and item_user_id != user_id:
                            continue
                            
                        duration = usage.get("duration", 0)
                        cost = usage.get("total_cost", 0)
                        
                        if unique_key not in history_dict:
                            history_dict[unique_key] = {
                                "id": task_id,
                                "title": data.get("title"),
                                "thumbnail": data.get("thumbnail"),
                                "url": url,
                                "mtime": mtime,
                                "total_cost": round(cost, 4)
                            }
                            total_stats["total_duration"] += duration
                            total_stats["total_cost"] += cost
                            total_stats["video_count"] += 1
                except: continue
        history_items = sorted(history_dict.values(), key=lambda x: x["mtime"], reverse=True)

    # Handle active tasks (remains local for now as they are transient)
    if os.path.exists(RESULTS_DIR):
        status_files = [f for f in os.listdir(RESULTS_DIR) if f.endswith("_status.json")]
        for sf in status_files:
            tid = sf.replace("_status.json", "")
            if tid in active_taskId_set:
                continue # Already added from Supabase
                
            if not os.path.exists(f"{RESULTS_DIR}/{tid}.json") and not os.path.exists(f"{RESULTS_DIR}/{tid}_error.json"):
                mtime = os.path.getmtime(f"{RESULTS_DIR}/{sf}")
                from datetime import datetime
                mtime_str = datetime.fromtimestamp(mtime).isoformat()
                # For queued/processing, don't limit to 3600s if it's recently submitted
                try:
                    with open(f"{RESULTS_DIR}/{sf}", "r") as f:
                        status_data = json.load(f)
                        status = status_data.get("status", "pending")
                        # If it's queued or processing, show it regardless of 1-hour limit (maybe up to 24h)
                        if status in ["queued", "processing"] or (time.time() - mtime < 3600):
                            active_tasks.append({
                                "id": tid, "status": status,
                                "progress": status_data.get("progress", 0), "mtime": mtime_str
                            })
                except: pass
                
        # 3. Fetch recent processing history (last 50, all statuses)
        recent_records = []
        try:
            recent_vid_res = supabase.table("videos") \
                .select("id, title, status, created_at, usage") \
                .order("created_at", desc=True) \
                .limit(50) \
                .execute()
            
            for v in recent_vid_res.data:
                usage = v.get("usage") or {}
                recent_records.append({
                    "id": v["id"],
                    "title": v.get("title") or v["id"],
                    "status": v["status"],
                    "mtime": v["created_at"],
                    "duration": round(usage.get("duration", 0), 1)
                })
        except Exception as e:
            print(f"Failed to fetch recent records: {e}")

        return {
            "items": history_items,
            "history": history_items,
            "active_tasks": sorted(active_tasks, key=lambda x: x["mtime"], reverse=True),
            "recent_tasks": recent_records,
            "summary": {
                "total_duration": total_stats["total_duration"],
                "total_cost": round(total_stats["total_cost"], 4),
                "video_count": total_stats["video_count"]
            }
        }
    
    # Fallback if no supabase
    return {
        "items": [],
        "active_tasks": [],
        "recent_tasks": [],
        "summary": {"total_duration": 0, "total_cost": 0, "video_count": 0}
    }

@app.get("/explore")
async def get_explore():
    if not supabase:
        # Fallback to local history but only YouTube ones
        res = await get_history()
        items = [i for i in res["items"] if len(i["id"]) == 11]
        return {"items": items}
    
    try:
        # Fetch videos from Supabase - Optimized to only get needed metadata
        # Large fields like raw_subtitles are excluded for performance
        response = supabase.table("videos") \
            .select("id, title, thumbnail, created_at, view_count, status, report_data->channel, report_data->channel_id, report_data->channel_avatar, report_data->summary, report_data->keywords") \
            .eq("status", "completed") \
            .order("created_at", desc=True) \
            .limit(100) \
            .execute()
        
        items = []
        for v in response.data:
            # Skip uploads - heuristic: youtube IDs are 11 chars
            if len(v["id"]) != 11 or v["id"].startswith("up_"):
                continue
            
            items.append({
                "id": v["id"],
                "title": v["title"],
                "thumbnail": v["thumbnail"],
                "channel": v.get("channel"),
                "channel_id": v.get("channel_id"),
                "channel_avatar": v.get("channel_avatar"),
                "summary": v.get("summary"),
                "keywords": v.get("keywords"),
                "date": v["created_at"],
                "views": v.get("view_count", 0)
            })
        return {"items": items}
    except Exception as e:
        print(f"Explore fetch failed: {e}")
        return {"items": []}

@app.get("/trending-keywords")
async def get_trending_keywords():
    if not supabase:
        return ["AI", "Finance", "Productivity", "Tech", "Education", "Crypto"]
    
    try:
        response = supabase.table("keywords") \
            .select("name") \
            .order("count", desc=True) \
            .limit(24) \
            .execute()
        
        return [item["name"] for item in response.data]
    except Exception as e:
        print(f"Failed to fetch trending keywords: {e}")
        return ["AI", "Finance", "Productivity", "Tech", "Education", "Crypto"]

@app.get("/project-history")
async def get_project_history():
    history_path = os.path.join(os.path.dirname(__file__), "..", ".antigravity", "PROJECT_HISTORY.md")
    if not os.path.exists(history_path):
        return []
    
    items = []
    try:
        with open(history_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            for line in lines:
                if "|" in line:
                    parts = [p.strip() for p in line.split("|")]
                    if len(parts) >= 5:
                        items.append({
                            "date": parts[0].strip("[]"),
                            "category": parts[1].strip("[]"),
                            "task": parts[2],
                            "description": parts[3],
                            "log_file": parts[4]
                        })
    except Exception as e:
        print(f"Error parsing project history: {e}")
        
    return items

@app.get("/dev-docs")
async def list_dev_docs():
    docs = []
    if os.path.exists(DEV_DOCS_DIR):
        for f in os.listdir(DEV_DOCS_DIR):
            if f.endswith(".md"):
                file_path = os.path.join(DEV_DOCS_DIR, f)
                mtime = os.path.getmtime(file_path)
                
                # Try to extract title from first line
                title = f
                try:
                    with open(file_path, "r", encoding="utf-8") as rf:
                        first_line = rf.readline().strip()
                        if first_line.startswith("#"):
                            title = first_line.lstrip("#").strip()
                except: pass
                
                docs.append({
                    "filename": f,
                    "title": title,
                    "mtime": mtime
                })
    
    return sorted(docs, key=lambda x: x["mtime"], reverse=True)

@app.get("/dev-docs/{filename}")
async def get_dev_doc(filename: str):
    # Security: check if it's strictly a markdown file in the dev_docs dir
    if not filename.endswith(".md") or ".." in filename or "/" in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")
    
    file_path = os.path.join(DEV_DOCS_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
        
    with open(file_path, "r", encoding="utf-8") as f:
        return {"content": f.read()}

@app.post("/result/{task_id}/view")
async def add_view(task_id: str):
    if not supabase:
        return {"status": "ok", "message": "Local mode, no DB update"}
    try:
        # Get current view count
        response = supabase.table("videos").select("view_count").eq("id", task_id).execute()
        if response.data:
            current_count = response.data[0].get("view_count", 0)
            supabase.table("videos").update({"view_count": current_count + 1}).eq("id", task_id).execute()
            return {"status": "success", "view_count": current_count + 1}
        return {"status": "error", "message": "Video not found"}
    except Exception as e:
        print(f"Failed to increment view count: {e}")
        return {"status": "error", "message": str(e)}

@app.post("/result/{task_id}/like")
async def toggle_like(task_id: str):
    if not supabase:
        return {"status": "ok", "message": "Local mode"}
    try:
        response = supabase.table("videos").select("interaction_count").eq("id", task_id).execute()
        if response.data:
            current_count = response.data[0].get("interaction_count", 0)
            # Simple increment for now
            new_count = current_count + 1
            supabase.table("videos").update({"interaction_count": new_count}).eq("id", task_id).execute()
            return {"status": "success", "interaction_count": new_count}
        return {"status": "error", "message": "Video not found"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/result/{task_id}/comments")
async def get_comments(task_id: str):
    if not supabase:
        return []
    try:
        response = supabase.table("comments").select("*, profiles(username, avatar_url)").eq("video_id", task_id).order("created_at", desc=True).execute()
        return response.data
    except Exception as e:
        print(f"Failed to fetch comments: {e}")
        return []

@app.post("/result/{task_id}/comments")
async def post_comment(task_id: str, request: CommentRequest):
    if not supabase:
        return {"status": "error", "message": "Database not connected"}
    try:
        data = {
            "video_id": task_id,
            "content": request.content,
            "user_id": request.user_id,
            "parent_id": request.parent_id
        }
        response = supabase.table("comments").insert(data).execute()
        return {"status": "success", "comment": response.data[0] if response.data else None}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/dev/compare/{video_id}")
async def dev_compare_subtitles(video_id: str):
    # Try to get basic video info
    title = "Unknown"
    thumbnail = ""
    youtube_id = video_id if len(video_id) == 11 else None
    media_path = ""
    
    try:
        # Re-use existing get_result logic to find metadata
        res = await get_result(video_id)
        if res:
            title = res.get("title", "Unknown")
            thumbnail = res.get("thumbnail", "")
            youtube_id = res.get("youtube_id")
            media_path = res.get("media_path", "")
    except Exception as e:
        print(f"Metadata fetch failed for compare: {e}")

    # Scan cache for multiple models
    models_data = {}
    
    # 1. Look for Ground Truth (Reference) in tests/data
    ref_filename = f"{video_id}.zh-CN.srv1"
    ref_path = os.path.join("tests", "data", ref_filename)
    if os.path.exists(ref_path):
        try:
            import xml.etree.ElementTree as ET
            tree = ET.parse(ref_path)
            root = tree.getroot()
            ref_subs = []
            for text_node in root.findall('text'):
                start = float(text_node.get('start', 0))
                dur = float(text_node.get('dur', 0))
                ref_subs.append({
                    "start": start,
                    "end": start + dur,
                    "text": text_node.text or ""
                })
            if ref_subs:
                models_data["reference"] = ref_subs
        except Exception as e:
            print(f"Failed to parse SRV1 reference: {e}")

    # 2. Look for cached models
    if os.path.exists(CACHE_DIR):
        for f in os.listdir(CACHE_DIR):
            if f.startswith(video_id) and f.endswith("_raw.json"):
                # Pattern: {video_id}_{mode}_{model}_raw.json or {video_id}_{mode}_raw.json
                filename = f.replace("_raw.json", "")
                parts = filename.split("_")
                
                # QVBpiuph3rM_local_sensevoice_raw.json -> sensevoice (index 2)
                # QVBpiuph3rM_local_raw.json -> default
                if len(parts) > 2:
                    model_name = parts[2]
                else:
                    model_name = "default"
                
                try:
                    with open(os.path.join(CACHE_DIR, f), "r", encoding="utf-8") as rf:
                        models_data[model_name] = json.load(rf)
                except: continue

    return {
        "title": title,
        "thumbnail": thumbnail,
        "youtube_id": youtube_id,
        "media_path": media_path,
        "models": models_data
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
