## 2024-05-23 - Sleep for Safety Anti-Pattern
**Learning:** Found a hardcoded `await page.wait_for_timeout(6000)` in PDF generation to "wait for diagrams". This imposes a 6s penalty on EVERY conversion, even those without diagrams.
**Action:** Always prefer `wait_for_selector` or `wait_for_function` over `sleep`. If sleep is "necessary", condition it on the presence of the element being waited for.

## 2024-05-24 - Regex Recompilation in Hot Paths
**Learning:** `sanitize_mermaid_code` was recompiling regex patterns every time it was called (per mermaid block) and for every string match inside the block. This caused measurable overhead (~25%).
**Action:** Move regex patterns to module-level constants (`re.compile`) when they are used in frequently called functions.
