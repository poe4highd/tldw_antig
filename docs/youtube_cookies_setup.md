# YouTube Cookie 设置指南

为了解决使用 `yt-dlp` 下载 YouTube 视频或提取元数据时出现的 `HTTP Error 429: Too Many Requests`（频率限制）或 `403 Forbidden` 错误，本项目支持通过 Cookie 文件进行鉴权。

## 1. 为什么需要 Cookie？
YouTube 对匿名请求（尤其是来自云服务器或数据中心的 IP）有严格的限流措施。使用有效登录状态的 Cookie 可以：
- 绕过 429 频率限制。
- 允许访问受地理限制、年龄限制的视频。
- 模拟真实用户行为，提高下载成功率。

## 2. 如何获取 Cookie 文件

### 推荐方法：使用 yt-dlp 自身导出 (跨机器最稳)
如果您发现浏览器插件导出的 Cookie 在 Ubuntu 上失效，请在您的 **Mac** 上使用项目自带的 `yt-dlp` 进行导出：
1. 在 Mac 终端进入项目目录，并进入 `venv` 环境：
   ```bash
   cd /Users/bu/Projects/Lijing/AppDev/tldw/tldw_antig/backend
   source venv/bin/activate
   ```
2. 运行导出指令（使用 `--cookies` 参数来保存从浏览器提取的内容）：
   ```bash
   # 获取视频信息的同时，会将 Cookie 自动同步到 youtube_cookies.txt
   # 如果使用 Edge, 改为 --cookies-from-browser edge
   yt-dlp --cookies-from-browser chrome --cookies youtube_cookies.txt --get-title "https://www.youtube.com/watch?v=NRDWBQWiYeg"
   ```
3. 将生成的 `youtube_cookies.txt` 文件拷贝到 Ubuntu 机器的 `backend/` 目录下。

## 3. 如何配置项目

### 第一步：放置文件
将上述生成的 Cookie 文件放置在项目的 `backend/` 目录下：
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
**重要**：YouTube 会检测请求者的 IP。
- **现象**：即使 Cookie 正确，Ubuntu (VPS) 仍可能因为与 Mac (导出地) IP 差异过大而被拦截。
- **建议**：
  1. 确保服务器 (Ubuntu) 所使用的加速器/Proxy 的出口地区与您 Mac 的上网地区一致。
  2. 尽量使用 `yt-dlp --cookies-from-browser` 命令导出的文件，它包含更精确的指纹信息。

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
最后更新：2026-02-08
