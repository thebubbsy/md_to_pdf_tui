## 2024-05-23 - Sleep for Safety Anti-Pattern
**Learning:** Found a hardcoded `await page.wait_for_timeout(6000)` in PDF generation to "wait for diagrams". This imposes a 6s penalty on EVERY conversion, even those without diagrams.
**Action:** Always prefer `wait_for_selector` or `wait_for_function` over `sleep`. If sleep is "necessary", condition it on the presence of the element being waited for.

## 2026-02-19 - Regex Compilation in Hot Path
**Learning:** `sanitize_mermaid_code` recompiled regex patterns and redefined helper functions on every invocation. This was inefficient for documents with many mermaid blocks.
**Action:** Moved regex patterns and helper functions to module level constants. Benchmarked ~14.6% improvement.

## 2025-02-28 - Fast Skip for Alert Regex in DOCX Export
**Learning:** During docx export, scanning every line of a large markdown file with a regex `ALERT_PATTERN.match(line)` to find markdown alerts (`> [!NOTE]`) introduces unnecessary overhead. Since an alert must contain a `>` character, checking `'>' not in line` as a fast pre-condition lets us skip the expensive regex match operation entirely for most lines in typical documents. This reduced the benchmark time for a 200,000 line file from ~0.29s to ~0.05s.
**Action:** When applying a regex to every line in a large dataset, try to identify a simple string operation (like `in`) that can act as a gatekeeper to skip the regex completely for non-matching lines.
