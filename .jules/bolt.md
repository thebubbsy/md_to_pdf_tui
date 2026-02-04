## 2025-02-04 - Playwright Browser Reuse
**Learning:** Launching a Playwright browser instance (`browser = await p.chromium.launch()`) has significant overhead. In batch operations, reusing the browser instance and creating new pages is much faster.
**Action:** When implementing batch processing with Playwright, lift the browser launch outside the loop.
