# YouTube Cookie 设置指南

为了解决使用 `yt-dlp` 下载 YouTube 视频或提取元数据时出现的 `HTTP Error 429: Too Many Requests`（频率限制）或 `403 Forbidden` 错误，本项目支持通过 Cookie 文件进行鉴权。

## 1. 为什么需要 Cookie？
YouTube 对匿名请求（尤其是来自云服务器或数据中心的 IP）有严格的限流措施。使用有效登录状态的 Cookie 可以：
- 绕过 429 频率限制。
- 允许访问受地理限制、年龄限制的视频。
- 模拟真实用户行为，提高下载成功率。

## 2. 如何获取 Cookie 文件

### 推荐方法 A：使用 yt-dlp 自身导出 (跨机器最稳)
如果您发现浏览器插件导出的 Cookie 在 Ubuntu 上失效，请在您的 **Mac** 上使用项目自带的 `yt-dlp` 进行导出：
1. 在 Mac 终端进入项目目录，并进入 `venv` 环境：
   ```bash
   cd backend
   source venv/bin/activate
   ```
2. 运行导出指令（使用 `--cookies` 参数来保存从浏览器提取的内容）：
   ```bash
   # 获取视频信息的同时，会将 Cookie 自动同步到 youtube_cookies.txt
   # 如果使用 Edge, 改为 --cookies-from-browser edge
   yt-dlp --cookies-from-browser chrome --cookies youtube_cookies.txt --get-title "https://www.youtube.com/watch?v=NRDWBQWiYeg"
   ```

### 推荐方法 B：使用浏览器插件手动导出 (简单快捷)
如果您无法在 Mac 上运行指令，可以使用浏览器插件：
1. 安装插件：推荐使用 [Get cookies.txt LOCALLY](https://chrome.google.com/webstore/detail/get-cookiestxt-locally/ccmclokmbihohadnopkpbinddahdmilb) (Chrome/Edge)。
2. 导出 Cookie：
   - 打开 [YouTube](https://www.youtube.com) 并确保已登录。
   - 点击插件图标，点击 "Export" 或 "Download" 按钮将 Cookie 保存为 `youtube_cookies.txt`。
   - **注意**：导出格式必须是 Netscape 格式（每行以 `.youtube.com` 开头）。
3. 将生成的 `youtube_cookies.txt` 文件拷贝到 Ubuntu 机器的 `backend/` 目录下。

### 备选方法：使用浏览器插件手动导出 (Netscape 格式)
如果由于权限或浏览器配置原因无法使用 `yt-dlp` 直接提取，可以手动导出：
1. 在浏览器（Chrome/Edge）中安装插件：**Get cookies.txt LOCALLY** 或 **EditThisCookie**。
2. 登录 YouTube。
3. 点击插件图标，选择 **Export as Netscape**。
4. 将导出的文本保存为 `youtube_cookies.txt`。

## 3. 如何配置项目

### 第一步：放置文件
将上述生成的 Cookie 文件放置在项目的 `backend/` 目录下：
```bash
# 目标路径
backend/youtube_cookies.txt
```

### 第二步：检查环境变量
打开 `backend/.env` 文件，确认 `YOUTUBE_COOKIES_PATH` 指向该文件：
```env
YOUTUBE_COOKIES_PATH=./youtube_cookies.txt
```

## 4. 常见问题：跨机器 IP 绑定
**重要**：YouTube 会检测请求者的 IP。
- **现象**：即使 Cookie 正确，Ubuntu (VPS) 仍可能因为与 Mac (导出地) IP 差异过大而被拦截。
- **建议**：
  1. 确保服务器 (Ubuntu) 所使用的加速器/Proxy 的出口地区与您 Mac 的上网地区一致。
  2. 尽量使用 `yt-dlp --cookies-from-browser` 命令导出的文件，它包含更精确的指纹信息。

## 5. 维护与更新频率

YouTube Cookie 的失效并非完全由时间决定，而是由“账号活动”和“风控检测”共同决定的。

### 5.1 理论有效期
在 Cookie 文件中，到期时间（Unix 时间戳）通常指向 1 年甚至更久以后。只要您不主动在浏览器中点击“退出登录”，Cookie 理论上是长期静态有效的。

### 5.2 什么时候需要更新？
出现以下情况时，说明原有 Cookie 已逻辑失效，需按上述步骤重新覆盖：
- **触发机器人校验**：当后台日志出现 `Sign in to confirm you’re not a bot` 报错时。这通常是因为抓取频率过高或服务器 IP 被标记。
- **IP 跨度过大**：如果您更换了出口节点（例如从香港代理换到了美国代理），YouTube 可能会为了安全强制该会话失效。
- **密码更改**：如果您在浏览器端修改了 YouTube/Google 账号密码。

### 5.3 建议策略：按需更新
对于本项目目前的低频自动检查（1小时/5个视频），**无需定期更新**。
- **推荐做法**：仅在发现视频更新停滞、或后台持续报错时，再花 1 分钟重新导出并覆盖 `youtube_cookies.txt`。
- **小技巧**：导出的浏览器账号平时可以偶尔正常观看一些视频，让 YouTube 算法认为这是一个真实的活跃用户，从而延长 Cookie 的抗风控寿命。

## 5. 验证设置
配置完成后，重启后端服务。当您再次提交视频时，后台日志如果不再出现 `429` 报错，则说明鉴权已生效。
此外，可以通过以下命令快速测试：
```bash
python3 -m yt_dlp --cookies backend/youtube_cookies.txt --get-title "https://www.youtube.com/watch?v=NRDWBQWiYeg"
```

> [!CAUTION]
> **OAuth2 已停用**：YouTube 已全面封禁了 OAuth2 登录方式，请勿再尝试此方法。

> [!IMPORTANT]
> **隐私安全警告**：
> Cookie 文件包含您的登录凭证。**严禁**将该文件提交到公共 Git 仓库。本项目已默认在 `.gitignore` 中忽略了 `*.txt`（在 backend 目录下）或特定文件名以保护您的隐私。

## 6. 技术经验：攻克 n-challenge (反爬突破)

在调试过程中，我们发现即使提供了完整的 Cookie，YouTube 仍可能屏蔽音视频流。以下是核心经验总结：

### 核心症结：n-challenge 挑战
YouTube 使用一种名为 `n-challenge` 的 JavaScript 脚本来检测客户端合法性。如果探测失败，它会返回 `Requested format is not available`（仅开放图片资源）。

### 解决方案项：
1. **必须环境**：服务器必须安装 **Node.js**。这是 `yt-dlp` 解密 JS 挑战的最可靠运行时。
2. **启用远程组件**：配置 `remote_components=['ejs:github']`。这允许 `yt-dlp` 从官方维护的远程仓库动态下载最新的解码算法包（EJS），极大增强了应对 YouTube 算法频繁变更的能力。
3. **User-Agent 对齐**：移除后端硬编码的 User-Agent。让 `yt-dlp` 自动尝试与 Cookie 中的指纹对齐，避免因 UA 冲突导致的会话失效。

这些配置已在 backend 核心代码中默认集成，您只需确保环境中安装了 Node.js 即可。

---
最后更新：2026-02-15
