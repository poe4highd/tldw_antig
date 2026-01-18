import os
import json
import re
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

PROMPT = """
你是一位极致专业的视频文本编辑。我会给你一段带有时间戳的原始语音转录。
你的任务是：
1. 【忠实原文（MUST）】：
   - 绝对禁止删除任何有意义的词汇。
   - **必须根据【目标语言】进行繁简体转换，这不视为修改原意。**
   - 仅纠正明显的误听错误（如将“窒息”听成“智席”），允许根据上下文修正。
2. 【标点符号（CRITICAL）】：必须为所有文本添加正确的标点符号。
   - 中文使用全角标点（，。？！“”）。
   - 英文使用半角标点（,.?!""）。
3. 【合并与分段】：
   - 将碎片化的文本合并为通顺的句子。
   - 根据逻辑进行自然分段。
4. 【语言一致要求】：
   - 必须严格输出指定的【目标语言】。
   - 如果原始文本是繁体但目标是简体（或反之），必须进行转换。
   - 严禁将中文翻译为英文，或将英文翻译为中文。

输出示例：
{{
  "paragraphs": [
    {{
      "sentences": [
        {{"start": 0.0, "text": "大家好，今天我们要聊的是人工智能。"}},
        {{"start": 3.4, "text": "很多人问我，未来它会取代我们吗？"}}
      ]
    }}
  ]
}}

原始文本（请处理以下内容）：
{text_with_timestamps}
"""

def get_youtube_thumbnail_url(url):
    video_id = ""
    # 尝试从常见格式提取 ID
    id_match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11})", url)
    if id_match:
        video_id = id_match.group(1)
    if not video_id:
        return ""
    return f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg"

def detect_language_preference(title, description):
    """
    根据标题和描述自动识别语言偏好。
    返回: "traditional", "english", "simplified"
    """
    # 组合标题和描述进行检查
    content_to_check = (title or "") + " " + (description or "")
    
    # 检测英文 (大部分是英文)
    # 简单启发式：如果非中文字符占比极高，且包含较多英文字符
    if re.search(r'[a-zA-Z]{5,}', title) and not re.search(r'[\u4e00-\u9fa5]', title):
         return "english"
    
    # 常用繁体字特征字符集
    trad_patterns = r'[這國個來們裏時後得會愛兒幾開萬鳥運龍門義專學聽實體禮觀]'
    if re.search(trad_patterns, content_to_check):
        return "traditional"
    
    return "simplified"

def split_into_paragraphs(subtitles, title="", description="", model="gpt-4o-mini"):
    """
    使用 LLM 将原始碎片段合并为自然段落。支持超长文本分段处理。
    并根据标题和描述自动选择简繁体或英文。
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("⚠️ Warning: OPENAI_API_KEY not found. Using fallback grouping.")
        return group_by_time(subtitles), {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}

    # 检测语言偏好 (不再使用 subtitles 样本)
    lang_pref = detect_language_preference(title, description)
    
    if lang_pref == "english":
        lang_instruction = "【目标语言】：英文。请使用英文校正，并添加半角标点。严禁翻译为中文。"
    elif lang_pref == "traditional":
        lang_instruction = "【目标语言】：繁体中文。请使用繁体输出，并添加全角标点。"
    else:
        lang_instruction = "【目标语言】：简体中文。请使用简体输出，并添加全角标点。"
    
    current_prompt = PROMPT + "\n" + lang_instruction

    client = OpenAI(api_key=api_key)
    
    # 如果片段太多（超过 100 个），分块处理以防输出被截断
    CHUNK_SIZE = 80 
    chunks = [subtitles[i:i + CHUNK_SIZE] for i in range(0, len(subtitles), CHUNK_SIZE)]
    
    all_paragraphs = []
    total_usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}

    print(f"--- Processing {len(subtitles)} segments in {len(chunks)} chunks ---")

    for idx, chunk in enumerate(chunks):
        raw_input = "\n".join([f"[{s['start']:.1f}] {s['text']}" for s in chunk])
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "你是一位专业的转录文本处理专家。你必须为文本添加标点符号并分段，且必须输出 JSON。"},
                    {"role": "user", "content": current_prompt.format(text_with_timestamps=raw_input)}
                ],
                response_format={ "type": "json_object" }
            )
            
            print(f"--- Chunk {idx+1}/{len(chunks)} LLM Response Received ---")
            content = response.choices[0].message.content
            try:
                data = json.loads(content)
            except Exception as je:
                print(f"JSON Decode Error in chunk {idx+1}: {je}")
                # 尝试用正则强行提取可能是 JSON 的内容
                match = re.search(r'\{.*\}', content, re.DOTALL)
                if match:
                    data = json.loads(match.group(0))
                else:
                    raise je
            
            # 记录 Token
            total_usage["prompt_tokens"] += response.usage.prompt_tokens
            total_usage["completion_tokens"] += response.usage.completion_tokens
            total_usage["total_tokens"] += response.usage.total_tokens

            # 解析段落 (更加鲁棒的查找)
            chunk_paras = []
            if isinstance(data, dict):
                # 优先清理键值对（处理 LLM 可能多带进来的换行符键名）
                clean_data = {k.strip().replace('"', ''): v for k, v in data.items()}
                
                if "paragraphs" in clean_data:
                    chunk_paras = clean_data["paragraphs"]
                else:
                    # 寻找第一个列表类型的值
                    for val in clean_data.values():
                        if isinstance(val, list):
                            chunk_paras = val
                            break
            elif isinstance(data, list):
                chunk_paras = data

            # 如果还是空，尝试 fallback
            if not chunk_paras:
                 print(f"Warning: No paragraphs found in chunk {idx+1} JSON. Keys: {list(data.keys())}")

            # 结构化
            for p in chunk_paras:
                if isinstance(p, dict) and "sentences" in p:
                    all_paragraphs.append(p)
                elif isinstance(p, dict) and "text" in p:
                    all_paragraphs.append({"sentences": [{"start": p.get("start", 0), "text": p["text"]}]})
                elif isinstance(p, str):
                    all_paragraphs.append({"sentences": [{"start": 0, "text": p}]})
            
            print(f"Chunk {idx+1}/{len(chunks)} structured.")

        except Exception as e:
            print(f"Error processing chunk {idx+1}: {e}")
            print(f"--- Raw LLM Response for Chunk {idx+1} ---")
            print(content if 'content' in locals() else "No content received")
            print("--- End Raw Response ---")
            # 失败块使用基础分组
            fallback_paras = group_by_time(chunk)
            all_paragraphs.extend(fallback_paras)

    if not all_paragraphs:
        return group_by_time(subtitles), total_usage

    return all_paragraphs, total_usage

def group_by_time(subtitles, seconds=45):
    """
    兜底方案：每 45 秒强制合并一段。
    返回格式: [{"sentences": [{"start":..., "text":...}, ...]}]
    """
    if not subtitles: return []
    
    paragraphs = []
    current_sentences = []
    chunk_start = subtitles[0]["start"]
    
    for s in subtitles:
        if s["start"] - chunk_start > seconds and current_sentences:
            paragraphs.append({"sentences": current_sentences})
            current_sentences = []
            chunk_start = s["start"]
        
        current_sentences.append({
            "start": s.get("start", 0),
            "text": s.get("text", "").strip()
        })
    
    if current_sentences:
        paragraphs.append({"sentences": current_sentences})
        
    return paragraphs
