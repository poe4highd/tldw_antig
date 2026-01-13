import os
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

PROMPT = """
你是一位专业的视频字幕整理员。我会给你一段带有时间戳的原始转录文本。
你的任务是：
1. 将破碎、短小的原始字幕合并成逻辑连贯、易于阅读的【自然段落】。
2. 每个段落包含一个句子列表，每个句子必须保留其在原始转录中的精确起始时间戳（start）。
3. 修正转录中的明显口误、重复词汇，或根据上下文修正错别字，但保持主旨不变。
4. 输出格式必须是 JSON 格式：
{
  "paragraphs": [
    {
      "sentences": [
        {"start": 1.2, "text": "句子1内容"},
        {"start": 5.6, "text": "句子2内容"}
      ]
    }
  ]
}

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
            # 将扁平列表转换为嵌套结构，以便前端统一处理
            if len(data) > 0 and "sentences" not in data[0]:
                return [{"sentences": [item]} for item in data]
            return data
            
        print(f"Unexpected data format from LLM: {type(data)}")
        return group_by_time(subtitles)
    except Exception as e:
        print(f"LLM paragraphing failed: {e}")
        return group_by_time(subtitles)

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
            "start": s["start"],
            "text": s["text"].strip()
        })
    
    if current_sentences:
        paragraphs.append({"sentences": current_sentences})
        
    return paragraphs
