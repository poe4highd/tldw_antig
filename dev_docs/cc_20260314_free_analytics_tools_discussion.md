# 免费网站分析工具调研讨论

> 来源：Claude Code 调研 | 日期：2026-03-14
> 目标：为 read-tube.com 选择合适的免费访问数据收集与分析方案

---

## 一、核心概念：两类工具各管什么？

| 维度 | 流量分析工具（GA4 等） | 搜索引擎工具（GSC） |
|------|----------------------|-------------------|
| **数据类型** | Post-click（用户进站后的行为） | Pre-click（用户搜索时看到什么） |
| **核心问题** | "用户来了之后做了什么？" | "用户是怎么发现我的？" |
| **典型指标** | PV、UV、停留时间、跳出率、转化 | 搜索词、排名、点击率、索引状态 |
| **数据来源** | JS 脚本埋点 | Google 爬虫 + 搜索引擎日志 |

**结论**：两类工具互补，不是二选一的关系。

---

## 二、Google 官方免费工具

### 2.1 Google Analytics 4 (GA4)

**定位**：全能型流量分析，行业标准

| 项目 | 详情 |
|------|------|
| 价格 | 完全免费（企业版 GA360 才收费） |
| 数据采集 | JS 脚本（gtag.js），自动追踪页面浏览 |
| 核心功能 | 实时报告、用户画像、流量来源、事件追踪、转化漏斗 |
| 隐私 | 需要 Cookie 同意横幅（GDPR 地区） |
| 集成方式 | `@next/third-parties/google` 一行代码 |

**优点**：
- 免费且功能最全面，市场占有率最高
- 与 Google Ads、GSC 深度集成
- 丰富的受众细分和归因分析

**缺点**：
- 界面复杂，学习曲线陡峭
- 数据归 Google 所有，隐私顾虑
- 需要 Cookie 同意机制
- 数据采样问题（高流量时）

**适合 read-tube.com？** 适合。作为基础层必装，因为后续做 Google Ads 推广时必须有 GA4。

---

### 2.2 Google Search Console (GSC)

**定位**：SEO 专用工具，监控 Google 搜索表现

| 项目 | 详情 |
|------|------|
| 价格 | 完全免费 |
| 数据采集 | 无需 JS 脚本，Google 自动收集 |
| 核心功能 | 搜索词排名、点击率、索引覆盖、Core Web Vitals、移动可用性 |
| 验证方式 | HTML meta tag / DNS TXT 记录 / HTML 文件 |
| 集成方式 | Next.js `metadata.verification.google` |

**核心价值**（GA4 做不到的）：
1. **搜索查询报告** — 用户搜了什么词找到你的？排名第几？点击率多少？
2. **索引覆盖** — 哪些页面被 Google 收录了？哪些有问题？
3. **Sitemap 提交** — 主动告诉 Google 你有哪些页面（read-tube.com 已有动态 sitemap.ts）
4. **Core Web Vitals** — 真实用户的 LCP、CLS、INP 数据
5. **手动操作警告** — 如果被 Google 惩罚会收到通知
6. **链接报告** — 谁在链接你的网站？内部链接结构如何？

**适合 read-tube.com？** 必装。零代码成本，纯 SEO 收益。尤其是 read-tube 已有 sitemap 和 SSR 结果页，GSC 能直接发挥作用。

---

### 2.3 GA4 + GSC 联合使用

两者可以在 GA4 后台直接关联（Admin → Product Links → Search Console Links），关联后可以在 GA4 中直接看到搜索词数据，形成完整的用户旅程：

```
搜索词 → 排名/点击率 (GSC) → 着陆页行为 → 转化 (GA4)
```

---

## 三、隐私友好型替代方案

如果不想把数据交给 Google，以下是值得考虑的免费/开源方案：

### 3.1 Umami（推荐关注）

| 项目 | 详情 |
|------|------|
| 价格 | 自托管完全免费（MIT 协议）；云版免费 100K events/月 |
| 脚本大小 | ~2KB（GA4 约 45KB） |
| Cookie | 无 Cookie，无需同意横幅 |
| 隐私合规 | GDPR/CCPA 开箱即用 |
| 自托管需求 | Node 18+ / PostgreSQL 12+（$5/月 VPS 即可） |
| 特色 | 可部署在 Vercel + Supabase 上（与 read-tube 技术栈完全一致！） |

**为什么特别推荐？**
- read-tube 已经用了 Vercel + Supabase，Umami 可以复用同一套基础设施
- 有[详细教程](https://hackernoon.com/your-complete-guide-to-self-hosting-umami-analytics-with-vercel-and-supabase)教你用 Vercel + Supabase 部署
- 界面简洁直观，一页看完所有数据
- 支持自定义事件追踪

**局限**：
- 没有用户画像、归因分析等高级功能
- 没有与 Google Ads 的集成
- 自托管需要维护

---

### 3.2 Rybbit（2025 年新星）

| 项目 | 详情 |
|------|------|
| 价格 | 自托管免费（AGPL-3）；云版免费 3K PV/月 |
| 特色功能 | Session Replay（录屏回放）、Core Web Vitals、用户流分析 |
| GitHub Stars | 10,000+（一年内） |
| Cookie | 无 Cookie |

**亮点**：免费开源方案中少见地提供 Session Replay（类似 Hotjar 的录屏回放），可以看到真实用户怎么操作你的网站。

**局限**：
- 项目较新（2025年1月创立），稳定性待验证
- 云版免费额度很小（3K PV/月）
- AGPL 协议对商业使用有限制

---

### 3.3 Microsoft Clarity（推荐关注）

| 项目 | 详情 |
|------|------|
| 价格 | 完全免费，无流量上限 |
| 核心功能 | 热力图（点击+滚动）、Session Replay（录屏）、AI 洞察 |
| Cookie | 需要 Cookie |
| 数据保留 | 13 个月 |
| 特色 | Copilot AI 自动生成行为洞察摘要 |

**为什么值得关注？**
- 完全免费且**无流量上限**（Umami/Rybbit 自托管也免费但需要自己的服务器）
- 热力图和录屏回放是 GA4 没有的能力
- 可以和 GA4 并行使用，互补而非替代
- 帮你理解"用户在页面上怎么操作"而非只是"看了哪些页面"

**局限**：
- 不提供传统流量指标（PV、UV、跳出率等），必须搭配 GA4 使用
- 不是开源的
- 数据归微软所有

---

### 3.4 Plausible / Matomo / PostHog 简评

| 工具 | 免费方案 | 脚本大小 | Cookie | 适合场景 |
|------|---------|---------|--------|---------|
| **Plausible** | 自托管免费（AGPL），云版 $9/月起 | ~1KB | 无 | 极简主义者，只想看基础流量 |
| **Matomo** | 自托管免费，云版 $23/月起 | ~23KB | 可选 | 需要 GA4 级别功能但想自己控制数据 |
| **PostHog** | 自托管免费；云版 1M events/月免费 | ~10KB | 可选 | 产品分析（漏斗、留存、A/B 测试） |

---

## 四、方案对比矩阵

针对 read-tube.com 当前阶段（早期增长、SEO 驱动、小团队）：

| 维度 | GA4 | GSC | Umami | Clarity | Vercel Analytics（已有） |
|------|-----|-----|-------|---------|------------------------|
| 价格 | 免费 | 免费 | 免费(自托管) | 免费 | 免费(Hobby) |
| 安装难度 | 极低 | 极低 | 中等 | 低 | 已完成 |
| 流量数据 | 全面 | 仅搜索 | 基础 | 无 | 基础 |
| 用户行为 | 中等 | 无 | 基础 | 深度(热力图+录屏) | 无 |
| SEO 洞察 | 无 | 深度 | 无 | 无 | 无 |
| 隐私友好 | 差 | N/A | 优秀 | 中等 | 好 |
| Google Ads 集成 | 原生 | 间接 | 无 | 无 | 无 |
| 维护成本 | 零 | 零 | 需要 | 零 | 零 |

---

## 五、推荐策略

### 第一阶段：立即实施（代码改动 <10 行）

1. **GA4** — 基础流量追踪，为未来 Google Ads 做准备
2. **GSC** — SEO 监控，提交 sitemap，监控索引状态

理由：两个都是 Google 官方工具，零成本，集成极简，且互相联动。对 SEO 驱动的增长策略来说是刚需。

### 第二阶段：按需扩展（可选）

3. **Microsoft Clarity** — 当需要理解"用户怎么操作页面"时加上（比如想优化首页转化率）
4. **Umami** — 如果对隐私有更高要求，或想要一个自己完全控制的备份分析系统

### 不推荐现阶段做的：

- **Matomo** — 功能强大但部署维护成本高，适合中大型团队
- **PostHog** — 产品分析工具，read-tube 当前阶段不需要漏斗/留存/A/B 测试
- **Plausible** — 太简单，GA4 免费且功能更全

---

## 六、关于隐私合规的提醒

read-tube.com 面向英文市场（主要是美国），需要注意：

- **美国**：目前无联邦级 Cookie 法规，GA4 可以直接用，但加州 CCPA 建议在隐私政策中说明
- **欧盟用户访问时**：GDPR 要求 Cookie 同意，GA4 需要同意横幅
- **简单方案**：如果欧盟流量占比很小，可以先用 GA4 不加同意横幅（大部分小网站这么做），等流量大了再加

---

## Sources

- [18 Best Google Analytics Alternatives In 2026](https://contentsquare.com/guides/google-analytics-4/alternatives/)
- [Umami vs Plausible vs Matomo for Self-Hosted Analytics](https://aaronjbecker.com/posts/umami-vs-plausible-vs-matomo-self-hosted-analytics/)
- [Google Search Console vs Google Analytics: Key Differences](https://agencyanalytics.com/blog/google-search-console-vs-google-analytics)
- [Microsoft Clarity - Free Heatmaps & Session Recordings](https://clarity.microsoft.com/)
- [Rybbit - Open Source Google Analytics Alternative](https://github.com/rybbit-io/rybbit)
- [Self-Hosting Umami with Vercel and Supabase](https://hackernoon.com/your-complete-guide-to-self-hosting-umami-analytics-with-vercel-and-supabase)
- [8 Best Open Source Analytics Tools](https://posthog.com/blog/best-open-source-analytics-tools)
- [Best Google Analytics Alternative in 2026](https://travis.media/blog/rybbit-best-google-analytics-alternative/)
- [Google Search Console vs Google Analytics: Key Differences 2026](https://www.localmighty.com/blog/google-search-console-vs-google-analytics/)



前置准备（用户需在 Google 操作）
GA4：访问 analytics.google.com → 创建账号 → 创建 GA4 属性 → 获取 Measurement ID（G- 开头） 
GSC：访问 search.google.com/search-console → 添加资产 https://read-tube.com → 选择 HTML tag 验证 → 复制验证码


<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-RWSPXR2SZJ"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());

  gtag('config', 'G-RWSPXR2SZJ');
</script>