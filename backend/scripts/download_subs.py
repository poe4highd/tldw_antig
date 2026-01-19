#!/usr/bin/env python3
import os
import sys
import argparse
import subprocess

def download_subtitles(video_input, output_dir="backend/tests/data"):
    """
    使用 yt-dlp 下载指定视频的字幕。
    """
    # 确保输出目录存在
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"创建目录: {output_dir}")

    # yt-dlp 基础选项
    # --skip-download: 不下载视频
    # --write-sub: 下载手工上传的字幕
    # --write-auto-sub: 下载自动生成的字幕
    # --sub-format: 优先选择 srv1, vtt, ttml
    # --sub-langs: 优先下载简体中文、中文、英文
    # --output: 指定保存路径和文件名格式
    
    cmd = [
        "yt-dlp",
        "--skip-download",
        "--write-sub",
        "--write-auto-sub",
        "--sub-format", "srv1/vtt/ttml",
        "--sub-langs", "zh-Hans,zh,zh-CN,zh-TW,en",
        "--output", f"{output_dir}/%(id)s.%(ext)s",
        video_input
    ]

    print(f"正在运行命令: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("下载完成！")
        print(result.stdout)
        
        # 提取 ID 进行匹配检查
        import re
        id_match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11})", video_input)
        video_id = id_match.group(1) if id_match else video_input
        
        files = os.listdir(output_dir)
        downloaded = [f for f in files if video_id in f]
        if downloaded:
            print(f"已下载文件: {', '.join(downloaded)}")
        else:
            print(f"未在 {output_dir} 中发现包含 {video_id} 的字幕文件。")
            
    except subprocess.CalledProcessError as e:
        print(f"执行出错: {e}")
        print(e.stderr)
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="YouTube 字幕下载脚本")
    parser.add_argument("input", help="YouTube 视频 URL 或视频 ID")
    parser.add_argument("--outdir", default="backend/tests/data", help="输出目录 (默认: backend/tests/data)")

    args = parser.parse_args()
    
    # 路径纠偏：如果用户直接在 backend 目录下运行，避免生成 backend/backend/...
    outdir = args.outdir
    cwd = os.getcwd()
    if cwd.endswith("backend") and outdir.startswith("backend/"):
        outdir = outdir.replace("backend/", "", 1)
        
    download_subtitles(args.input, outdir)
