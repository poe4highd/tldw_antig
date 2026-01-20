#!/usr/bin/env python3
import json
import sys
import os

def analyze_gaps(cache_file, normal_cps=3.5, gap_threshold=2.0):
    if not os.path.exists(cache_file):
        print(f"Error: {cache_file} not found")
        return

    with open(cache_file, 'r', encoding='utf-8') as f:
        subs = json.load(f)

    print(f"Analyzing {cache_file}...")
    print(f"{'Index':<6} | {'Start':<8} | {'Gap':<6} | {'Text':<30} | {'Status'}")
    print("-" * 80)

    for i in range(1, len(subs)):
        curr = subs[i]
        prev = subs[i-1]
        
        # 计算当前片段和上一个片段结束之间的间隙
        # 或者计算当前片段内部的密度
        gap = curr['start'] - prev['end']
        duration = curr['end'] - curr['start']
        text_len = len(curr['text'].strip())
        
        # 逻辑1：段间大空隙
        if gap > gap_threshold:
            print(f"{i:<6} | {curr['start']:<8.2f} | {gap:<6.2f}s | {curr['text'][:30]:<30} | [GAP DETECTED]")
            
        # 逻辑2：段内密度过低（幻觉或由于漏字导致的时间轴拉长）
        if duration > 5.0 and text_len > 0:
            cps = text_len / duration
            if cps < 1.0: # 语速低于1字/秒，可能有漏字
                estimated_missing = int((duration - (text_len / normal_cps)) * normal_cps)
                if estimated_missing > 5:
                    print(f"{i:<6} | {curr['start']:<8.2f} | {'-':<6} | {curr['text'][:30]:<30} | [LOW DENSITY] ~Est. missing: {estimated_missing} chars")

if __name__ == "__main__":
    video_id = "0_zgry0AGqU"
    cache_path = f"backend/cache/{video_id}_local_large-v3-turbo_raw.json"
    analyze_gaps(cache_path)
