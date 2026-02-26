#!/usr/bin/env python3
"""
test_regenerate_summaries.py
重新生成最近 10 个视频的 AI 摘要，并验证时间戳是否严格递增。

用法：
    # 正式执行（写入数据库 + 本地 JSON）
    python tests/test_regenerate_summaries.py

    # 仅预览，不写入任何数据
    python tests/test_regenerate_summaries.py --dry-run

    # 指定数量（默认 10）
    python tests/test_regenerate_summaries.py --limit 5
"""

import os
import sys
import re
import json
import argparse
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '../.env'))

from supabase import create_client, Client
from processor import summarize_text

# ── Supabase 连接 ────────────────────────────────────────────────────────────
supabase_url = os.environ.get("SUPABASE_URL")
supabase_key = os.environ.get("SUPABASE_SERVICE_KEY")
if not supabase_url or not supabase_key:
    print("❌ 缺少 SUPABASE_URL 或 SUPABASE_SERVICE_KEY 环境变量")
    sys.exit(1)

db: Client = create_client(supabase_url, supabase_key)

RESULTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../results'))


# ── 工具函数 ─────────────────────────────────────────────────────────────────

def ts_to_sec(ts_str: str) -> int:
    """将 [MM:SS] 或 [HH:MM:SS] 转换为秒数，未匹配返回 -1。"""
    m = re.search(r'\[(\d{2}):(\d{2})(?::(\d{2}))?\]', ts_str)
    if not m:
        return -1
    if m.group(3):
        return int(m.group(1)) * 3600 + int(m.group(2)) * 60 + int(m.group(3))
    return int(m.group(1)) * 60 + int(m.group(2))


def check_timestamps_ordered(summary: str) -> tuple[bool, list[int]]:
    """
    检查摘要中各行时间戳是否严格递增。
    返回 (is_ordered, [秒数列表])
    """
    lines = [l for l in summary.split('\n') if l.strip()]
    seconds = []
    for line in lines:
        s = ts_to_sec(line)
        if s >= 0:
            seconds.append(s)
    if len(seconds) < 2:
        return True, seconds
    ordered = all(seconds[i] < seconds[i + 1] for i in range(len(seconds) - 1))
    return ordered, seconds


def build_full_text(paragraphs: list) -> str:
    """将 paragraphs 结构转换为带时间戳的纯文本，供 summarize_text 使用。"""
    full_text = ""
    for p in paragraphs:
        for s in p.get("sentences", []):
            start_sec = int(s.get("start", 0))
            h, r = divmod(start_sec, 3600)
            mn, sv = divmod(r, 60)
            ts = f"[{h:02d}:{mn:02d}:{sv:02d}]" if h > 0 else f"[{mn:02d}:{sv:02d}]"
            full_text += f"{ts} {s.get('text', '')}\n"
    return full_text


def get_paragraphs(task: dict) -> list | None:
    """
    按优先级获取 paragraphs：
    1. 本地 results/{task_id}.json
    2. Supabase report_data.paragraphs
    """
    task_id = task["id"]

    # 优先本地文件
    local_path = os.path.join(RESULTS_DIR, f"{task_id}.json")
    if os.path.exists(local_path):
        with open(local_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        paragraphs = data.get("paragraphs", [])
        if paragraphs:
            return paragraphs, local_path, data

    # 从 Supabase report_data 取
    report = task.get("report_data") or {}
    paragraphs = report.get("paragraphs", [])
    if paragraphs:
        return paragraphs, None, report

    return None, None, None


# ── 主逻辑 ───────────────────────────────────────────────────────────────────

def run(limit: int = 10, dry_run: bool = False):
    mode_label = "[DRY-RUN] " if dry_run else ""
    print(f"\n{'='*60}")
    print(f"  {mode_label}重新生成最近 {limit} 个视频的摘要")
    print(f"  时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")

    # 拉取最近 N 条已完成任务
    resp = db.table("videos") \
        .select("id, title, report_data") \
        .eq("status", "completed") \
        .order("created_at", desc=True) \
        .limit(limit) \
        .execute()
    tasks = resp.data

    if not tasks:
        print("未找到已完成的任务。")
        return

    results = []

    for i, task in enumerate(tasks):
        task_id = task["id"]
        title = task.get("title", "（无标题）")
        print(f"[{i+1}/{len(tasks)}] {task_id}  {title[:40]}")

        paragraphs, local_path, raw_data = get_paragraphs(task)
        if not paragraphs:
            print(f"         ⚠️  找不到 paragraphs，跳过\n")
            results.append({"id": task_id, "title": title, "status": "skipped", "reason": "no paragraphs"})
            continue

        full_text = build_full_text(paragraphs)

        # 生成新摘要
        summary_data, usage = summarize_text(
            full_text,
            title=raw_data.get("title", title),
            description=raw_data.get("description", "")
        )
        new_summary = summary_data.get("summary", "")
        new_keywords = summary_data.get("keywords", [])

        if not new_summary:
            print(f"         ❌  摘要生成失败\n")
            results.append({"id": task_id, "title": title, "status": "failed", "reason": "empty summary"})
            continue

        # 验证时间戳顺序
        ordered, seconds = check_timestamps_ordered(new_summary)
        order_label = "✅ 有序" if ordered else "⚠️  乱序"
        print(f"         时间戳: {[f'{s//60:02d}:{s%60:02d}' for s in seconds]}  {order_label}")
        print(f"         条目数: {len([l for l in new_summary.split(chr(10)) if l.strip()])}")

        if not dry_run:
            # 更新本地 JSON（如果存在）
            if local_path and os.path.exists(local_path):
                with open(local_path, "r", encoding="utf-8") as f:
                    file_data = json.load(f)
                file_data["summary"] = new_summary
                file_data["keywords"] = new_keywords
                with open(local_path, "w", encoding="utf-8") as f:
                    json.dump(file_data, f, ensure_ascii=False, indent=2)
                print(f"         💾  本地 JSON 已更新: {os.path.basename(local_path)}")

            # 更新 Supabase
            report = task.get("report_data") or {}
            report["summary"] = new_summary
            report["keywords"] = new_keywords
            db.table("videos").update({"report_data": report}).eq("id", task_id).execute()
            print(f"         ☁️   Supabase 已更新")
        else:
            print(f"         (dry-run: 跳过写入)")

        results.append({
            "id": task_id,
            "title": title,
            "status": "ok",
            "timestamps_ordered": ordered,
            "item_count": len([l for l in new_summary.split('\n') if l.strip()]),
            "tokens": usage.get("total_tokens", 0)
        })
        print()

    # ── 汇总报告 ──────────────────────────────────────────────────────────────
    print(f"\n{'='*60}")
    print(f"  汇总报告")
    print(f"{'='*60}")
    ok       = [r for r in results if r["status"] == "ok"]
    skipped  = [r for r in results if r["status"] == "skipped"]
    failed   = [r for r in results if r["status"] == "failed"]
    disordered = [r for r in ok if not r.get("timestamps_ordered", True)]

    print(f"  成功:    {len(ok)}")
    print(f"  跳过:    {len(skipped)}")
    print(f"  失败:    {len(failed)}")
    print(f"  时间乱序: {len(disordered)}")
    if disordered:
        print(f"  ⚠️  以下视频时间戳仍乱序（AI 未遵守指令）：")
        for r in disordered:
            print(f"     - {r['id']}  {r['title'][:40]}")
    else:
        print(f"  ✅  所有成功视频时间戳均为递增顺序")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="重新生成最近 N 个视频的 AI 摘要并验证时间戳顺序")
    parser.add_argument("--limit", type=int, default=10, help="处理的视频数量（默认 10）")
    parser.add_argument("--dry-run", action="store_true", help="仅预览，不写入任何数据")
    args = parser.parse_args()
    run(limit=args.limit, dry_run=args.dry_run)
