## 2024-05-23 - Sleep for Safety Anti-Pattern
**Learning:** Found a hardcoded `await page.wait_for_timeout(6000)` in PDF generation to "wait for diagrams". This imposes a 6s penalty on EVERY conversion, even those without diagrams.
**Action:** Always prefer `wait_for_selector` or `wait_for_function` over `sleep`. If sleep is "necessary", condition it on the presence of the element being waited for.

## 2025-02-18 - Ephemeral Contexts & Network I/O
**Learning:** The "Paste & Preview" feature created a fresh temporary directory for every preview update, causing remote images to be re-downloaded every few seconds. This is a common TUI/GUI preview anti-pattern where "stateless" rendering accidentally becomes "expensive" rendering.
**Action:** Implement a persistent cache (e.g., `~/.app/cache`) for remote assets that outlives the temporary preview contexts. Use atomic file operations (write temp + rename) to safely handle concurrent downloads.
