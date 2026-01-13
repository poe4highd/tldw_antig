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

async def background_process(task_id, url, mode):
    try:
        # 0. Get ID
        video_id = ""
        id_match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11})", url)
        if id_match:
            video_id = id_match.group(1)
        else:
            import hashlib
            video_id = hashlib.md5(url.encode()).hexdigest()[:11]

        # 1. Check if final result exists
        # Note: We usually re-process if user clicks, but if we want true "resume",
        # we check existing JSON. However, task_id is time-based, so it's a new task.
        # We rely on video_id based cache.

        # 2. Information & Download (Checkpoint 1)
        # 支持多种可能的音频后缀
        possible_exts = ["m4a", "mp3", "mp4", "webm"]
        file_path = None
        for ext in possible_exts:
            p = f"{DOWNLOADS_DIR}/{video_id}.{ext}"
            if os.path.exists(p):
                file_path = p
                break

        # 获取元数据
        import yt_dlp
        with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
            try:
                info = ydl.extract_info(url, download=False)
                title = info.get('title', 'Unknown Title')
                thumbnail = info.get('thumbnail')
            except:
                title = "Unknown Title"
                thumbnail = get_youtube_thumbnail_url(url)

        if file_path:
            save_status(task_id, f"检测到本地媒体缓存 ({os.path.basename(file_path)})，跳过下载...", 40, eta=30 if mode == "cloud" else 150)
        else:
            def on_download_progress(p):
                # 将下载进度 0-100% 映射到整体进度的 20%-40%
                current_p = 20 + (p * 0.2)
                save_status(task_id, f"正在下载媒体文件... {p:.1f}%", int(current_p), eta=35)

            save_status(task_id, "开始调度下载任务...", 20, eta=40)
            try:
                file_path, _, _ = download_audio(url, output_path=DOWNLOADS_DIR, progress_callback=on_download_progress)
            except Exception as e:
                raise Exception(f"媒体下载失败: {str(e)}")

        # 3. Transcribe (Checkpoint 2)
        cache_sub_path = f"{CACHE_DIR}/{video_id}_{mode}_raw.json"
        if os.path.exists(cache_sub_path):
            save_status(task_id, "检测到转录缓存，正在加载报告...", 50, eta=5)
            with open(cache_sub_path, "r", encoding="utf-8") as rf:
                raw_subtitles = json.load(rf)
        else:
            save_status(task_id, f"正在进行 AI 语音转录 ({'云端模式' if mode == 'cloud' else '本地精调模式'})...", 60, eta=25 if mode == "cloud" else 120)
            print(f"--- Starting transcription for: {os.path.basename(file_path)} ---")
            raw_subtitles = transcribe_audio(file_path, mode=mode)
            # 保存转录检查点
            with open(cache_sub_path, "w", encoding="utf-8") as wf:
                json.dump(raw_subtitles, wf, ensure_ascii=False)
        
        # 4. LLM Processing (Checkpoint 3)
        duration = 0
        if raw_subtitles:
            duration = raw_subtitles[-1]["end"]
        
        save_status(task_id, "正在通过 LLM 进行深度语义分割与润色...", 80, eta=10)
        paragraphs, llm_usage = split_into_paragraphs(raw_subtitles)
        
        # 5. Final Result
        whisper_cost = (duration / 60.0) * 0.006 if mode == "cloud" else 0
        llm_cost = (llm_usage["prompt_tokens"] / 1000000.0 * 0.15) + (llm_usage["completion_tokens"] / 1000000.0 * 0.6)
        total_cost = whisper_cost + llm_cost
        
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
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        # 如果文件丢失（如下载了一半的 mp3 损坏），通常 os.path.exists 会通过但读取失败，
        # 这里建议简单重置检查点（删除相关损坏文件）
        # if "FFmpeg" in str(e) or "FileNotFound" in str(e):
        #    ...
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
    active_tasks = []
    total_stats = {"total_duration": 0, "total_cost": 0, "video_count": 0}
    
    if not os.path.exists(RESULTS_DIR):
        return {"items": [], "active_tasks": [], "summary": total_stats}

    all_files = os.listdir(RESULTS_DIR)
    
    # 1. 扫描进行中的任务
    status_files = [f for f in all_files if f.endswith("_status.json")]
    for sf in status_files:
        tid = sf.replace("_status.json", "")
        # 如果没有结果文件且没有错误文件，视为进行中
        if not os.path.exists(f"{RESULTS_DIR}/{tid}.json") and not os.path.exists(f"{RESULTS_DIR}/{tid}_error.json"):
            # 检查 mtime，如果超过 1 小时可能已经僵死了，不计入
            mtime = os.path.getmtime(f"{RESULTS_DIR}/{sf}")
            if time.time() - mtime < 3600:
                try:
                    with open(f"{RESULTS_DIR}/{sf}", "r") as f:
                        status_data = json.load(f)
                        active_tasks.append({
                            "id": tid,
                            "status": status_data.get("status", "pending"),
                            "progress": status_data.get("progress", 0),
                            "mtime": mtime
                        })
                except:
                    pass

    # 2. 扫描已完成的任务
    files = [f for f in all_files if f.endswith(".json") and not f.endswith("_error.json") and not f.endswith("_status.json")]
    file_infos = []
    for f in files:
        f_path = os.path.join(RESULTS_DIR, f)
        mtime = os.path.getmtime(f_path)
        file_infos.append((f, mtime))
    
    file_infos.sort(key=lambda x: x[1], reverse=True)
    
    for f, mtime in file_infos:
        task_id = f.replace(".json", "")
        with open(os.path.join(RESULTS_DIR, f), "r") as r:
            try:
                data = json.load(r)
                url = data.get("url")
                yt_id = data.get("youtube_id")
                if not url: continue
                
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
