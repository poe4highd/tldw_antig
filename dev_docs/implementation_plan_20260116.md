# Plan: Fix Subtitle Layout Shift

This plan addresses the UI issue where the active subtitle causes layout shifts due to font-weight and scaling changes.

## Proposed Changes

### [Frontend] [page.tsx](file:///frontend/app/dev-result/[id]/page.tsx)
- Remove `font-bold`, `scale-[1.01]`, and `inline-block` from the active sentence style.
- Maintain highlighting using `text-blue-400` and `bg-blue-400/10`.
- Ensure `text-slate-400` is used for inactive sentences to maintain contrast.

## Verification Plan

### Manual Verification
- Run the app locally.
- Play a video and observe the subtitles.
- Confirm that the layout remains stable as the highlight moves from one sentence to the next.
