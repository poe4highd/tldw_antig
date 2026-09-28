#!/bin/bash
# 每周升级 yt-dlp（由 tldw-ytdlp-upgrade.timer 触发）
# YouTube 频繁变更下载机制，yt-dlp 过旧会导致全部下载 403（2026-08 曾因此停摆 6 周）
set -uo pipefail
cd "$(dirname "$(readlink -f "$0")")/../../backend"

before=$(venv/bin/python -m yt_dlp --version 2>/dev/null || echo "unknown")
if venv/bin/pip install -q -U "yt-dlp[default]"; then
    after=$(venv/bin/python -m yt_dlp --version)
    echo "[yt-dlp upgrade] $before -> $after"
else
    echo "[yt-dlp upgrade] 升级失败（当前 $before）" >&2
    venv/bin/python -c "from alerting import send_email_alert; send_email_alert('yt-dlp 自动升级失败', '当前版本 $before，请查看 journalctl --user -u tldw-ytdlp-upgrade')"
    exit 1
fi
