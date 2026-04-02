## 2024-05-23 - Sleep for Safety Anti-Pattern
**Learning:** Found a hardcoded `await page.wait_for_timeout(6000)` in PDF generation to "wait for diagrams". This imposes a 6s penalty on EVERY conversion, even those without diagrams.
**Action:** Always prefer `wait_for_selector` or `wait_for_function` over `sleep`. If sleep is "necessary", condition it on the presence of the element being waited for.

## 2026-02-19 - Regex Compilation in Hot Path
**Learning:** `sanitize_mermaid_code` recompiled regex patterns and redefined helper functions on every invocation. This was inefficient for documents with many mermaid blocks.
**Action:** Moved regex patterns and helper functions to module level constants. Benchmarked ~14.6% improvement.
## 2026-03-03 - Prevent Expensive Browser Launch on Missing Content
**Learning:** Instantiating a headless browser (Playwright) takes significant time and resources. Generating PNGs for files without Mermaid diagrams was spending ~4.5s just to launch the browser, load the page, and realize there was no diagram to capture. Since the `generate_png_core` function is explicitly designed to only capture mermaid diagrams (it calls `element.screenshot()` on `.mermaid` only), launching the browser for files without them is a waste.
**Action:** Always perform a cheap static check (e.g., regex search for the target content) before initiating expensive external processes. Offload file I/O and regex to a thread pool to avoid blocking the async event loop. Early returns for non-applicable states improve throughput massively.

## 2026-03-05 - Concurrent Gallery Mode Race Condition
**Learning:** Running headless browser pages concurrently using `asyncio.gather` requires that shared temporary files (like `.tmp.html`) are uniquely named (e.g., via `uuid`). Otherwise, tasks overwrite each other's HTML files, leading to incorrect screenshots or silent failures.
**Action:** When parallelizing browser tasks, ensure all intermediate file I/O uses unique, non-overlapping paths.

## 2026-03-05 - Optimize CLI arguments lookup using module-level pre-computation
**Learning:** When parsing CLI arguments for predefined constants (like themes), generating search strings inside nested loops takes O(N*M) time. Pre-computing lookup dictionaries and using `next()` reduces this to a single O(N) pass.
**Action:** Prefer dictionary lookups for string matching in loops.

## 2026-03-05 - Optimize Regex match combining
**Learning:** Combining unique regex matches from multiple passes in Python using explicit `for` loops with `set.add()` is slower than using set comprehensions with the set union operator (`|`) due to native C iteration.
**Action:** Use set comprehensions and `|` when combining matches from multiple iterators into a set.

## 2026-03-05 - Fast-Path Bypass for O(n) Array Processing
**Learning:** In `generate_docx_core`, processing GitHub alerts line-by-line using `split('\n')` incurs O(n) array allocations and regex overhead for every line, even for documents without any alerts.
**Action:** Use cheap static checks (e.g., substring `"[!" in text` and a multiline regex search) as a fast-path to completely bypass expensive array allocations and line-by-line processing blocks for features that are not universally present in the input data.
