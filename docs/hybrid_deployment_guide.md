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

### 3. Vercel 环境变量 (Environment Variables)
在 Vercel 中，您**只需要**添加一个变量：
*   **Key**: `NEXT_PUBLIC_API_BASE`
*   **Value**: `https://api.yourdomain.com` (填写您在 Cloudflare 中准备映射给后端的完整二级域名)
*   **说明**: 后端的 `OPENAI_API_KEY` 等敏感信息保存在您本地的 `.env` 即可，不需要上传到 Vercel，因为处理任务是在您本地机器执行的。

---

## 准备工作一 (补充)：Vercel 绑定自定义域名

如果您希望通过您的自定义域名访问前端（例如 `www.yourdomain.com` 或 `tldw.yourdomain.com`）：

### 1. Vercel 控制台配置
1.  进入 Vercel 项目控制面板 -> **Settings** -> **Domains**。
2.  输入您的域名（例如 `tldw.yourdomain.com`），点击 **Add**。
3.  Vercel 会提示您配置 DNS 记录。它通常会提供两种选择：**A 记录** 或 **CNAME 记录**。
    *   **推荐模式**: 如果是二级域名（如 `tldw.vourdomain.com`），请使用 **CNAME** 指向 `cname.vercel-dns.com`。

### 2. Cloudflare DNS 配置
由于您的域名托管在 Cloudflare，请前往 [Cloudflare Dashboard](https://dash.cloudflare.com/)：
1.  选择您的域名 -> **DNS** -> **Records**。
2.  点击 **Add record**。
3.  **Type**: `CNAME`
4.  **Name**: `tldw` (即您的二级域名前缀)
5.  **Target**: `cname.vercel-dns.com`
6.  **Proxy status**: **DNS Only** (通常建议先关闭代理以加速 Vercel 自动化颁发 SSL 证书，稳定后可根据需要开启)。

### 3. 等待生效
*   回到 Vercel 域名设置页面，看到 **Valid Configuration** 变为绿色勾选，说明绑定成功。
*   现在您可以通过 `https://tldw.yourdomain.com` 访问您的前端。

---

## 准备工作二：Cloudflare Tunnel 详细操作 (自有域名版)

既然您已有 DNS 域名，建议使用最稳定的 **Dashboard 模式**：

### 第一步：域名接入 Cloudflare
*   确保您的域名 DNS 解析已托管在 Cloudflare（即 NameServers 已指向 Cloudflare）。

### 第二步：创建持久化隧道
1.  登录 [Cloudflare Zero Trust 控制台](https://one.dash.cloudflare.com/)。
2.  点击左侧 **Networks** -> **Tunnels**。
3.  点击 **Create a Tunnel**，选择 **Cloudflared** 方案。
4.  给隧道命名（例如 `mac-mini-tldw`）。

### 第三步：安装连接器 (Connector)
*   页面会显示一段安装命令。由于您已经通过 `brew` 安装了 `cloudflared`，您只需要运行页面提供的 **Connector Token** 命令（通常是以 `cloudflared service install ...` 开头的一行）。
*   运行后，回到网页，如果显示 **Status: Healthy**，说明您的本地机器已成功连上 Cloudflare 网络。

### 第四步：配置域名映射 (Public Hostname)
1.  在刚才创建的隧道后面点击 **Edit**。
2.  切换到 **Public Hostname** 标签页，点击 **Add a public hostname**。
3.  **Subdomain**: 输入 `api` (或其他您喜欢的名字)。
4.  **Domain**: 选择您已有的域名。
5.  **Service**:
    *   **Type**: `HTTP`
    *   **URL**: `localhost:8000` (这是您的后端端口)。
6.  点击 **Save hostname**。

### 第五步：验证
*   现在，您可以直接在浏览器访问 `https://api.yourdomain.com/history`。
*   如果能看到 JSON 数据，说明穿透成功。

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
