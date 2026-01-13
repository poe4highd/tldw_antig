import os
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

PROMPT = """
你是一位专业的视频字幕校对与排版专家。我会给你一段带有时间戳的原始录音转录文本。
你的任务是：
1. 【标点与分段】：在不改变原始字数和意思的前提下，为文本添加准确的中文标点符号（，。？！等），并将其整理成逻辑清晰的【自然段落】。
2. 【句级嵌套】：每个段落包含一个句子列表，每个句子必须严格对应原始转录中的精确起始时间戳（start）。
3. 【术语修正】：修正转录中的明显同音错别字或明显的口误，确保阅读体验顺滑，但禁止删减内容。
4. 【输出格式】：必须返回合法的 JSON：
{
  "paragraphs": [
    {
      "sentences": [
        {"start": 1.2, "text": "校对后的句子1内容"},
        {"start": 5.6, "text": "校对后的句子2内容"}
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
        usage = {
            "prompt_tokens": response.usage.prompt_tokens,
            "completion_tokens": response.usage.completion_tokens,
            "total_tokens": response.usage.total_tokens
        }

        # 兼容性处理：LLM 可能返回 {"paragraphs": [...] } 或 {"items": [...] } 等
        paragraphs = []
        if isinstance(data, dict):
            if "paragraphs" in data:
                paragraphs = data["paragraphs"]
            else:
                # 尝试找字典中第一个列表
                for val in data.values():
                    if isinstance(val, list):
                        paragraphs = val
                        break
        elif isinstance(data, list):
            paragraphs = data

        # 将扁平列表转换为嵌套结构，以便前端统一处理
        if paragraphs and isinstance(paragraphs, list):
            if "sentences" not in paragraphs[0]:
                paragraphs = [{"sentences": [item]} for item in paragraphs]
            return paragraphs, usage
            
        print(f"Unexpected data format from LLM: {type(data)}")
        return group_by_time(subtitles), usage
    except Exception as e:
        print(f"LLM paragraphing failed: {e}")
        return group_by_time(subtitles), {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}

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
