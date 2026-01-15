# 混合云部署指南 (Hybrid Lite Deployment Guide)

本指南详细说明了如何实现“前端 Vercel + 后端本地内网穿透”的部署方案，使您的服务可供全球用户访问，同时保持低成本运行。

---

## 准备工作一：前端部署 (Vercel)

### 1. 仓库准备
*   确保您的最新代码已推送至 GitHub/GitLab。
*   确认前端 `frontend` 目录下的 `package.json` 配置正确。

### 2. Vercel 项目创建
*   在 Vercel 控制台导入您的 GitHub 仓库。
*   **Root Directory**: 选中 `frontend` 目录。
*   **Framework Preset**: 选择 `Next.js`。

### 3. 环境参数配置
*   在 Vercel 项目设置中，预留一个名为 `NEXT_PUBLIC_API_BASE` 的环境变量（可选）。
    *   *注：正式版代码需适配该变量，以便切换本地 IP 和公网隧道地址。*

---

## 准备工作二：后端内网穿透 (Tunneling)

### 推荐方案 A：Cloudflare Tunnel (更稳定，适合长期)
1.  **安装 Cloudflared**: 在本地服务器安装 Cloudflare 官方客户端。
2.  **创建隧道**: 通过命令行执行 `cloudflared tunnel create <name>`。
3.  **路由配置**: 将您的端口 `8000` 映射到一个您拥有的二级域名（例如 `api-tldw.yourdomain.com`）。
4.  **运行隧道**: 保持客户端在后台运行，确保请求能转发至本地。

### 推荐方案 B：ngrok (配置简单，适合快速测试)
1.  **注册账号**: 并在本地安装 ngrok 客户端。
2.  **启动转发**: 执行 `ngrok http 8000`。
3.  **获取地址**: 复制生成的 `https://xxxx.ngrok-free.app` 地址，这就是您的公网 API 终点。

---

## 准备工作三：代码适配概要

1.  **CORS 策略**:
    *   后端 `main.py` 的 `CORSMiddleware` 需要允许来自 `*.vercel.app` 的域名请求。
2.  **API 地址切换**:
    *   前端代码需要增加逻辑：如果存在环境变量或用户手动指定，则使用穿透后的 `https` 域名而非 `localhost:8000`。
3.  **HTTPS 兼容性**:
    *   由于 Vercel 强制 HTTPS，穿透地址也**必须**支持 HTTPS（上述方案均自带）。

---
*版本：v1.0 | 更新日期：2026-01-14*
