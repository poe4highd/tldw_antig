#!/usr/bin/env python3
"""
从缓存重新处理LLM校正（支持幻觉检测与二次转录）。

用法: 
  python reprocess_from_cache.py <video_id> [title] [--detect-hallucination]

示例: 
  python reprocess_from_cache.py 0_zgry0AGqU "灵修与明白神的旨意" --detect-hallucination
"""

import json
import sys
import os
import glob
import argparse
from dotenv import load_dotenv

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from processor import split_into_paragraphs
from db import get_db

load_dotenv(os.path.join(os.path.dirname(__file__), '../.env'))

def find_cache_file(video_id: str) -> str:
    """查找视频对应的缓存文件"""
    cache_dir = os.path.join(os.path.dirname(__file__), '../cache')
    pattern = os.path.join(cache_dir, f"{video_id}*_raw.json")
    matches = glob.glob(pattern)
    if matches:
        return matches[0]
    return None

def find_audio_file(video_id: str) -> str:
    """查找视频对应的音频文件"""
    downloads_dir = os.path.join(os.path.dirname(__file__), '../downloads')
    for ext in ['.m4a', '.mp3', '.wav', '.webm']:
        path = os.path.join(downloads_dir, f"{video_id}{ext}")
        if os.path.exists(path):
            return path
    return None

def format_subtitles_for_llm(subtitles: list) -> list:
    """
    格式化字幕，将幻觉区域和备选字幕标记出来供LLM处理
    """
    formatted = []
    for seg in subtitles:
        text = seg.get("text", "")
        start = seg.get("start", 0)
        
        if seg.get("_hallucination_flag"):
            # 标记幻觉区域
            alt_subs = seg.get("_alternative_subtitles", [])
            alt_text = " ".join([s.get("text", "") for s in alt_subs]) if alt_subs else ""
            
            formatted.append({
                "start": start,
                "text": f"[HALLUCINATION] {text}",
                "words": seg.get("words", [])
            })
            
            if alt_text:
                # 添加备选字幕（使用备选的时间戳）
                alt_start = alt_subs[0].get("start", start) if alt_subs else start
                formatted.append({
                    "start": alt_start,
                    "text": f"[ALT:] {alt_text}",
                    "words": []
                })
        else:
            formatted.append({
                "start": start,
                "text": text,
                "words": seg.get("words", [])
            })
    
    return formatted

def reprocess_from_cache(video_id: str, title: str = "", detect_hallucination: bool = False):
    """从缓存重新处理LLM校正"""
    cache_file = find_cache_file(video_id)
    if not cache_file:
        print(f"错误: 找不到视频 {video_id} 的缓存文件")
        return False
    
    print(f"找到缓存: {cache_file}")
    
    with open(cache_file, 'r', encoding='utf-8') as f:
        raw_subtitles = json.load(f)
    
    print(f"原始片段数: {len(raw_subtitles)}")
    
    # 如果没有指定标题，尝试从数据库获取
    if not title:
        supabase = get_db()
        if supabase:
            try:
                response = supabase.table("videos").select("title, description").eq("id", video_id).execute()
                if response.data:
                    title = response.data[0].get("title", "")
                    print(f"从数据库获取标题: {title}")
            except Exception as e:
                print(f"获取标题失败: {e}")
    
    print(f"使用标题: {title or '(无)'}")
    
    # 幻觉检测与二次转录
    if detect_hallucination:
        print("--- 启用幻觉检测模式 ---")
        from hallucination_detector import process_with_hallucination_detection
        
        audio_file = find_audio_file(video_id)
        if audio_file:
            print(f"找到音频: {audio_file}")
            raw_subtitles = process_with_hallucination_detection(
                audio_file, raw_subtitles
            )
            # 格式化字幕以包含幻觉/补漏标记
            raw_subtitles = format_subtitles_for_llm(raw_subtitles)
        else:
            print("警告: 未找到音频文件，跳过二次转录")
    
    print("开始LLM校正...")
    
    paragraphs, usage = split_into_paragraphs(raw_subtitles, title=title)
    
    print(f"输出段落数: {len(paragraphs)}")
    print(f"Token用量: {usage}")
    
    # 更新数据库
    supabase = get_db()
    if supabase and paragraphs:
        try:
            # 先获取现有的 report_data
            res = supabase.table("videos").select("report_data, usage").eq("id", video_id).execute()
            if res.data:
                existing_report = res.data[0].get("report_data") or {}
                existing_usage = res.data[0].get("usage") or {}
                
                # 更新内部字段
                existing_report["paragraphs"] = paragraphs
                
                # 更新 usage
                if isinstance(usage, dict):
                    if "llm_tokens" not in existing_usage:
                        existing_usage["llm_tokens"] = {}
                    existing_usage["llm_tokens"] = usage
                
                supabase.table("videos").update({
                    "report_data": existing_report,
                    "usage": existing_usage
                }).eq("id", video_id).execute()
                print("✅ 已更新数据库 (report_data.paragraphs)")
            else:
                print(f"错误: 数据库中找不到 ID 为 {video_id} 的视频")
        except Exception as e:
            print(f"更新数据库失败: {e}")
    
    # 保存本地备份
    output_file = os.path.join(os.path.dirname(__file__), f'../results/{video_id}_reprocessed.json')
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({"paragraphs": paragraphs, "usage": usage}, f, ensure_ascii=False, indent=2)
    print(f"✅ 已保存到: {output_file}")
    
    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="从缓存重新处理LLM校正")
    parser.add_argument("video_id", help="视频ID")
    parser.add_argument("title", nargs="?", default="", help="视频标题（可选）")
    parser.add_argument("--detect-hallucination", "-d", action="store_true",
                        help="启用幻觉检测与二次转录")
    
    args = parser.parse_args()
    
    reprocess_from_cache(args.video_id, args.title, args.detect_hallucination)
