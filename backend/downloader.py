import os

def download_audio(url: str, output_path: str = "downloads", progress_callback=None):
    import yt_dlp
    if not os.path.exists(output_path):
        os.makedirs(output_path)
    
    def ydl_progress_hook(d):
        if d['status'] == 'downloading':
            p = d.get('_percent_str', '0%').replace('%','')
            try:
                if progress_callback:
                    progress_callback(float(p))
            except:
                pass

    ydl_opts = {
        'format': 'm4a[language*=zh]/bestaudio[language*=zh]/m4a/bestaudio/best',
        'outtmpl': f'{output_path}/%(id)s.%(ext)s',
        'progress_hooks': [ydl_progress_hook],
        'noplaylist': True,
        'quiet': True,
        'no_warnings': True,
        'nocheckcertificate': True,
        'headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://www.youtube.com/',
        },
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        # 默认使用 m4a 格式（YouTube 原生，无需转换更快速）
        filename = os.path.join(output_path, f"{info['id']}.m4a")
        
        # 检查实际下载的文件名（有时 ext 可能是 webm）
        actual_ext = info.get('ext', 'm4a')
        if actual_ext != 'm4a':
            filename = os.path.join(output_path, f"{info['id']}.{actual_ext}")

        thumbnail = info.get('thumbnail')
        return filename, info['title'], thumbnail
