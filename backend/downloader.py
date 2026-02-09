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
        'format': 'bestaudio/best',
        'outtmpl': f'{output_path}/%(id)s.%(ext)s',
        'progress_hooks': [ydl_progress_hook],
        'noplaylist': True,
        'quiet': True,
        'no_warnings': True,
        'nocheckcertificate': True,
        'js_runtimes': {'node': {}},
        'remote_components': {'ejs:github'},
        'extractor_args': {'youtube': {'player_client': ['android', 'web']}},
        # 字幕下载配置
        'writesubtitles': True,
        'writeautomaticsub': True,
        'subtitleslangs': ['zh.*', 'en.*'], # 优先下载中文或英文
        'subtitlesformat': 'vtt/srt/best',
    }

    # YouTube Cookies Support
    cookies_path = os.environ.get("YOUTUBE_COOKIES_PATH")
    if cookies_path and os.path.exists(cookies_path):
        ydl_opts['cookiefile'] = cookies_path
    
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
