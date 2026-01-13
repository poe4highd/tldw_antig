import os
import json
import time
import asyncio
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import re

from downloader import download_audio
from transcriber import transcribe_audio
from processor import split_into_paragraphs, get_youtube_thumbnail_url

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DOWNLOADS_DIR = "downloads"
RESULTS_DIR = "results"

for d in [DOWNLOADS_DIR, RESULTS_DIR]:
    if not os.path.exists(d):
        os.makedirs(d)

class ProcessRequest(BaseModel):
    url: str
    mode: str = "cloud"

def save_status(task_id, status, progress, eta=None):
    with open(f"{RESULTS_DIR}/{task_id}_status.json", "w") as f:
        json.dump({"status": status, "progress": progress, "eta": eta}, f)

async def background_process(task_id, url, mode):
    try:
        # 0. Get ID
        video_id = ""
        # 尝试从常见格式提取 ID
        id_match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11})", url)
        if id_match:
            video_id = id_match.group(1)
        else:
            # 回退使用 hash
            import hashlib
            video_id = hashlib.md5(url.encode()).hexdigest()[:11]

        save_status(task_id, "正在获取视频信息并下载音频...", 20, eta=45)
        
        # 1. Download (Check cache)
        file_path = f"{DOWNLOADS_DIR}/{video_id}.mp3"
        v_file_path = f"{DOWNLOADS_DIR}/{video_id}.mp4"
        
        # 获取基础信息
        import yt_dlp
        with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
            info = ydl.extract_info(url, download=False)
            title = info.get('title', 'Unknown Title')
            thumbnail = info.get('thumbnail')
        
        if os.path.exists(file_path):
            save_status(task_id, "检测到缓存数据，正在准备转录...", 40, eta=30 if mode == "cloud" else 150)
        else:
            save_status(task_id, "正在下载音频并提取元数据...", 40, eta=35 if mode == "cloud" else 160)
            file_path, _, _ = download_audio(url, output_path=DOWNLOADS_DIR)
        
        # 2. Transcribe
        save_status(task_id, f"正在进行 AI 语音转录 ({'云端模式' if mode == 'cloud' else '本地精调模式'})...", 60, eta=25 if mode == "cloud" else 120)
        raw_subtitles = transcribe_audio(file_path, mode=mode)
        
        # 计算音频时长 (秒)
        duration = 0
        if raw_subtitles:
            duration = raw_subtitles[-1]["end"]
        
        # 3. LLM Processing (Paragraphing)
        save_status(task_id, "正在通过 LLM 进行深度语义分割与润色...", 80, eta=10)
        paragraphs, llm_usage = split_into_paragraphs(raw_subtitles)
        
        # 费用计算 (估算)
        whisper_cost = (duration / 60.0) * 0.006 if mode == "cloud" else 0
        llm_cost = (llm_usage["prompt_tokens"] / 1000000.0 * 0.15) + (llm_usage["completion_tokens"] / 1000000.0 * 0.6)
        total_cost = whisper_cost + llm_cost
        
        # 4. Save result
        result = {
            "title": title,
            "url": url,
            "youtube_id": video_id,
            "thumbnail": thumbnail or get_youtube_thumbnail_url(url),
            "media_path": os.path.basename(file_path),
            "paragraphs": paragraphs,
            "usage": {
                "duration": round(duration, 2),
                "whisper_cost": round(whisper_cost, 6),
                "llm_tokens": llm_usage,
                "llm_cost": round(llm_cost, 6),
                "total_cost": round(total_cost, 6),
                "currency": "USD"
            },
            "raw_subtitles": raw_subtitles
        }
        with open(f"{RESULTS_DIR}/{task_id}.json", "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"--- [Task {task_id}] Task completed successfully! ---")
            
        # Cleanup old
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
async def process_video(request: ProcessRequest, background_tasks: BackgroundTasks):
    task_id = str(int(time.time()))
    save_status(task_id, "queued", 0)
    background_tasks.add_task(background_process, task_id, request.url, request.mode)
    return {"task_id": task_id}

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
    raise HTTPException(status_code=404, detail="Task not found")

@app.get("/history")
async def get_history():
    history_dict = {}
    total_stats = {"total_duration": 0, "total_cost": 0, "video_count": 0}
    
    files = [f for f in os.listdir(RESULTS_DIR) if f.endswith(".json") and not f.endswith("_error.json") and not f.endswith("_status.json")]
    
    # 获取所有文件的信息并缓存
    file_infos = []
    for f in files:
        f_path = os.path.join(RESULTS_DIR, f)
        mtime = os.path.getmtime(f_path)
        file_infos.append((f, mtime))
    
    # 按时间降序排序
    file_infos.sort(key=lambda x: x[1], reverse=True)
    
    for f, mtime in file_infos:
        task_id = f.replace(".json", "")
        with open(os.path.join(RESULTS_DIR, f), "r") as r:
            try:
                data = json.load(r)
                url = data.get("url")
                yt_id = data.get("youtube_id")
                if not url: continue
                
                # 使用 youtube_id 去重比 raw url 更准确
                unique_key = yt_id if yt_id else url
                
                usage = data.get("usage", {})
                duration = usage.get("duration", 0)
                cost = usage.get("total_cost", 0)
                
                if unique_key not in history_dict:
                    history_dict[unique_key] = {
                        "id": task_id,
                        "title": data.get("title"),
                        "thumbnail": data.get("thumbnail") or get_youtube_thumbnail_url(url),
                        "url": url,
                        "mtime": mtime,
                        "total_cost": round(cost, 4)
                    }
                    total_stats["total_duration"] += duration
                    total_stats["total_cost"] += cost
                    total_stats["video_count"] += 1
            except:
                continue
                
    return {
        "items": sorted(history_dict.values(), key=lambda x: x["mtime"], reverse=True),
        "summary": {
            "total_duration": total_stats["total_duration"],
            "total_cost": round(total_stats["total_cost"], 4),
            "video_count": total_stats["video_count"]
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
