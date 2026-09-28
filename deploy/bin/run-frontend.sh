#!/bin/bash
# 本地 Next.js 开发服务器（由 tldw-frontend.service 调用；生产前端在 Vercel）
set -euo pipefail
cd "$(dirname "$(readlink -f "$0")")/../../frontend"
fuser -k 3000/tcp 2>/dev/null || true
exec npm run dev
