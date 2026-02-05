# Markdown to PDF Converter TUI (Pro Suite)

**MDPDFM PRO v3.0** is a feature-rich, "zero-bullshit" Markdown to PDF/DOCX/PNG converter. It features a modern Terminal User Interface (TUI) powered by Textual, high-quality rendering via Playwright, and specialized support for advanced documentation styles (alerts, themes).

## Features

-   **Modern TUI**: Built with [Textual](https://github.com/Textualize/textual) for a beautiful terminal experience.
-   **High-Quality PDF Export**: Uses Chromium (via Playwright) for pixel-perfect rendering.
-   **DOCX Export**: Convert Markdown to Word documents with styled alerts (requires `pandoc`).
-   **PNG Export**: Generate high-resolution screenshots of your documents (up to 24K resolution supported).
-   **Mermaid Diagrams**: Native support for rendering Mermaid.js diagrams.
-   **Alert Blocks**: GitHub-flavored alert blocks (Note, Tip, Important, Warning, Caution) are fully styled.
-   **Theming**: Includes 10+ themes (GitHub Light/Dark, Solarized, Dracula, Cyberpunk, etc.).
-   **Headless Mode**: Run from scripts or CLI for automated pipelines.
-   **Gallery Mode**: Automatically generate PNG previews of a document in all available themes.

<img width="1919" height="1028" alt="image" src="https://github.com/user-attachments/assets/2e5f064a-6a48-4e10-891b-7f42376fad0b" />

## Installation

1.  Clone the repository:
    ```bash
    git clone https://github.com/thebubbsy/md_to_pdf_tui.git
    cd md_to_pdf_tui
    ```

2.  Install Python dependencies:
    ```bash
    pip install -r requirements.txt
    ```

3.  Install Playwright browsers:
    ```bash
    playwright install chromium
    ```

4.  (Optional) Install Pandoc for DOCX support:
    -   **Windows**: `winget install pandoc`
    -   **Mac**: `brew install pandoc`
    -   **Linux**: `sudo apt install pandoc`

## Usage

### TUI Mode (Interactive)

Simply run the script to launch the TUI:

```bash
python md_to_pdf_tui.py
```

-   **Ctrl+O**: Browse for input file.
-   **Ctrl+R**: Convert to PDF.
-   **Ctrl+D**: Convert to DOCX.
-   **Ctrl+P**: Open generated PDF.

### Command Line / Headless Mode

```bash
python md_to_pdf_tui.py input.md --headless [flags]
```

**Flags:**
-   `--headless`: Run without TUI.
-   `--docx`: Output as DOCX.
-   `--png`: Output as PNG.
-   `--gallery`: Generate PNGs in all available themes.
-   `--open`: Open the file after generation.
-   `--[theme]`: Apply a specific theme (e.g., `--github-dark`, `--dracula`).

**Example:**

```bash
# Convert to PDF with Dracula theme
python md_to_pdf_tui.py report.md --headless --dracula

# Generate DOCX
python md_to_pdf_tui.py report.md --headless --docx
```

## Themes

-   GitHub Light / Dark
-   Solarized Light / Dark
-   Dracula
-   Monokai Pro
-   Cyberpunk
-   Nordic
-   Forest
-   Obsidian

## Requirements

-   Python 3.8+
-   `textual`
-   `playwright`
-   `markdown-it-py`
-   `mdit-py-plugins`
-   `pandoc` (only for DOCX export)
