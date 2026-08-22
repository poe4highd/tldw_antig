# 2026-08-22 开发日志

### [UX] 首页强化 YouTube 提交入口

- **需求**：用户咨询 `read-tube.com` 是否为项目关联域名，并指出首页看不出如何提交 YouTube URL 获取字幕，希望在不占用额外空间的前提下改进主打功能入口的可见性。

- **受影响文件（计划）**：
  - `frontend/app/page.tsx`

- **计划**：
  1. 确认 `read-tube.com` 为生产域名——README、`layout.tsx` SEO metadata、`sitemap.ts`、`robots.txt`、`utils/api.ts` API 路由判断、`docs/cloudflare_tunnel_ops.md` Cloudflare Tunnel 部署文档均已关联该域名。
  2. 探索首页发现：右上角常驻按钮是唯一与"提交"相关的元素，但未登录态无图标提示，登录态直接变成纯文字 "Profile" 且跳转 `/dashboard`，完全无法识别主打功能是什么；真正的粘贴框藏在需登录的 `/tasks` 页面，首页无直接链接。
  3. 征询用户改进力度后，选择"仅强化常驻按钮"的最小改动方案：图标 `User`→`Youtube`，登录态文案改为"提交新的任务"并直跳 `/tasks`，不新增任何组件、不占用额外空间、不改动登录墙逻辑。

- **回顾**：
  1. `frontend/app/page.tsx` 右上角常驻按钮：图标由 `User` 改为组件内已导入但未使用的 `Youtube`；未登录态保留 `login.loginToSubmit` 文案与 `/login` 跳转不变；登录态文案由硬编码 `"Profile"` 改为 `t("tasks.submitNew")`，href 由 `/dashboard` 改为 `/tasks`，均复用既有翻译 key，未新增翻译内容。
  2. 清理因替换图标而变为未使用的 `User` import。
  3. 确认 `/tasks`、`/dashboard` 均挂载 `Sidebar` 组件（含 `nav.bookshelf → /dashboard`），改动不会造成用户丢失访问 dashboard 的路径。
  4. 验证：`npx tsc --noEmit` 全仓通过，无 `page.tsx` 相关报错。

- **经验**：
  - 登录态按钮不能想当然沿用登录前的 CTA 文案；未登录/已登录两种状态需要分别设计各自最有意义的下一步动作（未登录→引导登录，已登录→直达核心功能），否则登录后反而丢失了原本的操作线索。
  - `/login` 页面当前硬编码跳转 `/dashboard`（Google OAuth、邮箱魔法链接、Guest Entry 皆如此），`/tasks` 页面写的 `router.push("/login?redirect=/tasks")` 中的 `?redirect=` 参数实际未被登录页读取——这是一个既有的、独立于本次改动的历史遗留问题，已记录但未在本次任务中修复。

---
