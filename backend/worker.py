#!/usr/bin/env python3
"""
独立的转录任务 Worker
用于在独立进程中执行转录任务,避免 MLX/Torch Metal GPU 冲突
"""
import os
import sys
import json
import argparse
import traceback

# 设置环境变量(必须在导入任何库之前)
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
os.environ['OMP_NUM_THREADS'] = '1'
os.environ['MKL_NUM_THREADS'] = '1'
os.environ['KMP_BLOCKTIME'] = '0'

from transcriber import transcribe_audio
from processor import split_into_paragraphs
from sub_utils import find_downloaded_subtitles, parse_vtt_srt

RESULTS_DIR = "results"
CACHE_DIR = "cache"

def save_status(task_id, status, progress, eta=None):
    """保存任务状态"""
    status_file = f"{RESULTS_DIR}/{task_id}_status.json"
    with open(status_file, "w") as f:
        json.dump({
            "status": status, 
            "progress": progress, 
            "eta": eta
        }, f)

def main():
    parser = argparse.ArgumentParser(description='转录任务 Worker')
    parser.add_argument('task_id', help='任务ID')
    parser.add_argument('mode', choices=['cloud', 'local'], help='转录模式')
    parser.add_argument('--file', help='音频文件路径')
    parser.add_argument('--title', help='视频标题')
    parser.add_argument('--description', default='', help='视频描述')
    parser.add_argument('--video-id', help='YouTube 视频ID')
    parser.add_argument('--model', default='large-v3-turbo', help='模型名称')
    
    args = parser.parse_args()
    
    try:
        # 检查缓存
        cache_key = f"{args.video_id or args.task_id}_{args.mode}_{args.model}"
        cache_sub_path = f"{CACHE_DIR}/{cache_key}_raw.json"
        
        if os.path.exists(cache_sub_path):
            save_status(args.task_id, "loading_cache", 50, eta=5)
            print(f"[Worker] 使用缓存: {cache_sub_path}")
            with open(cache_sub_path, "r", encoding="utf-8") as rf:
                raw_subtitles = json.load(rf)
        else:
            # 尝试拦截现有字幕
            hijacked_sub_path = find_downloaded_subtitles(args.video_id) if args.video_id else None
            
            if hijacked_sub_path:
                save_status(args.task_id, "importing_subtitles", 55, eta=5)
                print(f"[Worker] 拦截到字幕文件: {hijacked_sub_path}")
                raw_subtitles = parse_vtt_srt(hijacked_sub_path)
                
                if not raw_subtitles:
                    print(f"[Worker] 警告: 字幕文件解析为空，将回退至正常转录流程")
                    hijacked_sub_path = None
            
            if not hijacked_sub_path:
                # 执行转录
                save_status(
                    args.task_id,
                    "transcribing_cloud" if args.mode == 'cloud' else "transcribing_local",
                    60,
                    eta=25 if args.mode == 'cloud' else 120
                )
                print(f"[Worker] 开始转录: {args.file} (模式: {args.mode}, 模型: {args.model})")
                print(f"[Worker] 提示词: {args.title}")
                
                raw_subtitles = transcribe_audio(
                    args.file, 
                    mode=args.mode, 
                    initial_prompt=args.title,
                    model_size=args.model
                )
            
            # 保存缓存
            with open(cache_sub_path, "w", encoding="utf-8") as wf:
                json.dump(raw_subtitles, wf, ensure_ascii=False)
            print(f"[Worker] 转录/导入完成,已保存缓存")
        
        # LLM 处理
        duration = raw_subtitles[-1]["end"] if raw_subtitles else 0
        save_status(args.task_id, "llm_processing", 80, eta=10)
        print(f"[Worker] 开始 LLM 处理...")
        
        paragraphs, llm_usage = split_into_paragraphs(
            raw_subtitles, 
            title=args.title, 
            description=args.description
        )
        
        # 8.5 提炼摘要与关键词 (新步骤)
        print(f"[Worker] 开始提取全文摘要与关键词...")
        from processor import summarize_text
        full_text = ""
        for p in paragraphs:
            for s in p["sentences"]:
                start_sec = int(s.get("start", 0))
                h, r = divmod(start_sec, 3600)
                m, s_v = divmod(r, 60)
                ts = f"[{h:02d}:{m:02d}:{s_v:02d}]" if h > 0 else f"[{m:02d}:{s_v:02d}]"
                full_text += f"{ts} {s['text']}\n"
        
        summary_data, summary_usage = summarize_text(
            full_text,
            title=args.title,
            description=args.description
        )
        
        # 合并 LLM Usage
        llm_usage["prompt_tokens"] += summary_usage.get("prompt_tokens", 0)
        llm_usage["completion_tokens"] += summary_usage.get("completion_tokens", 0)
        llm_usage["total_tokens"] += summary_usage.get("total_tokens", 0)

        # 计算成本
        whisper_cost = (duration / 60.0) * 0.006 if args.mode == "cloud" else 0
        llm_cost = (llm_usage["prompt_tokens"] / 1000000.0 * 0.15) + \
                   (llm_usage["completion_tokens"] / 1000000.0 * 0.6)
        
        # 保存最终结果
        result = {
            "title": args.title,
            "url": "N/A",  # 由主进程填充
            "youtube_id": args.video_id,
            "thumbnail": None,  # 由主进程填充
            "media_path": os.path.basename(args.file) if args.file else None,
            "summary": summary_data.get("summary", ""),
            "keywords": summary_data.get("keywords", []),
            "paragraphs": paragraphs,
            "usage": {
                "duration": round(duration, 2),
                "whisper_cost": round(whisper_cost, 6),
                "llm_tokens": llm_usage,
                "llm_cost": round(llm_cost, 6),
                "total_cost": round(whisper_cost + llm_cost, 6),
                "currency": "USD",
                "model": os.getenv("OLLAMA_MODEL", "qwen:8b") if os.getenv("LLM_PROVIDER") == "ollama" else "gpt-4o-mini"
            },
            "raw_subtitles": raw_subtitles,
            "user_id": None  # 由主进程填充
        }
        
        result_file = f"{RESULTS_DIR}/{args.task_id}.json"
        with open(result_file, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        save_status(args.task_id, "completed", 100)
        print(f"[Worker] 任务完成: {result_file}")
        sys.exit(0)
        
    except Exception as e:
        error_msg = str(e)
        error_trace = traceback.format_exc()
        print(f"[Worker] 错误: {error_msg}", file=sys.stderr)
        print(error_trace, file=sys.stderr)
        
        error_file = f"{RESULTS_DIR}/{args.task_id}_error.json"
        with open(error_file, "w") as f:
            json.dump({
                "error": error_msg,
                "traceback": error_trace
            }, f)
        
        save_status(args.task_id, "failed", 100)
        sys.exit(1)

if __name__ == "__main__":
    main()
