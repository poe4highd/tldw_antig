#!/usr/bin/env python3
import os
import sys
import json
import re
import argparse
import xml.etree.ElementTree as ET
from collections import Counter

import zhconv

def clean_text(text):
    """
    清理文本：
    1. 统一转为简体 (使用 zhconv)
    2. 移除所有非中文字符、数字和字母
    3. 人称代词归一化: 祂、它 -> 他
    4. 移除空格和常见标点
    """
    if not text:
        return ""
    
    # 1. 工业级简繁转换
    text = zhconv.convert(text, 'zh-hans')
    
    # 2. 数字归一化 (2 -> 二)
    num_map = {
        '0': '零', '1': '一', '2': '二', '3': '三', '4': '四',
        '5': '五', '6': '六', '7': '七', '8': '八', '9': '九'
    }
    for k, v in num_map.items():
        text = text.replace(k, v)
        
    # 3. 人称代词归一化 (样式对齐)
    # 将 祂、它 统一替换为 他，避免因宗教背景或指代选择导致的 CER 误差
    pronoun_map = {'祂': '他', '它': '他'}
    for k, v in pronoun_map.items():
        text = text.replace(k, v)

    # 4. 移除标点、空格、特殊字符
    text = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9]', '', text)
    
    return text.lower()

def srv1_to_text(srv1_path):
    """
    从 SRV1 XML 中提取纯文本。
    """
    try:
        tree = ET.parse(srv1_path)
        root = tree.getroot()
        texts = [t.text for t in root.findall('text') if t.text]
        return " ".join(texts)
    except Exception as e:
        print(f"解析 SRV1 出错: {e}")
        return ""

def ai_json_to_text(json_path):
    """
    从 AI 转录 JSON 或 Whisper 原始缓存中提取纯文本。
    支持格式：
    1. 结构化 JSON: {"paragraphs": [{"sentences": [{"text": "..."}]}]}
    2. Whisper 原始缓存: [{"start": 0, "end": 1, "text": "..."}]
    """
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        texts = []
        
        # 模式 1: 结构化 JSON (后端处理后的结果)
        if isinstance(data, dict) and "paragraphs" in data:
            paragraphs = data.get("paragraphs", [])
            for p in paragraphs:
                sentences = p.get("sentences", [])
                for s in sentences:
                    texts.append(s.get("text", ""))
        
        # 模式 2: Whisper 原始缓存 (List 格式)
        elif isinstance(data, list):
            for item in data:
                if isinstance(item, dict) and "text" in item:
                    texts.append(item.get("text", ""))
        
        return " ".join(texts)
    except Exception as e:
        print(f"解析 JSON 出错: {e}")
        return ""

def levenshtein_distance(s1, s2):
    """
    计算编辑距离并追踪操作。
    返回: distance, ops (list of 'S', 'D', 'I' or 'M')
    """
    m, n = len(s1), len(s2)
    dp = [[0] * (n + 1) for _ in range(m + 1)]

    for i in range(m + 1):
        dp[i][0] = i
    for j in range(n + 1):
        dp[0][j] = j

    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if s1[i-1] == s2[j-1]:
                dp[i][j] = dp[i-1][j-1]
            else:
                dp[i][j] = 1 + min(dp[i-1][j],    # Deletion
                                   dp[i][j-1],    # Insertion
                                   dp[i-1][j-1])  # Substitution

    # 回溯以获取具体操作 (为了统计错词)
    ops = []
    i, j = m, n
    while i > 0 or j > 0:
        if i > 0 and j > 0 and s1[i-1] == s2[j-1]:
            # ops.append(('M', s1[i-1], s2[j-1]))
            i -= 1
            j -= 1
        elif i > 0 and j > 0 and dp[i][j] == dp[i-1][j-1] + 1:
            ops.append(('S', s1[i-1], s2[j-1])) # Substitution: GroundTruth -> Prediction
            i -= 1
            j -= 1
        elif i > 0 and dp[i][j] == dp[i-1][j] + 1:
            ops.append(('D', s1[i-1], ''))      # Deletion in Prediction
            i -= 1
        else:
            ops.append(('I', '', s2[j-1]))      # Insertion in Prediction
            j -= 1
            
    return dp[m][n], ops

def calculate_cer(gt_text, pred_text):
    gt = clean_text(gt_text)
    pred = clean_text(pred_text)
    
    if not gt:
        return 0.0, []
    
    dist, ops = levenshtein_distance(gt, pred)
    cer = dist / len(gt)
    return cer, ops

def main():
    parser = argparse.ArgumentParser(description="字幕对比与评估脚本")
    parser.add_argument("--gt", required=True, help="基准字幕路径 (.srv1 或文本)")
    parser.add_argument("--pred", required=True, help="AI 转录结果路径 (.json 或文本)")
    parser.add_argument("--top", type=int, default=10, help="显示 Top N 错误词频")
    parser.add_argument("--outdir", default="validation", help="报告保存目录 (默认 backend/scripts/../validation)")
    
    args = parser.parse_args()
    
    # 路径处理
    script_dir = os.path.dirname(os.path.abspath(__file__))
    backend_dir = os.path.dirname(script_dir)
    
    # 如果 args.outdir 是 'validation' 且 backend_dir 结尾已经是 'backend'
    # 逻辑简化：如果不是绝对路径，则相对于 backend_dir
    val_dir = args.outdir if os.path.isabs(args.outdir) else os.path.join(backend_dir, args.outdir)
    
    # 额外检查：防止 backend/backend 的嵌套路径 (如果 args.outdir 里已经带了 backend)
    if "backend/validation" in val_dir and val_dir.count("backend") > 1:
        val_dir = val_dir.replace("backend/backend", "backend")

    if not os.path.exists(val_dir):
        os.makedirs(val_dir)
        
    # 推断视频 ID 和 类型
    video_id = os.path.basename(args.gt).split('.')[0]
    pred_basename = os.path.basename(args.pred).lower()
    comp_type = "raw" if "raw" in pred_basename or "cache" in args.pred else "llm"
    timestamp = __import__("datetime").datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 加载文本
    if args.gt.endswith(".srv1"):
        gt_text = srv1_to_text(args.gt)
    elif args.gt.endswith(".json"):
        gt_text = ai_json_to_text(args.gt)
    else:
        with open(args.gt, 'r', encoding='utf-8') as f:
            gt_text = f.read()
            
    if args.pred.endswith(".srv1"):
        pred_text = srv1_to_text(args.pred)
    elif args.pred.endswith(".json"):
        pred_text = ai_json_to_text(args.pred)
    else:
        with open(args.pred, 'r', encoding='utf-8') as f:
            pred_text = f.read()

    # 计算 CER
    cer, ops = calculate_cer(gt_text, pred_text)
    
    report = []
    report.append("="*40)
    report.append(" 字幕评估报告")
    report.append("="*40)
    report.append(f"基准文件: {os.path.basename(args.gt)}")
    report.append(f"预测文件: {os.path.basename(args.pred)}")
    report.append(f"基准总字数: {len(clean_text(gt_text))}")
    report.append(f"预测总字数: {len(clean_text(pred_text))}")
    report.append("-" * 20)
    report.append(f"错误率 (CER): {cer:.2%}")
    report.append(f"准确率: {1-cer:.2%}")
    report.append("-" * 20)
    
    # 统计错误词频 (Substitution 仅限)
    substitutions = [f"{o[1]} -> {o[2]}" for o in ops if o[0] == 'S']
    counter = Counter(substitutions)
    
    report.append(f"Top {args.top} 常见错字替换:")
    for pair, count in counter.most_common(args.top):
        report.append(f"  {pair}: {count} 次")
        
    # 统计遗漏和插入
    deletions = [o[1] for o in ops if o[0] == 'D']
    insertions = [o[2] for o in ops if o[0] == 'I']
    
    if deletions:
        report.append(f"\n常见遗漏字 (Top 5): {Counter(deletions).most_common(5)}")
    if insertions:
        report.append(f"常见插入字 (Top 5): {Counter(insertions).most_common(5)}")
    report.append("="*40)

    # 打印报告
    report_content = "\n".join(report)
    print(report_content)
    
    # 保存报告
    out_file = os.path.join(val_dir, f"{video_id}_{comp_type}_{timestamp}.txt")
    with open(out_file, 'w', encoding='utf-8') as f:
        f.write(report_content)
    print(f"\n报告已保存至: {out_file}")

if __name__ == "__main__":
    main()
