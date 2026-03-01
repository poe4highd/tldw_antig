import os
import sys
import json
import time
import asyncio
import re
import hashlib
import random
import shutil
from fastapi import FastAPI, BackgroundTasks, HTTPException, UploadFile, File, Header, Depends, Request
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

# ========== 后台调度器配置 ==========
CHANNEL_CHECK_INTERVAL_HOURS = 1  # 每小时检查一次频道更新
MAX_VIDEOS_PER_HOUR = 5           # 每小时最多处理5个新视频
MAX_VIDEOS_PER_DAY = 50           # 每天最多处理50个视频
_daily_video_count = 0
_last_reset_day = None
_scheduler_started = False

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
    mode: str = "local"
    user_id: str = None
    is_public: bool = True

class CommentRequest(BaseModel):
    video_id: str
    content: str
    user_id: str = None
    parent_id: str = None

class LikeRequest(BaseModel):
    video_id: str
    user_id: str

def save_status(task_id, status, progress, eta=None):
    with open(f"{RESULTS_DIR}/{task_id}_status.json", "w") as f:
        json.dump({"status": status, "progress": progress, "eta": eta}, f)

def background_process(task_id, mode, url=None, local_file=None, title=None, thumbnail=None, user_id=None, is_public=True):
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
                'js_runtimes': {'node': {}},
                'remote_components': {'ejs:github'},
            }

            # YouTube Cookies Support
            cookies_path = os.environ.get("YOUTUBE_COOKIES_PATH")
            if cookies_path and os.path.exists(cookies_path):
                ydl_opts_meta['cookiefile'] = cookies_path
            
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
                        # If extraction failed but we have a channel_id, 
                        # we'll try to use channel_name if it was already set elsewhere,
                        # but we won't default to the ID here to avoid UCo2... showing as Name.
                        pass

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
        # 优先使用本地缩略图文件（稳定可靠），仅在不存在时回退到 URL
        if video_id:
            local_thumb = f"{DOWNLOADS_DIR}/{video_id}.jpg"
            if os.path.exists(local_thumb):
                thumbnail = os.path.basename(local_thumb)
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
                    "user_id": user_id,
                    "is_public": is_public,
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
                        "video_id": video_data["id"],
                        "user_id": user_id,
                        "task_id": task_id
                    }
                    try:
                        supabase.table("submissions").insert(submission_data).execute()
                    except Exception as sub_e:
                        print(f"Submission record already exists or insert failed: {sub_e}")
                        # Fallback to update to ensure video_id is correctly linked to task_id
                        supabase.table("submissions").update({
                            "video_id": video_data["id"]
                        }).eq("task_id", task_id).execute()
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
        # 更精确地正则匹配 YouTube ID，避免误匹配本站结果页
        youtube_regex = r"(?:v=|\/|embed\/|shorts\/|youtu\.be\/)([0-9A-Za-z_-]{11})(?:[?&]|$)"
        if "youtube.com" in url or "youtu.be" in url:
            id_match = re.search(youtube_regex, url)
            if id_match:
                task_id = id_match.group(1)
        elif len(url) == 11 and re.match(r"^[0-9A-Za-z_-]{11}$", url):
            # 如果直接输入的是 11 位 ID
            task_id = url
    
    # 如果无法提取 YouTube ID,使用时间戳
    if not task_id:
        task_id = str(int(time.time()))
    
    save_status(task_id, "queued", 0)

    # 清理旧的结果和错误文件，防止 GET /result 返回陈旧数据（重新提交场景）
    for suffix in [".json", "_error.json"]:
        old_file = f"{RESULTS_DIR}/{task_id}{suffix}"
        if os.path.exists(old_file):
            os.remove(old_file)

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
                "user_id": request.user_id,
                "is_public": request.is_public,
                "report_data": {
                    "url": request.url,
                    "mode": request.mode,
                    "user_id": request.user_id,
                    "is_public": request.is_public,
                    "source": "manual"
                }
            }
            supabase.table("videos").upsert(video_data).execute()
            
            if request.user_id:
                try:
                    # 改用 insert + try-update 逻辑,避开缺失的 task_id 唯一约束导致的 upsert 错误
                    supabase.table("submissions").insert({
                        "user_id": request.user_id,
                        "video_id": task_id,
                        "task_id": task_id
                    }).execute()
                except Exception as sub_e:
                    # 如果 insert 失败(如记录已存在),尝试使用 update
                    print(f"Submission insert failed in /process (expected if exists): {sub_e}")
                    supabase.table("submissions").update({
                        "video_id": task_id
                    }).eq("task_id", task_id).execute()

        except Exception as e:
            print(f"Failed to create queued record in Supabase: {e}")

    # 不再直接启动 BackgroundTasks，由外部 scheduler.py 轮关注
    # background_tasks.add_task(background_process, task_id, request.mode, url=request.url, user_id=request.user_id)
    return {"task_id": task_id}

@app.post("/upload")
async def upload_audio(background_tasks: BackgroundTasks, file: UploadFile = File(...), mode: str = "local", user_id: str = None, is_public: bool = True):
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

    # 清理旧的结果和错误文件，防止 GET /result 返回陈旧数据（重新提交场景）
    for suffix in [".json", "_error.json"]:
        old_file = f"{RESULTS_DIR}/{task_id}{suffix}"
        if os.path.exists(old_file):
            os.remove(old_file)

    # 记录到 Supabase
    if supabase:
        try:
            video_data = {
                "id": task_id,
                "title": file.filename,
                "thumbnail": random_color,
                "media_path": os.path.basename(file_path),
                "status": "queued",
                "user_id": user_id,
                "is_public": is_public,
                "report_data": {
                    "mode": mode,
                    "user_id": user_id,
                    "is_public": is_public,
                    "local_file": file_path,
                    "source": "manual"
                }
            }
            supabase.table("videos").upsert(video_data).execute()
            
            if user_id:
                try:
                    # 避开缺少 task_id 唯一约束导致的 upsert 错误
                    supabase.table("submissions").insert({
                        "user_id": user_id,
                        "video_id": task_id,
                        "task_id": task_id
                    }).execute()
                except Exception as sub_e:
                    print(f"Submission insert failed in /upload (expected if exists): {sub_e}")
                    supabase.table("submissions").update({
                        "video_id": task_id
                    }).eq("task_id", task_id).execute()

        except Exception as e:
            print(f"Failed to create queued record in Supabase: {e}")

    # background_tasks.add_task(background_process, mode, local_file=file_path, title=file.filename, thumbnail=random_color, user_id=user_id, is_public=is_public)
    
    return {"task_id": task_id}

@app.get("/result/{task_id}")
async def get_result_status(request: Request, task_id: str, user_id: str = None):
    # 0. Try Supabase first
    if supabase:
        try:
            # Fetch video
            response = supabase.table("videos").select("*").eq("id", task_id).execute()
            if response.data:
                video = response.data[0]
                
                is_liked = False
                
                # 根据 Supabase 状态精确路由，避免 fall-through 读到旧本地文件
                if video["status"] == "completed":
                    if user_id:
                        like_res = supabase.table("user_likes") \
                            .select("id") \
                            .eq("user_id", user_id) \
                            .eq("video_id", task_id) \
                            .execute()
                        is_liked = len(like_res.data) > 0

                    # Check if reports are actually ready
                    paragraphs = video["report_data"].get("paragraphs")
                    if not paragraphs and video["status"] == "completed":
                        print(f"[Result] Warning: Task {task_id} marked as completed but has no paragraphs. Returning processing status.")
                        return {
                            "status": "processing",
                            "progress": 95,
                            "detail": "Finalizing data sync..."
                        }

                    return {
                        "title": video["title"],
                        "url": "N/A",
                        "youtube_id": video["id"] if len(video["id"]) == 11 else None,
                        "thumbnail": get_full_thumbnail_url(video["thumbnail"], request),
                        "media_path": video["media_path"],
                        "paragraphs": paragraphs,
                        "summary": video["report_data"].get("summary"),
                        "keywords": video["report_data"].get("keywords"),
                        "usage": video["usage"],
                        "raw_subtitles": video["report_data"].get("raw_subtitles"),
                        "channel": video["report_data"].get("channel"),
                        "channel_id": video["report_data"].get("channel_id"),
                        "channel_avatar": video["report_data"].get("channel_avatar"),
                        "view_count": video.get("view_count", 0),
                        "interaction_count": video.get("interaction_count", 0),
                        "is_liked": is_liked,
                        "mtime": video.get("created_at"),
                        "status": "completed",
                        "progress": 100
                    }
                elif video["status"] in ("queued", "processing"):
                    # 任务正在排队或处理中，从本地 _status.json 读取实时进度
                    status_path = f"{RESULTS_DIR}/{task_id}_status.json"
                    if os.path.exists(status_path):
                        with open(status_path, "r") as f:
                            local_status = json.load(f)
                        # 竞态修复：本地已 failed 但 Supabase 尚未同步，走 failed 分支逻辑
                        if local_status.get("status") == "failed":
                            error_path = f"{RESULTS_DIR}/{task_id}_error.json"
                            detail = "Unknown error"
                            if os.path.exists(error_path):
                                with open(error_path, "r") as ef:
                                    detail = json.load(ef).get("error", detail)
                            return {"status": "failed", "detail": detail, "progress": 0}
                        return local_status
                    return {"status": video["status"], "progress": 0, "eta": None}
                elif video["status"] == "failed":
                    # 任务已失败，从本地错误文件获取详情
                    error_path = f"{RESULTS_DIR}/{task_id}_error.json"
                    detail = "Unknown error"
                    if os.path.exists(error_path):
                        with open(error_path, "r") as f:
                            detail = json.load(f).get("error", detail)
                    return {"status": "failed", "detail": detail, "progress": 0}
        except Exception as e:
            print(f"Supabase fetch failed: {e}")

    file_path = f"{RESULTS_DIR}/{task_id}.json"
    error_path = f"{RESULTS_DIR}/{task_id}_error.json"
    status_path = f"{RESULTS_DIR}/{task_id}_status.json"
    
    # 1. Try finding by Task ID directly
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            result = json.load(f)
            if "thumbnail" in result:
                result["thumbnail"] = get_full_thumbnail_url(result["thumbnail"], request)
            return {**result, "status": "completed", "progress": 100}
    
    # 2. If task_id looks like a YouTube ID (11 chars), search in results
    if len(task_id) == 11:
        for f_name in os.listdir(RESULTS_DIR):
            if f_name.endswith(".json") and not f_name.endswith("_status.json") and not f_name.endswith("_error.json"):
                try:
                    with open(f"{RESULTS_DIR}/{f_name}", "r", encoding="utf-8") as f:
                        data = json.load(f)
                        if data.get("youtube_id") == task_id:
                            if "thumbnail" in data:
                                data["thumbnail"] = get_full_thumbnail_url(data["thumbnail"], request)
                            return {**data, "status": "completed", "progress": 100}
                except:
                    continue

    if os.path.exists(error_path):
        with open(error_path, "r") as f:
            return {"status": "failed", "detail": json.load(f).get("error"), "progress": 0}
    elif os.path.exists(status_path):
        with open(status_path, "r") as f:
            result = json.load(f)
            if "thumbnail" in result:
                result["thumbnail"] = get_full_thumbnail_url(result["thumbnail"], request)
            return result
            
    raise HTTPException(status_code=404, detail="Task not found")

def get_full_thumbnail_url(thumbnail: str, request: Request = None) -> str:
    """补全缩略图 URL：如果是本地文件名则添加前缀"""
    if not thumbnail:
        return ""
    if thumbnail.startswith(("http://", "https://")):
        return thumbnail
    if thumbnail.startswith("#"):
        # 这是一个十六进制颜色占位符，直接返回
        return thumbnail
    
    # 补全本地路径逻辑
    base_url = ""
    if request:
        # 尝试从请求中获取原始 Host
        base_url = str(request.base_url).rstrip("/")
    
    return f"{base_url}/media/{thumbnail}"

# API Endpoints
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
                if v["status"] in ["queued", "processing", "failed"]:
                    # failed 任务进度归零，不显示误导性的 100%
                    if v["status"] == "failed":
                        real_progress = 0
                    elif v["status"] == "processing":
                        # 尝试从本地 _status.json 提取真实进度
                        real_progress = 5
                        real_status = "processing"
                        local_status_path = f"{RESULTS_DIR}/{v['id']}_status.json"
                        if os.path.exists(local_status_path):
                            try:
                                with open(local_status_path, "r") as f:
                                    status_data = json.load(f)
                                    local_s = status_data.get("status")
                                    # 竞态修复：本地已 failed 但 Supabase 尚未同步
                                    if local_s == "failed":
                                        real_progress = 0
                                        real_status = "failed"
                                    elif local_s == "completed":
                                        real_progress = 100
                                        real_status = "completed"
                                    else:
                                        real_progress = status_data.get("progress", real_progress)
                            except:
                                pass
                        v["status"] = real_status
                    else:
                        real_progress = 0
                            
                    active_tasks.append({
                        "id": v["id"],
                        "status": v["status"],
                        "progress": real_progress,
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
async def get_explore(request: Request, page: int = 1, limit: int = 24, q: str = None, user_id: str = None):
    req_user_id = user_id # Rename locally for clarity
    if not supabase:
        # Fallback to local history but only YouTube ones
        try:
            res = await get_history(user_id=req_user_id)
            items = [i for i in res.get("items", []) if len(str(i.get("id", ""))) == 11]
            
            # Simple local pagination and search
            if q:
                q = q.lower()
                items = [i for i in items if q in str(i.get("title", "")).lower()]
                
            start = (page - 1) * limit
            end = start + limit
            return {
                "items": items[start:end],
                "total": len(items),
                "page": page,
                "limit": limit
            }
        except Exception as e:
            print(f"Explore fallback failed: {e}")
            return {"items": [], "total": 0, "page": page, "limit": limit}
    
    try:
        # 获取隐藏频道列表
        hidden_channel_ids = set()
        try:
            hidden_channels = supabase.table("channel_settings") \
                .select("channel_id") \
                .eq("hidden_from_home", True) \
                .execute()
            if hidden_channels.data:
                hidden_channel_ids = {c["channel_id"] for c in hidden_channels.data}
        except Exception as e:
            # 表可能不存在，忽略错误
            print(f"[Explore] channel_settings 查询失败（表可能不存在）: {e}")
        
        # Start building the query
        # 确保 req_user_id 在查询中可用（如果需要隐私过滤）
        query = supabase.table("videos") \
            .select("id, title, thumbnail, created_at, view_count, status, hidden_from_home, is_public, report_data->channel, report_data->channel_id, report_data->channel_avatar, report_data->summary, report_data->keywords", count="exact") \
            .eq("status", "completed") \
            .eq("is_public", True)
            
        if q:
            search_query = f"%{q}%"
            query = query.or_(f"title.ilike.{search_query},report_data->>channel.ilike.{search_query},report_data->>summary.ilike.{search_query}")

        # Execute with pagination
        start = (page - 1) * limit
        end = start + limit - 1
        
        response = query.order("created_at", desc=True) \
            .range(start, end) \
            .execute()
        
        # If req_user_id is provided, fetch their liked videos to mark items
        liked_ids = set()
        if req_user_id:
            try:
                like_res = supabase.table("user_likes").select("video_id").eq("user_id", req_user_id).execute()
                if like_res.data:
                    liked_ids = {l["video_id"] for l in like_res.data}
            except Exception as le:
                print(f"Failed to fetch likes in explore: {le}")

        items = []
        if response.data:
            for v in response.data:
                # Skip uploads - heuristic: youtube IDs are 11 chars
                vid = str(v.get("id", ""))
                if len(vid) != 11 or vid.startswith("up_"):
                    continue
                
                # Skip hidden videos (individual or by channel)
                if v.get("hidden_from_home"):
                    continue
                
                video_channel_id = v.get("channel_id")
                if video_channel_id and video_channel_id in hidden_channel_ids:
                    continue
                
                items.append({
                    "id": vid,
                    "title": v.get("title", "Untitled"),
                    "thumbnail": get_full_thumbnail_url(v.get("thumbnail", ""), request),
                    "channel": v.get("channel"),
                    "channel_id": v.get("channel_id"),
                    "channel_avatar": v.get("channel_avatar"),
                    "summary": v.get("summary"),
                    "keywords": v.get("keywords"),
                    "date": v.get("created_at"),
                    "views": v.get("view_count", 0),
                    "is_liked": vid in liked_ids
                })
            
        return {
            "items": items,
            "total": response.count if response.count is not None else len(items),
            "page": page,
            "limit": limit
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"[Explore] Fetch failed: {e}")
        # Explicitly check for NameError to debug if it persists
        if isinstance(e, NameError):
            print(f"[Explore] Critical NameError: {e}. Check local scope.")
        return {"items": [], "total": 0, "page": page, "limit": limit}


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

@app.post("/like")
async def toggle_user_like(request: LikeRequest):
    if not supabase:
        return {"status": "error", "message": "Supabase not connected"}
    
    try:
        # Check if already liked
        existing = supabase.table("user_likes") \
            .select("id") \
            .eq("user_id", request.user_id) \
            .eq("video_id", request.video_id) \
            .execute()
        
        if existing.data:
            # Unlike
            supabase.table("user_likes") \
                .delete() \
                .eq("user_id", request.user_id) \
                .eq("video_id", request.video_id) \
                .execute()
            status = "unliked"
        else:
            # Like
            supabase.table("user_likes") \
                .insert({
                    "user_id": request.user_id,
                    "video_id": request.video_id
                }) \
                .execute()
            status = "liked"
        
        return {"status": "success", "action": status}
    except Exception as e:
        print(f"Failed to toggle like: {e}")
        return {"status": "error", "message": str(e)}

@app.get("/bookshelf")
async def get_bookshelf(request: Request, user_id: str, limit: int = 40):
    if not supabase:
        return {"history": []}
    
    try:
        # Define fetch functions for parallel execution
        def fetch_submissions():
            return supabase.table("submissions") \
                .select("video_id, created_at, videos(*)") \
                .eq("user_id", user_id) \
                .order("created_at", desc=True) \
                .limit(limit) \
                .execute()

        def fetch_likes():
            return supabase.table("user_likes") \
                .select("video_id, created_at, videos(*)") \
                .eq("user_id", user_id) \
                .order("created_at", desc=True) \
                .limit(limit) \
                .execute()

        # Execute parallelly using asyncio.to_thread
        sub_res, like_res = await asyncio.gather(
            asyncio.to_thread(fetch_submissions),
            asyncio.to_thread(fetch_likes)
        )
        
        # Combine and deduplicate
        bookshelf_map = {}
        
        for item in sub_res.data:
            vid = item.get("video_id")
            video = item.get("videos")
            if video:
                bookshelf_map[vid] = {
                    "id": video["id"],
                    "title": video["title"],
                    "thumbnail": get_full_thumbnail_url(video["thumbnail"], request),
                    "mtime": item["created_at"],
                    "status": video["status"],
                    "is_public": video.get("is_public", True),
                    "summary": video.get("report_data", {}).get("summary") if video.get("report_data") else None,
                    "keywords": video.get("report_data", {}).get("keywords") if video.get("report_data") else [],
                    "source": "submission"
                }

        for item in like_res.data:
            vid = item.get("video_id")
            video = item.get("videos")
            if video:
                # If already in bookshelf via submission, we mark it liked
                if vid not in bookshelf_map:
                    bookshelf_map[vid] = {
                        "id": video["id"],
                        "title": video["title"],
                        "thumbnail": get_full_thumbnail_url(video["thumbnail"], request),
                        "mtime": item["created_at"],
                        "status": video["status"],
                        "is_public": video.get("is_public", True),
                        "summary": video.get("report_data", {}).get("summary") if video.get("report_data") else None,
                        "keywords": video.get("report_data", {}).get("keywords") if video.get("report_data") else [],
                        "source": "like",
                        "is_liked": True
                    }
                else:
                    bookshelf_map[vid]["is_liked"] = True

        # Convert to list and sort by date
        sorted_items = sorted(bookshelf_map.values(), key=lambda x: x["mtime"], reverse=True)
        
        # Apply limit
        if limit > 0:
            sorted_items = sorted_items[:limit]
            
        return {"history": sorted_items}
    except Exception as e:
        print(f"Failed to fetch bookshelf: {e}")
        return {"status": "error", "message": str(e)}

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
async def toggle_like_legacy(task_id: str):
    # This is a legacy endpoint that just increments interaction_count
    # Keep it for backward compatibility or remove if not used.
    pass

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

# ========== 管理认证 ==========
async def verify_admin_key(x_admin_key: str = Header(None)):
    admin_secret = os.getenv("ADMIN_SECRET_KEY")
    # 如果没设置密钥，默认一个简单的密钥用于防护，或者可以设置为 None 以跳过验证（不推荐）
    if not admin_secret:
        admin_secret = "tldw-admin-secret"
        
    if x_admin_key != admin_secret:
        raise HTTPException(status_code=403, detail="Invalid Admin Key")

# ========== 管理 API ==========

class ChannelSettingsRequest(BaseModel):
    channel_id: str
    channel_name: str = None
    hidden_from_home: bool = None
    track_new_videos: bool = None

class VideoVisibilityRequest(BaseModel):
    video_id: str
    hidden_from_home: bool

@app.get("/admin/visibility", dependencies=[Depends(verify_admin_key)])
async def get_visibility_settings(request: Request):
    """获取所有频道设置和所有视频列表"""
    if not supabase:
        return {"channels": [], "all_videos": [], "error": "Database not connected"}
    
    try:
        # 获取所有频道设置
        channel_res = supabase.table("channel_settings").select("*").execute()
        channels = channel_res.data if channel_res.data else []
    except Exception as e:
        channels = []
        print(f"Failed to fetch channel_settings: {e}")
    
    try:
        # 获取所有已完成的视频（带隐藏状态）
        videos_res = supabase.table("videos") \
            .select("id, title, thumbnail, hidden_from_home, report_data->channel, report_data->channel_id") \
            .eq("status", "completed") \
            .order("created_at", desc=True) \
            .limit(200) \
            .execute()
        raw_videos = videos_res.data if videos_res.data else []
        
        # 补全缩略图 URL
        all_videos = []
        for v in raw_videos:
            v_copy = v.copy()
            v_copy["thumbnail"] = get_full_thumbnail_url(v.get("thumbnail"), request)
            all_videos.append(v_copy)
    except Exception as e:
        all_videos = []
        print(f"Failed to fetch videos: {e}")
    
    try:
        # 获取所有已知频道（从 videos 表中提取）
        all_channels_res = supabase.table("videos") \
            .select("report_data->channel, report_data->channel_id") \
            .not_.is_("report_data->channel_id", "null") \
            .execute()
        
        known_channels = {}
        for v in all_channels_res.data:
            c_id = v.get("channel_id")
            # Try both 'channel' and 'channel_name' for compatibility
            c_name = v.get("channel") or v.get("channel_name")
            if c_id and c_name and c_id not in known_channels:
                known_channels[c_id] = c_name
            elif c_id and not c_name and c_id not in known_channels:
                known_channels[c_id] = None
    except:
        known_channels = {}
    
    return {
        "channels": channels,
        "all_videos": all_videos,
        "known_channels": known_channels
    }

@app.get("/admin/stats", dependencies=[Depends(verify_admin_key)])
async def get_admin_stats():
    """获取管理驾驶舱的核心统计数据"""
    if not supabase:
        return {"error": "Database not connected"}
    
    try:
        # 1. 获取所有视频的基本数据用于统计
        # 增加 report_data 字段以进行用量估算
        all_videos_res = supabase.table("videos") \
            .select("id, title, status, usage, report_data, interaction_count, view_count, created_at") \
            .execute()
        all_videos = all_videos_res.data if all_videos_res.data else []
        
        video_count = len(all_videos)
        
        # 2. 活跃用户 (DAU) - 过去 24 小时有行为的用户数
        from datetime import datetime, timedelta
        yesterday = (datetime.utcnow() - timedelta(days=1)).isoformat()
        
        dau_res = supabase.table("interactions") \
            .select("user_id") \
            .not_.is_("user_id", "null") \
            .gt("created_at", yesterday) \
            .execute()
        
        unique_users = set(v["user_id"] for v in dau_res.data) if dau_res.data else set()
        dau_count = len(unique_users)
        
        # 3. 统计项初始化
        total_interactions = 0
        total_views = 0
        total_llm_cost = 0.0
        llm_usage_history = []
        
        # 估算函数：基于文本长度估算 Token 和费用
        def estimate_llm_usage(report_data):
            if not report_data: return 0, 0, 0.0
            
            # 提取文本
            text = ""
            paragraphs = report_data.get("paragraphs") or []
            if paragraphs:
                for p in paragraphs:
                    for s in p.get("sentences", []):
                        text += s.get("text", "")
            
            if not text:
                raw_subs = report_data.get("raw_subtitles") or []
                text = "".join([s.get("text", "") for s in raw_subs])
            
            char_count = len(text)
            if char_count == 0: return 0, 0, 0.0
            
            # 估算逻辑：1汉字 ≈ 1.5 token (考虑提示词开销 * 2.5 倍率)
            estimated_tokens = int(char_count * 2.5)
            # 按照 gpt-4o-mini 平均值 $0.15/1M tokens 估算
            estimated_cost = (estimated_tokens / 1000000.0) * 0.15
            
            return int(estimated_tokens * 0.7), int(estimated_tokens * 0.3), estimated_cost

        # 4. 遍历视频进行聚合
        for v in all_videos:
            total_interactions += (v.get("interaction_count") or 0)
            total_views += (v.get("view_count") or 0)
            
            usage = v.get("usage") or {}
            cost = usage.get("llm_cost")
            
            is_estimated = False
            if cost is None or cost == 0:
                if v.get("status") == "completed":
                    _, _, est_cost = estimate_llm_usage(v.get("report_data"))
                    cost = est_cost
                    is_estimated = True
                else:
                    cost = 0.0
            
            total_llm_cost += cost

            # 构建历史记录（取最近 20 条）
            # 我们先存起来，后面排序
        
        # 5. 构建 LLM 历史记录
        sorted_videos = sorted(all_videos, key=lambda x: x.get("created_at", ""), reverse=True)
        for v in sorted_videos[:20]:
            usage = v.get("usage") or {}
            report_data = v.get("report_data") or {}
            
            p_tokens = usage.get("llm_tokens", {}).get("prompt_tokens")
            c_tokens = usage.get("llm_tokens", {}).get("completion_tokens")
            cost = usage.get("llm_cost")
            model = usage.get("model", "gpt-4o-mini")
            is_estimated = False
            
            if cost is None or cost == 0:
                if v.get("status") == "completed":
                    p_tokens, c_tokens, cost = estimate_llm_usage(report_data)
                    is_estimated = True
                else:
                    p_tokens, c_tokens, cost = 0, 0, 0.0

            llm_usage_history.append({
                "id": v["id"],
                "title": v["title"],
                "model": model if not is_estimated else f"{model} (est.)",
                "prompt_tokens": p_tokens or 0,
                "completion_tokens": c_tokens or 0,
                "cost": cost or 0.0,
                "is_estimated": is_estimated,
                "created_at": v["created_at"]
            })

        # 6. 热力图数据
        heatmap_res = supabase.table("admin_heatmap_data").select("*").execute()
        
        # 7. 爆款视频 Top 5
        top_videos = sorted(all_videos, key=lambda x: (x.get("interaction_count") or 0), reverse=True)[:5]
        
        return {
            "stats": {
                "video_count": f"{video_count:,}",
                "dau": str(dau_count),
                "total_clicks": f"{total_interactions + total_views:,}", 
                "total_llm_cost": f"${total_llm_cost:,.2f}",
                "retention": "84%" 
            },
            "heatmap": heatmap_res.data,
            "top_videos": [{"id": v["id"], "title": v["title"], "interaction_count": v.get("interaction_count", 0)} for v in top_videos],
            "llm_usage_history": llm_usage_history
        }
    except Exception as e:
        print(f"Failed to fetch admin stats: {e}")
        return {"error": str(e)}


@app.post("/admin/visibility/channel", dependencies=[Depends(verify_admin_key)])
async def update_channel_settings(request: ChannelSettingsRequest):
    """更新频道设置"""
    if not supabase:
        return {"status": "error", "message": "Database not connected"}
    
    try:
        data = {"channel_id": request.channel_id}
        if request.channel_name is not None:
            data["channel_name"] = request.channel_name
        if request.hidden_from_home is not None:
            data["hidden_from_home"] = request.hidden_from_home
        if request.track_new_videos is not None:
            data["track_new_videos"] = request.track_new_videos
        data["updated_at"] = "now()"
        
        supabase.table("channel_settings").upsert(data).execute()
        return {"status": "success"}
    except Exception as e:
        print(f"Failed to update channel settings: {e}")
        return {"status": "error", "message": str(e)}

@app.post("/admin/visibility/video", dependencies=[Depends(verify_admin_key)])
async def update_video_visibility(request: VideoVisibilityRequest):
    """更新单个视频的隐藏状态"""
    if not supabase:
        return {"status": "error", "message": "Database not connected"}
    
    try:
        supabase.table("videos") \
            .update({"hidden_from_home": request.hidden_from_home}) \
            .eq("id", request.video_id) \
            .execute()
        return {"status": "success"}
    except Exception as e:
        print(f"Failed to update video visibility: {e}")
        return {"status": "error", "message": str(e)}

# ========== 后台调度任务 ==========
async def run_channel_tracker():
    """异步运行频道追踪脚本"""
    global _daily_video_count, _last_reset_day
    
    from datetime import date
    import subprocess
    
    # 每日重置计数器
    today = date.today()
    if _last_reset_day != today:
        _daily_video_count = 0
        _last_reset_day = today
        print(f"[Scheduler] 新的一天，重置每日视频计数器")
    
    # 检查每日限额
    if _daily_video_count >= MAX_VIDEOS_PER_DAY:
        print(f"[Scheduler] 已达每日处理上限 ({MAX_VIDEOS_PER_DAY})，跳过本次检查")
        return
    
    print(f"[Scheduler] 开始检查频道更新... (今日已处理: {_daily_video_count}/{MAX_VIDEOS_PER_DAY})")
    
    try:
        # 运行 channel_tracker.py
        script_path = os.path.join(os.path.dirname(__file__), "scripts", "channel_tracker.py")
        env = os.environ.copy()
        env["PYTHONPATH"] = os.path.dirname(__file__)
        
        result = subprocess.run(
            ["python3", script_path],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(__file__),
            env=env,
            timeout=300  # 5分钟超时
        )
        
        if result.returncode == 0:
            # 解析添加了多少新任务（包括新视频和重试的失败视频）
            import re
            match = re.search(r"Added (\d+) tasks", result.stdout)
            if match:
                added = int(match.group(1))
                _daily_video_count += added
                print(f"[Scheduler] 频道检查完成，已排队 {added} 个任务")
        else:
            print(f"[Scheduler] 频道检查失败: {result.stderr}")
    except subprocess.TimeoutExpired:
        print(f"[Scheduler] 频道检查超时")
    except Exception as e:
        print(f"[Scheduler] 频道检查异常: {e}")


async def scheduler_loop():
    """后台调度循环"""
    global _scheduler_started
    
    if _scheduler_started:
        return
    _scheduler_started = True
    
    print(f"[Scheduler] 启动后台调度器，间隔: {CHANNEL_CHECK_INTERVAL_HOURS}小时")
    
    # 首次启动延迟5分钟，避免与服务启动冲突
    await asyncio.sleep(300)
    
    while True:
        try:
            await run_channel_tracker()
        except Exception as e:
            print(f"[Scheduler] 调度循环异常: {e}")
        
        # 等待下一个周期
        await asyncio.sleep(CHANNEL_CHECK_INTERVAL_HOURS * 3600)


@app.on_event("startup")
async def start_scheduler():
    """FastAPI 启动时启动后台调度器"""
    asyncio.create_task(scheduler_loop())
    print("[Scheduler] 后台调度任务已注册")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
