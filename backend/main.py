import os
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
from transcriber import transcribe_audio
from processor import split_into_paragraphs, get_youtube_thumbnail_url
from db import get_db

supabase = get_db()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files for audio playback
app.mount("/media", StaticFiles(directory="downloads"), name="media")

DOWNLOADS_DIR = "downloads"
RESULTS_DIR = "results"
CACHE_DIR = "cache"

for d in [DOWNLOADS_DIR, RESULTS_DIR, CACHE_DIR]:
    if not os.path.exists(d):
        os.makedirs(d)

class ProcessRequest(BaseModel):
    url: str
    mode: str = "cloud"

def save_status(task_id, status, progress, eta=None):
    with open(f"{RESULTS_DIR}/{task_id}_status.json", "w") as f:
        json.dump({"status": status, "progress": progress, "eta": eta}, f)

def background_process(task_id, mode, url=None, local_file=None, title=None, thumbnail=None):
    try:
        video_id = ""
        if url:
            id_match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11})", url)
            if id_match:
                video_id = id_match.group(1)
            else:
                video_id = hashlib.md5(url.encode()).hexdigest()[:11]
        elif local_file:
            # For local files, we use the hash of the filename + size or just filename as ID 
            # or pre-calculated hash from upload
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
            
            # Metadata
            import yt_dlp
            with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
                try:
                    info = ydl.extract_info(url, download=False)
                    title = info.get('title', 'Unknown Title')
                    thumbnail = info.get('thumbnail')
                except:
                    title = title or "Unknown Title"
                    thumbnail = thumbnail or get_youtube_thumbnail_url(url)

            if not file_path:
                def on_download_progress(p):
                    current_p = 20 + (p * 0.2)
                    save_status(task_id, f"正在下载媒体文件... {p:.1f}%", int(current_p), eta=35)
                
                save_status(task_id, "开始调度下载任务...", 20, eta=40)
                file_path, _, _ = download_audio(url, output_path=DOWNLOADS_DIR, progress_callback=on_download_progress)
        
        # 1.5 Audio Extraction (for uploaded videos)
        # We need to transcribe a pure audio file, especially for cloud mode size limits.
        # But we keep 'media_path' pointing to the ORIGINAL video for frontend playback.
        
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
                    # Capture at 1 second mark
                    subprocess.run(
                        ["ffmpeg", "-i", file_path, "-ss", "00:00:01", "-vframes", "1", extracted_thumb_path, "-y"],
                        check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                    )
                    thumbnail = os.path.basename(extracted_thumb_path)
                except Exception as e:
                    print(f"Thumbnail extraction failed: {e}")
            else:
                thumbnail = os.path.basename(extracted_thumb_path)

        # 2. Transcribe
        cache_sub_path = f"{CACHE_DIR}/{video_id}_{mode}_raw.json"
        if os.path.exists(cache_sub_path):
            save_status(task_id, "检测到转录缓存，正在加载报告...", 50, eta=5)
            with open(cache_sub_path, "r", encoding="utf-8") as rf:
                raw_subtitles = json.load(rf)
        else:
            save_status(task_id, f"正在进行 AI 语音转录 ({'云端模式' if mode == 'cloud' else '本地精调模式'})...", 60, eta=25 if mode == 'cloud' else 120)
            print(f"--- Starting transcription for: {os.path.basename(transcription_source_path)} ---")
            raw_subtitles = transcribe_audio(transcription_source_path, mode=mode)
            with open(cache_sub_path, "w", encoding="utf-8") as wf:
                json.dump(raw_subtitles, wf, ensure_ascii=False)

        # 3. LLM Processing
        duration = raw_subtitles[-1]["end"] if raw_subtitles else 0
        save_status(task_id, "正在通过 LLM 进行深度语义分割与润色...", 80, eta=10)
        paragraphs, llm_usage = split_into_paragraphs(raw_subtitles, title=title)

        # 4. Save Final Result
        whisper_cost = (duration / 60.0) * 0.006 if mode == "cloud" else 0
        llm_cost = (llm_usage["prompt_tokens"] / 1000000.0 * 0.15) + (llm_usage["completion_tokens"] / 1000000.0 * 0.6)
        
        result = {
            "title": title,
            "url": url or "Uploaded File",
            "youtube_id": video_id if url else None,
            "thumbnail": thumbnail,
            "media_path": os.path.basename(file_path),
            "paragraphs": paragraphs,
            "usage": {
                "duration": round(duration, 2),
                "whisper_cost": round(whisper_cost, 6),
                "llm_tokens": llm_usage,
                "llm_cost": round(llm_cost, 6),
                "total_cost": round(whisper_cost + llm_cost, 6),
                "currency": "USD"
            },
            "raw_subtitles": raw_subtitles
        }
        with open(f"{RESULTS_DIR}/{task_id}.json", "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
            
        # 5. Save to Supabase
        if supabase:
            try:
                # Prepare data for 'videos' table
                video_data = {
                    "id": video_id if url else task_id,
                    "title": title,
                    "thumbnail": thumbnail,
                    "media_path": os.path.basename(file_path),
                    "report_data": {
                        "paragraphs": paragraphs,
                        "raw_subtitles": raw_subtitles
                    },
                    "usage": result["usage"],
                    "status": "completed"
                }
                supabase.table("videos").upsert(video_data).execute()
                print(f"Successfully saved to Supabase: {video_data['id']}")
            except Exception as e:
                print(f"Failed to save to Supabase: {e}")
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        with open(f"{RESULTS_DIR}/{task_id}_error.json", "w") as f:
            json.dump({"error": str(e)}, f)

@app.post("/process")
async def process_video(request: ProcessRequest, background_tasks: BackgroundTasks):
    task_id = str(int(time.time()))
    save_status(task_id, "queued", 0)
    background_tasks.add_task(background_process, task_id, request.mode, url=request.url)
    return {"task_id": task_id}

@app.post("/upload")
async def upload_audio(background_tasks: BackgroundTasks, file: UploadFile = File(...), mode: str = "local"):
    task_id = str(int(time.time()))
    
    # 1. Save uploaded file
    # Use content hash to avoid duplicate uploads
    content = await file.read()
    file_hash = hashlib.md5(content).hexdigest()[:11]
    ext = os.path.splitext(file.filename)[1] or ".mp3"
    file_path = os.path.join(DOWNLOADS_DIR, f"{file_hash}{ext}")
    
    with open(file_path, "wb") as f:
        f.write(content)
    
    # Generate random colored thumbnail
    colors = ["#3B82F6", "#10B981", "#F59E0B", "#EF4444", "#8B5CF6", "#EC4899"]
    random_color = random.choice(colors)
    
    save_status(task_id, "queued", 0)
    background_tasks.add_task(background_process, task_id, mode, local_file=file_path, title=file.filename, thumbnail=random_color)
    
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
                    "url": "N/A", # Supabase schema currently doesn't store original URL in videos table, but we could add it
                    "youtube_id": video["id"] if len(video["id"]) == 11 else None,
                    "thumbnail": video["thumbnail"],
                    "media_path": video["media_path"],
                    "paragraphs": video["report_data"].get("paragraphs"),
                    "usage": video["usage"],
                    "raw_subtitles": video["report_data"].get("raw_subtitles"),
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
async def get_history():
    history_items = []
    total_stats = {"total_duration": 0, "total_cost": 0, "video_count": 0}
    active_tasks = []

    # 1. Fetch from Supabase if available
    if supabase:
        try:
            response = supabase.table("videos").select("id, title, thumbnail, usage, created_at").order("created_at", desc=True).execute()
            for video in response.data:
                usage = video.get("usage", {})
                duration = usage.get("duration", 0)
                cost = usage.get("total_cost", 0)
                
                history_items.append({
                    "id": video["id"],
                    "title": video["title"],
                    "thumbnail": video["thumbnail"],
                    "url": "N/A",
                    "mtime": video["created_at"],
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
            if not os.path.exists(f"{RESULTS_DIR}/{tid}.json") and not os.path.exists(f"{RESULTS_DIR}/{tid}_error.json"):
                mtime = os.path.getmtime(f"{RESULTS_DIR}/{sf}")
                if time.time() - mtime < 3600:
                    try:
                        with open(f"{RESULTS_DIR}/{sf}", "r") as f:
                            status_data = json.load(f)
                            active_tasks.append({
                                "id": tid, "status": status_data.get("status", "pending"),
                                "progress": status_data.get("progress", 0), "mtime": mtime
                            })
                    except: pass
                
    return {
        "items": history_items,
        "active_tasks": sorted(active_tasks, key=lambda x: x["mtime"], reverse=True),
        "summary": {
            "total_duration": total_stats["total_duration"],
            "total_cost": round(total_stats["total_cost"], 4),
            "video_count": total_stats["video_count"]
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
