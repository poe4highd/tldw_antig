import os
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

PROMPT = """
你是一位专业的视频字幕整理员。我会给你一段带有时间戳的原始转录文本。
你的任务是：
1. 将破碎、短小的原始字幕合并成逻辑连贯、易于阅读的【自然段落】。
2. 为每个段落保留起始时间戳（start）。
3. 修正转录中的明显口误、重复词汇，或根据上下文修正错别字，但保持主旨不变。
4. 输出格式必须是 JSON 格式的列表，每个对象包含:
   - "start": 段落起始秒数 (float)
   - "text": 整个段落的文本 (string)

原始文本：
{text_with_timestamps}
"""

def split_into_paragraphs(subtitles, model="gpt-4o-mini"):
    """
    使用 LLM 将原始碎片段合并为自然段落。
    """
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    if not client.api_key:
        # 如果没有 API Key，退而求其次：简单合并
        return group_by_time(subtitles)

    # 准备输入的文本数据
    raw_input = "\\n".join([f"[{s['start']:.1f}] {s['text']}" for s in subtitles])
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "你是一位专业的转录文本处理专家。"},
                {"role": "user", "content": PROMPT.format(text_with_timestamps=raw_input)}
            ],
            response_format={ "type": "json_object" }
        )
        
        data = json.loads(response.choices[0].message.content)
        # 兼容性处理：LLM 可能返回 {"paragraphs": [...] } 或 {"items": [...] } 等
        if isinstance(data, dict):
            if "paragraphs" in data:
                return data["paragraphs"]
            # 尝试找字典中第一个列表
            for val in data.values():
                if isinstance(val, list):
                    return val
        if isinstance(data, list):
            return data
            
        print(f"Unexpected data format from LLM: {type(data)}")
        return group_by_time(subtitles)
    except Exception as e:
        print(f"LLM paragraphing failed: {e}")
        return group_by_time(subtitles)

def group_by_time(subtitles, seconds=30):
    """
    兜底方案：每 30 秒强制合并一段。
    """
    if not subtitles: return []
    
    paragraphs = []
    current_p = {"start": subtitles[0]["start"], "text": ""}
    
    for s in subtitles:
        if s["start"] - current_p["start"] > seconds:
            paragraphs.append(current_p)
            current_p = {"start": s["start"], "text": s["text"]}
        else:
            current_p["text"] += " " + s["text"]
    
    paragraphs.append(current_p)
    return paragraphs
