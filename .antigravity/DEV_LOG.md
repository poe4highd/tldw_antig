# 2026-01-24 解决 YouTube 下载 403 与前端报警

## 任务背景
- 用户报告 `yt-dlp` 下载视频时出现 `HTTP Error 403: Forbidden`。
- 前端控制台出现 `postMessage` origin 匹配错误，导致 YouTube 播放器与页面通信异常。

## 实施内容
### 后端修复
- **升级组件**：将 `yt-dlp` 从 `2025.6.9` 升级至 `2025.12.8`。
- **配置优化**：在 `downloader.py` 和 `main.py` 中为 `yt-dlp` 添加了模拟浏览器的 `User-Agent`、`Referer` 及 `Accept-Language` 请求头。
- **环境适配**：移除了在本地环境下容易触发 `152 - 18` 错误的特定 `extractor_args`。

### 前端修复
- **Origin 注入**：为全站所有 YouTube 播放器组件（`react-youtube` 和原生 `iframe`）显式注入了 `origin={window.location.origin}` 参数。

## 验证结果
- 经过测试，`yt-dlp` 已恢复正常抓取和下载功能。
- 前端控制台 Origin 报错已消失。

---

# 2026-01-24 修复 Cloudflare Tunnel 连接问题

## 任务背景
用户报告 Cloudflare Tunnel 'mac-read-tube' 无活跃连接，且版本已过时。

## 实施内容
- 诊断并修复隧道连接
- 升级 cloudflared
