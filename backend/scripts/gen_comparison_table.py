#!/usr/bin/env python3
"""
生成四列逐句对比表格：GT | raw Whisper | gpt-4o-mini | gemma4:e4b
以 GT 句子时间轴为基准，其他来源按时间区间对齐，供逐句核查。
"""
import json
import xml.etree.ElementTree as ET
import os
import sys

VIDEO_ID = "QVBpiuph3rM"
BASE = os.path.join(os.path.dirname(__file__), "..", "..")

GT_PATH       = os.path.join(BASE, f"backend/tests/data/{VIDEO_ID}.zh-CN.srv1")
RAW_PATH      = os.path.join(BASE, f"backend/cache/{VIDEO_ID}_local_large-v3-turbo_raw.json")
GPT_PATH      = os.path.join(BASE, f"backend/results/eval_gpt-4o-mini_{VIDEO_ID}.json")
GEMMA_V1_PATH = os.path.join(BASE, f"backend/results/eval_gemma4_e4b_{VIDEO_ID}.json")
GEMMA_V2_PATH = os.path.join(BASE, f"backend/results/eval_gemma4_e4b-v2_{VIDEO_ID}.json")
OUT_PATH      = os.path.join(BASE, f"backend/validation/{VIDEO_ID}_5way_comparison.md")


def load_gt(path):
    """返回 [(start, end, text), ...]"""
    tree = ET.parse(path)
    rows = []
    for t in tree.getroot().findall("text"):
        start = float(t.get("start", 0))
        dur   = float(t.get("dur", 0))
        text  = (t.text or "").strip()
        if text:
            rows.append((start, start + dur, text))
    return rows


def load_raw(path):
    """Whisper cache: [{start, end, text}, ...]"""
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    rows = []
    for s in data:
        start = float(s.get("start", 0))
        end   = float(s.get("end", start + 1))
        text  = (s.get("text") or "").strip()
        if text:
            rows.append((start, end, text))
    return rows


def load_result(path):
    """矫正结果 JSON: {paragraphs: [{sentences: [{start, text}]}]}"""
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    rows = []
    paragraphs = data.get("paragraphs", [])
    for p in paragraphs:
        sentences = p.get("sentences", [])
        for i, s in enumerate(sentences):
            start = float(s.get("start", 0))
            # end 用下一句 start 近似；最后一句加 10s
            if i + 1 < len(sentences):
                end = float(sentences[i + 1].get("start", start + 5))
            else:
                end = start + 10
            text = (s.get("text") or "").strip()
            if text:
                rows.append((start, end, text))
    return rows


def find_overlap(rows, gt_start, gt_end, tol=0.5):
    """找与 [gt_start, gt_end] 时间区间有重叠的所有句子，返回拼接文本。"""
    matched = []
    for (s, e, text) in rows:
        # 宽松匹配：句子开始在 GT 区间内，或 GT 开始在句子区间内
        if s < gt_end + tol and e > gt_start - tol:
            matched.append(text)
    return " ".join(matched)


def escape_cell(text):
    """Markdown 表格单元格转义。"""
    return text.replace("|", "｜").replace("\n", " ")


def main():
    gt_rows      = load_gt(GT_PATH)
    raw_rows     = load_raw(RAW_PATH)
    gpt_rows     = load_result(GPT_PATH)
    gemma_v1_rows = load_result(GEMMA_V1_PATH)
    gemma_v2_rows = load_result(GEMMA_V2_PATH)

    lines = [
        "| 参考文本 (GT) | raw Whisper | gpt-4o-mini | gemma4:e4b V1 | gemma4:e4b V2 |",
        "| :--- | :--- | :--- | :--- | :--- |",
    ]

    for (gt_s, gt_e, gt_text) in gt_rows:
        raw_text    = find_overlap(raw_rows,      gt_s, gt_e)
        gpt_text    = find_overlap(gpt_rows,      gt_s, gt_e)
        gemv1_text  = find_overlap(gemma_v1_rows, gt_s, gt_e)
        gemv2_text  = find_overlap(gemma_v2_rows, gt_s, gt_e)
        lines.append(
            f"| {escape_cell(gt_text)} "
            f"| {escape_cell(raw_text)} "
            f"| {escape_cell(gpt_text)} "
            f"| {escape_cell(gemv1_text)} "
            f"| {escape_cell(gemv2_text)} |"
        )

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    print(f"生成完成：{OUT_PATH}（共 {len(gt_rows)} 行）")


if __name__ == "__main__":
    main()
