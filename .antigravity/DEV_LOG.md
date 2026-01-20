# 2026-01-20 登录重定向隔离问题修复

## 任务背景
解决本地通过 Google Auth 登录后会错误跳转到生产域名 `read-tube.com` 的问题。确认是由于用户使用的访问方式（如 LAN IP）未包含在 Supabase 重定向白名单中。

## 实施内容
1. **注入调试工具**：在 `LoginPage` 临时加入 `confirm` 和详细日志，精确捕捉跳转参数。
2. **环境感知优化**：重构 `frontend/utils/api.ts` 中的 `getSiteUrl`，自动处理尾部斜杠，提高与 Supabase 的匹配兼容性。
3. **白名单指引**：协助用户定位 Supabase URL Configuration 页面，确定必须添加的 `localhost` 及其变体地址。
4. **清理交付**：问题解决后，移除所有调试代码与弹窗。

## 验证结论
用户确认通过 `localhost` 访问且配置正确白名单后，重定向跳转逻辑恢复正常，实现了完美的环境隔离。

---

# 2026-01-20 统一 API 地址获取逻辑与环境隔离修复

## 任务背景
修复生产环境用户访问部分页面（如项目历史、结果详情）时触发“本地网络访问”弹窗的问题。根源在于代码中存在硬编码的 `localhost:8000` 作为 Fallback 逻辑。

## 实施内容
1.  **统一工具函数集成**：将所有页面的 API 请求逻辑从硬编码或手动推导修改为统一调用 `@/utils/api` 中的 `getApiBase()`。
2.  **严格环境隔离**：
    *   在 `getApiBase` 中强化逻辑：只有 `hostname` 为 `localhost` 或类本地 IP 时才返回本地地址。
    *   在生产域名（`read-tube.com`）下强制返回生产 API 地址。
3.  **受影响页面重构**：
    *   `frontend/app/project-history/page.tsx`
    *   `frontend/app/result/[id]/page.tsx`
    *   `frontend/app/tasks/page.tsx` (化简了复杂的推导逻辑)
    *   `frontend/app/dev-result/[id]/page.tsx`
    *   `frontend/app/dev-compare/[id]/page.tsx`

## 验证结果
- **隔离性**：本地开发环境依然正确连接本地后端，生产环境不再尝试连接本地网络。
- **稳定性**：各页面数据加载恢复正常，无跨域或地址错误。

## 关联文件
- `frontend/app/project-history/page.tsx`
- `frontend/app/result/[id]/page.tsx`
- `frontend/app/tasks/page.tsx`
- `frontend/app/dev-result/[id]/page.tsx`
- `frontend/app/dev-compare/[id]/page.tsx`

---

# 2026-01-20 产品预览图设计与“我的书架”品牌同步

## 任务背景
统一产品核心术语，将“见地”更名为“我的书架”，并配套高质感的产品预览图以提升第一眼视觉冲击力。

## 实施内容
1. **视觉资产生成**：使用 AI 生成 Hero Mockup 并在营销页集成，替换占位符。
2. **术语与图标同步**：
   - 侧边栏图标更新：`LayoutGrid` → `Library`。
   - 系统元数据更新：`description` 强化“音视频书架”概念。
   - 营销页文案微调：强调构建“个人数字书架”。

## 关联文件
- `frontend/components/Sidebar.tsx`
- `frontend/app/layout.tsx`
- `frontend/app/page.tsx`
- `frontend/public/images/hero_mockup.png`

---

# 2026-01-20 路径规范化与模型存储优化

## 任务背景
解决中间文件散落在系统目录（/var/folders）以及大模型文件占用系统缓存（~/.cache）的问题，确保项目自包含。

## 实施内容
1. **环境锁定**：在 `transcriber.py` 中设置 `HF_HOME` 和 `MODELSCOPE_CACHE` 指向 `backend/models`。
2. **临时目录同步**：创建 `backend/data/temp` 并修改 `hallucination_detector.py` 的音频切片生成逻辑。
3. **模型迁移与清理**：
   - 迁移核心模型：`large-v3-turbo`, `small-mlx`, `SenseVoice`。
   - 清理冗余模型：删除 `medium-mlx`, `large-v3-mlx`, `base-mlx` 及过期 2 个月的旧模型。

## 关联文件
- `backend/transcriber.py`
- `backend/hallucination_detector.py`
- `backend/.env`

---

# 2026-01-20 处理转录幻觉：双模型校验方案

## 问题分析
识别到转录模型在低信号区会出现“单字循环”幻觉，以及“罗布/萝卜”这类字义断层。

## 解决方案
1.  **实现 `hallucination_detector.py`**：使用正则匹配循环模式（如 `(.{1,4})\1{2,}`）。
2.  **双模型工作流**：检测到幻觉后，动态切片音频，使用 `whisper base` 模型重转录作为备选。
3.  **提示词升级**：新增规则 5 (幻觉处理) 和 规则 6 (删除例外)，赋予 LLM 处理 `[HALLUCINATION]` 和 `[ALT:]` 标记的能力。

## 验证结果
视频 `0_zgry0AGqU` 重处理成功，“罗布”精确修正为“萝卜”，乱码循环被剔除，最终文本不含任何 AI 标记。

## 关联文件
- [processor.py](file:///Users/bu/Projects/Lijing/AppDev/tldw/tldw_antig/backend/processor.py)
- [hallucination_detector.py](file:///Users/bu/Projects/Lijing/AppDev/tldw/tldw_antig/backend/hallucination_detector.py)
- [reprocess_from_cache.py](file:///Users/bu/Projects/Lijing/AppDev/tldw/tldw_antig/backend/tests/reprocess_from_cache.py)

---

# 2026-01-20 LLM校正提示词优化（字数守恒）

## 问题
LLM校正过于宽泛，大段删减原始转录文字。由于转录模型已大幅改进，校正应尽量保持原始字数。

## 修改 `backend/processor.py` PROMPT
1. **新增核心原则**：输出字数必须与输入高度接近（误差不超过5%）
2. **替换激进指令**：
   - ~~"必须大胆修正听力错误"~~ → "只替换明显的同音错别字，1:1字数对应"
   - ~~"禁止出现无意义词组...还原为通顺的常用词"~~ → "禁止合并简化：不要将多个词合并为一个词"
3. **移除合并逻辑**：
   - ~~"合并与分段：将碎片化的文本合并为通顺的句子"~~ → "分段：保持所有原始内容，只是重新组织段落结构"

---


## 1. 问题回顾
- 延迟加载方案无法完全解决 `Segmentation fault: 11`
- MLX 和 Torch 在同一进程中初始化时会发生 Metal GPU 资源冲突
- OpenMP 符号污染导致运行时冲突

## 2. 终极方案:进程隔离
**核心思路**:将转录任务从 FastAPI 主进程中完全分离,使用独立的 Python 子进程执行。

**实施内容**:
1. **创建 `backend/worker.py`**:
   - 独立的转录任务执行脚本
   - 接收命令行参数(task_id, mode, file, title 等)
   - 在独立进程空间中加载 MLX/Torch,彻底避免冲突
   - 通过文件系统与主进程通信(状态文件、结果文件)

2. **重构 `backend/main.py`**:
   - 移除直接调用 `transcribe_audio`
   - 使用 `subprocess.Popen` 启动 worker.py
   - 实时转发 worker 日志到主进程
   - 读取 worker 生成的结果并补充元数据

3. **优势**:
   - **彻底隔离**: 每个转录任务在独立进程中,崩溃不影响主服务
   - **并发安全**: 可以同时运行多个转录任务(不同模型)
   - **资源清理**: 进程结束自动释放所有 GPU 资源
   - **易于调试**: 可以单独测试 worker.py

## 3. 验证
建议用户重启 `./dev.sh` 并提交转录任务测试。

---
# 2026-01-20 后端段错误深度清理 (Final Fix)
## 1. 现象
- 即使设置了 `KMP_DUPLICATE_LIB_OK` 和 `OMP_NUM_THREADS=1`，后端在调用 `mlx-whisper` 时仍偶发 `Segmentation fault: 11`。
- 伴随 `OMP: Info #276` 警告，提示 OpenMP 运行时冲突。

## 2. 深度诊断
- **资源竞争**：`torch` (MPS) 和 `mlx` (Metal) 在同一进程内过早初始化且持有 GPU 句柄，导致内存地址空间冲突。
- **符号冲突**：`sherpa-onnx`、`torch` 和 `faster-whisper` (CTranslate2) 各自携带不同的 OpenMP/MKL 链接，全局加载导致符号污染。

## 3. 修复方案
- **极致延迟加载**：重构 `transcriber.py`，将所有 AI 基础库 (`torch`, `mlx_whisper`, `sherpa_onnx`) 的导入移动至函数内部。确保在调用 `mlx` 时，如果不需要 `torch` 则完全不加载它。
- **环境隔离优化**：
    - `dev.sh` 增加 `export KMP_BLOCKTIME=0` 以减少 OpenMP 线程等待。
    - 强化了 `mlx-whisper` 调用前的 `Memory Flush` 逻辑（仅在 `torch` 已加载时执行）。

## 4. 验证
- 建议用户重启 `./dev.sh` 后再次提交任务。

---
## 1. 现象
- 前端访问 `https://api.read-tube.com` 报错 `CORS policy: No 'Access-Control-Allow-Origin' header is present`。
- 实际请求返回 `HTTP 530`，暗示 Cloudflare 隧道离线。

## 2. 诊断与修复
- 经检查，本地 `mac-read-tube` 隧道处于断开状态。
- 手动拉起隧道：`cloudflared tunnel run mac-read-tube`。
- 验证：`curl -I` 测试 OPTIONS 请求，成功返回 200 及 `access-control-allow-origin: https://read-tube.com`。

## 3. 改进
- 优化了 `dev.sh` 的隧道检测提示，提供了 `nohup` 运行建议。

---
# 2026-01-19 开发日志 (双重崩溃深度修复)

## 任务背景
后端在并发请求和处理 MLX-Whisper 转录时连续遭遇两次崩溃：`Abort trap: 6` 与 `Segmentation fault: 11`。

## 诊断与修复
1. **OpenMP 冲突 (Abort trap: 6)**
   - 原因：torch, numpy, intel-openmp 在 macOS 下重复加载 libomp.dylib。
   - 修复：设置 `export KMP_DUPLICATE_LIB_OK=TRUE`。

2. **MLX 线程/内存冲突 (Segmentation fault: 11)**
   - 原因：MLX-Whisper 在多核高负载及多模型共享显存时触发段错误。
   - 修复：
     - 在 `dev.sh` 中强制限制 `export OMP_NUM_THREADS=1` 处理线程安全。
     - 在 `transcriber.py` 中，于 MLX 转录开始前强制执行 `Memory Flush`，清理 Torch 显存。

## 验证结论
服务已恢复稳定，能够同时挂载前端并处理 API。
