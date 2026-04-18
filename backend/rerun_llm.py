#!/usr/bin/env python3
"""
重新跑指定任务的 LLM 矫正步骤（不重新转录），更新本地 JSON 和 Supabase。
用法: python rerun_llm.py <task_id> [task_id2 ...]
"""
import os
import sys
import json
from dotenv import load_dotenv
load_dotenv()

from db import get_db
from processor import split_into_paragraphs, summarize_text, detect_language_preference

RESULTS_DIR = "results"
supabase = get_db()


def rerun_task(task_id: str):
    print(f"\n{'='*60}")
    print(f"[RerunLLM] 开始重新处理: {task_id}")

    # 1. 读取本地 JSON（含 raw_subtitles）
    result_file = f"{RESULTS_DIR}/{task_id}.json"
    if not os.path.exists(result_file):
        print(f"[RerunLLM] ERROR: {result_file} 不存在")
        return False

    with open(result_file, "r", encoding="utf-8") as f:
        result = json.load(f)

    raw_subtitles = result.get("raw_subtitles", [])
    if not raw_subtitles:
        print(f"[RerunLLM] ERROR: raw_subtitles 为空，无法重新处理")
        return False

    title = result.get("title", "")
    description = ""
    print(f"[RerunLLM] title={title}, raw_subtitles={len(raw_subtitles)} 句")

    # 2. 重新跑 split_into_paragraphs（现在 ollama 自动用 v2）
    print(f"[RerunLLM] 开始 LLM 段落矫正...")
    paragraphs, llm_usage = split_into_paragraphs(
        raw_subtitles,
        title=title,
        description=description,
    )
    print(f"[RerunLLM] 矫正完成: {len(paragraphs)} 段落, tokens={llm_usage}")

    # 3. 验证标点
    all_text = " ".join(
        s.get("text", "")
        for p in paragraphs
        for s in p.get("sentences", [])
    )
    punct_count = sum(1 for c in all_text if c in "，。？！,.")
    print(f"[RerunLLM] 标点符号数: {punct_count} / {len(all_text)} 字符")
    if punct_count == 0:
        print(f"[RerunLLM] WARNING: 仍然没有标点符号！")

    # 4. 重新跑 summary
    print(f"[RerunLLM] 开始重新生成摘要...")
    full_text = ""
    for p in paragraphs:
        for s in p["sentences"]:
            start_sec = int(s.get("start", 0))
            h, r = divmod(start_sec, 3600)
            m, sv = divmod(r, 60)
            ts = f"[{h:02d}:{m:02d}:{sv:02d}]" if h > 0 else f"[{m:02d}:{sv:02d}]"
            full_text += f"{ts} {s['text']}\n"

    title_lang = detect_language_preference(title, description)
    lang_map = {"english": "en", "simplified": "zh", "traditional": "zh-TW",
                "korean": "ko", "japanese": "ja"}
    detected_language = lang_map.get(title_lang, "zh")

    summary_data, summary_usage = summarize_text(
        full_text, title=title, description=description, language=detected_language
    )
    print(f"[RerunLLM] 摘要完成: summary_len={len(summary_data.get('summary',''))}")

    # 5. 更新 result JSON
    result["paragraphs"] = paragraphs
    result["summary"] = summary_data.get("summary", result.get("summary", ""))
    result["keywords"] = summary_data.get("keywords", result.get("keywords", []))

    # 更新 usage
    old_usage = result.get("usage", {})
    total_prompt = llm_usage.get("prompt_tokens", 0) + summary_usage.get("prompt_tokens", 0)
    total_completion = llm_usage.get("completion_tokens", 0) + summary_usage.get("completion_tokens", 0)
    llm_cost = (total_prompt / 1_000_000 * 0.15) + (total_completion / 1_000_000 * 0.6)
    result["usage"] = {
        **old_usage,
        "llm_tokens": {
            "prompt_tokens": total_prompt,
            "completion_tokens": total_completion,
            "total_tokens": total_prompt + total_completion,
        },
        "llm_cost": round(llm_cost, 6),
        "total_cost": round(old_usage.get("whisper_cost", 0) + llm_cost, 6),
    }

    with open(result_file, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"[RerunLLM] 本地 JSON 已更新: {result_file}")

    # 6. 更新 Supabase
    if supabase:
        try:
            # 读现有 report_data
            db_row = supabase.table("videos").select("report_data").eq("id", task_id).execute()
            existing_report = (db_row.data[0].get("report_data") or {}) if db_row.data else {}

            report_data = {
                **existing_report,
                "paragraphs": paragraphs,
                "summary": result["summary"],
                "keywords": result["keywords"],
            }
            supabase.table("videos").update({
                "report_data": report_data,
                "usage": result["usage"],
            }).eq("id", task_id).execute()
            print(f"[RerunLLM] Supabase 已更新")
        except Exception as e:
            print(f"[RerunLLM] Supabase 更新失败: {e}")

    return True


if __name__ == "__main__":
    task_ids = sys.argv[1:] if len(sys.argv) > 1 else ["up_9f2ea319", "up_820a8fef"]
    for tid in task_ids:
        ok = rerun_task(tid)
        print(f"[RerunLLM] {tid}: {'SUCCESS' if ok else 'FAILED'}")
