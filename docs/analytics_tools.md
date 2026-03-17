# 网站分析工具指南

Read-Tube 集成了三个免费分析工具，分别负责不同维度的数据收集。

## 工具总览

| 工具 | 用途 | 仪表板入口 |
|------|------|-----------|
| **Google Search Console** | SEO：搜索词排名、索引状态、Core Web Vitals | [search.google.com/search-console](https://search.google.com/search-console) |
| **Google Analytics 4** | 流量：用户来源、页面浏览、停留时间、用户画像 | [analytics.google.com](https://analytics.google.com) |
| **Microsoft Clarity** | 行为：热力图、录屏回放、愤怒点击检测 | [clarity.microsoft.com](https://clarity.microsoft.com) |

三者的关系：
```
用户搜索 → GSC（搜了什么词、排名第几）
    ↓ 点击进站
用户浏览 → GA4（从哪来、看了什么、待了多久）
    ↓ 同时
用户操作 → Clarity（怎么滚动、点了哪里、是否困惑）
```

---

## 环境变量

在 `frontend/.env.local` 中配置（生产环境需在 Vercel Dashboard 同步设置）：

```bash
# Google Search Console — 通过 DNS/Cloudflare 验证则无需填写
NEXT_PUBLIC_GOOGLE_SITE_VERIFICATION=

# Google Analytics 4 — Measurement ID (G-开头)
NEXT_PUBLIC_GA_ID=G-XXXXXXXXXX

# Microsoft Clarity — Project ID
NEXT_PUBLIC_CLARITY_ID=xxxxxxxxxx
```

> 本地开发时留空即可，分析脚本不会加载，避免污染生产数据。

---

## Google Search Console (GSC)

### 核心功能

| 报告 | 路径 | 看什么 |
|------|------|--------|
| **效果** | 左侧 → 效果 | 搜索词、点击数、展示数、排名、点击率 |
| **页面** | 左侧 → 页面 | 哪些页面已被收录、哪些有错误 |
| **Core Web Vitals** | 左侧 → 体验 → 核心网页指标 | LCP、CLS、INP 真实用户数据 |
| **链接** | 左侧 → 链接 | 外部链接来源、内部链接结构 |
| **网址检查** | 顶部搜索栏 | 单个页面的索引状态和渲染预览 |

### 关键操作

- **提交 Sitemap**：左侧 → 站点地图 → 输入 `sitemap.xml` → 提交（已完成）
- **筛选国家**：效果报告 → "+ 新建"筛选器 → 按国家/设备/页面过滤
- **对比时间段**：日期范围旁 → "对比" → 查看 SEO 趋势
- **导出数据**：右上角导出 → Google Sheets 或 CSV

### 注意事项

- 数据延迟 2-3 天，最多 28 天才完全填充
- read-tube.com 使用 Cloudflare DNS 验证（非 HTML tag）
- Sitemap 由 `frontend/app/sitemap.ts` 动态生成，含所有公开结果页

---

## Google Analytics 4 (GA4)

### 核心功能

| 报告 | 路径 | 看什么 |
|------|------|--------|
| **实时** | 报告 → 实时 | 当前在线用户数、正在访问的页面 |
| **获客** | 报告 → 生命周期 → 获客 | 流量来源（搜索/直接/社交/推荐） |
| **互动** | 报告 → 生命周期 → 互动 | 页面浏览量、平均停留时间 |
| **页面和屏幕** | 报告 → 互动 → 页面和屏幕 | 每个页面的 PV、用户数 |
| **用户属性** | 报告 → 用户 → 用户属性 | 国家、城市、语言、年龄段 |
| **技术** | 报告 → 用户 → 技术 | 浏览器、操作系统、设备类型 |
| **探索** | 左侧 → 探索 | 自定义漏斗、路径分析 |

### 建议配置

1. **数据保留**：Admin → 数据设置 → 数据保留 → 改为 **14 个月**（默认 2 个月）
2. **关联 GSC**：Admin → Product Links → Search Console Links → 在 GA4 中查看搜索词
3. **增强型衡量**：默认开启，自动追踪页面浏览、滚动、外链点击

### 技术实现

使用 `@next/third-parties/google` 的 `GoogleAnalytics` 组件，在 `frontend/app/layout.tsx` 中条件渲染：
- 有 `NEXT_PUBLIC_GA_ID` 时加载，无则跳过
- App Router 路由变化自动追踪，无需手动埋点

---

## Microsoft Clarity

### 核心功能

| 功能 | 路径 | 看什么 |
|------|------|--------|
| **仪表板** | 首页 | 会话数、页面浏览、滚动深度 |
| **录屏回放** | 左侧 → Recordings | 真实用户操作的视频回放 |
| **热力图** | 左侧 → Heatmaps | 点击热力图 + 滚动热力图 |
| **Copilot 洞察** | 仪表板 → AI Insights | AI 自动生成的行为总结 |
| **愤怒点击** | Dashboard → Rage Clicks | 用户反复点击同一位置 |
| **死点击** | Dashboard → Dead Clicks | 点击了无反应的元素 |

### 实用技巧

- **按页面筛选录屏**：Recordings → 按 URL 筛选（如只看 `/result/*`）
- **关联 GA4**：Settings → Google Analytics integration → 在 Clarity 中按 GA4 指标筛选录屏
- **关注愤怒点击**：通常意味着 bug 或 UX 问题，优先修复
- 完全免费，无流量上限，数据保留 13 个月

### 技术实现

使用 `next/script` 注入 Clarity JS 脚本，`strategy="afterInteractive"` 不阻塞页面加载。

---

## 日常检查清单

| 频率 | 检查项 | 工具 |
|------|--------|------|
| 每天 | 实时访问量是否正常 | GA4 实时报告 |
| 每周 | 搜索词排名变化 | GSC 效果报告 |
| 每周 | 热门页面和流量趋势 | GA4 页面报告 |
| 每两周 | 热力图和愤怒点击 | Clarity Heatmaps |
| 每月 | 索引覆盖状态 | GSC 页面报告 |
| 每月 | 用户画像（国家、设备） | GA4 用户属性 |
| 按需 | 录屏回放（调查 UI 问题时） | Clarity Recordings |

---

## 关联设置（推荐都做）

1. **GA4 ↔ GSC**：GA4 Admin → Product Links → Search Console Links
2. **Clarity ↔ GA4**：Clarity Settings → Google Analytics integration

关联后效果：
- 在 GA4 中直接看到搜索词数据
- 在 Clarity 中按 GA4 指标（如流量来源）筛选录屏
