import json
import os
import xml.etree.ElementTree as ET
import re

def parse_srv1(path):
    tree = ET.parse(path)
    root = tree.getroot()
    segments = []
    for t in root.findall('text'):
        start = float(t.get('start', 0))
        dur = float(t.get('dur', 0))
        text = t.text if t.text else ""
        segments.append({"start": start, "end": start + dur, "text": text.strip()})
    return segments

def parse_raw_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return [{"start": s['start'], "end": s['end'], "text": s['text'].strip()} for s in data]

def parse_result_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    sentences = []
    for p in data.get("paragraphs", []):
        for s in p.get("sentences", []):
            sentences.append({"start": s['start'], "text": s['text'].strip()})
    return sentences

def find_text_at(time, source_list):
    # 对于带有 start/end 的 raw 模型
    # 或者仅有 start 的校正模型
    best_text = ""
    for item in source_list:
        if 'end' in item:
            if item['start'] <= time <= item['end']:
                return item['text']
        else:
            # 寻找最接近的时间点
            if abs(item['start'] - time) < 3.0: # 3秒内容差
                return item['text']
    return ""

def clean(t):
    return re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9]', '', t)

def main():
    ref_path = "backend/tests/data/QVBpiuph3rM.zh-CN.srv1"
    s0_path = "backend/cache/QVBpiuph3rM_local_raw.json"
    sm_path = "backend/cache/QVBpiuph3rM_local_medium_raw.json"
    st_path = "backend/cache/QVBpiuph3rM_local_large-v3-turbo_raw.json"
    sv_path = "backend/cache/QVBpiuph3rM_local_sensevoice_raw.json"
    s1_path = "backend/cache/QVBpiuph3rM_local_large-v3_raw.json"
    s2_path = "backend/results/QVBpiuph3rM_step2.json"
    s3_path = "backend/results/QVBpiuph3rM_step3.json"

    ref = parse_srv1(ref_path)
    s0 = parse_raw_json(s0_path) if os.path.exists(s0_path) else []
    sm = parse_raw_json(sm_path) if os.path.exists(sm_path) else []
    st = parse_raw_json(st_path) if os.path.exists(st_path) else []
    sv = parse_raw_json(sv_path) if os.path.exists(sv_path) else []
    s1 = parse_raw_json(s1_path) if os.path.exists(s1_path) else []
    s2 = parse_result_json(s2_path) if os.path.exists(s2_path) else []
    s3 = parse_result_json(s3_path) if os.path.exists(s3_path) else []

    table = []
    table.append("| 参考文本 (GT) | Base | Medium | Turbo | SenseVoice | large-v3 | Step 2 | Step 3 |")
    table.append("| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |")

    # 我们以参考文本的每一行为基准
    for r in ref:
        t0 = find_text_at(r['start'], s0)
        tm = find_text_at(r['start'], sm)
        tt = find_text_at(r['start'], st)
        tv = find_text_at(r['start'], sv)
        t1 = find_text_at(r['start'], s1)
        t2 = find_text_at(r['start'], s2)
        t3 = find_text_at(r['start'], s3)

        # 只要有一个不同（且不是纯空格/标点差异）就记录
        c_ref = clean(r['text'])
        if any(clean(t) != c_ref for t in [t0, tm, tt, tv, t1, t2, t3] if t):
            # 转义表格中的管道符
            row = [
                r['text'].replace('|', '｜'),
                t0.replace('|', '｜'),
                tm.replace('|', '｜'),
                tt.replace('|', '｜'),
                tv.replace('|', '｜'),
                t1.replace('|', '｜'),
                t2.replace('|', '｜'),
                t3.replace('|', '｜')
            ]
            line = f"| {' | '.join(row)} |"
            table.append(line)

    with open("backend/validation/comparison_table.md", "w") as f:
        f.write("\n".join(table))

if __name__ == "__main__":
    main()
