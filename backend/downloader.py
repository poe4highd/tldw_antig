import os
import shutil

def _find_ffmpeg():
    """查找 ffmpeg 路径，优先系统 PATH，后备 anaconda"""
    path = shutil.which('ffmpeg')
    if path:
        return os.path.dirname(path)
    # 常见后备路径
    for candidate in ['/home/xs/anaconda3/bin', '/usr/local/bin', '/usr/bin']:
        if os.path.isfile(os.path.join(candidate, 'ffmpeg')):
            return candidate
    return None

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
        # 缩略图下载与转换
        'writethumbnail': True,
        'postprocessors': [{
            'key': 'FFmpegThumbnailsConvertor',
            'format': 'jpg',
            'when': 'before_dl',
        }],
        # 字幕下载配置
        'writesubtitles': True,
        'writeautomaticsub': True,
        'subtitleslangs': ['zh.*', 'en.*'], # 优先下载中文或英文
        'subtitlesformat': 'vtt/srt/best',
    }

    # ffmpeg 路径（systemd 环境可能不含 anaconda PATH）
    ffmpeg_dir = _find_ffmpeg()
    if ffmpeg_dir:
        ydl_opts['ffmpeg_location'] = ffmpeg_dir

    # YouTube Cookies Support
    cookies_path = os.environ.get("YOUTUBE_COOKIES_PATH")
    if cookies_path and os.path.exists(cookies_path):
        ydl_opts['cookiefile'] = cookies_path

    # 多层重试策略：
    # 尝试 1: 完整下载（cookies + 字幕）
    # 尝试 2: 禁用字幕（cookies, 无字幕）—— 处理字幕 429 限流
    # 尝试 3: 禁用 cookies（无 cookies, 无字幕）—— 处理过期 cookies 导致格式不可用
    for attempt in range(3):
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                if info is None:
                    raise Exception("yt-dlp extract_info returned None")
                # 默认使用 m4a 格式（YouTube 原生，无需转换更快速）
                filename = os.path.join(output_path, f"{info['id']}.m4a")

                # 检查实际下载的文件名（有时 ext 可能是 webm 或 mp4）
                actual_ext = info.get('ext', 'm4a')
                if actual_ext != 'm4a':
                    filename = os.path.join(output_path, f"{info['id']}.{actual_ext}")

                # 返回本地化的缩略图文件名
                thumbnail_path = os.path.join(output_path, f"{info['id']}.jpg")
                thumbnail = info.get('thumbnail')
                if os.path.exists(thumbnail_path):
                    thumbnail = os.path.basename(thumbnail_path)

                return filename, info['title'], thumbnail
        except Exception as e:
            err = str(e)
            if attempt == 0 and ('429' in err or 'subtitle' in err.lower()):
                # 字幕下载 429 限流，禁用字幕重试
                print(f"[Downloader] Subtitle download failed, retrying without subtitles...")
                ydl_opts['writesubtitles'] = False
                ydl_opts['writeautomaticsub'] = False
                continue
            if attempt <= 1 and ('format' in err.lower() and 'not available' in err.lower()):
                # 格式不可用（通常是过期 cookies 导致），去掉 cookies 重试
                print(f"[Downloader] Format not available, retrying without cookies...")
                ydl_opts.pop('cookiefile', None)
                ydl_opts['writesubtitles'] = False
                ydl_opts['writeautomaticsub'] = False
                continue
            raise
