## 2024-05-23 - Sleep for Safety Anti-Pattern
**Learning:** Found a hardcoded `await page.wait_for_timeout(6000)` in PDF generation to "wait for diagrams". This imposes a 6s penalty on EVERY conversion, even those without diagrams.
**Action:** Always prefer `wait_for_selector` or `wait_for_function` over `sleep`. If sleep is "necessary", condition it on the presence of the element being waited for.

## 2026-02-19 - Regex Compilation in Hot Path
**Learning:** `sanitize_mermaid_code` recompiled regex patterns and redefined helper functions on every invocation. This was inefficient for documents with many mermaid blocks.
**Action:** Moved regex patterns and helper functions to module level constants. Benchmarked ~14.6% improvement.

## 2025-02-23 - Regex Inefficiency in Alert Loop
**Learning:** In `generate_docx_core` within `md_to_pdf_tui.py`, iterating over large files line-by-line and applying a regex (`ALERT_PATTERN.match`) on every single line introduced significant overhead, even for completely normal Markdown files lacking any GitHub-style alerts.
**Action:** Implemented a 'fast skip' early return (`if not in_alert and ">" not in line`) inside the loop. This skips regex evaluation completely on standard lines, providing an ~80% reduction in parsing time for normal text documents during DOCX export.
