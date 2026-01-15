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

### 推荐方案 A：Cloudflare Tunnel (更稳定，推荐)

Cloudflare Tunnel 是目前最专业的内网穿透方案，属于 Cloudflare Zero Trust 产品线。

#### 1. 免费版 vs 付费版
*   **免费版 (Free Plan)**: 
    *   **费用**: $0 / 月。
    *   **能力**: 支持无限数量的隧道，支持自定义域名（需将域名托管在 Cloudflare），提供 SSL 证书。对于大众公测完全足够。
    *   **限制**: 基础的安全策略，但对个人开发者来说几乎无感。
*   **付费版 (Standard/Enterprise)**:
    *   **费用**: 约 $7 / 用户 / 月起。
    *   **能力**: 提供更高级的身份验证（SAML）、更细致的访问控制、以及 WARP 客户端的高级性能优化。
    *   **建议**: 除非您需要极高安全等级的企业级身份管控，否则**无需购买**。

#### 2. 详细操作步骤 (免费版)
1.  **准备域名**: 将您的域名（或从第三方购买的域名）的 DNS 托管给 Cloudflare。
2.  **开通 Zero Trust**: 在 Cloudflare 控制台左侧进入 `Zero Trust`，选择连接付款方式（免费版也需要绑定，但不会扣费）。
3.  **创建隧道 (Dashboard 方式)**:
    *   进入 `Networks` -> `Tunnels` -> `Create a tunnel`。
    *   选择 `Cloudflared`，给隧道起个名字库（如 `tldw-backend`）。
    *   **安装连接器**: 根据页面提示，在您的本地服务器运行相应的安装命令（支持 Mac, Linux, Windows, Docker）。
4.  **配置公开主机名 (Public Hostname)**:
    *   在隧道设置中增加 `Public Hostname`。
    *   **Domain**: 输入您的二级域名（如 `api.yourdomain.com`）。
    *   **Service**: 选中 `HTTP`，URL 输入 `localhost:8000`。
5.  **完成**: Cloudflare 会自动创建对应的 DNS 记录。现在访问该域名即可直连您的本地后端。

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
