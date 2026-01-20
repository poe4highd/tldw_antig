"""
幻觉检测与二次转录模块
检测转录结果中的幻觉区域，使用备选模型重新转录
"""

import re
import os
import tempfile
from typing import List, Tuple, Dict, Any

def detect_hallucination_patterns(text: str) -> List[str]:
    """
    检测文本中的幻觉模式，返回匹配到的模式类型列表
    """
    patterns = []
    
    # 模式1: 单/多字循环 (如 "用用用" 或 "能否？！能否？！")
    if re.search(r'(.{1,4})[？！\s]*\1{2,}', text):
        patterns.append("repeat_cycle")
    
    # 模式2: 过多标点符号 (超过5个问号/感叹号)
    if len(re.findall(r'[？！?!]', text)) > 5:
        patterns.append("excess_punctuation")
    
    # 模式3: 极短内容或空
    if len(text.strip()) < 2:
        patterns.append("too_short")
    
    # 模式4: 连续相同字符超过3个 (如 "用用用用")
    if re.search(r'(.)\1{3,}', text):
        patterns.append("char_repeat")
    
    # 模式5: 文本主要由标点组成
    non_punct = re.sub(r'[？！?!\s]', '', text)
    if len(text) > 3 and len(non_punct) < len(text) * 0.3:
        patterns.append("mostly_punctuation")
    
    return patterns


def detect_hallucinations(subtitles: List[Dict[str, Any]]) -> List[Tuple[int, int, float, float]]:
    """
    检测幻觉区域，返回需要重转录的片段范围。
    
    返回格式: [(start_idx, end_idx, start_time, end_time), ...]
    每个范围包含幻觉片段及其前后各1个片段（用于上下文）
    """
    hallucination_indices = []
    
    for i, seg in enumerate(subtitles):
        text = seg.get("text", "")
        patterns = detect_hallucination_patterns(text)
        if patterns:
            hallucination_indices.append(i)
            seg["_hallucination_patterns"] = patterns
    
    if not hallucination_indices:
        return []
    
    # 合并连续索引并扩展前后1个片段
    ranges = merge_and_expand_ranges(hallucination_indices, len(subtitles))
    
    # 转换为带时间戳的范围
    result = []
    for start_idx, end_idx in ranges:
        start_time = subtitles[start_idx].get("start", 0)
        end_time = subtitles[end_idx].get("end", subtitles[end_idx].get("start", 0) + 5)
        result.append((start_idx, end_idx, start_time, end_time))
    
    return result


def merge_and_expand_ranges(indices: List[int], total_count: int, expand: int = 1) -> List[Tuple[int, int]]:
    """
    合并连续索引为范围，并向前后扩展指定数量的片段
    
    Args:
        indices: 检测到的幻觉片段索引列表
        total_count: 字幕总数
        expand: 向前后扩展的片段数
    
    Returns:
        合并后的范围列表 [(start, end), ...]
    """
    if not indices:
        return []
    
    indices = sorted(set(indices))
    ranges = []
    start = indices[0]
    end = indices[0]
    
    for i in indices[1:]:
        if i <= end + 2:  # 允许间隔1个正常片段
            end = i
        else:
            ranges.append((start, end))
            start = i
            end = i
    ranges.append((start, end))
    
    # 扩展范围
    expanded = []
    for start, end in ranges:
        new_start = max(0, start - expand)
        new_end = min(total_count - 1, end + expand)
        expanded.append((new_start, new_end))
    
    return expanded


def extract_audio_segment(audio_path: str, start_sec: float, end_sec: float) -> str:
    """
    提取指定时间范围的音频片段
    
    Returns:
        临时音频文件路径
    """
    try:
        from pydub import AudioSegment
    except ImportError:
        raise ImportError("pydub is required for audio slicing. Install with: pip install pydub")
    
    # 加载音频
    if audio_path.endswith('.m4a'):
        audio = AudioSegment.from_file(audio_path, format="m4a")
    elif audio_path.endswith('.mp3'):
        audio = AudioSegment.from_file(audio_path, format="mp3")
    else:
        audio = AudioSegment.from_file(audio_path)
    
    # 提取片段（添加0.5秒缓冲）
    start_ms = max(0, int((start_sec - 0.5) * 1000))
    end_ms = min(len(audio), int((end_sec + 0.5) * 1000))
    
    segment = audio[start_ms:end_ms]
    
    # 导出到临时文件
    temp_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    segment.export(temp_file.name, format="wav")
    
    return temp_file.name


def retranscribe_with_alternative_model(
    audio_path: str,
    subtitles: List[Dict[str, Any]],
    hallucination_ranges: List[Tuple[int, int, float, float]],
    alt_model_size: str = "base"
) -> List[Dict[str, Any]]:
    """
    对幻觉区域使用备选模型重新转录
    
    Args:
        audio_path: 原始音频文件路径
        subtitles: 原始字幕列表
        hallucination_ranges: 幻觉区域范围
        alt_model_size: 备选模型大小 (base/small)
    
    Returns:
        标记了备选字幕的字幕列表
    """
    from transcriber import transcribe_local
    
    for start_idx, end_idx, start_time, end_time in hallucination_ranges:
        print(f"--- [幻觉检测] 重转录区域: {start_time:.1f}s - {end_time:.1f}s (片段 {start_idx}-{end_idx}) ---")
        
        try:
            # 提取音频片段
            temp_audio = extract_audio_segment(audio_path, start_time, end_time)
            
            # 使用备选模型重转录
            alt_subtitles = transcribe_local(temp_audio, model_size=alt_model_size)
            
            # 调整时间戳（相对时间 → 绝对时间）
            time_offset = max(0, start_time - 0.5)
            for seg in alt_subtitles:
                seg["start"] = seg.get("start", 0) + time_offset
                seg["end"] = seg.get("end", 0) + time_offset
            
            # 标记备选字幕到原始字幕
            for idx in range(start_idx, end_idx + 1):
                if idx < len(subtitles):
                    subtitles[idx]["_alternative_subtitles"] = alt_subtitles
                    subtitles[idx]["_hallucination_flag"] = True
            
            # 清理临时文件
            os.unlink(temp_audio)
            
        except Exception as e:
            print(f"--- [警告] 重转录失败: {e} ---")
            for idx in range(start_idx, end_idx + 1):
                if idx < len(subtitles):
                    subtitles[idx]["_hallucination_flag"] = True
                    subtitles[idx]["_retranscribe_error"] = str(e)
    
    return subtitles


def process_with_hallucination_detection(
    audio_path: str,
    subtitles: List[Dict[str, Any]],
    alt_model_size: str = "base"
) -> List[Dict[str, Any]]:
    """
    主入口：检测幻觉并进行二次转录
    
    Args:
        audio_path: 音频文件路径
        subtitles: 原始转录字幕
        alt_model_size: 备选模型大小
    
    Returns:
        处理后的字幕列表（可能包含备选字幕）
    """
    print(f"--- [幻觉检测] 开始扫描 {len(subtitles)} 个片段 ---")
    
    # 检测幻觉区域
    hallucination_ranges = detect_hallucinations(subtitles)
    
    if not hallucination_ranges:
        print("--- [幻觉检测] 未发现幻觉区域 ---")
        return subtitles
    
    print(f"--- [幻觉检测] 发现 {len(hallucination_ranges)} 个幻觉区域 ---")
    
    # 检查音频文件是否存在
    if not os.path.exists(audio_path):
        print(f"--- [警告] 音频文件不存在: {audio_path}，跳过二次转录 ---")
        return subtitles
    
    # 二次转录
    subtitles = retranscribe_with_alternative_model(
        audio_path, subtitles, hallucination_ranges, alt_model_size
    )
    
    return subtitles
