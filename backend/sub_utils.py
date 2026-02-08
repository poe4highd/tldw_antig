import re
import os
import json

def parse_vtt_srt(file_path):
    """
    极简解析 VTT 或 SRT 文件，提取时间轴和文本。
    返回格式: [{"start": float, "end": float, "text": str}, ...]
    """
    if not os.path.exists(file_path):
        return []
        
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
        
    # 统一换行符
    content = content.replace("\r\n", "\n")
    
    # 匹配时间轴和文本
    # VTT/SRT 时间格式: 00:00:01.000 --> 00:00:04.000 或 00:00:01,000 --> 00:00:04,000
    # 我们使用通用的正则表达式
    pattern = re.compile(r"(\d{2}:\d{2}:\d{2}[.,]\d{3}) --> (\d{2}:\d{2}:\d{2}[.,]\d{3})\n(.*?)(?=\n\n|\n\d+\n|\n\d{2}:|$)", re.DOTALL)
    
    matches = pattern.findall(content)
    
    def time_to_seconds(t_str):
        t_str = t_str.replace(",", ".")
        h, m, s = t_str.split(":")
        return int(h) * 3600 + int(m) * 60 + float(s)

    results = []
    for m in matches:
        start_t = time_to_seconds(m[0])
        end_t = time_to_seconds(m[1])
        text = m[2].replace("\n", " ").strip()
        # 移除 VTT 的一些标签 如 <v ...>
        text = re.sub(r"<[^>]+>", "", text)
        if text:
            results.append({
                "start": start_t,
                "end": end_t,
                "text": text,
                "words": [] # Whisper 格式通常包含 words，这里留空
            })
            
    return results

def find_downloaded_subtitles(video_id, directory="downloads"):
    """
    在下载目录中寻找该视频的字幕文件。
    返回找到的第一个有效字幕文件路径。
    """
    if not os.path.exists(directory):
        return None
        
    # yt-dlp 下载的字幕通常命名为 {id}.{lang}.vtt 或 {id}.{lang}.srt
    # 也有可能是 {id}.vtt 直接
    for f in os.listdir(directory):
        if f.startswith(video_id) and (f.endswith(".vtt") or f.endswith(".srt")):
            # 优先选择中文
            if ".zh" in f:
                return os.path.join(directory, f)
                
    # 如果没找到中文，返回第一个找到的
    for f in os.listdir(directory):
        if f.startswith(video_id) and (f.endswith(".vtt") or f.endswith(".srt")):
            return os.path.join(directory, f)
            
    return None
