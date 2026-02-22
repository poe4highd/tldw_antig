import os
import json
import re
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

PROMPT = """
你是一位专业的视频文本编辑。我会给你一段带有时间戳的原始语音转录。

【核心原则：字数守恒】（CRITICAL）
输出文本的字数必须与输入字数高度接近（误差不超过5%）。转录模型已十分精准，你的任务只是**润色**而非**改写**。

你的任务是：
1. 【同音字纠错（仅限必要替换）】：
   - **只替换明显的同音错别字**，替换时必须保持1:1字数对应。
   - **禁止删除任何内容**：即使某个词看起来多余或重复，也不得删除。
   - **标题权重优先（CRITICAL）**：如果原始转录中的文字，其【拼音或读音】与下方视频上下文（标题、描述）中的核心关键词、长句高度相似，哪怕字面上看起来完全不同，也**必须优先替换为上下文中的正确词汇**。（例如：标题有“灵修”，正文听成“零修”或“领袖”，必须统一改为“灵修”）。
   - **深度识别同音错别字**：尤其是那些【同音但不同语调】的候选字。请结合上下文语义和视频主题背景，找出最符合逻辑的字进行替换。
   - **确保术语一致性**：对于全文反复出现的特定词组或术语，必须确保其写法和语义在全篇范围一致。
   - **禁止合并简化**：不要将多个词合并为一个词，不要用概括性词语替代原文。
2. 【标点符号（CRITICAL）】：必须为所有文本添加正确的标点符号。
   - 中文使用全角标点（，。？！“”）。
   - 英文使用半角标点（,.?!""）。
3. 【分段】：
   - 根据语义逻辑进行自然分段。
   - 保持所有原始内容，只是重新组织段落结构。
4. 【语言一致要求】：
   - 必须严格输出指定的【目标语言】。
   - 如果原始文本是繁体但目标是简体（或反之），必须进行转换。
   - 严禁将中文翻译为英文，或将英文翻译为中文。
5. 【幻觉区域处理】：
   - 部分片段可能标记为 `[HALLUCINATION]` 并包含 `[ALT:]` 备选转录。
   - **必须移除所有 `[HALLUCINATION]` 和 `[ALT:]` 标签**，输出纯净文本。
   - 当主文本是无意义的重复循环（如"用？！用？！"），应**完全采用备选文本，丢弃主文本**。
   - 当主文本和备选都不通顺，尝试结合两者推断实际内容。
   - 如果判断为幻觉，使用备选的时间戳替换主时间戳。
   - 对于意义断层词汇（如"罗布"在讨论食物时），替换为读音相近的常用词（如"萝卜"）。
6. 【允许删除的例外】：
   - 仅限删除确认是无意义幻觉的内容（如连续十几个"用？！"）。
   - 删除后必须保持时间线连续性。

视频上下文参考：
===== START OF CONTEXT =====
{video_context}
核心关键词（必须优先匹配）：{keywords}
-----
上一段上下文参考（跨块一致性）：
{context_last_chunk}
===== END OF CONTEXT =====

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

def get_llm_client():
    """
    根据环境变量 LLM_PROVIDER 返回对应的 OpenAI 或 Ollama 客户端。
    """
    provider = os.getenv("LLM_PROVIDER", "openai").lower()
    
    if provider == "ollama":
        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
        print(f"--- Using Ollama Provider: {base_url} ---")
        return OpenAI(
            base_url=base_url,
            api_key="ollama"  # Ollama 不需要真正的 key，但 OpenAI 客户端初始化通常需要非空字符串
        )
    
    # 默认使用 OpenAI
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
    return OpenAI(api_key=api_key)

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

def extract_keywords(title, description=""):
    """
    一个简单的关键词提取逻辑。
    目前主要从标题中提取长于2个字符的词，或者预定义的领域关键词。
    """
    if not title:
        return ""
    
    # 移除简单助词（示例）
    stop_words = ["如何", "怎么", "一个", "这种", "关于", "我们可以", "之", "与", "或"]
    
    # 使用正则提取可能的名词或术语 (简单启发式：非助词的长词)
    # 这里可以根据需要接入更复杂的 NLP
    words = re.findall(r'[\u4e00-\u9fa5]{2,}', title)
    keywords = [w for w in words if w not in stop_words]
    
    return ", ".join(keywords)

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
    
    video_context = f"标题: {title or '无'}\n描述: {description or '无'}"
    keywords = extract_keywords(title, description)
    current_prompt = PROMPT + "\n" + lang_instruction

    client = get_llm_client()
    default_model = os.getenv("OLLAMA_MODEL", "qwen:8b") if os.getenv("LLM_PROVIDER") == "ollama" else "gpt-4o-mini"
    actual_model = model if model != "gpt-4o-mini" else default_model
    
    # 如果片段太多（超过 100 个），分块处理以防输出被截断
    CHUNK_SIZE = 80 
    chunks = [subtitles[i:i + CHUNK_SIZE] for i in range(0, len(subtitles), CHUNK_SIZE)]
    
    all_paragraphs = []
    total_usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
    last_context = "无（这是第一段）"

    print(f"--- Processing {len(subtitles)} segments in {len(chunks)} chunks ---")

    for idx, chunk in enumerate(chunks):
        raw_input = "\n".join([f"[{s['start']:.1f}] {s['text']}" for s in chunk])
        try:
            response = client.chat.completions.create(
                model=actual_model,
                messages=[
                    {"role": "system", "content": "你是一位专业的转录文本处理专家。你必须为文本添加标点符号并分段，且必须输出 JSON。"},
                    {"role": "user", "content": current_prompt.format(text_with_timestamps=raw_input, video_context=video_context, keywords=keywords, context_last_chunk=last_context)}
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
            chunk_results_text = []
            for p in chunk_paras:
                if isinstance(p, dict) and "sentences" in p:
                    all_paragraphs.append(p)
                    for s in p["sentences"]: chunk_results_text.append(s.get("text", ""))
                elif isinstance(p, dict) and "text" in p:
                    all_paragraphs.append({"sentences": [{"start": p.get("start", 0), "text": p["text"]}]})
                    chunk_results_text.append(p["text"])
                elif isinstance(p, str):
                    all_paragraphs.append({"sentences": [{"start": 0, "text": p}]})
                    chunk_results_text.append(p)
            
            # 更新上下文给下一块
            if chunk_results_text:
                full_text = "".join(chunk_results_text)
                last_context = "..." + full_text[-200:] # 取最后 200 字作为下文参考
            
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

def summarize_text(full_text, title="", description=""):
    """
    调用 LLM 对全文本进行总结并提炼关键词。
    """
    client = get_llm_client()
    if not client:
        return {"summary": "无总结", "keywords": []}, {"prompt_tokens": 0, "completion_tokens": 0}

    system_prompt = "你是一位专业的视频内容分析师。请通过阅读视频标题、描述及包含时间戳的转录全文，总结核心观点并提取 5-10 个最能代表视频核心主题且具备分类或搜索价值的关键词（Tag）。"
    user_prompt = f"""
视频标题: {title}
视频描述: {description}

待分析转录文本:
{full_text}

【任务要求】：
1. 总结视频内容为不超过 7 个重点内容。
2. 每个重点不超过 3 句话。
3. 在每个重点甚至每句话后，必须添加对应内容的视频时间戳链接（格式如 [01:23]），依据所提供文本中的时间标识。
4. 总结部分必须全部使用中文回复（无论视频原本是什么语言）。
5. 综合标题中的核心概念和全文讨论的细节提取关键词。
6. 提取具备通用性、能帮助用户快速点击筛选的关键词（如：AI, 科技, 生产力, 财经, 育儿 等）。
7. **中英双语对齐（CRITICAL）**：对于具备行业通用性或分类价值的关键词，必须输出为“中文 (English)”格式。例如：将“财经”输出为“财经 (Finance)”，“人工智能”输出为“人工智能 (AI)”。
8. 关键词应简洁有力，通常为 2-4 个汉字配合英文，排除掉没意义的泛指词。

请严格按以下 JSON 格式输出:
{{
  "summary": "以文本格式输出的重点总结内容（由于需支持多段落，请结合换行符排版，切勿使用 JSON 不支持的单行纯文本限制）...",
  "keywords": ["关键词1", "关键词2"]
}}
"""

    default_model = os.getenv("OLLAMA_MODEL", "qwen:8b") if os.getenv("LLM_PROVIDER") == "ollama" else "gpt-4o-mini"
    
    try:
        response = client.chat.completions.create(
            model=default_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
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
        return data, usage
    except Exception as e:
        print(f"Summarization Error: {e}")
        return {"summary": "总结生成失败", "keywords": []}, {"prompt_tokens": 0, "completion_tokens": 0}

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
