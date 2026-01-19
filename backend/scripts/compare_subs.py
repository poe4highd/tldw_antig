#!/usr/bin/env python3
import os
import sys
import json
import re
import argparse
import xml.etree.ElementTree as ET
from collections import Counter

def clean_text(text):
    """
    清洗文本：移除标点符号、空格，统一转为小写。
    """
    if not text:
        return ""
    # 移除标点符号和空格
    text = re.sub(r'[^\w\u4e00-\u9fa5]', '', text)
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
    从 AI 转录 JSON 中提取纯文本。
    """
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        texts = []
        paragraphs = data.get("paragraphs", [])
        for p in paragraphs:
            sentences = p.get("sentences", [])
            for s in sentences:
                texts.append(s.get("text", ""))
        
        return " ".join(texts)
    except Exception as e:
        print(f"解析 AI JSON 出错: {e}")
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
    
    args = parser.parse_args()
    
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
    
    print("="*40)
    print(" 字幕评估报告")
    print("="*40)
    print(f"基准文件: {os.path.basename(args.gt)}")
    print(f"预测文件: {os.path.basename(args.pred)}")
    print(f"基准总字数: {len(clean_text(gt_text))}")
    print(f"预测总字数: {len(clean_text(pred_text))}")
    print("-" * 20)
    print(f"错误率 (CER): {cer:.2%}")
    print(f"准确率: {1-cer:.2%}")
    print("-" * 20)
    
    # 统计错误词频 (Substitution 仅限)
    substitutions = [f"{o[1]} -> {o[2]}" for o in ops if o[0] == 'S']
    counter = Counter(substitutions)
    
    print(f"Top {args.top} 常见错字替换:")
    for pair, count in counter.most_common(args.top):
        print(f"  {pair}: {count} 次")
        
    # 统计遗漏和插入
    deletions = [o[1] for o in ops if o[0] == 'D']
    insertions = [o[2] for o in ops if o[0] == 'I']
    
    if deletions:
        print(f"\n常见遗漏字 (Top 5): {Counter(deletions).most_common(5)}")
    if insertions:
        print(f"常见插入字 (Top 5): {Counter(insertions).most_common(5)}")
    print("="*40)

if __name__ == "__main__":
    main()
