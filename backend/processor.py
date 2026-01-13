import os
import json
import re
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

PROMPT = """
你是一位极致专业的视频文本编辑。我会给你一段带有时间戳的原始语音转录。
你的任务是：
1. 【标点补完】：必须按照语义为文本添加精准的标点符号（如，。？！“”）。原始转录通常没有标点，你必须根据语感补齐。
2. 【分段处理】：在不改变原意和字数的前提下，将文本整理成逻辑严密的自然段落。
3. 【嵌套 JSON 结构】：严格按照以下 JSON 格式输出，每个句子（sentence）必须保留其在原始转录中的精确起始时间戳（start）。
4. 【禁止删减】：绝对禁止删除任何词汇，哪怕是口语词，仅做标点添加和极少量的同音字修正。

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

def split_into_paragraphs(subtitles, model="gpt-4o-mini"):
    """
    使用 LLM 将原始碎片段合并为自然段落。
    """
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    if not client.api_key:
        # 如果没有 API Key，退而求其次：简单合并
        return group_by_time(subtitles), {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}

    # 准备输入的文本数据
    raw_input = "\n".join([f"[{s['start']:.1f}] {s['text']}" for s in subtitles])
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "你是一位专业的转录文本处理专家。"},
                {"role": "user", "content": PROMPT.format(text_with_timestamps=raw_input)}
            ],
            response_format={ "type": "json_object" }
        )
        
        content = response.choices[0].message.content
        data = json.loads(content)
        usage = {
            "prompt_tokens": response.usage.prompt_tokens,
            "completion_tokens": response.usage.completion_tokens,
            "total_tokens": response.usage.total_tokens
        }

        # 兼容性处理
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

        if paragraphs and isinstance(paragraphs, list):
            # 确保每个段落内部是嵌套的句子结构
            if len(paragraphs) > 0 and "sentences" not in paragraphs[0]:
                # 如果是扁平结构，自动包装
                new_paras = []
                for p in paragraphs:
                    if isinstance(p, dict) and "text" in p:
                        new_paras.append({"sentences": [{"start": p.get("start", 0), "text": p["text"]}]})
                    elif isinstance(p, str):
                        new_paras.append({"sentences": [{"start": 0, "text": p}]})
                paragraphs = new_paras
            return paragraphs, usage
            
        print(f"Unexpected data format from LLM: {type(data)}")
        return group_by_time(subtitles), usage
    except Exception as e:
        print(f"LLM paragraphing failed: {e}")
        # 如果解析失败，尝试直接从 content 中找有没有 json 结构 (简单加固)
        return group_by_time(subtitles), {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}

def group_by_time(subtitles, seconds=45):
    """
    兜底方案：每 45 秒强制合并一段。
    返回格式: [{"sentences": [{"start":..., "text":...}, ...]}]
    """
    if not subtitles: return []
    
    paragraphs = []
    current_sentences = []
    if not subtitles: return []
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
