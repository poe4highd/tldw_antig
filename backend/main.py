import os
import json
import re
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from downloader import download_audio
from transcriber import transcribe_audio
from processor import split_into_paragraphs

app = FastAPI()

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static dirs
DOWNLOADS_DIR = "downloads"
RESULTS_DIR = "results"
for d in [DOWNLOADS_DIR, RESULTS_DIR]:
    if not os.path.exists(d):
        os.makedirs(d)

app.mount("/media", StaticFiles(directory=DOWNLOADS_DIR), name="media")
app.mount("/results", StaticFiles(directory=RESULTS_DIR), name="results")

def save_status(task_id, status, progress):
    with open(f"{RESULTS_DIR}/{task_id}_status.json", "w") as f:
        json.dump({"status": status, "progress": progress}, f)

def extract_youtube_id(url: str) -> str:
    """提取 YouTube 视频 ID"""
    patterns = [
        r"(?:v=|\/)([0-9A-Za-z_-]{11}).*", # standard and embed
        r"be\/([0-9A-Za-z_-]{11}).*",      # youtu.be
        r"shorts\/([0-9A-Za-z_-]{11}).*",  # shorts
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

def get_youtube_thumbnail_url(url: str) -> str:
    """根据 URL 推导缩略图"""
    video_id = extract_youtube_id(url)
    if video_id:
        return f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg"
    return "https://images.unsplash.com/photo-1611162617474-5b21e879e113"

class DownloadRequest(BaseModel):
    url: str
    mode: str = "cloud"

def background_process(url: str, mode: str, task_id: str):
    print(f"--- [Task {task_id}] Starting background process (Mode: {mode}) ---")
    try:
        save_status(task_id, "Downloading...", 20)
        print(f"--- [Task {task_id}] Stage 1: Downloading media... ---")
        
        # 1. Download (Check cache)
        import yt_dlp
        with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
            info = ydl.extract_info(url, download=False)
            video_id = info['id']
            title = info['title']
            thumbnail = info.get('thumbnail')
        
        file_path = f"{DOWNLOADS_DIR}/{video_id}.mp3"
        if os.path.exists(file_path):
            save_status(task_id, "Using cached audio", 40)
        else:
            file_path, _, _ = download_audio(url, output_path=DOWNLOADS_DIR)
        
        # 2. Transcribe
        save_status(task_id, "Transcribing...", 60)
        raw_subtitles = transcribe_audio(file_path, mode=mode)
        
        # 3. LLM Processing (Paragraphing)
        save_status(task_id, "Natural Segmenting...", 80)
        paragraphs = split_into_paragraphs(raw_subtitles)
        
        # 4. Save result
        result = {
            "title": title,
            "url": url,
            "thumbnail": thumbnail or get_youtube_thumbnail_url(url),
            "media_path": os.path.basename(file_path),
            "paragraphs": paragraphs,
            "raw_subtitles": raw_subtitles
        }
        with open(f"{RESULTS_DIR}/{task_id}.json", "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"--- [Task {task_id}] Task completed successfully! ---")
            
        # 4. Cleanup old media files (older than 48 hours)
        import time
        now = time.time()
        for f in os.listdir(DOWNLOADS_DIR):
            fpath = os.path.join(DOWNLOADS_DIR, f)
            if os.stat(fpath).st_mtime < now - 48 * 3600:
                if f.endswith(".mp3"):
                    os.remove(fpath)
                    
    except Exception as e:
        import traceback
        traceback.print_exc()
        with open(f"{RESULTS_DIR}/{task_id}_error.json", "w") as f:
            json.dump({"error": str(e)}, f)

@app.post("/process")
async def process_video(request: DownloadRequest, background_tasks: BackgroundTasks):
    import uuid
    task_id = str(uuid.uuid4())
    background_tasks.add_task(background_process, request.url, request.mode, task_id)
    return {"task_id": task_id, "status": "started"}

@app.get("/result/{task_id}")
async def get_result(task_id: str):
    file_path = f"{RESULTS_DIR}/{task_id}.json"
    error_path = f"{RESULTS_DIR}/{task_id}_error.json"
    status_path = f"{RESULTS_DIR}/{task_id}_status.json"
    
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            return {**json.load(f), "status": "completed", "progress": 100}
    elif os.path.exists(error_path):
        with open(error_path, "r") as f:
            err_data = json.load(f)
            return {"status": "failed", "detail": err_data.get("error"), "progress": 100}
    elif os.path.exists(status_path):
        with open(status_path, "r") as f:
            return json.load(f)
    
@app.get("/history")
async def get_history():
    history_dict = {}  # {url: item}
    for f in os.listdir(RESULTS_DIR):
        if f.endswith(".json") and not f.endswith("_error.json") and not f.endswith("_status.json"):
            task_id = f.replace(".json", "")
            f_path = os.path.join(RESULTS_DIR, f)
            mtime = os.path.getmtime(f_path)
            with open(f_path, "r") as r:
                try:
                    data = json.load(r)
                    url = data.get("url")
                    if not url: continue
                    
                    item = {
                        "id": task_id,
                        "title": data.get("title"),
                        "thumbnail": data.get("thumbnail") or get_youtube_thumbnail_url(url),
                        "url": url,
                        "mtime": mtime
                    }
                    
                    # 如果 URL 已存在，只保留更新的一份
                    if url not in history_dict or mtime > history_dict[url]["mtime"]:
                        history_dict[url] = item
                except:
                    continue
                    
    # 按时间降序排序（最新的在前）
    sorted_history = sorted(history_dict.values(), key=lambda x: x["mtime"], reverse=True)
    return sorted_history
