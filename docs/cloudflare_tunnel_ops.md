# Cloudflare Tunnel 运维操作指南

本指南详细记录了使用 `cloudflared` CLI 管理本地隧道的常用命令与配置规范。适用于修复连接问题或迁移开发环境。

## 1. 核心概念
*   **Tunnel**: 建立在 Cloudflare 边缘网络与你本地机器之间的安全加密通道。
*   **Credentials**: 文件通常位于 `~/.cloudflared/<UUID>.json`，是启动隧道的密钥，**必须保密且不能丢失**。
*   **Config (`config.yml`)**: 定义隧道如何将外部流量（Ingress）转发到本地端口（如 localhost:8000）。

## 2. 常用操作命令

### 2.1 状态检查
```bash
# 查看所有隧道列表
cloudflared tunnel list

# 查看特定隧道的详细信息
cloudflared tunnel info <NAME_OR_UUID>

# 检查本地是否有运行中的隧道进程
pgrep -fl cloudflared
```

### 2.2 启动隧道
```bash
# 启动指定隧道（需确保本地已有 credentials 和 config.yml）
cloudflared tunnel run <NAME>

# 示例
cloudflared tunnel run mac-read-tube
```

## 3. 重建/新建隧道流程 (完整)

如果遇到“凭证丢失”或需要迁移到新机器，请按以下步骤操作：

### 步骤一：登录认证
```bash
cloudflared tunnel login
```
*   这会打开浏览器进行 SSO 登录，并在 `~/.cloudflared/cert.pem` 生成用户证书（用于创建/删除隧道，**不是**运行隧道的凭证）。

### 步骤二：创建隧道
```bash
cloudflared tunnel create <NEW_NAME>
# 示例：cloudflared tunnel create mac-read-tube
```
*   **关键产物**: 此命令会自动生成 `~/.cloudflared/<UUID>.json` 凭证文件。

### 步骤三：配置 Ingress (`config.yml`)
在 `~/.cloudflared/config.yml` 中写入以下内容（注意替换你的 UUID）：

```yaml
tunnel: <UUID>
credentials-file: /Users/bu/.cloudflared/<UUID>.json

ingress:
  # 将 api.read-tube.com 的流量转发到本地后端
  - hostname: api.read-tube.com
    service: http://localhost:8000
    
  # 兜底规则（必须存在）
  - service: http_status:404
```

### 步骤四：绑定 DNS
将域名 CNAME 记录指向该隧道：
```bash
# 如果记录已存在(指向旧隧道)，需加 -f 强制覆盖
cloudflared tunnel route dns -f <NAME> <HOSTNAME>

# 示例
cloudflared tunnel route dns -f mac-read-tube api.read-tube.com
```

### 步骤五：启动
```bash
cloudflared tunnel run mac-read-tube
```

## 4. 故障排查

| 错误信息 | 可能原因 | 解决方案 |
| :--- | :--- | :--- |
| `tunnel credentials file not found` | 本地 `.json` 凭证文件丢失或路径错误 | 检查 `config.yml` 中的路径；或重新执行“创建隧道”流程生成新凭证 |
| `Error: code: 1003 ... record already exists` | DNS 记录已被占用（通常是旧隧道） | 使用 `tunnel route dns -f` 强制覆盖 |
| `HTTP 530` | 隧道未启动，或 DNS 未生效 | 1. 确认 `tunnel run` 正在运行<br>2. 等待几分钟 DNS 全球生效 |
| `failed to connect to origin` (Backend Log) | 后端服务未运行 | 确保 ./dev.sh 已启动且 8000 端口正常 |

## 5. 参考文件路径
*   **配置文件**: `~/.cloudflared/config.yml`
*   **凭证目录**: `~/.cloudflared/*.json`
*   **用户证书**: `~/.cloudflared/cert.pem`
