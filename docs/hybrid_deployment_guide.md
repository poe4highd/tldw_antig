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

### 推荐方案 A：Cloudflare Tunnel (多服务穿透)

由于 Vercel (HTTPS) 要求 API 也必须是 HTTPS，且 `cloudflared` 默认一个 URL 对应一个端口，您需要确保**前后端同时穿透**。

#### 1. 双隧道方案 (推荐)
为了性能和独立管理，建议运行两个隧道：
*   **前端隧道**: `cloudflared tunnel --url http://localhost:3000` -> 获得 URL A。
*   **后端隧道**: `cloudflared tunnel --url http://localhost:8000` -> 获得 URL B。

#### 2. 配置与常见报错 (Mixed Content)
如果您发现页面能打开但数据加载失败，并提示 `Mixed Content`：
*   **原因**: HTTPS 页面请求了 HTTP 的 API。
*   **修复**: 我们的代码已支持动态协议检测。如果您的页面是 `https://...`，它会自动尝试使用 `https://` 请求后端。
*   **关键配置**: 在 Vercel 或启动前端时，设置环境变量 `NEXT_PUBLIC_API_BASE=https://您的后端隧道地址`。如果不设置且在本地访问，系统会自动尝试 `http://localhost:8000`。

#### 3. Cloudflare Tunnel 免费版指南 (Dashboard 方式)
1.  **准备域名**: 将您的域名 DNS 托管给 Cloudflare。
2.  **创建隧道**: 在 Zero Trust 控制台创建隧道，并安装连接器。
3.  **配置 Public Hostname**:
    *   **域名 1 (UI)**: `tldw.yourdomain.com` -> `http://localhost:3000`
    *   **域名 2 (API)**: `api-tldw.yourdomain.com` -> `http://localhost:8000`
4.  **完成**: 这种方式最稳定，且完全免费。

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
