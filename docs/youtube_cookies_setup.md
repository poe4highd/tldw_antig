# YouTube Cookie 设置指南

为了解决使用 `yt-dlp` 下载 YouTube 视频或提取元数据时出现的 `HTTP Error 429: Too Many Requests`（频率限制）或 `403 Forbidden` 错误，本项目支持通过 Cookie 文件进行鉴权。

## 1. 为什么需要 Cookie？
YouTube 对匿名请求（尤其是来自云服务器或数据中心的 IP）有严格的限流措施。使用有效登录状态的 Cookie 可以：
- 绕过 429 频率限制。
- 允许访问受地理限制、年龄限制的视频。
- 模拟真实用户行为，提高下载成功率。

## 2. 如何获取 Cookie 文件

### 推荐方法：使用浏览器扩展
1. 在 Chrome 或 Edge 浏览器中安装扩展：**Get cookies.txt LOCALLY** (或类似的 Netscape 格式导出工具)。
2. 登录您的 **YouTube/Google** 账号。
3. 点击扩展图标，选择 **Export Options** -> **Export as Netscape HTTP Cookie File**。
### 备选方法：使用 OAuth2 (推荐服务器使用)
如果您发现 Cookie 失效（例如 Mac 导出后在 Ubuntu 上不可用），可以使用 `oauth2` 模式：
1. 打开 `backend/.env`，设置 `YOUTUBE_USE_OAUTH2=true`。
2. 在 Ubuntu 服务器终端手动执行一次以下命令进行授权：
   ```bash
   python3 -m yt_dlp --username oauth2 --password "" https://www.youtube.com/watch?v=NRDWBQWiYeg
   ```
3. 终端会给出一个 8 位验证码并提供一个 Google 验证网址（`https://www.google.com/device`）。
4. 在您的 Mac 浏览器中打开该网址，登录您的 YouTube 账号并输入验证码。
5. 完成后，Ubuntu 端的 `yt-dlp` 会保存授权 Token，之后即可免 Cookie 运行。

## 3. 如何配置项目

### 第一步：放置文件
将导出的 Cookie 文件重命名为 `youtube_cookies.txt`，并放置在项目的 `backend/` 目录下：
```bash
# 目标路径
/Users/bu/Projects/Lijing/AppDev/tldw/tldw_antig/backend/youtube_cookies.txt
```

### 第二步：检查环境变量
打开 `backend/.env` 文件，确认 `YOUTUBE_COOKIES_PATH` 指向该文件：
```env
YOUTUBE_COOKIES_PATH=./youtube_cookies.txt
```

## 4. 常见问题：跨机器 IP 绑定
**重要**：YouTube 的有效会话通常与您的 **IP 地址** 绑定。
- **现象**：在 Mac 上导出的 Cookie 在 Ubuntu (尤其是境外 VPS) 上运行时仍报 429 或 "Requested format is not available"。
- **原因**：YouTube 探测到登录地 (Mac) 与请求地 (Ubuntu) 显著不同，出于安全原因使该会话受限。

### 解决方案：
1. **IP 一致性**：在 Mac 浏览器上导出 Cookie 时，请开启加速器或 Proxy，确保 Mac 的出口 IP 与 Ubuntu 服务器的 IP 属于同一区域或同一个代理。
2. **使用 OAuth2 (新)**：
   本项目现已支持 YouTube OAuth2 认证。如果您无法同步 IP，可以在配置文件中启用 OAuth2 模式。它会引导您在浏览器中输入验证码完成一次性授权。

## 5. 验证设置
配置完成后，重启后端服务。当您再次提交视频时，后台日志如果不再出现 `429` 报错，则说明鉴权已生效。
此外，可以通过以下命令快速测试：
```bash
python3 -m yt_dlp --cookies backend/youtube_cookies.txt --get-title "https://www.youtube.com/watch?v=NRDWBQWiYeg"
```

> [!IMPORTANT]
> **隐私安全警告**：
> Cookie 文件包含您的登录凭证。**严禁**将该文件提交到公共 Git 仓库。本项目已默认在 `.gitignore` 中忽略了 `*.txt`（在 backend 目录下）或特定文件名以保护您的隐私。

---
最后更新：2026-02-08
