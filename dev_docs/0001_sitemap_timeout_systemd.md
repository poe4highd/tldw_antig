# 0001 Sitemap 超时修复 + systemd 部署配置入库

- 日期：2026-09-27
- 分支：`shad` → `main`（合并即上线，后端 `uvicorn --reload` 自动重载）

## 1. 背景与证据

### 1.1 Supabase statement timeout
- 现象：`tldw-backend` 日志每天 20~30 次 `postgrest.exceptions.APIError: canceling statement due to statement timeout (57014)`，持续至少 7 天。
- 触发请求：`GET /explore?limit=1000`，来源 IP 均为 AWS us-east-1（Vercel 每小时 revalidate `frontend/app/sitemap.ts`）。
- 实测（`videos` 表仅 623 行，已有索引 `idx_videos_is_public_created`）：

| 查询 | 耗时 |
|---|---|
| `id, created_at` × 1000 | 0.25~0.6s |
| 完整字段 × 80（首页） | 1.4s |
| 完整字段 × 1000 | **7.95s** |

- 根因：`report_data->summary` 等路径需要对每行大 JSONB 解 TOAST，与索引无关。**加索引无效**。

### 1.2 sitemap 从未生效
- `sitemap.ts` 对 `/explore` 返回值直接 `items.map(...)`，但接口返回 `{items, total, page, limit}` 对象 → 抛异常 → 被 `catch` 静默吞掉。
- 结果：sitemap 只有静态页，`/result/*` 从未被收录，后端却每小时白跑一次重查询。

### 1.3 systemd 单元文件游离在仓库外
- `~/.config/systemd/user/{tldw-backend,tldw-frontend,tldw-scheduler,cloudflared-tldw}.service`、`tldw.target` 以及 `~/bin/rt` 均不受 git 管理。
- 约束：systemd 只从固定搜索路径加载单元；单元文件不支持相对路径（仅 `%h` 等占位符）。

## 2. 方案

### 2a 后端 `backend/main.py`
- 新增 `GET /sitemap-ids`：只查 `id, created_at, hidden_from_home`（不碰 `report_data`），过滤 11 位 YouTube ID 与单视频隐藏，Supabase 1000 行上限下分页拉全，返回 `[{id, date}]`。
  - **取舍**：不按频道隐藏过滤。`channel_id` 只存在于 `report_data` JSONB 中，读取 `report_data->channel_id` 实测仍需 ~6s（解 TOAST 是瓶颈）。频道隐藏只影响首页展示，结果页仍为公开页面；影响 7 个视频。
  - 实测：7.95s → 0.15~0.36s，598 条。
  - 后续可选：给 `videos` 增加 `channel_id` 普通列（需迁移 + 回填），可同时加速首页。
- `/explore` 的 `limit` 钳制为 1~100（前端首页最大 80）；隐藏频道查询抽成 `_get_hidden_channel_ids()` 复用。

### 2b 前端 `frontend/app/sitemap.ts`
- 改调 `/sitemap-ids`，正确解析数组。
- `API_BASE` 默认值改为 `https://api.read-tube.com`（与 `utils/api.ts` 一致）。

### 3 部署配置入库 `deploy/`
```
deploy/
├── systemd/          # 单元文件，唯一绝对锚点 %h/projects/tldw_antig
├── bin/run-*.sh      # 启动逻辑，按脚本自身位置解析仓库路径
├── bin/rt            # 原 ~/bin/rt
└── install.sh        # 幂等：软链接单元与 rt 到 ~/.config/systemd/user、~/bin，然后 daemon-reload
```
- `.env` 仍由单元文件 `EnvironmentFile=` 加载，不在 bash 中 `source`（systemd 与 bash 对引号、`$` 的解析不同，避免密钥被静默改写）。
- 软链接必须指向**主仓库**（生产），不指向 worktree。
- 修改 `run-*.sh` → 合并后 restart 对应服务即可；修改 `deploy/systemd/*` → 需 `systemctl --user daemon-reload` 后再 restart。
- `~/.cloudflared/config.yml` 不入库（同目录有隧道凭证）。

## 3. 上线步骤
1. `shad` 上改代码 + 更新 `.dev-audit/`，venv 导入检查、`tsc --noEmit`，提交。
2. 主仓库 `git merge --ff-only shad`（后端自动重载）。
3. 备份原单元与 `~/bin/rt` 至 `~/.config/systemd/user/backup-20260927/`，执行 `deploy/install.sh`。
4. 确认 scheduler 空闲后逐个重启 `tldw-backend`、`tldw-scheduler`、`tldw-frontend`。
5. `git push origin main` → Vercel 自动部署前端。
6. 验证：服务状态、`/sitemap-ids`、`sitemap.xml` 含 `/result/`、后续日志无 `statement timeout`。

## 4. 回滚
- 代码：`git revert` 对应提交并推送。
- systemd：删除软链接，从 `backup-20260927/` 拷回原文件，`daemon-reload` 后重启。
