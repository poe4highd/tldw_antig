#!/usr/bin/env python3
"""
从缓存重新处理LLM校正。
用法: python reprocess_from_cache.py <video_id> [title]
示例: python reprocess_from_cache.py 0_zgry0AGqU "灵修与明白神的旨意"
"""

import json
import sys
import os
import glob
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

def reprocess_from_cache(video_id: str, title: str = ""):
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
    print("开始LLM校正...")
    
    paragraphs, usage = split_into_paragraphs(raw_subtitles, title=title)
    
    print(f"输出段落数: {len(paragraphs)}")
    print(f"Token用量: {usage}")
    
    # 更新数据库
    supabase = get_db()
    if supabase and paragraphs:
        try:
            supabase.table("videos").update({
                "paragraphs": paragraphs,
                "usage": {"llm_tokens": usage}
            }).eq("id", video_id).execute()
            print("✅ 已更新数据库")
        except Exception as e:
            print(f"更新数据库失败: {e}")
    
    # 保存本地备份
    output_file = os.path.join(os.path.dirname(__file__), f'../results/{video_id}_reprocessed.json')
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({"paragraphs": paragraphs, "usage": usage}, f, ensure_ascii=False, indent=2)
    print(f"✅ 已保存到: {output_file}")
    
    return True

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python reprocess_from_cache.py <video_id> [title]")
        print("示例: python reprocess_from_cache.py 0_zgry0AGqU \"灵修与明白神的旨意\"")
        sys.exit(1)
    
    video_id = sys.argv[1]
    title = sys.argv[2] if len(sys.argv) > 2 else ""
    
    reprocess_from_cache(video_id, title)
