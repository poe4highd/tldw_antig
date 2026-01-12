import yt_dlp
import os

def download_audio(url: str, output_path: str = "downloads"):
    if not os.path.exists(output_path):
        os.makedirs(output_path)
    
    ydl_opts = {
        'format': 'm4a/bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '128', # 降低到 128k 以减小体积，适配 OpenAI 25MB 限制
        }],
        'outtmpl': f'{output_path}/%(id)s.%(ext)s', # 使用 ID 作为文件名方便缓存
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = f"{output_path}/{info['id']}.mp3"
        return filename, info['title']
