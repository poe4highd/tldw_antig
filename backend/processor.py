import os
import json
import re
import time
import itertools
from concurrent.futures import ThreadPoolExecutor, as_completed
from openai import OpenAI
from dotenv import load_dotenv
from server_pool import ServerPool, OllamaServer

load_dotenv()

PROMPT_V2 = """
你是一位专业的语音转录校对员。我会给你一段带有时间戳的原始语音转录，每行格式为 `[时间] 文字`。

【任务：原句校对，严禁改变句子数量或合并句子】

规则如下：
1. 【严格保持句子数量和边界】（CRITICAL）
   - 输入有多少行，输出就必须有多少个 sentence。
   - **禁止合并、拆分或跳过任何一行**。每一行输入对应输出中恰好一个 sentence，时间戳完全不变。

2. 【同音字纠错（原位替换）】
   - 只替换明显的同音/近音错别字，替换后字数必须与原文相同（1换1）。
   - **禁止增加或删除任何字**，不得插入语气词、连词或额外解释。
   - **标题关键词优先**：若原文读音与视频标题/描述的关键词高度接近，必须优先替换为正确词汇。
   - 示例：`零修→灵修`、`抄令→操练`、`质疑→旨意`、`哭乾→枯干`。

3. 【仅添加句末标点】
   - 在每个句子末尾加上适当的中文全角标点（，。？！）。
   - 句子内部**不得插入额外标点**（逗号、顿号等），保持原始分词节奏。
   - 英文句子使用半角标点。

4. 【不做任何其他改动】
   - 不重组段落，不改变语序，不做语义润色，不翻译。

视频上下文参考：
===== START OF CONTEXT =====
{video_context}
核心关键词（必须优先匹配）：{keywords}
-----
上一段上下文参考（跨块一致性）：
{context_last_chunk}
===== END OF CONTEXT =====

输出格式（字段名严格为 "start" 和 "text"，不得使用其他变体）：
{{
  "paragraphs": [
    {{
      "sentences": [
        {{"start": 0.43, "text": "他要像一棵树栽在溪水旁，"}},
        {{"start": 3.53, "text": "按时候结果子，叶子也不枯干。"}},
        {{"start": 6.49, "text": "凡他所作的尽都顺利。"}}
      ]
    }}
  ]
}}

注意：输出的 sentences 数量必须与下方输入行数完全一致。

原始文本（请处理以下内容）：
{text_with_timestamps}
"""

PROMPT = """
你是一位专业的视频文本编辑。我会给你一段带有时间戳的原始语音转录。

【核心原则：字数守恒】（CRITICAL）
输出文本的字数必须与输入字数高度接近（误差不超过5%）。转录模型已十分精准，你的任务只是**润色**而非**改写**。

你的任务是：
1. 【同音字纠错（仅限必要替换）】：
   - **只替换明显的同音错别字**，替换时必须保持1:1字数对应。
   - **禁止删除任何内容**：即使某个词看起来多余或重复，也不得删除。
   - **标题权重优先（CRITICAL）**：如果原始转录中的文字，其【拼音或读音】与下方视频上下文（标题、描述）中的核心关键词、长句高度相似，哪怕字面上看起来完全不同，也**必须优先替换为上下文中的正确词汇**。（例如：标题有"灵修"，正文听成"零修"或"领袖"，必须统一改为"灵修"）。
   - **深度识别同音错别字**：尤其是那些【同音但不同语调】的候选字。请结合上下文语义和视频主题背景，找出最符合逻辑的字进行替换。
   - **确保术语一致性**：对于全文反复出现的特定词组或术语，必须确保其写法和语义在全篇范围一致。
   - **禁止合并简化**：不要将多个词合并为一个词，不要用概括性词语替代原文。
2. 【标点符号（CRITICAL）】：必须为所有文本添加正确的标点符号。
   - 中文使用全角标点（，。？！""）。
   - 英文使用半角标点（,.?!""）。
3. 【分段（CRITICAL）】：
   - **以语义话题为单位划分段落**：每个段落围绕一个完整的论点、事例或叙述单元，话题自然切换时才换段。
   - **段落长度均衡**：目标每段 3～8 句，每段文字量约 80～300 字。严禁出现只有 1 句的"单句段"（除非该句本身构成完整独立单元，如开场白或结束语）；也严禁将整块输入堆入 1～2 个超长段落。
   - **禁止机械等分**：不要以固定句数均匀切割，要依据内容的语义边界（换话题、转观点、举新例子）决定断句位置。
   - **保持所有原始内容**，只重新组织段落结构，不得增减文字。
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

输出示例（严格遵守字段名，不得使用 text_content、content 或其他变体）：
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

def get_llm_client(fallback=False):
    """
    根据环境变量 LLM_PROVIDER 返回对应的 OpenAI 或 Ollama 客户端。
    fallback=True 时返回备用 provider 客户端（OpenAI→Ollama 或 Ollama→OpenAI）。
    返回 (client, provider_name) 元组。
    """
    provider = os.getenv("LLM_PROVIDER", "openai").lower()

    if fallback:
        if provider != "ollama":
            # 主是 OpenAI，fallback 到 Ollama
            base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
            ollama_model = os.getenv("OLLAMA_MODEL", "qwen3:8b")
            print(f"--- [LLM Fallback] Switching to Ollama: {base_url}, model={ollama_model} ---")
            return OpenAI(base_url=base_url, api_key="ollama"), "ollama"
        else:
            # 主是 Ollama，fallback 到 OpenAI
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                return None, None
            print(f"--- [LLM Fallback] Switching to OpenAI ---")
            return OpenAI(api_key=api_key), "openai"

    if provider == "ollama":
        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
        print(f"--- Using Ollama Provider: {base_url} ---")
        return OpenAI(base_url=base_url, api_key="ollama"), "ollama"

    # 默认使用 OpenAI
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None, None
    return OpenAI(api_key=api_key), "openai"

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
    返回: "english", "korean", "japanese", "traditional", "simplified"
    策略：以字符数量最多的语言为主（高权重），英文作为无 CJK 字符时的兜底。
    """
    content = (title or "") + " " + (description or "")

    # 统计各语言专属字符数量
    chinese_chars  = len(re.findall(r'[\u4e00-\u9fa5]', content))
    korean_chars   = len(re.findall(r'[\uac00-\ud7a3]', content))       # 韩文音节
    japanese_chars = len(re.findall(r'[\u3040-\u309f\u30a0-\u30ff]', content))  # 平假名+片假名

    lang_counts = {
        "korean":   korean_chars,
        "japanese": japanese_chars,
        "chinese":  chinese_chars,
    }
    dominant = max(lang_counts, key=lang_counts.get)

    if lang_counts[dominant] > 0:
        if dominant == "korean":
            return "korean"
        if dominant == "japanese":
            return "japanese"
        if dominant == "chinese":
            trad_patterns = r'[這國個來們裏時後得會愛兒幾開萬鳥運龍門義專學聽實體禮觀]'
            return "traditional" if re.search(trad_patterns, content) else "simplified"

    # 无 CJK 字符：默认英文
    return "english"

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

def split_into_paragraphs(subtitles, title="", description="", model="gpt-4o-mini", prompt_mode="v1"):
    """
    使用 LLM 将原始碎片段合并为自然段落。支持超长文本分段处理。
    并根据标题和描述自动选择简繁体或英文。

    prompt_mode:
      "v1" - 原版：合并分段 + 同音纠错（默认，适合 OpenAI）
      "v2" - 句子保留：保持原始句子边界，只做同音纠错和句末标点（适合本地 Ollama）
    """
    # 检查是否有可用的 LLM 提供者（Ollama 不需要 API key）
    llm_provider = os.getenv("LLM_PROVIDER", "openai").lower()
    api_key = os.getenv("OPENAI_API_KEY")
    has_ollama = os.getenv("OLLAMA_SERVERS") or os.getenv("OLLAMA_BASE_URL")
    if not api_key and llm_provider != "ollama" and not has_ollama:
        print("⚠️ Warning: No LLM provider configured. Using fallback grouping.")
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

    client, provider = get_llm_client()
    default_model = os.getenv("OLLAMA_MODEL", "qwen:8b") if provider == "ollama" else "gpt-4o-mini"
    actual_model = model if model != "gpt-4o-mini" else default_model

    # 选择 prompt 模板
    if prompt_mode == "v2":
        base_prompt = PROMPT_V2
    else:
        base_prompt = PROMPT
    current_prompt = base_prompt + "\n" + lang_instruction

    # V2 用更小的 chunk，保证输入行数 ≤ 60，减少遗漏输出行的概率
    CHUNK_SIZE = 60 if prompt_mode == "v2" else 80
    chunks = [subtitles[i:i + CHUNK_SIZE] for i in range(0, len(subtitles), CHUNK_SIZE)]
    
    # ── 预计算每个 chunk 的上下文（用原始字幕文本，消除串行依赖） ──
    chunk_contexts = ["无（这是第一段）"]
    for i in range(1, len(chunks)):
        raw_text = "".join([s["text"] for s in chunks[i - 1]])
        chunk_contexts.append("..." + raw_text[-200:])

    # ── 构建共享参数 ──
    chunk_params = dict(
        actual_model=actual_model,
        current_prompt=current_prompt,
        video_context=video_context,
        keywords=keywords,
        prompt_mode=prompt_mode,
        total_chunks=len(chunks),
    )

    # ── 判断并行 or 串行 ──
    pool = ServerPool()
    available = pool.get_available_servers()

    print(f"--- Processing {len(subtitles)} segments in {len(chunks)} chunks "
          f"(servers available: {len(available)}) ---")

    if len(available) > 1 and len(chunks) > 1:
        all_paragraphs, total_usage = _process_chunks_parallel(
            chunks, chunk_contexts, pool, chunk_params)
    else:
        # 单服务器或单 chunk：使用原有串行逻辑
        server = available[0] if available else pool.servers[0] if pool.servers else None
        fallback_client = server.client if server else client
        all_paragraphs, total_usage = _process_chunks_sequential(
            chunks, chunk_contexts, fallback_client, provider, chunk_params)

    if not all_paragraphs:
        return group_by_time(subtitles), total_usage

    return all_paragraphs, total_usage


# ═══════════════════════════════════════════════════════════════
# 单 chunk 处理核心逻辑（供串行/并行共用）
# ═══════════════════════════════════════════════════════════════

def _process_chunk_single(idx, chunk, context, llm_client, model, prompt_template,
                          video_context, keywords, prompt_mode, total_chunks):
    """
    处理单个 chunk，返回 (chunk_idx, paragraphs, usage, quality_ok, reason)。
    线程安全：每个调用使用自己的 client 实例，不共享可变状态。
    """
    raw_input = "\n".join([f"[{s['start']:.1f}] {s['text']}" for s in chunk])

    if prompt_mode == "v2":
        system_msg = (
            "你是一位专业的语音转录校对员。"
            "输入有多少行，输出 sentences 就必须有多少个，不得合并或跳过任何一行。"
            "只做同音字原位替换和句末标点，禁止增删字词。必须输出 JSON。"
        )
    else:
        system_msg = (
            "你是一位专业的转录文本处理专家。"
            "你必须为文本添加标点符号并分段，且必须输出 JSON。"
            "分段原则：每段 3～8 句，围绕一个完整语义单元，严禁单句段和超长段。"
        )

    call_kwargs = dict(
        model=model,
        messages=[
            {"role": "system", "content": system_msg},
            {"role": "user", "content": prompt_template.format(
                text_with_timestamps=raw_input,
                video_context=video_context,
                keywords=keywords,
                context_last_chunk=context
            )}
        ],
        response_format={"type": "json_object"},
        temperature=0.1,
        extra_body={"options": {"num_gpu": int(os.getenv("OLLAMA_NUM_GPU", "-1"))}}
    )

    # 空响应重试（最多 5 次，指数退避）
    content = None
    response = None
    max_attempts = 5
    for attempt in range(max_attempts):
        response = llm_client.chat.completions.create(**call_kwargs)
        content = response.choices[0].message.content
        if content and content.strip():
            break
        wait = 2 ** attempt
        print(f"Chunk {idx+1}: empty response (attempt {attempt+1}/{max_attempts}), retrying in {wait}s...")
        time.sleep(wait)

    print(f"--- Chunk {idx+1}/{total_chunks} LLM Response Received ---")

    # JSON 解析
    try:
        data = json.loads(content)
    except Exception as je:
        print(f"JSON Decode Error in chunk {idx+1}: {je}")
        match = re.search(r'\{.*\}', content or "", re.DOTALL)
        if match:
            data = json.loads(match.group(0))
        else:
            raise je

    # Token 记录
    usage = {
        "prompt_tokens": response.usage.prompt_tokens,
        "completion_tokens": response.usage.completion_tokens,
        "total_tokens": response.usage.total_tokens,
    }

    # 解析段落（鲁棒查找）
    chunk_paras = []
    if isinstance(data, dict):
        clean_data = {k.strip().replace('"', ''): v for k, v in data.items()}
        if "paragraphs" in clean_data:
            chunk_paras = clean_data["paragraphs"]
        else:
            for val in clean_data.values():
                if isinstance(val, list):
                    chunk_paras = val
                    break
    elif isinstance(data, list):
        chunk_paras = data

    if not chunk_paras:
        print(f"Warning: No paragraphs found in chunk {idx+1} JSON. Keys: {list(data.keys()) if isinstance(data, dict) else 'list'}")

    # 结构化 + 字段名归一化
    structured_paras = []
    for p in chunk_paras:
        if isinstance(p, dict) and "sentences" in p:
            for s in p["sentences"]:
                if "text" not in s and "text_content" in s:
                    s["text"] = s.pop("text_content")
                elif "text" not in s and "content" in s:
                    s["text"] = s.pop("content")
            structured_paras.append(p)
        elif isinstance(p, dict) and "text" in p:
            structured_paras.append({"sentences": [{"start": p.get("start", 0), "text": p["text"]}]})
        elif isinstance(p, str):
            structured_paras.append({"sentences": [{"start": 0, "text": p}]})

    # 质量检查
    quality_ok, reason = _validate_chunk_quality(chunk, structured_paras, prompt_mode)
    print(f"Chunk {idx+1}/{total_chunks} structured. quality={quality_ok} {reason}")

    return idx, structured_paras, usage, quality_ok, reason


def _validate_chunk_quality(chunk_input, chunk_paras, prompt_mode):
    """验证单个 chunk 的 LLM 输出质量，返回 (is_ok, reason)"""
    from hallucination_detector import detect_hallucination_patterns

    # 检查 1: 空响应
    if not chunk_paras:
        return False, "empty_response"

    # 检查 2: V2 模式句子数偏差（>20% 丢失 → 不合格）
    if prompt_mode == "v2":
        output_count = sum(len(p.get("sentences", [])) for p in chunk_paras)
        input_count = len(chunk_input)
        if input_count > 0 and output_count < input_count * 0.8:
            return False, f"sentence_drop:{output_count}/{input_count}"

    # 检查 3: 字符数异常偏差
    input_chars = sum(len(s.get("text", "")) for s in chunk_input)
    output_chars = sum(
        len(s.get("text", ""))
        for p in chunk_paras
        for s in p.get("sentences", [])
    )
    if input_chars > 0:
        ratio = output_chars / input_chars
        if ratio < 0.5 or ratio > 2.0:
            return False, f"char_ratio:{ratio:.2f}"

    # 检查 4: 幻觉模式
    all_text = " ".join(
        s.get("text", "")
        for p in chunk_paras
        for s in p.get("sentences", [])
    )
    patterns = detect_hallucination_patterns(all_text)
    if patterns:
        return False, f"hallucination:{patterns}"

    return True, "ok"


# ═══════════════════════════════════════════════════════════════
# 并行处理路径
# ═══════════════════════════════════════════════════════════════

def _process_chunks_parallel(chunks, chunk_contexts, pool, params):
    """用 ThreadPoolExecutor 并行分派 chunks 到多台服务器"""
    total = len(chunks)
    results = [None] * total  # 按索引存放结果
    retry_queue = []
    total_usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}

    available = pool.get_available_servers()
    print(f"--- [Parallel] 启动并行处理: {total} chunks → {len(available)} servers ---")

    with ThreadPoolExecutor(max_workers=len(available)) as executor:
        futures = {}
        server_cycle = itertools.cycle(available)

        for idx, chunk in enumerate(chunks):
            server = next(server_cycle)
            server.busy = True
            future = executor.submit(
                _process_chunk_single,
                idx, chunk, chunk_contexts[idx],
                server.client,
                params["actual_model"],
                params["current_prompt"],
                params["video_context"],
                params["keywords"],
                params["prompt_mode"],
                params["total_chunks"],
            )
            futures[future] = (idx, server)

        for future in as_completed(futures):
            idx, server = futures[future]
            try:
                chunk_idx, paras, usage, quality_ok, reason = future.result()
                server.report_success()
                if quality_ok:
                    results[chunk_idx] = paras
                    for k in total_usage:
                        total_usage[k] += usage.get(k, 0)
                else:
                    print(f"--- [Parallel] Chunk {chunk_idx+1} 质量不合格 ({reason})，加入重试队列 ---")
                    retry_queue.append(chunk_idx)
                    # 即使质量不合格也记录 token 消耗
                    for k in total_usage:
                        total_usage[k] += usage.get(k, 0)
            except Exception as e:
                server.report_failure()
                print(f"--- [Parallel] Chunk {idx+1} 处理异常: {e} ---")
                retry_queue.append(idx)

    # ── 重试阶段 ──
    if retry_queue:
        print(f"--- [Retry] {len(retry_queue)} chunks 需要重试: {[i+1 for i in retry_queue]} ---")
        for idx in retry_queue:
            retried = False

            # 策略 1: 尝试另一台可用 Ollama 服务器
            for server in pool.get_available_servers():
                try:
                    print(f"--- [Retry] Chunk {idx+1} → {server.base_url} ---")
                    _, paras, usage, quality_ok, reason = _process_chunk_single(
                        idx, chunks[idx], chunk_contexts[idx],
                        server.client, params["actual_model"],
                        params["current_prompt"], params["video_context"],
                        params["keywords"], params["prompt_mode"], params["total_chunks"])
                    for k in total_usage:
                        total_usage[k] += usage.get(k, 0)
                    if quality_ok:
                        results[idx] = paras
                        server.report_success()
                        retried = True
                        break
                    server.report_success()
                except Exception as e:
                    server.report_failure()
                    print(f"--- [Retry] Chunk {idx+1} 在 {server.base_url} 失败: {e} ---")

            # 策略 2: OpenAI 兜底
            if not retried:
                api_key = os.getenv("OPENAI_API_KEY")
                if api_key:
                    try:
                        print(f"--- [Retry] Chunk {idx+1} → OpenAI gpt-4o-mini 兜底 ---")
                        openai_client = OpenAI(api_key=api_key)
                        _, paras, usage, quality_ok, reason = _process_chunk_single(
                            idx, chunks[idx], chunk_contexts[idx],
                            openai_client, "gpt-4o-mini",
                            params["current_prompt"], params["video_context"],
                            params["keywords"], params["prompt_mode"], params["total_chunks"])
                        for k in total_usage:
                            total_usage[k] += usage.get(k, 0)
                        if quality_ok or paras:  # OpenAI 即使质量检查不完美也接受
                            results[idx] = paras
                            retried = True
                    except Exception as e:
                        print(f"--- [Retry] Chunk {idx+1} OpenAI 兜底失败: {e} ---")

            # 策略 3: group_by_time 最终兜底
            if not retried:
                print(f"--- [Retry] Chunk {idx+1} 所有重试失败，使用基础分组 ---")
                results[idx] = group_by_time(chunks[idx])

    # ── 按序组装 ──
    all_paragraphs = []
    for idx in range(total):
        if results[idx]:
            all_paragraphs.extend(results[idx])

    return all_paragraphs, total_usage


# ═══════════════════════════════════════════════════════════════
# 串行处理路径（单服务器回退，保持原有行为）
# ═══════════════════════════════════════════════════════════════

def _process_chunks_sequential(chunks, chunk_contexts, llm_client, provider, params):
    """单服务器串行处理（原有逻辑，作为回退路径）"""
    all_paragraphs = []
    total_usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}

    for idx, chunk in enumerate(chunks):
        try:
            _, paras, usage, quality_ok, reason = _process_chunk_single(
                idx, chunk, chunk_contexts[idx],
                llm_client, params["actual_model"],
                params["current_prompt"], params["video_context"],
                params["keywords"], params["prompt_mode"], params["total_chunks"])
            for k in total_usage:
                total_usage[k] += usage.get(k, 0)
            if paras:
                all_paragraphs.extend(paras)
            else:
                all_paragraphs.extend(group_by_time(chunk))
        except Exception as e:
            print(f"Error processing chunk {idx+1}: {e}")
            all_paragraphs.extend(group_by_time(chunk))

    return all_paragraphs, total_usage

def summarize_text(full_text, title="", description="", language=None):
    """
    调用 LLM 对全文本进行总结并提炼关键词。
    语言优先使用 language 参数（ISO 码，由 worker.py 加权检测后传入），
    未传入时 fallback 到标题/描述文本检测。
    """
    client, provider = get_llm_client()
    if not client:
        return {"summary": "无总结", "keywords": []}, {"prompt_tokens": 0, "completion_tokens": 0}

    # 确定语言：优先使用外部传入的 ISO 语言码
    if language:
        lang = language
    else:
        lang_pref = detect_language_preference(title, description)
        lang = {"english": "en", "traditional": "zh-TW", "simplified": "zh",
                "korean": "ko", "japanese": "ja"}.get(lang_pref, "en")

    print(f"[summarize_text] 使用语言: {lang}")

    if lang == "en":
        system_prompt = "You are a professional video content analyst. Read the video title, description, and timestamped transcript to summarize key insights and extract 5-10 relevant tags."
        user_prompt = f"""
Video title: {title}
Video description: {description}

Transcript to analyze:
{full_text}

[Requirements]:
1. Summarize the video into exactly 7 key points.
2. Each point should be no more than 3 sentences.
3. Each point must end with a timestamp indicating when it appears in the video (format: [01:23]), based on the timestamps in the transcript.
4. **Strict chronological order**: The 7 timestamps must be strictly increasing (point 1 < point 2 < ... < point 7). No time reversal allowed.
5. Write the entire summary in English (matching the video's original language).
6. Extract keywords combining core concepts from the title and details discussed in the transcript.
7. Choose tags that are useful for filtering and discovery (e.g.: AI, productivity, finance, science, etc.).
8. **English only**: Keywords must be concise English terms (1-3 words). No Chinese characters.
9. Exclude generic or meaningless terms.

Output strictly in the following JSON format:
{{
  "summary": "The 7 key points with timestamps, one per line...",
  "keywords": ["keyword1", "keyword2"]
}}
"""
    elif lang in ("zh-TW", "yue"):
        system_prompt = "你是一位專業的視頻內容分析師。請透過閱讀視頻標題、描述及包含時間戳的轉錄全文，總結核心觀點並提取 5-10 個最能代表視頻核心主題且具備分類或搜索價值的關鍵詞（Tag）。"
        user_prompt = f"""
視頻標題: {title}
視頻描述: {description}

待分析轉錄文本:
{full_text}

【任務要求】：
1. 總結視頻內容為恰好 7 個重點內容。
2. 每個重點不超過 3 句話。
3. 每個重點末尾必須添加對應內容在視頻中出現位置的時間戳（格式如 [01:23]），依據所提供文本中的時間標識。
4. **嚴格按視頻播放順序排列**：7 個重點的時間戳必須嚴格遞增（第1條 < 第2條 < … < 第7條），不允許出現時間倒退。
5. 總結部分必須全部使用繁體中文回覆。
6. 綜合標題中的核心概念和全文討論的細節提取關鍵詞。
7. 提取具備通用性、能幫助用戶快速點擊篩選的關鍵詞（如：AI, 科技, 生產力, 財經, 育兒 等）。
8. **繁體中文為主**：關鍵詞使用繁體中文，如有行業通用英文術語可附英文（格式：繁中詞 (English)）。
9. 關鍵詞應簡潔有力，排除掉沒意義的泛指詞。

請嚴格按以下 JSON 格式輸出:
{{
  "summary": "以文本格式輸出的重點總結內容（由於需支持多段落，請結合換行符排版）...",
  "keywords": ["關鍵詞1", "關鍵詞2"]
}}
"""
    elif lang == "ko":
        system_prompt = "당신은 전문 영상 콘텐츠 분석가입니다. 영상 제목, 설명, 타임스탬프가 포함된 전체 스크립트를 읽고 핵심 내용을 요약하고 5-10개의 키워드를 추출하세요."
        user_prompt = f"""
영상 제목: {title}
영상 설명: {description}

분석할 스크립트:
{full_text}

【요구 사항】:
1. 영상 내용을 정확히 7개의 핵심 포인트로 요약하세요.
2. 각 포인트는 3문장 이내로 작성하세요.
3. 각 포인트 끝에 해당 내용이 영상에서 등장하는 시간의 타임스탬프를 추가하세요 (형식: [01:23]).
4. **엄격한 시간순 정렬**: 7개 포인트의 타임스탬프는 반드시 순서대로 증가해야 합니다.
5. 요약 전체를 한국어로 작성하세요.
6. 제목의 핵심 개념과 스크립트에서 논의된 세부 사항을 결합하여 키워드를 추출하세요.
7. 필터링과 검색에 유용한 키워드를 선택하세요 (예: AI, 생산성, 재테크, 과학 등).
8. **한국어 우선**: 키워드는 한국어로 작성하고, 필요시 영어 전문 용어를 병기하세요 (예: 인공지능 (AI)).
9. 의미 없는 일반적인 단어는 제외하세요.

다음 JSON 형식으로 엄격히 출력하세요:
{{
  "summary": "타임스탬프가 포함된 7개의 핵심 포인트 (줄바꿈으로 구분)...",
  "keywords": ["키워드1", "키워드2"]
}}
"""
    elif lang == "ja":
        system_prompt = "あなたはプロのビデオコンテンツアナリストです。ビデオのタイトル、説明、タイムスタンプ付き文字起こしを読んで、重要なポイントをまとめ、5〜10個のキーワードを抽出してください。"
        user_prompt = f"""
動画タイトル: {title}
動画説明: {description}

分析するトランスクリプト:
{full_text}

【要件】:
1. 動画の内容をちょうど7つのポイントに要約してください。
2. 各ポイントは3文以内にしてください。
3. 各ポイントの末尾に、その内容が動画で登場するタイムスタンプを追加してください（形式: [01:23]）。
4. **厳密な時系列順**: 7つのポイントのタイムスタンプは必ず増加する順序にしてください。
5. 要約全体を日本語で記述してください。
6. タイトルのコアコンセプトと文字起こしで議論された詳細を組み合わせてキーワードを抽出してください。
7. フィルタリングと検索に役立つキーワードを選んでください（例: AI, 生産性, 財務, 科学など）。
8. **日本語優先**: キーワードは日本語で記述し、必要に応じて英語の専門用語を付記してください（例: 人工知能 (AI)）。
9. 意味のない一般的な用語は除外してください。

以下のJSON形式で厳密に出力してください:
{{
  "summary": "タイムスタンプ付きの7つの重要ポイント（改行で区切り）...",
  "keywords": ["キーワード1", "キーワード2"]
}}
"""
    elif lang in ("zh", "cmn"):
        # simplified Chinese (default for Mandarin)
        system_prompt = "你是一位专业的视频内容分析师。请通过阅读视频标题、描述及包含时间戳的转录全文，总结核心观点并提取 5-10 个最能代表视频核心主题且具备分类或搜索价值的关键词（Tag）。"
        user_prompt = f"""
视频标题: {title}
视频描述: {description}

待分析转录文本:
{full_text}

【任务要求】：
1. 总结视频内容为恰好 7 个重点内容。
2. 每个重点不超过 3 句话。
3. 每个重点末尾必须添加对应内容在视频中出现位置的时间戳（格式如 [01:23]），依据所提供文本中的时间标识。
4. **严格按视频播放顺序排列**：7 个重点的时间戳必须严格递增（第1条 < 第2条 < … < 第7条），不允许出现时间倒退。
5. 总结部分必须全部使用简体中文回复。
6. 综合标题中的核心概念和全文讨论的细节提取关键词。
7. 提取具备通用性、能帮助用户快速点击筛选的关键词（如：AI, 科技, 生产力, 财经, 育儿 等）。
8. **中英双语对齐（CRITICAL）**：对于具备行业通用性或分类价值的关键词，必须输出为"中文 (English)"格式。例如：将"财经"输出为"财经 (Finance)"，"人工智能"输出为"人工智能 (AI)"。
9. 关键词应简洁有力，通常为 2-4 个汉字配合英文，排除掉没意义的泛指词。

请严格按以下 JSON 格式输出:
{{
  "summary": "以文本格式输出的重点总结内容（由于需支持多段落，请结合换行符排版，切勿使用 JSON 不支持的单行纯文本限制）...",
  "keywords": ["关键词1", "关键词2"]
}}
"""
    else:
        # 通用兜底：其他语言（法语、西班牙语、阿拉伯语等）
        system_prompt = "You are a professional video content analyst. Read the video title, description, and timestamped transcript to summarize key insights and extract 5-10 relevant tags."
        user_prompt = f"""
Video title: {title}
Video description: {description}

Transcript to analyze:
{full_text}

[Requirements]:
1. Summarize the video into exactly 7 key points.
2. Each point should be no more than 3 sentences.
3. Each point must end with a timestamp indicating when it appears in the video (format: [01:23]), based on the timestamps in the transcript.
4. **Strict chronological order**: The 7 timestamps must be strictly increasing (point 1 < point 2 < ... < point 7). No time reversal allowed.
5. **Respond entirely in the same language as the video transcript** (detected language: {lang}).
6. Extract keywords combining core concepts from the title and details discussed in the transcript.
7. Choose tags that are useful for filtering and discovery.
8. Keywords should be in the video's primary language; append English equivalent in parentheses if it aids searchability.
9. Exclude generic or meaningless terms.

Output strictly in the following JSON format:
{{
  "summary": "The 7 key points with timestamps, one per line...",
  "keywords": ["keyword1", "keyword2"]
}}
"""

    default_model = os.getenv("OLLAMA_MODEL", "qwen:8b") if provider == "ollama" else "gpt-4o-mini"

    def _call_llm(llm_client, llm_model, use_json_format=True):
        """执行 LLM 调用，返回 (data, usage)。"""
        kwargs = dict(
            model=llm_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
        )
        if use_json_format:
            kwargs["response_format"] = {"type": "json_object"}
        response = llm_client.chat.completions.create(**kwargs)
        content = response.choices[0].message.content
        # 从 response 中提取 JSON（Ollama 可能把 JSON 嵌在 markdown 代码块里）
        try:
            data = json.loads(content)
        except Exception:
            import re as _re
            match = _re.search(r'```(?:json)?\s*(\{.*?\})\s*```', content, _re.DOTALL)
            if match:
                data = json.loads(match.group(1))
            else:
                match2 = _re.search(r'\{.*\}', content, _re.DOTALL)
                data = json.loads(match2.group(0)) if match2 else {}
        usage_obj = response.usage
        usage = {
            "prompt_tokens": usage_obj.prompt_tokens if usage_obj else 0,
            "completion_tokens": usage_obj.completion_tokens if usage_obj else 0,
            "total_tokens": usage_obj.total_tokens if usage_obj else 0,
        }
        return data, usage

    def _postprocess(data):
        """对 summary 做后处理：分行、整理时间戳、排序。"""
        if not data.get("summary"):
            return data
        import re as _re

        def _ts_to_sec(ts):
            m = _re.match(r'\[(\d{2}):(\d{2})(?::(\d{2}))?\]', ts)
            if not m: return 0
            h = int(m.group(1)) if m.group(3) else 0
            mn = int(m.group(2)) if m.group(3) else int(m.group(1))
            s = int(m.group(3)) if m.group(3) else int(m.group(2))
            return h * 3600 + mn * 60 + s

        summary = data["summary"]
        lines = [l for l in summary.split('\n') if l.strip()]
        if len(lines) <= 1:
            parts = _re.split(r'(?=\d+\.\s)', summary.strip())
            parts = [p.strip() for p in parts if p.strip()]
            if len(parts) > 1:
                lines = parts
            else:
                parts = _re.split(r'(?<=\[\d{2}:\d{2}\])\s*(?=\S)|(?<=\[\d{2}:\d{2}:\d{2}\])\s*(?=\S)', summary.strip())
                parts = [p.strip() for p in parts if p.strip()]
                if len(parts) > 1:
                    lines = parts

        fixed_lines = []
        for line in lines:
            timestamps = _re.findall(r'\[\d{2}:\d{2}(?::\d{2})?\]', line)
            if timestamps:
                last_ts = timestamps[-1]
                text = _re.sub(r'\s*\[\d{2}:\d{2}(?::\d{2})?\]\s*', ' ', line).strip()
                fixed_lines.append(f"{text}{last_ts}")
            else:
                fixed_lines.append(line)

        if any(_re.search(r'\[\d{2}:\d{2}(?::\d{2})?\]', l) for l in fixed_lines):
            fixed_lines.sort(key=lambda l: _ts_to_sec(
                _re.search(r'\[\d{2}:\d{2}(?::\d{2})?\]', l).group()
                if _re.search(r'\[\d{2}:\d{2}(?::\d{2})?\]', l) else '[00:00]'
            ))

        data["summary"] = '\n'.join(fixed_lines)
        return data

    try:
        data, usage = _call_llm(client, default_model, use_json_format=True)
        return _postprocess(data), usage
    except Exception as e:
        print(f"Summarization Error ({provider}): {e}")
        # Fallback：切换到备用 provider 重试一次
        fb_client, fb_provider = get_llm_client(fallback=True)
        if fb_client:
            try:
                fb_model = os.getenv("OLLAMA_MODEL", "qwen3:8b") if fb_provider == "ollama" else "gpt-4o-mini"
                print(f"[summarize_text] Retrying with fallback provider: {fb_provider}, model={fb_model}")
                # Ollama 对 json_object 支持不稳定，先不传 response_format
                use_json = fb_provider != "ollama"
                data, usage = _call_llm(fb_client, fb_model, use_json_format=use_json)
                return _postprocess(data), usage
            except Exception as e2:
                print(f"Summarization Fallback Error ({fb_provider}): {e2}")
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


# ═══════════════════════════════════════════════════════════════
# 双语翻译模块
# ═══════════════════════════════════════════════════════════════

LANG_NAME_MAP = {
    "en": "English",
    "english": "English",
    "zh": "简体中文",
    "simplified": "简体中文",
    "traditional": "繁體中文",
    "korean": "한국어",
    "japanese": "日本語",
}

def _get_target_lang_name(target_lang):
    return LANG_NAME_MAP.get(target_lang, target_lang)


def _translate_metadata(title, summary, keywords, source_lang, target_lang, llm_client, model):
    """
    翻译标题、摘要和关键词（合并为一次 LLM 调用节省 token）。
    返回: ({"title": ..., "summary": ..., "keywords": [...]}, usage)
    """
    target_name = _get_target_lang_name(target_lang)

    prompt = f"""你是一位专业翻译。请将以下内容翻译为{target_name}。

规则：
1. summary 中的时间戳 [MM:SS] 或 [HH:MM:SS] 必须原样保留，不翻译。
2. summary 的每行结构保持不变（一行一个要点）。
3. keywords 逐个翻译，保持数组长度不变。
4. 翻译要自然流畅，符合目标语言表达习惯。

输入：
{{
  "title": {json.dumps(title, ensure_ascii=False)},
  "summary": {json.dumps(summary, ensure_ascii=False)},
  "keywords": {json.dumps(keywords, ensure_ascii=False)}
}}

请输出相同结构的 JSON：
{{"title": "...", "summary": "...", "keywords": [...]}}"""

    response = llm_client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": f"你是专业翻译，将内容翻译为{target_name}。保持格式不变。"},
            {"role": "user", "content": prompt}
        ],
        response_format={"type": "json_object"},
        temperature=0.1,
    )

    content = response.choices[0].message.content
    usage = {
        "prompt_tokens": response.usage.prompt_tokens,
        "completion_tokens": response.usage.completion_tokens,
        "total_tokens": response.usage.total_tokens,
    }

    try:
        data = json.loads(content)
    except Exception:
        match = re.search(r'\{.*\}', content or "", re.DOTALL)
        if match:
            data = json.loads(match.group(0))
        else:
            raise ValueError(f"翻译元数据 JSON 解析失败: {content[:200]}")

    return data, usage


def _translate_paragraphs_chunk(idx, paragraphs_chunk, source_lang, target_lang, llm_client, model, total_chunks):
    """
    翻译一个 chunk 的段落（保持时间戳和结构不变，只翻译 text 字段）。
    返回: (idx, translated_paragraphs, usage)
    """
    target_name = _get_target_lang_name(target_lang)

    # 构建输入文本
    input_lines = []
    for p_idx, para in enumerate(paragraphs_chunk):
        for s in para.get("sentences", []):
            input_lines.append(f"[{s['start']:.1f}] {s['text']}")
        input_lines.append("---")  # 段落分隔符

    prompt = f"""你是一位专业翻译。请将以下字幕翻译为{target_name}。

规则：
1. 每行格式为 [时间戳] 文字，翻译后保持相同格式：[时间戳] 翻译后文字。
2. 时间戳必须原样保留。
3. "---" 是段落分隔符，必须原样保留。
4. 输入多少行，输出就必须多少行（不含分隔符的行数必须一致）。
5. 翻译要自然流畅，符合{target_name}表达习惯。

输入：
{chr(10).join(input_lines)}

请输出与输入完全相同结构的 JSON：
{{
  "paragraphs": [
    {{
      "sentences": [
        {{"start": 0.0, "text": "translated text here"}}
      ]
    }}
  ]
}}"""

    response = llm_client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": f"你是专业字幕翻译，翻译为{target_name}。保持时间戳和段落结构不变，只翻译文字内容。必须输出 JSON。"},
            {"role": "user", "content": prompt}
        ],
        response_format={"type": "json_object"},
        temperature=0.1,
    )

    content = response.choices[0].message.content
    usage = {
        "prompt_tokens": response.usage.prompt_tokens,
        "completion_tokens": response.usage.completion_tokens,
        "total_tokens": response.usage.total_tokens,
    }

    print(f"--- [Translate] Chunk {idx+1}/{total_chunks} 完成 ---")

    try:
        data = json.loads(content)
    except Exception:
        match = re.search(r'\{.*\}', content or "", re.DOTALL)
        if match:
            data = json.loads(match.group(0))
        else:
            raise ValueError(f"翻译段落 JSON 解析失败: {content[:200]}")

    # 解析段落
    translated_paras = []
    if isinstance(data, dict) and "paragraphs" in data:
        translated_paras = data["paragraphs"]
    elif isinstance(data, dict):
        for val in data.values():
            if isinstance(val, list):
                translated_paras = val
                break

    # 如果 LLM 输出的段落数与输入不匹配，尝试用原始时间戳修补
    if len(translated_paras) != len(paragraphs_chunk):
        print(f"Warning: [Translate] Chunk {idx+1} 段落数不匹配 (期望 {len(paragraphs_chunk)}, 得到 {len(translated_paras)})")
        # 尽量保留已翻译内容，用原始时间戳补齐
        for p_idx, para in enumerate(translated_paras):
            if p_idx < len(paragraphs_chunk):
                orig_sentences = paragraphs_chunk[p_idx].get("sentences", [])
                trans_sentences = para.get("sentences", [])
                for s_idx, s in enumerate(trans_sentences):
                    if s_idx < len(orig_sentences):
                        s["start"] = orig_sentences[s_idx]["start"]

    return idx, translated_paras, usage


def translate_content(title, paragraphs, summary, keywords, source_lang, target_lang):
    """
    将视频内容从 source_lang 翻译到 target_lang。

    返回: (translated_dict, total_usage)
        translated_dict = {"title": ..., "paragraphs": [...], "summary": ..., "keywords": [...]}
    """
    print(f"=== [Translate] 开始翻译: {source_lang} → {target_lang} ===")

    llm_client, provider = get_llm_client()
    if not llm_client:
        raise ValueError("无可用的 LLM 客户端")

    if provider == "ollama":
        model = os.getenv("OLLAMA_MODEL", "qwen3:8b")
    else:
        model = "gpt-4o-mini"

    total_usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}

    # 1. 翻译 metadata（title + summary + keywords）
    print(f"--- [Translate] 翻译标题/摘要/关键词 ---")
    meta_result, meta_usage = _translate_metadata(
        title, summary or "", keywords or [], source_lang, target_lang, llm_client, model
    )
    for k in total_usage:
        total_usage[k] += meta_usage.get(k, 0)

    # 2. 翻译 paragraphs（分 chunk 处理）
    if not paragraphs:
        translated_paras = []
    else:
        CHUNK_SIZE = 15  # 每 chunk 约 15 个段落
        chunks = [paragraphs[i:i+CHUNK_SIZE] for i in range(0, len(paragraphs), CHUNK_SIZE)]
        total_chunks = len(chunks)
        print(f"--- [Translate] 翻译字幕: {len(paragraphs)} 段落 → {total_chunks} chunks ---")

        # 尝试使用 ServerPool 并行处理
        pool = ServerPool()
        available = pool.get_available_servers() if pool else []

        if len(available) > 1 and total_chunks > 1:
            # 并行翻译
            print(f"--- [Translate] 并行处理: {total_chunks} chunks → {len(available)} servers ---")
            translated_paras = [None] * total_chunks
            with ThreadPoolExecutor(max_workers=len(available)) as executor:
                server_cycle = itertools.cycle(available)
                futures = {}
                for idx, chunk in enumerate(chunks):
                    server = next(server_cycle)
                    future = executor.submit(
                        _translate_paragraphs_chunk,
                        idx, chunk, source_lang, target_lang,
                        server.client, model, total_chunks
                    )
                    futures[future] = idx

                for future in as_completed(futures):
                    idx = futures[future]
                    try:
                        _, paras, usage = future.result()
                        translated_paras[idx] = paras
                        for k in total_usage:
                            total_usage[k] += usage.get(k, 0)
                    except Exception as e:
                        print(f"--- [Translate] Chunk {idx+1} 并行翻译失败: {e}，使用原文 ---")
                        translated_paras[idx] = chunks[idx]

            # 展平
            all_paras = []
            for paras in translated_paras:
                if paras:
                    all_paras.extend(paras)
            translated_paras = all_paras
        else:
            # 串行翻译
            translated_paras = []
            for idx, chunk in enumerate(chunks):
                try:
                    _, paras, usage = _translate_paragraphs_chunk(
                        idx, chunk, source_lang, target_lang,
                        llm_client, model, total_chunks
                    )
                    translated_paras.extend(paras)
                    for k in total_usage:
                        total_usage[k] += usage.get(k, 0)
                except Exception as e:
                    print(f"--- [Translate] Chunk {idx+1} 串行翻译失败: {e}，使用原文 ---")
                    translated_paras.extend(chunk)

    result = {
        "title": meta_result.get("title", title),
        "paragraphs": translated_paras,
        "summary": meta_result.get("summary", summary),
        "keywords": meta_result.get("keywords", keywords),
    }

    print(f"=== [Translate] 翻译完成: tokens={total_usage['total_tokens']} ===")
    return result, total_usage
