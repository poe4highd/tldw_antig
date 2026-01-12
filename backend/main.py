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

# Progress tracking
task_status = {}

class DownloadRequest(BaseModel):
    url: str
    mode: str = "cloud"

def background_process(url: str, mode: str, task_id: str):
    try:
        task_status[task_id] = {"status": "Downloading...", "progress": 20}
        
        # 1. Download (Check cache)
        # Use video ID as filename for caching
        import yt_dlp
        with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
            info = ydl.extract_info(url, download=False)
            video_id = info['id']
            title = info['title']
        
        file_path = f"{DOWNLOADS_DIR}/{video_id}.mp3"
        if os.path.exists(file_path):
            task_status[task_id] = {"status": "Using cached audio", "progress": 40}
        else:
            file_path, _ = download_audio(url, output_path=DOWNLOADS_DIR)
        
        # 2. Transcribe
        task_status[task_id] = {"status": "Transcribing...", "progress": 60}
        subtitles = transcribe_audio(file_path, mode=mode)
        
        # 3. Save result
        task_status[task_id] = {"status": "Finalizing...", "progress": 90}
        result = {
            "title": title,
            "url": url,
            "media_url": f"http://localhost:8000/media/{os.path.basename(file_path)}",
            "subtitles": subtitles
        }
        with open(f"{RESULTS_DIR}/{task_id}.json", "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
            
        # 4. Cleanup old media files (older than 48 hours)
        import time
        now = time.time()
        for f in os.listdir(DOWNLOADS_DIR):
            fpath = os.path.join(DOWNLOADS_DIR, f)
            if os.stat(fpath).st_mtime < now - 48 * 3600:
                if f.endswith(".mp3"):
                    os.remove(fpath)
                    
    except Exception as e:
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
    
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            return {**json.load(f), "status": "completed", "progress": 100}
    elif os.path.exists(error_path):
        with open(error_path, "r") as f:
            return {"status": "failed", "detail": json.load(f), "progress": 100}
    
    return task_status.get(task_id, {"status": "processing", "progress": 0})
