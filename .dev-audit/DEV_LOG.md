# 2026-09-27 开发日志

### [Bugfix/Ops] yt-dlp 403 导致下载停摆 6 周 + 失败告警

- **需求**：用户发现首页最新视频停在 Aug 17，怀疑频道自动追踪停止。关键错误：`ERROR: unable to download video data: HTTP Error 403: Forbidden`（自 08-18 起 104 次）。详见 `dev_docs/0002_ytdlp_403_alert.md`。

- **受影响文件（计划）**：`backend/downloader.py`、`backend/scheduler.py`、`backend/alerting.py`（新）、`backend/scripts/requeue_failed.py`（新）、`backend/requirements.txt`、`backend/.env.example`、`deploy/**`、`docs/development_guide.md`

- **计划**：升级 yt-dlp → downloader 配置 node JS 运行时 → scheduler 卡住判定改为最后活动时间 + 连续失败邮件告警 → 每周自动升级 yt-dlp 的 timer → 补跑最近 40 个失败任务（用户决定不补 8 月的）。

- **回顾**：
  1. 诊断：追踪正常（每天约 24 轮），8/17 后 108 个入队视频 106 个 failed，retry_count 全部耗尽（=3）。
  2. 隔离 venv 复现：旧版 2026.02.21 完整下载 403，新版 2026.08.19 成功；`--test`（仅 10KiB）两者都成功，是个误导点。
  3. 生产 venv 已升级 yt-dlp 2026.08.19 + yt-dlp-ejs 0.8.0（非 git 管理的环境变更）。
  4. `downloader.py` 新增 `_find_js_runtimes()`；以 systemd 同等精简 PATH 端到端测试 `download_audio('FUxw9s2VAxk')` 成功（音频 15MB + 字幕 + 缩略图）。
  5. 发现并修复 `check_stuck_tasks` 以 `created_at` 判卡住的 bug（旧任务重新入队 30 分钟内即被打回 failed），改为 max(created_at, _status.json mtime)，queued 阈值 24h→72h；修复 `logger.info(file=sys.stderr)` TypeError。
  6. 新增 `alerting.py` 与连续失败告警（阈值 5，恢复通知）；mock 测试：6 次失败只告警 1 次、成功后发 1 次恢复；SMTP 未配置时返回 False 不抛异常。
  7. 新增 `tldw-ytdlp-upgrade.{service,timer}` 与 `upgrade-ytdlp.sh`；`install.sh` 自动 enable `*.timer`。
  8. 新增 `scripts/requeue_failed.py`，dry-run 确认最近 40 个为 9/11~9/28。
  9. 自愈：`alerting.py` 命令行测试未加载 `.env` 导致用户测试无输出，`__main__` 中补 `load_dotenv`；清理用户 `.env` 中误粘贴的占位行（已备份）；测试邮件发送成功，systemd `EnvironmentFile` 解析校验通过（pw_len=16）。

- **经验**：
  - "追踪停止"是表象，真实故障在下游；先按环节（追踪→入队→下载→处理）逐段找证据。
  - yt-dlp 这类对抗性依赖，不升级比升级危险得多：不锁版本 + 定期自动升级 + 失败告警。
  - 超时/卡住判定不能基于创建时间，必须基于最后活动时间，否则重试机制形同虚设。
  - 静默失败 6 周比 403 本身更严重：任何后台流水线都要有失败告警。

---

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
