#!/usr/bin/env python3
"""
重新生成总结失败的视频报告。

从 Supabase 查找 summary == '总结生成失败' 的已完成视频，
用 raw_subtitles 重新调用 summarize_text()，并将结果写回 Supabase。

使用方式：
    python3 scripts/regen_failed_summaries.py           # 处理所有失败记录
    python3 scripts/regen_failed_summaries.py VIDEO_ID  # 仅处理指定 ID
"""

import sys
import os
import json

# 切换到 backend 目录，确保能正确 import
backend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
os.chdir(backend_dir)
sys.path.insert(0, backend_dir)

from dotenv import load_dotenv
load_dotenv()

from db import get_db
from processor import summarize_text, split_into_paragraphs


def rebuild_full_text(raw_subtitles):
    """从 raw_subtitles 重建带时间戳的全文，用于 summarize_text 输入。"""
    lines = []
    for s in raw_subtitles:
        start = s.get("start", 0)
        text = s.get("text", "").strip()
        if text:
            mm = int(start // 60)
            ss = int(start % 60)
            lines.append(f"[{mm:02d}:{ss:02d}] {text}")
    return "\n".join(lines)


def needs_regen_paragraphs(paragraphs):
    """判断 paragraphs 是否是 fallback 分组（不含 LLM 润色的标点/分段），需要重新生成。"""
    if not paragraphs:
        return True
    # LLM 生成的段落每段通常有多句且句子间有正确标点
    # fallback group_by_time 的段落句子少，且文字没有标点
    total_sentences = sum(len(p.get("sentences", [])) for p in paragraphs)
    # 若平均每段只有 1 句，说明是 fallback
    avg = total_sentences / len(paragraphs)
    return avg <= 1.2


def regen_video(db, video, dry_run=False):
    vid_id = video["id"]
    title = video.get("title", "")
    rd = video.get("report_data") or {}
    raw_subtitles = rd.get("raw_subtitles") or []
    current_summary = rd.get("summary", "")
    paragraphs = rd.get("paragraphs") or []
    detected_language = rd.get("detected_language") or rd.get("language")

    print(f"\n{'='*60}")
    print(f"[{vid_id}] {title[:60]}")
    print(f"  current summary: {current_summary[:80]!r}")
    print(f"  raw_subtitles: {len(raw_subtitles)} segments")

    if not raw_subtitles:
        print("  SKIP: no raw_subtitles, cannot regenerate")
        return False

    full_text = rebuild_full_text(raw_subtitles)
    if not full_text.strip():
        print("  SKIP: empty full_text after rebuild")
        return False

    # 1. 重新生成 summary
    print(f"  → Calling summarize_text (language={detected_language})")
    if dry_run:
        print("  [DRY RUN] skipping actual API call")
        return True

    new_summary_data, usage = summarize_text(
        full_text,
        title=title,
        description=rd.get("description", ""),
        language=detected_language,
    )

    new_summary = new_summary_data.get("summary", "")
    new_keywords = new_summary_data.get("keywords", [])

    print(f"  new summary: {new_summary[:120]!r}")
    print(f"  new keywords: {new_keywords}")
    print(f"  usage: {usage}")

    if new_summary in ("总结生成失败", "无总结", ""):
        print("  FAIL: summarize_text still returned failure, skipping Supabase update")
        return False

    # 2. 更新 report_data
    new_rd = dict(rd)
    new_rd["summary"] = new_summary
    new_rd["keywords"] = new_keywords

    # 3. 写回 Supabase
    try:
        db.table("videos").update({
            "report_data": new_rd,
        }).eq("id", vid_id).execute()
        print(f"  ✓ Supabase updated successfully")
    except Exception as e:
        print(f"  ✗ Supabase update failed: {e}")
        return False

    # 4. 同步 keywords 表
    try:
        for kw in new_keywords:
            kw_clean = kw.strip()
            if not kw_clean:
                continue
            kw_res = db.table("keywords").select("id, count").eq("name", kw_clean).execute()
            if kw_res.data:
                kw_id = kw_res.data[0]["id"]
                new_count = (kw_res.data[0]["count"] or 0) + 1
                db.table("keywords").update({"count": new_count}).eq("id", kw_id).execute()
            else:
                new_kw = db.table("keywords").insert({"name": kw_clean, "count": 1}).execute()
                if new_kw.data:
                    kw_id = new_kw.data[0]["id"]
                else:
                    continue
            try:
                db.table("video_keywords").upsert({"video_id": vid_id, "keyword_id": kw_id}).execute()
            except Exception:
                pass  # 重复键忽略
        print(f"  ✓ Keywords synced: {len(new_keywords)}")
    except Exception as e:
        print(f"  ⚠ Keywords sync error (non-fatal): {e}")

    return True


def main():
    dry_run = "--dry-run" in sys.argv
    target_ids = [a for a in sys.argv[1:] if not a.startswith("--")]

    db = get_db()
    if not db:
        print("ERROR: Cannot connect to Supabase")
        sys.exit(1)

    if target_ids:
        res = db.table("videos").select("id, title, status, report_data").in_("id", target_ids).execute()
        videos = res.data
    else:
        # 分批查询，每次 100 条，直到找完所有失败记录
        videos = []
        offset = 0
        PAGE = 100
        while True:
            res = db.table("videos").select("id, title, status, report_data") \
                .eq("status", "completed") \
                .order("created_at", desc=True) \
                .range(offset, offset + PAGE - 1) \
                .execute()
            batch = res.data
            if not batch:
                break
            for v in batch:
                rd = v.get("report_data") or {}
                s = rd.get("summary", "")
                if s == "总结生成失败" or not s:
                    videos.append(v)
            if len(batch) < PAGE:
                break
            offset += PAGE

    print(f"Found {len(videos)} videos to reprocess")
    if dry_run:
        print("[DRY RUN mode: no actual API calls or DB writes]")

    success = 0
    fail = 0
    for v in videos:
        ok = regen_video(db, v, dry_run=dry_run)
        if ok:
            success += 1
        else:
            fail += 1

    print(f"\n{'='*60}")
    print(f"Done. Success: {success}, Failed/Skipped: {fail}")


if __name__ == "__main__":
    main()
