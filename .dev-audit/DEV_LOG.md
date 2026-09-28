# 2026-09-27 开发日志

### [Perf/Deploy] Sitemap 超时修复 + systemd 部署配置入库

- **需求**：
  - 后端日志每天 20~30 次 `postgrest.exceptions.APIError: {'message': 'canceling statement due to statement timeout', 'code': '57014'}`，触发请求为 Vercel sitemap 每小时调用的 `GET /explore?limit=1000`。
  - systemd 单元文件与 `~/bin/rt` 游离在仓库外，希望以仓库为唯一源头。
  - 详细计划见 `dev_docs/0001_sitemap_timeout_systemd.md`。

- **受影响文件（计划）**：`backend/main.py`、`frontend/app/sitemap.ts`、`deploy/**`（新增）、`docs/development_guide.md`、`README.md`

- **计划**：
  1. 新增 `/sitemap-ids` 轻量接口，`/explore` limit 钳制 ≤100。
  2. `sitemap.ts` 改调新接口并修复返回值解析 bug。
  3. 新建 `deploy/`（systemd 单元 + run 脚本 + rt + install.sh），更新文档。
  4. 合并 main 上线，执行 install.sh，重启服务，推送触发 Vercel 部署。

- **回顾**：
  1. 实测排除"缺索引"假设：`videos` 仅 623 行且已有 `idx_videos_is_public_created`；瓶颈是 `report_data->...` 对大 JSONB 解 TOAST（完整字段 ×1000 = 7.95s，仅 `id,created_at` = 0.3s）。
  2. `backend/main.py`：新增 `GET /sitemap-ids`（仅 `id, created_at, hidden_from_home`，1000 行分页拉全），`/explore` 的 page/limit 钳制（limit 1~100），抽出 `_get_hidden_channel_ids()`。实测 0.15~0.36s / 598 条；`/explore?limit=1000` 返回 limit=100、1.09s。
  3. 首版 `/sitemap-ids` 读取了 `report_data->channel_id` 用于频道隐藏过滤，实测仍 6.03s，改为不按频道过滤（仅影响 7 个视频，结果页本身公开）。
  4. `frontend/app/sitemap.ts`：修复把 `{items,...}` 对象当数组 `.map` 导致 sitemap 从未包含 `/result/*` 的 bug；`API_BASE` 默认值对齐 `https://api.read-tube.com`；错误改为 `console.error` 不再静默。`tsc --noEmit` 通过。
  5. 新增 `deploy/systemd/*`（`%h/projects/tldw_antig` 为唯一锚点）、`deploy/bin/run-{backend,scheduler,frontend}.sh`（按脚本位置解析仓库路径并 `exec`）、`deploy/bin/rt`、`deploy/install.sh`（校验只能从主仓库运行、备份普通文件后软链接、daemon-reload）。
  6. 更新 `docs/development_guide.md` 第 5 节与 README 部署说明。

- **经验**：
  - 表很小时查询慢，先怀疑大字段（TOAST）而非索引；PostgREST 的 `col->key` 选择仍会读取整个 JSONB。
  - `try/catch` 静默吞异常让 sitemap 空了几个月没人发现——降级可以，但必须留日志。
  - systemd 只从固定目录加载单元且不支持相对路径；"仓库为源头"的正确形态是仓库存文件 + 安装脚本生成软链接，启动逻辑下沉到脚本以减少 daemon-reload。
  - `.env` 继续交给 systemd `EnvironmentFile` 解析，避免 bash `source` 改写含 `$`/引号的值。
