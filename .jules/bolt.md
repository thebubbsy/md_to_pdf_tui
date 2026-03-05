## 2024-05-23 - Sleep for Safety Anti-Pattern
**Learning:** Found a hardcoded `await page.wait_for_timeout(6000)` in PDF generation to "wait for diagrams". This imposes a 6s penalty on EVERY conversion, even those without diagrams.
**Action:** Always prefer `wait_for_selector` or `wait_for_function` over `sleep`. If sleep is "necessary", condition it on the presence of the element being waited for.

## 2026-02-19 - Regex Compilation in Hot Path
**Learning:** `sanitize_mermaid_code` recompiled regex patterns and redefined helper functions on every invocation. This was inefficient for documents with many mermaid blocks.
**Action:** Moved regex patterns and helper functions to module level constants. Benchmarked ~14.6% improvement.

## 2026-03-01 - Avoid Regex Overhead for Non-Alert Lines in DOCX Generation
**Learning:** In `generate_docx_core`'s alert processing step, `ALERT_PATTERN.match(line)` was executed for every single line of a markdown document. For large documents with few alerts, this regex operation introduces substantial overhead. Since markdown alerts and blockquotes always contain a `>`, we can use a fast-skip heuristic string check before running the regex.
**Action:** Implemented a fast-skip check `if not in_alert and ">" not in line:` that skips regex processing and immediately appends the line for standard text. This reduces processing time by avoiding expensive regex operations.
