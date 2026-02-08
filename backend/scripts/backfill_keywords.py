#!/usr/bin/env python3
import os
import sys
import json
import time

# 添加父目录到路径以便导入
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db import get_db
from processor import summarize_text

def backfill():
    supabase = get_db()
    if not supabase:
        print("Error: Supabase client not initialized.")
        return

    print("--- Starting Keywords Backfill ---")
    
    # 1. 获取所有视频
    response = supabase.table("videos").select("id, title, report_data").execute()
    videos = response.data
    print(f"Total videos to check: {len(videos)}")

    for v in videos:
        vid = v["id"]
        title = v["title"]
        report_data = v.get("report_data", {})
        existing_keywords = report_data.get("keywords", [])
        
        # 如果关键词为空，执行重新提取
        if not existing_keywords or len(existing_keywords) == 0:
            print(f"\nProcessing [{vid}] {title}...")
            
            # 拼接全文
            paragraphs = report_data.get("paragraphs")
            full_text = ""
            if paragraphs:
                for p in paragraphs:
                    if p and "sentences" in p:
                        sentences = p.get("sentences")
                        if sentences:
                            for s in sentences:
                                full_text += s.get("text", "")
            
            if not full_text:
                print(f"Skipping {vid}: No transcription text found.")
                continue
                
            # 调用 LLM 重新提取
            description = report_data.get("description", "")
            try:
                # 重新提取摘要和关键词
                summary_data, usage = summarize_text(full_text, title=title, description=description)
                keywords = summary_data.get("keywords", [])
                summary = summary_data.get("summary", "")
                
                if keywords:
                    print(f"Extracted Keywords: {keywords}")
                    
                    # 更新 report_data
                    report_data["keywords"] = keywords
                    report_data["summary"] = summary
                    
                    # 更新数据库 videos 表
                    supabase.table("videos").update({"report_data": report_data}).eq("id", vid).execute()
                    
                    # 尝试同步到关系表 (keywords / video_keywords)
                    # 如果表不存在，此步会打印错误但不会中断整个回填
                    try:
                        for kw in keywords:
                            kw_clean = kw.strip()
                            if not kw_clean: continue
                            
                            # 获取或创建关键词
                            kw_res = supabase.table("keywords").select("id, count").eq("name", kw_clean).execute()
                            if kw_res.data:
                                kw_id = kw_res.data[0]["id"]
                                new_count = (kw_res.data[0]["count"] or 0) + 1
                                supabase.table("keywords").update({"count": new_count}).eq("id", kw_id).execute()
                            else:
                                new_kw = supabase.table("keywords").insert({"name": kw_clean, "count": 1}).execute()
                                if new_kw.data:
                                    kw_id = new_kw.data[0]["id"]
                                else: continue
                            
                            # 建立关联
                            supabase.table("video_keywords").upsert({
                                "video_id": vid,
                                "keyword_id": kw_id
                            }).execute()
                        print(f"Successfully synced relational keywords for {vid}")
                    except Exception as relational_err:
                        print(f"Warning: Relational sync failed (Keywords tables may not exist yet): {relational_err}")
                else:
                    print(f"LLM returned no keywords for {vid}")
                    
            except Exception as e:
                print(f"Error processing {vid}: {e}")
            
            # 稍作停顿，避免请求过快
            time.sleep(0.5)
        else:
            print(f"Skipping {vid}: Already has {len(existing_keywords)} keywords.")

    print("\n--- Backfill Completed ---")

if __name__ == "__main__":
    backfill()
