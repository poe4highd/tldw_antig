import os
import json
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from downloader import download_audio
from transcriber import transcribe_audio

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

class DownloadRequest(BaseModel):
    url: str
    mode: str = "cloud"

def background_process(url: str, mode: str, task_id: str):
    print(f"--- [Task {task_id}] Starting background process (Mode: {mode}) ---")
    try:
        save_status(task_id, "Downloading...", 20)
        print(f"--- [Task {task_id}] Stage 1: Downloading media... ---")
        
        # 1. Download (Check cache)
        # Use video ID as filename for caching
        import yt_dlp
        with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
            info = ydl.extract_info(url, download=False)
            video_id = info['id']
            title = info['title']
        
        file_path = f"{DOWNLOADS_DIR}/{video_id}.mp3"
        if os.path.exists(file_path):
            save_status(task_id, "Using cached audio", 40)
            print(f"--- [Task {task_id}] Stage 1: Audio found in cache: {file_path} ---")
        else:
            file_path, _ = download_audio(url, output_path=DOWNLOADS_DIR)
            print(f"--- [Task {task_id}] Stage 1: Download completed: {file_path} ---")
        
        # 2. Transcribe
        save_status(task_id, "Transcribing...", 60)
        print(f"--- [Task {task_id}] Stage 2: Starting transcription (this may take a while)... ---")
        subtitles = transcribe_audio(file_path, mode=mode)
        
        # 3. Save result
        save_status(task_id, "Finalizing...", 90)
        print(f"--- [Task {task_id}] Stage 2: Transcription done. Saving results... ---")
        result = {
            "title": title,
            "url": url,
            "media_path": os.path.basename(file_path),
            "subtitles": subtitles
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
    
    return {"status": "queued", "progress": 0}
