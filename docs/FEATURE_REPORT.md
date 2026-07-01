# MDPDFM Pro — Feature & Roadmap Report

*Generated 2026-07-02. Covers the Python/Textual TUI (`md_to_pdf_tui.py`, v3.1) and the new WinUI 3 companion app (`winui3/`).*

## 1. What the app does today

MDPDFM Pro is a single-file (~1,600 line) Python tool that turns Markdown into PDF, DOCX, or PNG using a headless Chromium instance (via Playwright) as the rendering engine — the same trick VS Code's "Markdown PDF" extension uses, but wrapped in a full [Textual](https://github.com/Textualize/textual) TUI instead of being editor-bound. Highlights:

- **Rendering pipeline**: `markdown-it-py` (+ front-matter, footnote, table plugins) → HTML → Chromium → `page.pdf()` / `page.screenshot()` / pandoc.
- **Mermaid diagrams**: rendered client-side via mermaid.js inside the Chromium page, sanitized against a known "list marker inside quoted string" parser bug, then either kept as live SVG (PDF) or screenshotted to PNG and spliced into the Markdown before the DOCX pandoc pass (pandoc has no mermaid support of its own).
- **10 built-in themes**, each a small palette (bg/text/heading/code/border/line colors) reused for HTML/CSS, Mermaid's `themeVariables`, and DOCX alert-box colors.
- **GitHub-style alert blocks** (`> [!NOTE]` etc.) hand-parsed into styled HTML tables for the DOCX path (pandoc doesn't understand GFM alerts).
- **Headless/CLI mode** for CI or automation (`--headless --docx --dracula ...`), a **gallery mode** (render one document in all 10 themes), and now a **batch mode** (this session's addition).
- **Perf work already landed** (per prior session, see `git log`): browser-instance reuse across conversions, conditional Mermaid.js injection, O(N) DOCX text rebuild instead of O(N²), off-loop `shutil.copy2`, fast-path skips for documents with no images/alerts.

## 2. Bugs fixed / gaps closed this session

These were found by reading the full source, not guessed — each is cited by symptom, not just line number, since the file has shifted during editing:

| Issue | Why it mattered |
|---|---|
| `add_to_recent()` / `load_recent_files()` were fully implemented but **never called from the UI** — `self.recent_files` was loaded on startup and then discarded. | Dead feature. Fixed: recent files now populate a `Select` in the Settings tab, refresh after every successful file conversion, and clicking one reloads that file into the input + preview. |
| Duplicate `MAX_RECENT_FILES = 10` (declared twice back-to-back). | Harmless but sloppy — removed. |
| Redundant `import threading` inside `notify_user()`, shadowing the module-level import already in scope. | Removed. |
| `is_pure_mermaid(processed_text)` was checked in the PDF export path but the branch body was a bare `pass` — dead conditional. | Replaced with an actual informational log tip ("this is a single diagram — PNG usually looks tighter than a full A4 page"), since that's what the check was clearly meant to drive. |
| `content_width` existed in the settings schema and was fully wired into `create_html_content()`, but **no UI control ever set it** — only editable by hand-editing `settings.json`. | Added a "Page Width" input in the Aesthetics section. |
| No way to cancel a running PDF/DOCX export — a large Mermaid-heavy doc could block the UI's only feedback (the Cancel button didn't exist) for the full render time. | Added a Cancel button wired to the Textual `Worker` object returned by the `@work(exclusive=True)`-decorated `run_conversion`. |
| No live feedback in the Paste & Preview editor about document size. | Added a word/char counter that updates on every `TextArea.Changed`. |
| Headless mode could only convert **one file per process invocation** — a folder of 50 docs needed 50 process spawns (50× Chromium cold starts, since the browser-reuse optimization is per-process). | Added `--batch <folder-or-glob>`, which launches Chromium once and converts every matched file through it. |

All changes were smoke-tested: `python -m py_compile`, the existing `unittest` suite (8/8 passing), and a Textual `run_test()` headless mount that asserts the new widgets (`#recent-select`, `#width-input`, `#cancel-btn`, `#word-count`) exist and the app doesn't crash on startup.

## 3. Known issues not fixed (flagged, not silently ignored)

- **`open_file_dialog`/`open_folder_dialog` depend on `tkinter`.** Tkinter ships with the standard CPython Windows/macOS installers but is often missing from minimal Linux Python builds. On those systems Browse buttons silently no-op (the `except Exception: return None` swallows the `ImportError`). A `zenity`/`kdialog` fallback on Linux would close this gap — left alone since it's a Linux-only paper cut and out of scope for a "make it better" pass focused on Windows-first usage.
- **`_get_browser()`'s atexit cleanup** juggles `asyncio.get_event_loop()` (deprecated pattern) and swallows all exceptions. In practice Chromium terminates fine when the process exits regardless, but this is fragile if Textual ever changes its event-loop shutdown order. Worth revisiting if you see orphaned `chrome.exe` processes.
- **No true concurrent request queueing** — if a user mashes Convert PDF then Convert DOCX, `@work(exclusive=True)` cancels the first job outright rather than queueing it. That's arguably correct behavior for a TUI (one export at a time, cancel-and-restart), but it's not documented anywhere, so a user could be confused about why their PDF job silently died.
- **Paste-mode relative image paths don't resolve** — if you paste Markdown containing `![x](./img.png)`, there's no "current directory" concept for pasted text, so `process_resources()` will fail to find it (`Path(url).resolve()` resolves against the process CWD, not any meaningful document root). Only absolute paths and remote URLs work reliably in Paste mode.

## 4. Feature ideas, prioritized

### Quick wins (hours, not days)
- **Custom CSS override**: let a settings field point at a user CSS file that gets appended after the theme `<style>` block. Near-zero implementation cost since `create_html_content` already builds a single HTML string.
- **Syntax highlighting for fenced code blocks**: currently code blocks render as plain `<pre><code>` with no highlighting. `markdown-it-py` has a `highlight` callback hook already exposed by the API in use — wiring in `pygments` (already a soft dependency of many docs pipelines) would be a visually large win for near-zero architectural change.
- **Table of contents / bookmarks in PDF output**: Chromium's `page.pdf()` doesn't auto-generate a PDF outline from headings, but a small pre-pass that injects heading `id`s (already implicit via markdown-it) plus a `pdf.js`-style bookmark post-processor (or just a rendered ToC block at the top) would meaningfully help long documents.
- **"Open Containing Folder" for DOCX/PNG, not just the button that already exists for the output folder in general.**
- **Drag-and-drop file support** — Textual doesn't have native DnD, but terminal emulators that support the OSC 52/dropped-path escape sequences (Windows Terminal, iTerm2) could be wired through `on_paste`.

### Medium effort (a day or two)
- **File-watch / live preview**: use `watchfiles` (already a Textual dependency transitively) to re-render the preview automatically when the on-disk source file changes — turns this into a true live-preview tool instead of "preview on submit."
- **Multi-file conversion queue in the TUI itself**, not just headless — a small list widget where you drop in several file paths and convert them all with one progress bar, mirroring the new `--batch` CLI flag.
- **Per-document front-matter overrides**: `markdown-it-py`'s front-matter plugin is already enabled and parsed but currently completely unused — YAML front matter like `theme: dracula` or `width: 1000` could override the app-wide settings on a per-document basis, which is the more natural UX for a "these are my report's build settings" mental model.
- **PDF headers/footers with page numbers**: `page.pdf()` supports `displayHeaderFooter` + `headerTemplate`/`footerTemplate` HTML strings — currently unused. Straightforward since the whole pipeline already funnels through one `opts` dict in `generate_pdf_core`.

### Bigger bets
- **Custom theme editor**: a form-based color picker that lets users define an 11th+ theme and persist it to `settings.json` (the `THEMES` dict would need to merge in a user-themes file rather than being a hardcoded module constant).
- **Non-Mermaid diagram support** (PlantUML, Graphviz/dot) using the same "render off-thread, screenshot, splice into DOCX" pattern already proven for Mermaid.
- **Native DOCX generation without pandoc**, using `python-docx` directly for the text and only shelling out (or using Playwright) for diagram images. This removes the hard external dependency on a system-installed `pandoc` binary, which is currently a support burden (see `_PANDOC_AVAILABLE` check and its unhelpful `RuntimeError` when missing).
- **A plugin/extension model** for the theme + alert-style system so third parties can add themes or output formats without editing the 1,600-line core file.

## 5. WinUI 3 companion app

A new native Windows app lives in [`winui3/MdToPdf`](../winui3/MdToPdf). It's a from-scratch **C#/.NET 8, MVVM, NavigationView + Mica** app — not a Python-to-C# transpile — built with the same rendering philosophy (Chromium via WebView2, `Markdig` for Markdown parsing) but idiomatic WinUI 3 patterns throughout (CommunityToolkit.Mvvm source generators, `ObservableObject`/`RelayCommand`, async/await everywhere, `SystemBackdrop`).

**Fully working (this is the "solid MVP" scope you picked):**
- File picker + Paste-and-preview editor with live WebView2-rendered Markdown preview.
- All 10 themes ported 1:1 (same hex palettes) with a theme picker.
- PDF export via `CoreWebView2.PrintToPdfAsync` with configurable page width/margins.
- Settings persistence (theme, page width, output folder) to a local JSON file, same shape as the Python app's `settings.json` philosophy.
- Recent files list.

**Deliberately stubbed with `// TODO` markers** (per your choice of "solid MVP over broad-but-thin"), each is a genuine design decision left for you rather than a placeholder for its own sake:
- **DOCX export** — the open decision is pandoc shell-out (matches Python behavior, needs pandoc installed) vs. `DocumentFormat.OpenXml` native generation (zero external deps, more code). See `Services/DocxExportService.cs`.
- **Mermaid diagram rendering** — WebView2 can run mermaid.js identically to the Python app's approach; this needs the JS-side wait-for-render polling logic ported. See `Services/MermaidRenderService.cs`.
- **PNG gallery mode** — depends on the Mermaid piece landing first.

See [`winui3/MdToPdf/README.md`](../winui3/MdToPdf/README.md) for build instructions, prerequisites (Visual Studio 2022 with the "Windows application development" workload — this sandbox has neither Visual Studio nor the Windows SDK installed, so the project has been written to official Microsoft WinUI 3 conventions but **not compiled in this session**; treat first build as the verification step), and the full list of TODOs.
