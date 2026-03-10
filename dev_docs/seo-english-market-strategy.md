# SEO Strategy: English Market & Result Page SSR

**Date**: 2026-03-06
**Category**: Growth / SEO
**Status**: Planning → Implementation

---

## Background

A traffic audit revealed that most site visits come from Google Search, but the site has almost no SEO optimization in place. This document captures the analysis and decisions made to address this.

---

## Current SEO Audit: Critical Issues Found

### 1. Client-Side Rendering = Google Sees Empty Pages

Every page in the app uses `"use client"`, meaning content is injected by JavaScript at runtime. While Google *can* crawl JS-rendered pages, it is significantly less effective than Server-Side Rendering (SSR). The most impactful pages — `/result/[id]` — contain rich transcribed content that should be indexed but currently appear as near-empty shells to crawlers.

### 2. `lang="en"` but Chinese Description

```tsx
// frontend/app/layout.tsx (before fix)
<html lang="en">   // ← signals English site to Google
description: "AI 驱动的音视频个人书架 - 极速转录与深度阅读"  // ← Chinese text
```

Google receives conflicting signals about the target audience. This hurts ranking in both markets.

### 3. Missing SEO Infrastructure

| Element | Status |
|---------|--------|
| `<meta description>` (global) | ✅ Exists (but Chinese) |
| Page-specific `<title>` | ❌ Missing |
| Open Graph tags (og:*) | ❌ Missing |
| Twitter Card tags | ❌ Missing |
| Schema.org structured data | ❌ Missing |
| `sitemap.xml` | ❌ Missing |
| `robots.txt` | ❌ Missing |
| Dynamic metadata on result pages | ❌ Missing |

---

## Strategic Decision: English Market First

**Rationale**: The AI transcription tool space is dominated by English-language searches. Competing in the Chinese market requires different channels (WeChat, Bilibili, Xiaohongshu). For web-based Google SEO, targeting English-speaking users offers:

- Higher search volume for target keywords
- More established intent-based search behavior
- Easier distribution via ProductHunt, Reddit, Twitter/X

### Target Keywords

| Keyword | Intent | Competition |
|---------|--------|-------------|
| `youtube transcript` | Direct need | High |
| `youtube to text free` | Free tool seeker | Medium |
| `AI video summarizer` | Feature-aware user | Medium |
| `AI youtube summary` | Feature-aware user | Medium |
| `[video title] transcript` | Long-tail, per result | Low |

The **long-tail keyword opportunity** (`[video title] transcript`) is the most underutilized: every public result page on the site could rank for the specific video being transcribed. This requires result pages to be SSR with dynamic metadata.

---

## The Biggest SEO Opportunity: Result Page SSR

Each `/result/[id]` page contains:
- Video title
- AI-generated summary
- Full transcript with timestamps
- Keywords extracted by AI

If these pages are server-side rendered with dynamic `<title>` and `<meta description>`, they become individually indexable content pages. A user searching `"Lex Fridman Elon Musk transcript"` could find the result page directly.

### Architecture Change

**Before**: Single `use client` component, 752 lines, no server-side metadata.

**After**: Server/Client split following Next.js App Router best practices:

```
app/result/[id]/
├── page.tsx          ← Server Component: generateMetadata() + renders <ResultClient>
└── ResultClient.tsx  ← Client Component: all interactive logic (YouTube player, scroll sync, etc.)
```

`generateMetadata()` runs on the server, fetches the result data, and returns:
- `title`: `"{video title} | Read-Tube"`
- `description`: First 155 chars of AI summary
- `openGraph.images`: Video thumbnail
- `keywords`: AI-extracted keywords from the result

---

## Implementation Scope

### Files Changed

| File | Change |
|------|--------|
| `frontend/app/result/[id]/page.tsx` | Rewrite as Server Component with `generateMetadata` |
| `frontend/app/result/[id]/ResultClient.tsx` | New file: all existing client logic |
| `frontend/app/layout.tsx` | English metadata, OG tags, `lang="en"` |
| `frontend/app/sitemap.ts` | New: dynamic sitemap including all public result pages |
| `frontend/public/robots.txt` | New: allow crawling of result pages |

### Sitemap Strategy

The sitemap dynamically includes:
- Static pages: `/`, `/login`
- All public result pages: `/result/{id}` (fetched from `/explore` API)

This tells Google exactly which pages to index, dramatically improving crawl efficiency.

---

## Development Priority Roadmap

### Phase 1 (This Sprint) — Highest ROI
- [x] Result page SSR + `generateMetadata`
- [x] English metadata on root layout
- [x] `sitemap.xml` auto-generation
- [x] `robots.txt`

### Phase 2 — Medium Priority
- [ ] OG default image (`/og-default.png` — 1200×630 branded image)
- [ ] Home page metadata refinement (A/B test descriptions)
- [ ] Explore page: add category/tag pages for topic-based SEO

### Phase 3 — Long-term Growth
- [ ] Blog/content pages targeting `youtube transcript` keywords
- [ ] Chrome extension (drives direct installs + brand searches)
- [ ] Social sharing: auto-generated summary cards (Xiaohongshu / Twitter)

---

## Verification Checklist

After implementation, verify SSR is working:

```bash
# Should see <title> and <meta name="description"> in raw HTML (not injected by JS)
curl -s https://your-domain.com/result/{id} | grep -E '<title>|<meta name="description"'

# Sitemap should list all public result pages
curl https://your-domain.com/sitemap.xml
```

Also use [Google Rich Results Test](https://search.google.com/test/rich-results) to validate structured markup once OG tags are in place.

---

*Author: SEO audit session, 2026-03-06*
