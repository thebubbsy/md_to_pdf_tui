## 2024-05-23 - Sleep for Safety Anti-Pattern
**Learning:** Found a hardcoded `await page.wait_for_timeout(6000)` in PDF generation to "wait for diagrams". This imposes a 6s penalty on EVERY conversion, even those without diagrams.
**Action:** Always prefer `wait_for_selector` or `wait_for_function` over `sleep`. If sleep is "necessary", condition it on the presence of the element being waited for.

## 2026-02-19 - Regex Compilation in Hot Path
**Learning:** `sanitize_mermaid_code` recompiled regex patterns and redefined helper functions on every invocation. This was inefficient for documents with many mermaid blocks.
**Action:** Moved regex patterns and helper functions to module level constants. Benchmarked ~14.6% improvement.

## 2026-03-04 - [Async Worker Refactoring & I/O Optimization]
**Learning:** Mixing synchronous I/O or CPU-heavy tasks in an async context (like Textual @work async methods) blocks the main event loop, causing UI stutters. Positional arguments in `run_in_executor` are risky for functions with many defaults (like `Path.mkdir`).
**Action:** Refactor @work(thread=True) workers to async workers and offload all blocking calls (Path, tempfile, Image, create_html_content) to an executor using lambdas for safety and clarity.
