## 2024-05-23 - Sleep for Safety Anti-Pattern
**Learning:** Found a hardcoded `await page.wait_for_timeout(6000)` in PDF generation to "wait for diagrams". This imposes a 6s penalty on EVERY conversion, even those without diagrams.
**Action:** Always prefer `wait_for_selector` or `wait_for_function` over `sleep`. If sleep is "necessary", condition it on the presence of the element being waited for.

## 2026-02-19 - Regex Compilation in Hot Path
**Learning:** `sanitize_mermaid_code` recompiled regex patterns and redefined helper functions on every invocation. This was inefficient for documents with many mermaid blocks.
**Action:** Moved regex patterns and helper functions to module level constants. Benchmarked ~14.6% improvement.

## 2024-05-28 - Avoid Expensive Operations without Quick Checks
**Learning:** Found that `generate_png_core` in `md_to_pdf_tui.py` was instantiating a Playwright browser and rendering an HTML document even if the markdown document didn't contain any mermaid diagrams, relying on timeouts and element counts to fail gracefully, but suffering an enormous execution time penalty (~3 seconds) to do nothing.
**Action:** Always verify if expensive resources are needed before allocating them. Adding an early return using a fast regex search (`MERMAID_PATTERN.search(md_text)`) reduced execution time for non-mermaid files from ~3.2s to ~0.003s.
