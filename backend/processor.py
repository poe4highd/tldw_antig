import os
import json
import re
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

PROMPT = """
你是一位极致专业的视频文本编辑。我会给你一段带有时间戳的原始语音转录。
你的任务是：
1. 【精准修正】：在不改变字数的前提下，根据上下文纠正多音字或同音字。
2. 【标点与分段】：为文本添加精准的标点符号（如，。？！“”），并根据逻辑进行自然分段。
3. 【嵌套 JSON 结构】：严格按照以下 JSON 格式输出，每个句子（sentence）必须保留其在原始转录中的精确起始时间戳（start）。
4. 【禁止删减】：绝对禁止删除任何词汇，哪怕是口语词，仅做修正、标点添加和分段。

输出示例：
{
  "paragraphs": [
    {
      "sentences": [
        {"start": 0.0, "text": "大家好，今天我们要聊的是人工智能。"},
        {"start": 3.4, "text": "很多人问我，未来它会取代我们吗？"}
      ]
    }
  ]
}

原始文本：
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

def is_traditional(text):
    """
    检查文本是否包含明显的繁体中文字符。
    """
    # 常用繁体字特征字符集
    trad_patterns = r'[這國個來們裏時後得會愛兒幾開萬鳥運龍門義專學聽實體禮觀]'
    return bool(re.search(trad_patterns, text))

def split_into_paragraphs(subtitles, title="", model="gpt-4o-mini"):
    """
    使用 LLM 将原始碎片段合并为自然段落。支持超长文本分段处理。
    并根据标题自动选择简繁体。
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("⚠️ Warning: OPENAI_API_KEY not found. Using fallback grouping.")
        return group_by_time(subtitles), {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}

    # 检测标题语言偏好
    is_trad = is_traditional(title)
    lang_instruction = "【字体要求】：识别到标题为繁体，你必须使用『繁体中文』输出所有文本内容。" if is_trad else "【字体要求】：默认使用『简体中文』输出所有文本内容（除非原文是英文）。"
    
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
