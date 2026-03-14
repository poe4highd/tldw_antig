# 分析工具配置指南：获取 Key + 数据可视化使用

> 来源：Claude Code | 日期：2026-03-14
> 涵盖：Google Search Console / Google Analytics 4 / Microsoft Clarity

---

## 一、Google Search Console (GSC) — 获取验证码

### 步骤

1. 访问 [Google Search Console](https://search.google.com/search-console)
2. 用你的 Google 账号登录
3. 点击左上角 **"添加资产"**（Add Property）
4. 选择 **"网址前缀"**（URL prefix）类型
5. 输入 `https://read-tube.com`，点击"继续"
6. 在验证方法中选择 **"HTML 标记"**（HTML tag）
7. 你会看到一段代码：
   ```html
   <meta name="google-site-verification" content="xxxxxxxxxxxxxx" />
   ```
8. 复制 `content` 引号里的值（即 `xxxxxxxxxxxxxx`）
9. 将该值填入 `.env.local`：
   ```
   NEXT_PUBLIC_GOOGLE_SITE_VERIFICATION=xxxxxxxxxxxxxx
   ```
10. 部署到 Vercel 后，回到 GSC 页面点击 **"验证"**

### 验证成功后要做的事

1. **提交 Sitemap**：
   - 左侧菜单 → "站点地图"（Sitemaps）
   - 输入 `sitemap.xml`，点击提交
   - read-tube.com 已有动态 sitemap（`/frontend/app/sitemap.ts`），会自动包含所有公开结果页

2. **等待数据**：GSC 数据通常需要 **2-3 天** 才开始出现，最多 **28 天** 才完全填充

### 数据可视化 — GSC 能看到什么？

访问 [search.google.com/search-console](https://search.google.com/search-console) → 选择你的资产

| 报告 | 位置 | 能看到什么 | 对 read-tube 的价值 |
|------|------|-----------|-------------------|
| **效果** (Performance) | 左侧菜单 → 效果 | 搜索词、点击数、展示数、平均排名、点击率 | 知道用户搜什么词找到你的 |
| **索引覆盖** (Coverage/Pages) | 左侧菜单 → 页面 | 哪些页面已被 Google 收录、哪些有错误 | 确认结果页是否都被索引了 |
| **Core Web Vitals** | 左侧菜单 → 体验 → 核心网页指标 | LCP、CLS、INP 真实用户数据 | 监控网站性能 |
| **移动可用性** | 左侧菜单 → 体验 → 移动设备易用性 | 移动端渲染问题 | 确保手机体验正常 |
| **链接** | 左侧菜单 → 链接 | 外部链接来源、内部链接结构 | 了解 SEO 外链情况 |
| **网址检查** | 顶部搜索栏输入 URL | 单个页面的索引状态和渲染预览 | 调试特定页面的 SEO 问题 |

### 实用技巧

- **筛选国家**：效果报告中点击"+ 新建"筛选器，可以按国家/设备/页面过滤
- **对比时间段**：点击日期范围旁的"对比"，可以看到 SEO 趋势
- **导出数据**：右上角导出按钮可以导出为 Google Sheets 或 CSV
- **与 GA4 关联**：在 GA4 后台 Admin → Product Links → Search Console Links，可以在 GA4 中直接看到搜索词数据

---

## 二、Google Analytics 4 (GA4) — 获取 Measurement ID

### 步骤

1. 访问 [Google Analytics](https://analytics.google.com)
2. 用你的 Google 账号登录（建议和 GSC 用同一个账号，方便关联）
3. 点击左下角齿轮 ⚙️ **"管理"**（Admin）
4. 点击 **"+ 创建"** → **"账号"**（第一次用）或 **"媒体资源"**（已有账号）
5. **账号名称**：输入 `Read-Tube`
6. **媒体资源名称**：输入 `read-tube.com`
7. **时区**：选择你的主要用户时区（建议 US Eastern 或 UTC）
8. **货币**：USD
9. 完成创建后，进入 **数据流**（Data Streams）
10. 点击 **"添加数据流"** → **"网站"**
11. 输入 `https://read-tube.com`，流名称填 `Read-Tube Web`
12. 点击创建后，你会看到 **Measurement ID**，格式为 `G-XXXXXXXXXX`
13. 复制该 ID，填入 `.env.local`：
    ```
    NEXT_PUBLIC_GA_ID=G-XXXXXXXXXX
    ```

### 重要设置

创建完数据流后，建议检查以下设置：

1. **增强型衡量** (Enhanced Measurement)：默认开启，自动追踪页面浏览、滚动、外链点击等
2. **数据保留** (Data Retention)：Admin → 数据设置 → 数据保留 → 改为 **14 个月**（默认只有 2 个月）
3. **Google Signals**：Admin → 数据设置 → 数据收集 → 开启（获取更多受众数据）

### 数据可视化 — GA4 能看到什么？

访问 [analytics.google.com](https://analytics.google.com) → 选择你的媒体资源

| 报告 | 位置 | 能看到什么 | 对 read-tube 的价值 |
|------|------|-----------|-------------------|
| **实时** (Realtime) | 报告 → 实时 | 当前在线用户数、正在访问的页面 | 即时验证追踪是否工作 |
| **用户获取** (Acquisition) | 报告 → 生命周期 → 获客 | 流量来源（搜索/直接/社交/推荐） | 知道用户从哪里来 |
| **互动** (Engagement) | 报告 → 生命周期 → 互动 | 页面浏览量、平均停留时间、事件 | 了解哪些内容最受欢迎 |
| **页面和屏幕** | 报告 → 互动 → 页面和屏幕 | 每个页面的 PV、用户数、停留时间 | 找出最热门的转录结果页 |
| **用户属性** (Demographics) | 报告 → 用户 → 用户属性 | 国家、城市、语言、年龄段 | 了解用户画像 |
| **技术** (Tech) | 报告 → 用户 → 技术 | 浏览器、操作系统、设备类型 | 优化重点设备/浏览器 |
| **探索** (Explore) | 左侧菜单 → 探索 | 自定义漏斗、路径分析、自由表格 | 深入分析用户行为路径 |

### 实用技巧

- **设置转化事件**：Admin → 事件 → 将关键事件标记为"转化"（如 `page_view` 结果页）
- **自定义仪表板**：报告 → 资源库 → 可以创建自定义报告集合
- **关联 GSC**：Admin → Product Links → Search Console Links → 关联后可在 GA4 中看到搜索词

---

## 三、Microsoft Clarity — 获取 Project ID

### 步骤

1. 访问 [Microsoft Clarity](https://clarity.microsoft.com)
2. 用微软账号登录（也支持 Google/Facebook 登录）
3. 点击 **"+ 新建项目"**（Add new project）
4. **项目名称**：输入 `Read-Tube`
5. **网站 URL**：输入 `https://read-tube.com`
6. 点击创建
7. 在设置页面 → **"安装"**（Setup）→ 你会看到一段安装代码
8. 在代码中找到类似 `clarity("set", "xxxxxx")` 或 `src` URL 末尾的 ID
9. 也可以在 Settings → Overview 中看到 **Project ID**
10. 复制该 ID，填入 `.env.local`：
    ```
    NEXT_PUBLIC_CLARITY_ID=xxxxxx
    ```

### 数据可视化 — Clarity 能看到什么？

访问 [clarity.microsoft.com](https://clarity.microsoft.com) → 选择你的项目

| 功能 | 位置 | 能看到什么 | 对 read-tube 的价值 |
|------|------|-----------|-------------------|
| **仪表板** (Dashboard) | 首页 | 会话数、页面浏览量、滚动深度、死点击 | 整体用户行为概览 |
| **录屏回放** (Recordings) | 左侧 → Recordings | 真实用户操作的视频回放 | 发现 UI/UX 问题（如按钮点不到） |
| **热力图** (Heatmaps) | 左侧 → Heatmaps | 点击热力图 + 滚动热力图 | 了解用户关注页面哪个区域 |
| **Copilot 洞察** | 仪表板 → AI Insights | AI 自动生成的行为模式总结 | 快速发现异常和趋势 |
| **愤怒点击** (Rage Clicks) | Dashboard → Rage Clicks | 用户反复点击同一位置（表示困惑/bug） | 快速定位 UI 问题 |
| **死点击** (Dead Clicks) | Dashboard → Dead Clicks | 用户点击了无反应的元素 | 发现缺少交互的地方 |

### Clarity 独有优势

- **完全免费**，无流量上限（GA4 也免费但 Clarity 的录屏和热力图是 GA4 没有的）
- **零采样**：所有会话都会被记录
- **可与 GA4 集成**：Settings → Google Analytics integration → 关联后可以在 Clarity 中按 GA4 的指标筛选录屏

### 实用技巧

- **按页面筛选录屏**：Recordings 页面顶部可以按 URL 筛选，比如只看 `/result/*` 页面的操作
- **标记有趣的会话**：看到典型行为的录屏时可以加标签，方便回顾
- **关注"愤怒点击"**：这通常意味着 bug 或 UX 问题，优先修复

---

## 四、Vercel 环境变量配置

代码部署到 Vercel 后，需要在 Vercel Dashboard 配置环境变量：

1. 访问 [vercel.com](https://vercel.com) → 选择 read-tube 项目
2. 进入 **Settings** → **Environment Variables**
3. 添加以下变量：

| Key | Value | Environment |
|-----|-------|-------------|
| `NEXT_PUBLIC_GOOGLE_SITE_VERIFICATION` | 你的 GSC 验证码 | Production |
| `NEXT_PUBLIC_GA_ID` | `G-XXXXXXXXXX` | Production |
| `NEXT_PUBLIC_CLARITY_ID` | 你的 Clarity Project ID | Production |

> **建议**：只在 Production 环境设置这些变量，Preview 和 Development 不设置，避免测试流量污染分析数据。

4. 添加完后点击 **Save**
5. 需要重新部署才能生效：Deployments → 最新的 → 点击 "..." → Redeploy

---

## 五、三工具协同使用策略

```
用户搜索 → GSC（搜了什么词、排名第几）
    ↓ 点击
用户进站 → GA4（从哪来、看了什么、待了多久）
    ↓ 同时
用户操作 → Clarity（怎么滚动、点了哪里、有没有困惑）
```

### 日常检查清单

| 频率 | 检查项 | 工具 |
|------|--------|------|
| 每天 | 实时访问量是否正常 | GA4 实时报告 |
| 每周 | 搜索词排名变化 | GSC 效果报告 |
| 每周 | 热门页面和流量趋势 | GA4 页面报告 |
| 每两周 | 热力图和愤怒点击 | Clarity Heatmaps |
| 每月 | 索引覆盖状态 | GSC 页面报告 |
| 每月 | 用户画像（国家、设备） | GA4 用户属性 |
| 按需 | 录屏回放（调查 UI 问题） | Clarity Recordings |

### 关联设置（推荐都做）

1. **GA4 ↔ GSC**：GA4 Admin → Product Links → Search Console Links
2. **Clarity ↔ GA4**：Clarity Settings → Google Analytics integration
3. 关联后可以实现：在 GA4 中看搜索词，在 Clarity 中按 GA4 指标筛选录屏
