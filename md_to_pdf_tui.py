"""
Markdown to PDF Converter TUI v2.8.2 Pro - Suite
The most feature-rich version ever. Zero-bullshit logic.
Now with background CLI mode for automated exports and high-contrast light-mode.
Added themes and png output to docx
"""

import asyncio
import concurrent.futures
import json
import os
import subprocess
import sys
import threading
import traceback
from datetime import datetime
from pathlib import Path
from typing import Optional
import re
import tempfile
import uuid
import urllib.request
import shutil
import hashlib
import webbrowser

try:
    from rich_pixels import Pixels
    from PIL import Image
    HAS_PIXELS = True
except ImportError:
    HAS_PIXELS = False

# Textual imports (only if needed)
try:
    from textual.app import App, ComposeResult, events
    from textual.containers import Container, Horizontal, Vertical, ScrollableContainer, VerticalScroll, Center
    from textual.widgets import (
        Button, Footer, Header, Input, Label, RichLog, Static, 
        Select, Switch, ProgressBar, Rule, TabbedContent, TabPane, Markdown, TextArea, ContentSwitcher
    )
    from textual.binding import Binding
    from textual.screen import ModalScreen
    from textual import work
    HAS_TEXTUAL = True
except ImportError:
    HAS_TEXTUAL = False

from playwright.async_api import async_playwright
import markdown_it
from mdit_py_plugins.front_matter import front_matter_plugin
from mdit_py_plugins.footnote import footnote_plugin

# --- Constants ---
CONFIG_DIR = Path.home() / ".md_to_pdf"
RECENT_FILES_PATH = CONFIG_DIR / "recent_files.json"
SETTINGS_PATH = CONFIG_DIR / "settings.json"
MAX_RECENT_FILES = 10
MAX_RECENT_FILES = 10
A4_WIDTH_PX = 800

# --- Theme Definitions ---
THEMES = {
    "GitHub Light": {
        "bg": "#ffffff", "txt": "#1b1f23", "head": "#000000", "code": "#f6f8fa", "brd": "#d1d5da",
        "primary": "#000000", "secondary": "#f6f8fa", "line": "#333333"
    },
    "GitHub Dark": {
        "bg": "#0d1117", "txt": "#c9d1d9", "head": "#58a6ff", "code": "#161b22", "brd": "#30363d",
        "primary": "#c9d1d9", "secondary": "#161b22", "line": "#8b949e"
    },
    "Solarized Light": {
        "bg": "#fdf6e3", "txt": "#657b83", "head": "#b58900", "code": "#eee8d5", "brd": "#93a1a1",
        "primary": "#657b83", "secondary": "#eee8d5", "line": "#586e75"
    },
    "Solarized Dark": {
        "bg": "#002b36", "txt": "#839496", "head": "#b58900", "code": "#073642", "brd": "#586e75",
        "primary": "#93a1a1", "secondary": "#073642", "line": "#839496"
    },
    "Dracula": {
        "bg": "#282a36", "txt": "#f8f8f2", "head": "#bd93f9", "code": "#44475a", "brd": "#6272a4",
        "primary": "#f8f8f2", "secondary": "#282a36", "line": "#bd93f9"
    },
    "Monokai Pro": {
        "bg": "#2d2a2e", "txt": "#fcfcfa", "head": "#ffd866", "code": "#19181a", "brd": "#5d5d5d",
        "primary": "#fcfcfa", "secondary": "#2d2a2e", "line": "#ffd866"
    },
    "Cyberpunk": {
        "bg": "#05051e", "txt": "#00ff9f", "head": "#ff003c", "code": "#0d0221", "brd": "#00ff9f",
        "primary": "#f5ed00", "secondary": "#0d0221", "line": "#00ff9f"
    },
    "Nordic": {
        "bg": "#2e3440", "txt": "#eceff4", "head": "#88c0d0", "code": "#3b4252", "brd": "#4c566a",
        "primary": "#d8dee9", "secondary": "#2e3440", "line": "#81a1c1"
    },
    "Forest": {
        "bg": "#0b1a0b", "txt": "#d4e1d4", "head": "#78a75a", "code": "#1a2f1a", "brd": "#3d5a3d",
        "primary": "#a3bfa3", "secondary": "#0b1a0b", "line": "#78a75a"
    },
    "Obsidian": {
        "bg": "#050000", "txt": "#e0e0e0", "head": "#ff4500", "code": "#1a0000", "brd": "#ff0000",
        "primary": "#ff4500", "secondary": "#050000", "line": "#ff0000"
    }
}
def load_recent_files() -> list[str]:
    if RECENT_FILES_PATH.exists():
        try:
            return json.loads(RECENT_FILES_PATH.read_text())[:MAX_RECENT_FILES]
        except Exception:
            return []
    return []

def save_recent_files(files: list[str]) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    RECENT_FILES_PATH.write_text(json.dumps(files[:MAX_RECENT_FILES]))

def add_to_recent(filepath: str) -> list[str]:
    files = load_recent_files()
    path_str = str(Path(filepath).resolve())
    if path_str in files:
        files.remove(path_str)
    files.insert(0, path_str)
    save_recent_files(files)
    return files

def load_settings() -> dict:
    if SETTINGS_PATH.exists():
        try:
            return json.loads(SETTINGS_PATH.read_text())
        except Exception:
            pass
    return {
        "theme": "GitHub Light", 
        "content_width": 800, 
        "mermaid_enabled": True, 
        "output_folder": str(Path.home() / "Documents"), 
        "save_html": False, 
        "unlimited_height": True,
        "a4_fixed_width": True,
        "save_diagrams": False
    }

def save_settings(settings: dict) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    SETTINGS_PATH.write_text(json.dumps(settings, indent=2))

def open_file_dialog() -> Optional[str]:
    try:
        import tkinter as tk
        from tkinter import filedialog
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        filepath = filedialog.askopenfilename(
            title="Select Markdown File",
            filetypes=[("Markdown files", "*.md *.markdown"), ("All files", "*.*")]
        )
        root.destroy()
        return filepath if filepath else None
    except Exception:
        return None

def open_folder_dialog() -> Optional[str]:
    try:
        import tkinter as tk
        from tkinter import filedialog
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        folder = filedialog.askdirectory(title="Select Output Folder")
        root.destroy()
        return folder if folder else None
    except Exception:
        return None

def open_file_externally(path: str) -> None:
    """Opens a file or directory using the default system application."""
    import platform
    p = Path(path).resolve()
    if not p.exists():
        raise FileNotFoundError(f"Path not found: {path}")

    system = platform.system()
    try:
        if system == "Windows":
            os.startfile(str(p))
        elif system == "Darwin":
            subprocess.run(["open", str(p)], check=False)
        else: # Linux
            subprocess.run(["xdg-open", str(p)], check=False)
    except Exception as e:
        raise RuntimeError(f"Failed to open {path}: {e}")

# --- Regex Patterns ---
# Regex for standard markdown images. Handles optional title: ![alt](url "title")
MD_IMG_PATTERN = re.compile(r'!\[([^\]]*)\]\s*\(\s*([^\s)]+)(?:\s+["\'].*?["\'])?\s*\)')
# Regex for HTML images
HTML_IMG_PATTERN = re.compile(r'<img\s+[^>]*src=["\']([^"\']+)["\'][^>]*>')
# Regex for Alerts
ALERT_PATTERN = re.compile(r"^\s*>\s*\[!(NOTE|TIP|IMPORTANT|WARNING|CAUTION)\]", re.IGNORECASE)
# Regex for Mermaid
MERMAID_PATTERN = re.compile(r"^(?:`{3,}|~{3,})mermaid\s*\n(.*?)\n(?:`{3,}|~{3,})", re.DOTALL | re.MULTILINE)

# Pre-compiled patterns for mermaid sanitization
_MERMAID_STRING_PATTERN = re.compile(r'"((?:[^"\\]|\\.)*)"' + r"|'((?:[^'\\]|\\.)*)'", re.DOTALL)
_MERMAID_LIST_MARKER_PATTERN = re.compile(r"(^|\n)(\s*)(?:([-*])|(\d+\.))\s+")

def process_resources(md_text: str, temp_dir: Path) -> str:
    """
    Scans markdown text for images and resources.
    Downloads remote images to temp_dir.
    Updates markdown references to point to absolute paths for local files.
    """
    def _hash_url(url: str) -> str:
        return hashlib.md5(url.encode()).hexdigest()

    def _process_single_resource(url: str) -> tuple[str, Optional[str]]:
        # Returns (url, local_filename) or (url, None)
        if url.startswith("http://") or url.startswith("https://"):
            try:
                # Download
                ext = Path(url).suffix or ".png"
                if "?" in ext: ext = ext.split("?")[0]
                local_filename = f"remote_{_hash_url(url)}{ext}"
                local_path = temp_dir / local_filename

                if not local_path.exists():
                    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                    with urllib.request.urlopen(req, timeout=15) as response, open(local_path, 'wb') as out_file:
                        shutil.copyfileobj(response, out_file)
                return url, local_filename
            except Exception:
                return url, None
        else:
            # Local file
            try:
                src_path = Path(url).resolve()
                if src_path.exists():
                    # Optimization: Use absolute path directly instead of copying
                    return url, src_path.as_posix()
                return url, None
            except Exception:
                return url, None

    # 1. Identify all unique URLs
    urls = set()
    for match in MD_IMG_PATTERN.finditer(md_text):
        urls.add(match.group(2))
    for match in HTML_IMG_PATTERN.finditer(md_text):
        urls.add(match.group(1))

    # Optimization: Early return if no resources to process, avoiding expensive substitution passes
    if not urls:
        return md_text

    # 2. Process in parallel
    url_map = {}
    if urls:
        with concurrent.futures.ThreadPoolExecutor(max_workers=min(32, len(urls) + 4)) as executor:
            future_to_url = {executor.submit(_process_single_resource, url): url for url in urls}
            for future in concurrent.futures.as_completed(future_to_url):
                try:
                    url, local_name = future.result()
                    if local_name:
                        url_map[url] = local_name
                except Exception:
                    pass
    else:
        # Optimization: No resources found, return early to avoid unnecessary regex substitution passes
        return md_text

    # 3. Replace in text
    def replace_link(match):
        alt = match.group(1)
        url = match.group(2)
        local_name = url_map.get(url)
        if local_name:
            return f'![{alt}]({local_name})'
        return match.group(0)

    def replace_html_src(match):
        url = match.group(1)
        full_tag = match.group(0)
        local_name = url_map.get(url)
        if local_name:
            return full_tag.replace(url, local_name)
        return full_tag

    new_text = MD_IMG_PATTERN.sub(replace_link, md_text)
    new_text = HTML_IMG_PATTERN.sub(replace_html_src, new_text)

    return new_text

def is_pure_mermaid(text: str) -> bool:
    """
    Checks if the text contains only a mermaid block.
    """
    stripped = text.strip()
    return (stripped.startswith("```mermaid") and stripped.endswith("```")) or \
           (stripped.startswith("~~~mermaid") and stripped.endswith("~~~"))

# --- Core Conversion Logic (Decoupled from TUI) ---
# --- Core Conversion Logic (Decoupled from TUI) ---
def _mermaid_insert_space(m):
    prefix = m.group(1) + m.group(2)
    marker = m.group(3) if m.group(3) else m.group(4)
    # Insert zero-width space to break the list marker pattern
    return f"{prefix}{marker}&#8203; "

def _mermaid_replacer(match):
    if match.group(1) is not None:
        content = match.group(1)
        quote = '"'
    else:
        content = match.group(2)
        quote = "'"

    new_content = _MERMAID_LIST_MARKER_PATTERN.sub(_mermaid_insert_space, content)
    return f"{quote}{new_content}{quote}"

def sanitize_mermaid_code(code: str) -> str:
    """
    Sanitizes mermaid code to prevent "Unsupported markdown" errors in nodes.
    Specifically handles list markers (-, *, 1.) inside quoted strings.
    """
    return _MERMAID_STRING_PATTERN.sub(_mermaid_replacer, code)

_MD_PARSER = None
_PANDOC_AVAILABLE = None

def _get_md_parser():
    global _MD_PARSER
    if _MD_PARSER is None:
        _MD_PARSER = markdown_it.MarkdownIt().use(front_matter_plugin).use(footnote_plugin).enable("table")

        def mf(tokens, idx, options, env):
            t = tokens[idx]
            m_enabled = env.get("mermaid_enabled", True) if env else True
            if t.info.strip() == "mermaid" and m_enabled:
                content = sanitize_mermaid_code(t.content)
                return f'<div class="m-wrap"><div class="mermaid">{content}</div></div>'
            return f"<pre><code>{t.content}</code></pre>"

        _MD_PARSER.renderer.rules["fence"] = mf
    return _MD_PARSER

def create_html_content(md_text: str, settings: dict) -> str:
    theme_name = settings.get("theme", "GitHub Light")
    # Fallback if theme name not found
    if theme_name not in THEMES: theme_name = "GitHub Light"
    
    t_data = THEMES[theme_name]
    c_width = int(settings.get("content_width", 800))
    m_enabled = settings.get("mermaid_enabled", True)
    
    it = _get_md_parser()
    body = it.render(md_text, env={"mermaid_enabled": m_enabled})
    
    # Configure Mermaid Theme based on our palette
    m_theme_init = f'''theme: "base",
            themeVariables: {{
                primaryColor: "{t_data['bg']}",
                primaryTextColor: "{t_data['primary']}",
                primaryBorderColor: "{t_data['line']}",
                lineColor: "{t_data['line']}",
                secondaryColor: "{t_data['secondary']}",
                tertiaryColor: "{t_data['bg']}"
            }}'''
            
    return f'''<!DOCTYPE html><html><head><meta charset="UTF-8">
<script src="https://cdn.jsdelivr.net/npm/mermaid@11.4.1/dist/mermaid.min.js"></script>
<script>
mermaid.initialize({{ 
    startOnLoad: true, 
    {m_theme_init},
    maxTextSize: 10000000,
    maxNodes: 10000,
    flowchart: {{ useMaxWidth: false, htmlLabels: true, curve: "linear" }},
    securityLevel: "loose"
}});
</script>
<style>
body {{ background: {t_data['bg']}; color: {t_data['txt']}; font-family: -apple-system, "Segoe UI", sans-serif; line-height: 1.6; margin: 0; padding: 0; display: flex; flex-direction: column; align-items: center; width: 100%; }}
#canvas {{ padding: 60px 40px; width: 100%; max-width: {c_width}px; box-sizing: border-box; }}
h1, h2 {{ color: {t_data['head']}; border-bottom: 2px solid {t_data['brd']}; padding-bottom: 8px; }}
pre {{ background: {t_data['code']}; padding: 16px; border-radius: 6px; overflow-x: auto; border: 1px solid {t_data['brd']}; }}
table {{ border-collapse: collapse; width: 100%; margin: 16px 0; border: 2px solid {t_data['brd']}; }}
th, td {{ border: 1px solid {t_data['brd']}; padding: 8px 12px; text-align: left; }}
th {{ background: {t_data['code']}; font-weight: bold; }}
.m-wrap {{ width: 100%; margin: 32px 0; background: {t_data['code']}; border-radius: 8px; padding: 20px; border: 2px solid {t_data['brd']}; box-sizing: border-box; }}
.mermaid svg {{ width: 100% !important; height: auto !important; }}
/* Dynamic Mermaid Overrides from Theme */
.mermaid .node rect, .mermaid .node circle, .mermaid .node polygon, .mermaid .node path, .mermaid .cluster rect {{ stroke: {t_data['line']} !important; stroke-width: 2px !important; fill: {t_data['bg']} !important; }}
.mermaid .edgePath path {{ stroke: {t_data['line']} !important; stroke-width: 2px !important; }}
.mermaid .label {{ color: {t_data['primary']} !important; }}
.mermaid .arrowheadPath {{ fill: {t_data['line']} !important; }}
.mermaid-error {{ background: #fee2e2 !important; color: #991b1b !important; border: 2px solid #ef4444 !important; padding: 20px !important; margin: 20px 0 !important; font-family: monospace !important; border-radius: 8px !important; white-space: pre-wrap !important; }}
</style></head><body><div id="canvas">{body}</div></body></html>'''

async def generate_pdf_core(md_path: Path, pdf_path: Path, settings: dict, log_fn=print, prog_fn=None) -> None:
    u_height = settings.get("unlimited_height", True)
    a4_width = settings.get("a4_fixed_width", True)
    theme_name = settings.get("theme", "GitHub Light")
    
    if log_fn: log_fn(f"Parsing Markdown: {md_path.name}")
    try:
        md_text = await asyncio.get_running_loop().run_in_executor(None, md_path.read_text, "utf-8")
    except UnicodeDecodeError:
        raise ValueError(f"The file '{md_path.name}' is not a valid text file. Please ensure you are converting a Markdown (.md) file, not a binary file like PDF.")
    if prog_fn: prog_fn(20)
    
    html_content = create_html_content(md_text, settings)
    if prog_fn: prog_fn(30)
    
    tmp_h = md_path.with_suffix(".tmp.html")
    await asyncio.get_running_loop().run_in_executor(None, tmp_h.write_text, html_content, "utf-8")
    if prog_fn: prog_fn(40)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        v_w = 800 if a4_width else 1200
        page = await browser.new_page(viewport={"width": v_w, "height": 1000})
        abs_url = f"file:///{str(tmp_h.resolve()).replace(os.sep, '/')}"
        # using 'load' instead of 'networkidle' saves ~500ms per PDF
        await page.goto(abs_url, wait_until="load")
        
        # Smart wait for diagrams
        mermaid_count = await page.locator(".mermaid").count()
        if mermaid_count > 0:
            if log_fn: log_fn(f"Waiting for {mermaid_count} diagrams to render...")
            try:
                await page.wait_for_function("""
                    () => {
                        const all = document.querySelectorAll('.mermaid');
                        const processed = document.querySelectorAll('.mermaid[data-processed="true"]');
                        const error = document.querySelectorAll('.mermaid-error');
                        return (processed.length + error.length) === all.length;
                    }
                """, timeout=10000)
                await page.wait_for_timeout(500) # Buffer for layout
            except Exception as e:
                if log_fn: log_fn(f"Warning: Timeout waiting for diagrams: {e}")
        else:
            if log_fn: log_fn("No diagrams detected, skipping wait.")
        if prog_fn: prog_fn(70)
        
        # Save Diagrams if enabled
        if settings.get("save_diagrams", False):
            elements = await page.locator(".mermaid").all()
            if elements:
                if log_fn: log_fn(f"Saving {len(elements)} diagrams to separate files...")
                out_dir = pdf_path.parent
                stem = pdf_path.stem
                for i, element in enumerate(elements):
                    d_path = out_dir / f"{stem}_diagram_{i+1}.png"
                    await element.screenshot(path=str(d_path))
                    if log_fn: log_fn(f"Saved diagram: {d_path}")

        opts = {"path": str(pdf_path.resolve()), "print_background": True}
        if u_height:
            h = await page.evaluate("document.body.scrollHeight")
            if log_fn: log_fn(f"Canvas: {v_w}px x {h}px")
            opts["width"] = f"{v_w}px"; opts["height"] = f"{h+100}px"; opts["margin"] = {"top":"0","bottom":"0","left":"0","right":"0"}
        else:
            opts["format"] = "A4"; opts["margin"] = {"top": "1cm", "bottom": "1cm", "left": "1cm", "right": "1cm"}
        
        await page.pdf(**opts)
        await browser.close()
    
    if not settings.get("save_html", False): 
        try: os.remove(tmp_h)
        except: pass

async def render_png_page(browser, md_path: Path, png_path: Path, settings: dict, log_fn=print, prog_fn=None) -> None:
    theme_name = settings.get("theme", "GitHub Light")
    if log_fn: log_fn(f"Rendering PNG ({theme_name}): {md_path.name}")
    
    md_text = await asyncio.get_running_loop().run_in_executor(None, md_path.read_text, "utf-8")
    html_content = create_html_content(md_text, settings)
    
    tmp_h = md_path.with_suffix(".tmp.html")
    await asyncio.get_running_loop().run_in_executor(None, tmp_h.write_text, html_content, "utf-8")
        
    # Use an extreme viewport and device scale for 24K resolution
    page = await browser.new_page(
        viewport={"width": 6000, "height": 6000},
        device_scale_factor=4
    )

    # Log console messages with prefix
    page.on("console", lambda msg: log_fn(f"BROWSER CONSOLE: {msg.text}"))
    page.on("pageerror", lambda exc: log_fn(f"BROWSER ERROR: {exc}"))

    abs_url = f"file:///{str(tmp_h.resolve()).replace(os.sep, '/')}"
    if log_fn: log_fn(f"Loading: {abs_url}")
    # using 'load' instead of 'networkidle' saves ~500ms
    await page.goto(abs_url, wait_until="load")

    # Wait for mermaid to finish rendering
    try:
        if log_fn: log_fn("Waiting for Mermaid SVG (60s timeout)...")

        # Check if mermaid blocks exist first to avoid 60s timeout on files without diagrams
        has_mermaid = await page.evaluate("() => document.querySelectorAll('.mermaid').length > 0")

        if not has_mermaid:
            if log_fn: log_fn("No mermaid diagrams found to wait for.")
        else:
            # Wait for either a successful render or an error message
            await page.wait_for_function("""
                () => document.querySelector('.mermaid svg') ||
                        document.querySelector('.mermaid-error') ||
                        document.querySelector('.mermaid[data-processed="true"]')
            """, timeout=60000)
        
        # Check for error elements or "Syntax error" in SVG
        is_error = await page.evaluate("""
            () => {
                if (document.querySelector('.mermaid-error')) return true;
                const svg = document.querySelector('.mermaid svg');
                if (svg && (svg.textContent.includes('Syntax error') || svg.id.includes('error'))) return true;
                // Some versions use data-processed="error" (hypothetical, but safe to check)
                if (document.querySelector('.mermaid[data-processed="error"]')) return true;
                return false;
            }
        """)

        if is_error:
            error_msg = await page.evaluate("""
                () => {
                    const errEl = document.querySelector('.mermaid-error');
                    if (errEl) return errEl.innerText;
                    const svg = document.querySelector('.mermaid svg');
                    if (svg) return svg.textContent;
                    return "Unknown Mermaid Error";
                }
            """)
            # Standardized error reporting for terminal detection
            clean_msg = error_msg.strip().split('\n')[0] # Get just the first line
            if log_fn:
                log_fn(f"\n[!] MERMAID RENDER FAILURE [!]")
                log_fn(f"Reason: {clean_msg}")
                log_fn(f"Status: ABORTED\n")
            
            await page.close()
            if "--gallery" not in sys.argv:
                try: os.remove(tmp_h)
                except: pass
            sys.exit(1)

        await page.wait_for_timeout(2000) # Final stabilization
    except Exception as e:
        if log_fn: log_fn(f"Timeout or Error: {e}")
        # Check if it was a timeout but maybe it still rendered
        has_svg = await page.evaluate("() => document.querySelectorAll('.mermaid svg').length > 0")
        if not has_svg:
            if log_fn: log_fn("FAILED: No SVG generated and no explicit error detected. Probably a silent crash.")
            await page.close()
            sys.exit(1)
    
    # Get the first mermaid diagram
    element = await page.query_selector(".mermaid")
    if element:
        # Clip to the element size
        await element.screenshot(path=str(png_path.resolve()), scale="device", omit_background=False)
        if log_fn: log_fn(f"Created: {png_path.resolve()}")
    else:
        if log_fn: log_fn("Error: No Mermaid diagram found to capture.")

    await page.close()

    # KEEP tmp_h for debugging in gallery mode
    if "--gallery" not in sys.argv:
        try: os.remove(tmp_h)
        except: pass

async def generate_png_core(md_path: Path, png_path: Path, settings: dict, log_fn=print, prog_fn=None, browser=None) -> None:
    if browser:
        await render_png_page(browser, md_path, png_path, settings, log_fn, prog_fn)
    else:
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            await render_png_page(browser, md_path, png_path, settings, log_fn, prog_fn)
            await browser.close()

async def generate_docx_core(md_path: Path, docx_path: Path, log_fn=print, prog_fn=None, settings: dict=None) -> None:
    if log_fn: log_fn(f"Converting to DOCX: {md_path.name}")
    if prog_fn: prog_fn(10)
    
    # Check for pandoc
    global _PANDOC_AVAILABLE
    if _PANDOC_AVAILABLE is None:
        try:
            proc = await asyncio.create_subprocess_exec("pandoc", "--version", stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL)
            await proc.wait()
            if proc.returncode != 0:
                raise subprocess.CalledProcessError(proc.returncode, ["pandoc", "--version"])
            _PANDOC_AVAILABLE = True
        except FileNotFoundError:
            _PANDOC_AVAILABLE = False

    if _PANDOC_AVAILABLE is False:
        raise RuntimeError("Pandoc not found. Please install pandoc to export to DOCX.")
    
    # Determine Theme Colors for Alerts
    theme_name = settings.get("theme", "GitHub Light") if settings else "GitHub Light"
    if theme_name not in THEMES: theme_name = "GitHub Light"
    t = THEMES[theme_name]
    
    # Define Alert Styles based on Theme
    # Note: Pandoc handles minimal CSS on tables. We use border-left and background.
    alert_styles = {
        "NOTE": {"color": "#0969da", "bg": t['secondary'], "icon": "ℹ️"},
        "TIP": {"color": "#1f883d", "bg": t['secondary'], "icon": "💡"},
        "IMPORTANT": {"color": "#8250df", "bg": t['secondary'], "icon": "📢"},
        "WARNING": {"color": "#bf8700", "bg": t['secondary'], "icon": "⚠️"},
        "CAUTION": {"color": "#cf222e", "bg": t['secondary'], "icon": "🛑"}
    }
    
    # Override for Dark Modes to ensure visibility
    if "Dark" in theme_name or "Dracula" in theme_name or "Cyberpunk" in theme_name or "Obsidian" in theme_name or "Monokai" in theme_name:
         alert_styles["NOTE"]["color"] = "#58a6ff"
         alert_styles["TIP"]["color"] = "#3fb950"
         alert_styles["IMPORTANT"]["color"] = "#a371f7"
         alert_styles["WARNING"]["color"] = "#d29922"
         alert_styles["CAUTION"]["color"] = "#f85149"

    if prog_fn: prog_fn(20)

    try:
        md_text = await asyncio.get_running_loop().run_in_executor(None, md_path.read_text, "utf-8")
    except UnicodeDecodeError:
        raise ValueError(f"The file '{md_path.name}' is not a valid text file. Please ensure you are converting a Markdown (.md) file, not a binary file like PDF or Image.")
    
    # --- PROCESS ALERTS ---
    # Regex to capture > [!TYPE] ... content ...
    # We iterate line by line to handle the quote blocks correctly
    lines = md_text.split('\n')
    processed_lines = []
    in_alert = False
    alert_type = None
    alert_content = []

    for line in lines:
        # Check for alert header with flexible whitespace
        # matches: > [!NOTE],   > [!NOTE], >[!NOTE]
        match = ALERT_PATTERN.match(line)
        if match:
            # If we were already in an alert, close it first
            if in_alert:
                style = alert_styles.get(alert_type.upper(), alert_styles["NOTE"])
                c_html = "<br/>".join(alert_content)
                html_table = f'<table style="width:100%; border-left: 5px solid {style["color"]}; background-color: {style["bg"]}; margin-bottom: 10px;"><tr><td style="padding: 10px;"><strong>{style["icon"]} {alert_type.upper()} - </strong><br/>{c_html}</td></tr></table>'
                processed_lines.append(html_table)
                processed_lines.append("") # Ensure separation
                alert_content = []
            
            in_alert = True
            alert_type = match.group(1).upper()
            continue
            
        if in_alert:
            # Check if line continues the blockquote
            if line.strip().startswith(">"):
                # Remove the first > and stripping leading spaces
                # Be careful not to strip too much indentation from content
                content = line.strip()[1:]
                if content.startswith(" "): content = content[1:]
                alert_content.append(content)
            else:
                # End of alert block
                style = alert_styles.get(alert_type.upper(), alert_styles["NOTE"])
                c_html = "<br/>".join(alert_content)
                html_table = f'<table style="width:100%; border-left: 5px solid {style["color"]}; background-color: {style["bg"]}; margin-bottom: 10px;"><tr><td style="padding: 10px; color: {t["txt"]};"><strong>{style["icon"]} {alert_type.upper()} - </strong><br/>{c_html}</td></tr></table>'
                processed_lines.append(html_table)
                processed_lines.append("") # Spacer
                in_alert = False
                alert_content = []
                processed_lines.append(line)
        else:
            processed_lines.append(line)
            
    # Flush pending alert at end of file
    if in_alert:
        style = alert_styles.get(alert_type.upper(), alert_styles["NOTE"])
        c_html = "<br/>".join(alert_content)
        html_table = f'<table style="width:100%; border-left: 5px solid {style["color"]}; background-color: {style["bg"]}; margin-bottom: 10px;"><tr><td style="padding: 10px; color: {t["txt"]};"><strong>{style["icon"]} {alert_type.upper()} - </strong><br/>{c_html}</td></tr></table>'
        processed_lines.append(html_table)
        processed_lines.append("")
        
    md_text = "\n".join(processed_lines)
    
    mermaid_blocks = list(MERMAID_PATTERN.finditer(md_text))
    
    temp_images = []
    temp_files_to_cleanup = []
    
    if mermaid_blocks:
        if log_fn: log_fn(f"Found {len(mermaid_blocks)} diagrams. Rendering...")
        if prog_fn: prog_fn(30)
        
        # Override settings for images to use the selected Theme
        img_settings = settings.copy() if settings else {"theme": "GitHub Light", "mermaid_enabled": True, "content_width": 800}
        img_settings["mermaid_enabled"] = True
        
        html_content = create_html_content(md_text, img_settings)
        
        tmp_h = md_path.with_suffix(f".{uuid.uuid4()}.tmp.html")
        temp_files_to_cleanup.append(tmp_h)
        with open(tmp_h, "w", encoding="utf-8") as f:
            f.write(html_content)
            
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page(device_scale_factor=2) # Higher DPI for docs
            abs_url = f"file:///{str(tmp_h.resolve()).replace(os.sep, '/')}"
            await page.goto(abs_url, wait_until="load")
            
            # Smart wait for diagrams
            try:
                await page.wait_for_function("""
                    () => {
                        const all = document.querySelectorAll('.mermaid');
                        const processed = document.querySelectorAll('.mermaid[data-processed="true"]');
                        const error = document.querySelectorAll('.mermaid-error');
                        return (processed.length + error.length) === all.length;
                    }
                """, timeout=10000)
                await page.wait_for_timeout(500) # Buffer for layout
            except Exception as e:
                if log_fn: log_fn(f"Warning: Timeout waiting for diagrams: {e}")

            elements = await page.locator(".mermaid").all()
            
            if len(elements) != len(mermaid_blocks):
                 if log_fn: log_fn(f"Warning: Block count ({len(mermaid_blocks)}) != Element count ({len(elements)})")
            
            for i, (block, element) in enumerate(zip(mermaid_blocks, elements)):
                 img_path = md_path.parent / f"diagram_{uuid.uuid4()}.png"
                 await element.screenshot(path=str(img_path))
                 temp_images.append(img_path)
                 temp_files_to_cleanup.append(img_path)

                 # Save to output if enabled
                 if settings and settings.get("save_diagrams", False):
                     try:
                         d_out = docx_path.parent / f"{docx_path.stem}_diagram_{i+1}.png"
                         shutil.copy2(img_path, d_out)
                         if log_fn: log_fn(f"Saved diagram: {d_out}")
                     except Exception as e:
                         if log_fn: log_fn(f"Failed to save diagram png: {e}")

                 if log_fn: log_fn(f"Captured diagram {i+1}")

            await browser.close()
            
        # Replace blocks in MD text with images
        # Do it in reverse order to not mess up indices
        modified_md = md_text
        for i in range(len(mermaid_blocks) - 1, -1, -1):
            if i < len(temp_images):
                match = mermaid_blocks[i]
                img_path = temp_images[i]
                rel_path = img_path.name # Pandoc will resolve relative to cwd or we give abs
                # Using absolute path for safety since we might run pandoc from anywhere
                abs_img_path = str(img_path.resolve()).replace("\\", "/")
                replacement = f"![Diagram]({abs_img_path})"
                modified_md = modified_md[:match.start()] + replacement + modified_md[match.end():]
                
    else:
        modified_md = md_text

    if prog_fn: prog_fn(60)
    
    # Save modified markdown
    tmp_md = md_path.with_suffix(f".{uuid.uuid4()}.tmp.md")
    temp_files_to_cleanup.append(tmp_md)
    tmp_md.write_text(modified_md, encoding="utf-8")
    
    cmd = ["pandoc", str(tmp_md), "-o", str(docx_path)]
    
    if log_fn: log_fn(f"Running pandoc...")
    proc = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    stdout, stderr = await proc.communicate()
    
    # Cleanup
    for p in temp_files_to_cleanup:
        try:
            if p.exists(): os.remove(p)
        except: pass
    
    if proc.returncode != 0:
        raise RuntimeError(f"Pandoc failed: {stderr.decode()}")
        
    if prog_fn: prog_fn(100)
    if log_fn: log_fn(f"Created: {docx_path.name}")



# --- Textual GUI Wrapper ---
if HAS_TEXTUAL:
    class HelpScreen(ModalScreen):
        BINDINGS = [Binding("escape", "dismiss", "Close"), Binding("f1", "dismiss", "Close")]
        def compose(self) -> ComposeResult:
            yield Container(Static("[b]⌨️ Keyboard Shortcuts[/b]\n"), Static("[cyan]Ctrl+O[/] Browse\n[cyan]Ctrl+R[/] Convert\n[cyan]Ctrl+P[/] Open PDF\n[cyan]F1[/] Help"), Rule(), id="help-dialog")
        CSS = "#help-dialog { width: 50; padding: 2; background: #1a1a1a; border: round #555; }"

    class MarkdownToPdfApp(App):
        CSS = """
        Screen { background: #0d1117; }
        #app-header { dock: top; height: 1; background: #161b22; color: #58a6ff; text-align: center; }
        .section { background: #161b22; border: solid #30363d; padding: 0 1; margin-bottom: 1; }
        .row { height: 3; align: left middle; }
        .row Label { width: 18; }
        .row Input { width: 1fr; border: solid #30363d; }
        #log-area { height: 20%; min-height: 3; max-height: 10; background: #010409; border-top: solid #30363d; }
        #button-bar { dock: bottom; height: 3; align: center middle; background: #161b22; }
        #convert-btn { background: #238636; color: white; width: 22; margin-left: 1; }
        #docx-btn { background: #1f6feb; color: white; width: 22; margin-left: 1; }
        #preview-controls { height: 3; align: right middle; padding-right: 1; }
        #editor-toolbar { height: 3; margin-bottom: 1; align: left middle; background: #21262d; padding-left: 1; }
        .tool-btn { min-width: 5; margin-right: 1; height: 1; background: #30363d; border: none; }
        .tool-btn:hover { background: #58a6ff; color: #161b22; }
        .icon-btn { min-width: 5; margin-left: 1; background: #30363d; border: none; }
        .icon-btn:hover { background: #58a6ff; color: #161b22; }
        """
        BINDINGS = [
            Binding("ctrl+o", "browse_file", "Browse"),
            Binding("ctrl+r", "convert", "PDF"),
            Binding("ctrl+d", "convert_docx", "DOCX"),
            Binding("ctrl+p", "open_pdf", "Open PDF"),
            Binding("f1", "show_help", "Help")
        ]

        def __init__(self, cli_file=None, paste_content=None):
            super().__init__(); self.cli_file = cli_file; self.paste_content = paste_content; self.settings = load_settings(); self.recent_files = load_recent_files(); self.last_output_path = None; self.use_paste_source = bool(paste_content)

        def update_file_preview(self, filepath: str) -> None:
            try:
                # Reset container to just text if needed
                container = self.query_one("#md-view", VerticalScroll)

                # Check if we need to reset the view (if it's not just the standard markdown widget)
                should_reset = True
                if len(container.children) == 1:
                    child = container.children[0]
                    if isinstance(child, Markdown) and child.id == "md-preview":
                        should_reset = False

                if should_reset:
                    container.remove_children()
                    container.mount(Markdown(id="md-preview"))

                path = Path(filepath).resolve()
                if path.exists() and path.is_file():
                    # Optimized reading: only read first 20k chars to prevent UI freeze on large files
                    with open(path, "r", encoding="utf-8") as f:
                        content = f.read(20001)
                    if len(content) > 20000:
                        content = content[:20000] + "\n\n...(Preview truncated)..."
                    self.query_one("#md-preview", Markdown).update(content)
                elif not filepath or not filepath.strip():
                    welcome_msg = """
# 👋 Welcome to MDPDFM Pro!

No file is currently selected.

**To get started:**
1. Enter a file path in the **Input** field above.
2. Or click **Browse** to select a file.
3. Or switch to the **Paste & Preview** tab to type Markdown directly.

**Pro Tip:** Press `Ctrl+O` to quickly browse for files.
"""
                    self.query_one("#md-preview", Markdown).update(welcome_msg)
                else:
                    error_msg = f"""
# ⚠️ File Not Found

The file `{filepath}` could not be found.

**Suggestions:**
- Check the file path for typos.
- Ensure the file exists on your system.
- Use the **Browse** button to locate the file safely.
"""
                    self.query_one("#md-preview", Markdown).update(error_msg)
            except Exception:
                pass # Fail silently or log

        def compose(self) -> ComposeResult:
            yield Static("MDPDFM PRO v3.0", id="app-header")
            with TabbedContent():
                with TabPane("🛠️ SETTINGS"):
                    with VerticalScroll():
                        with Container(classes="section"):
                            yield Static("📁 FILES")
                            with Horizontal(classes="row"):
                                yield Label("Input:"); yield Input(id="md-input", placeholder="Select file or enter path..."); yield Button("Browse", id="browse-btn", tooltip="Select a Markdown file to convert")
                            with Horizontal(classes="row"):
                                yield Label("Output Folder:"); yield Input(value=self.settings.get("output_folder", ""), id="out-input", placeholder="Leave empty to save alongside input file"); yield Button("Browse", id="browse-out-btn", tooltip="Select destination folder for generated files"); yield Button("📂", id="btn-open-folder", classes="icon-btn", tooltip="Open Output Folder")
                            with Horizontal(classes="row"):
                                yield Label("Use Paste:"); yield Switch(value=False, id="source-switch", tooltip="Toggle between file input and text editor")
                        with Container(classes="section"):
                            yield Static("🎨 AESTHETICS")
                            with Horizontal(classes="row"):
                                yield Label("Theme:"); yield Select.from_values(list(THEMES.keys()), allow_blank=False, value=self.settings.get("theme", "GitHub Light"), id="theme-select", tooltip="Select color theme for PDF/DOCX output")
                        with Container(classes="section"):
                            yield Static("⚙️ OPTIONS")
                            with Horizontal(classes="row"):
                                yield Label("A4 Lock:"); yield Switch(value=self.settings.get("a4_fixed_width", True), id="a4-width-switch", tooltip="Constrain content width to A4 paper size (800px)")
                            with Horizontal(classes="row"):
                                yield Label("Single Pg:"); yield Switch(value=self.settings.get("unlimited_height", True), id="unlimited-height-switch", tooltip="Generate a continuous PDF without page breaks")
                            with Horizontal(classes="row"):
                                yield Label("Save Diags:"); yield Switch(value=self.settings.get("save_diagrams", False), id="save-diags-switch", tooltip="Save extracted Mermaid diagrams as separate PNG files")
                    with Vertical(id="log-area"):
                        yield ProgressBar(id="progress-bar", show_eta=False); yield RichLog(id="log", markup=True)
                with TabPane("Paste & Preview"):
                    with Horizontal(id="editor-toolbar", classes="toolbar"):
                        yield Button("Bold", id="btn-bold", classes="tool-btn", tooltip="Bold (**text**)")
                        yield Button("Italic", id="btn-italic", classes="tool-btn", tooltip="Italic (*text*)")
                        yield Button("Code", id="btn-code", classes="tool-btn", tooltip="Code (`text`)")
                        yield Button("List", id="btn-list", classes="tool-btn", tooltip="List (- item)")
                        yield Button("Link", id="btn-link", classes="tool-btn", tooltip="Link ([text](url))")
                        yield Button("H1", id="btn-h1", classes="tool-btn", tooltip="Heading 1 (# text)")
                        yield Button("H2", id="btn-h2", classes="tool-btn", tooltip="Heading 2 (## text)")
                        yield Button("H3", id="btn-h3", classes="tool-btn", tooltip="Heading 3 (### text)")

                    with Horizontal(id="preview-controls"):
                         yield Button("👁️ TUI Preview", id="toggle-view-btn", disabled=True, variant="primary")
                         yield Button("🌐 Browser Preview", id="browser-preview-btn", variant="default")
                         if HAS_PIXELS:
                             yield Button("🖼️ Render Graphs", id="tui-render-btn", variant="default")
                    with ContentSwitcher(initial="md-view", id="preview-switcher"):
                        with VerticalScroll(id="md-view"):
                            yield Markdown(id="md-preview")
                        yield TextArea(id="paste-area")
            with Horizontal(id="button-bar"): 
                yield Button("📄 Open File", id="open-btn", disabled=True, tooltip="Open the last generated PDF/DOCX file")
                yield Button("📝 Export DOCX", id="docx-btn", tooltip="Convert the current Markdown to a Word document")
                yield Button("▶ GENERATE PDF", id="convert-btn", tooltip="Convert the current Markdown to a PDF file")
            yield Footer()

        def on_mount(self):
            if self.cli_file:
                self.query_one("#md-input", Input).value = str(Path(self.cli_file).resolve())
                self.update_file_preview(self.cli_file)
            else:
                self.update_file_preview("")

            if self.paste_content:
                self.query_one("#paste-area", TextArea).text = self.paste_content
                self.query_one("#source-switch", Switch).value = True
        
        def on_select_changed(self, event: Select.Changed):
            if event.select.id == "theme-select":
                self.settings["theme"] = str(event.value)
                save_settings(self.settings)

        def on_switch_changed(self, event: Switch.Changed):
            if event.switch.id == "a4-width-switch": self.settings["a4_fixed_width"] = event.value
            elif event.switch.id == "unlimited-height-switch": self.settings["unlimited_height"] = event.value
            elif event.switch.id == "save-diags-switch": self.settings["save_diagrams"] = event.value
            elif event.switch.id == "source-switch":
                self.use_paste_source = event.value
                toggle_btn = self.query_one("#toggle-view-btn", Button)
                switcher = self.query_one("#preview-switcher", ContentSwitcher)

                if event.value:
                    # Paste Mode
                    switcher.current = "paste-area"
                    toggle_btn.disabled = False
                    toggle_btn.label = "👁️ TUI Preview"
                    toggle_btn.variant = "primary"
                else:
                    # File Mode
                    switcher.current = "md-view"
                    toggle_btn.disabled = True
                    # Update preview when switching back to file mode
                    self.update_file_preview(self.query_one("#md-input", Input).value)
            save_settings(self.settings)

        def on_input_submitted(self, event: Input.Submitted):
            if event.input.id == "md-input":
                self.update_file_preview(event.value)

        def on_input_changed(self, event: Input.Changed):
             if event.input.id == "out-input":
                 self.settings["output_folder"] = event.value
                 save_settings(self.settings)

        def handle_editor_button(self, btn_id: str) -> None:
            ta = self.query_one("#paste-area", TextArea)
            sel = ta.selection
            text = ta.selected_text

            if btn_id == "btn-bold":
                ta.replace(f"**{text}**", sel.start, sel.end)
            elif btn_id == "btn-italic":
                ta.replace(f"*{text}*", sel.start, sel.end)
            elif btn_id == "btn-code":
                if "\n" in text:
                    ta.replace(f"```\n{text}\n```", sel.start, sel.end)
                else:
                    ta.replace(f"`{text}`", sel.start, sel.end)
            elif btn_id == "btn-link":
                ta.replace(f"[{text}](url)", sel.start, sel.end)
            elif btn_id == "btn-list":
                lines = text.split('\n')
                new_lines = [f"- {line}" for line in lines]
                ta.replace("\n".join(new_lines), sel.start, sel.end)
            elif btn_id == "btn-h1":
                ta.replace(f"# {text}", sel.start, sel.end)
            elif btn_id == "btn-h2":
                ta.replace(f"## {text}", sel.start, sel.end)
            elif btn_id == "btn-h3":
                ta.replace(f"### {text}", sel.start, sel.end)

            ta.focus()

        async def on_button_pressed(self, event: Button.Pressed):
            if event.button.id and event.button.id.startswith("btn-"):
                self.handle_editor_button(event.button.id)
                return

            if event.button.id == "convert-btn": self.action_convert()
            elif event.button.id == "docx-btn": self.action_convert_docx()
            elif event.button.id == "open-btn": self.action_open_pdf()
            elif event.button.id == "browse-btn": self.action_browse_file()
            elif event.button.id == "browse-out-btn":
                d = open_folder_dialog()
                if d: self.query_one("#out-input", Input).value = d
            elif event.button.id == "btn-open-folder":
                out_val = self.query_one("#out-input", Input).value.strip()
                target_dir = None

                if out_val:
                    target_dir = Path(out_val)
                elif self.query_one("#md-input", Input).value.strip():
                    try:
                        inp = Path(self.query_one("#md-input", Input).value.strip())
                        if inp.exists():
                            target_dir = inp.parent
                    except Exception:
                        pass

                if not target_dir:
                     target_dir = Path(self.settings.get("output_folder", str(Path.home() / "Documents")))

                if target_dir and target_dir.exists():
                     try:
                        open_file_externally(str(target_dir))
                        self.query_one("#log", RichLog).write(f"[green]Opened folder: {target_dir}[/]")
                     except Exception as e:
                        self.query_one("#log", RichLog).write(f"[red]Error opening folder: {e}[/]")
                else:
                     self.query_one("#log", RichLog).write(f"[yellow]Folder not found: {target_dir}[/]")
            elif event.button.id == "browser-preview-btn":
                self.action_browser_preview()
            elif event.button.id == "tui-render-btn":
                self.action_render_tui()
            elif event.button.id == "toggle-view-btn":
                switcher = self.query_one("#preview-switcher", ContentSwitcher)
                btn = event.button
                if switcher.current == "paste-area":
                    # Switch to Preview
                    content = self.query_one("#paste-area", TextArea).text

                    # Reset view to text only first
                    container = self.query_one("#md-view", VerticalScroll)

                    should_reset = True
                    if len(container.children) == 1:
                        child = container.children[0]
                        if isinstance(child, Markdown) and child.id == "md-preview":
                            should_reset = False

                    if should_reset:
                        container.remove_children()
                        container.mount(Markdown(id="md-preview"))

                    self.query_one("#md-preview", Markdown).update(content)
                    switcher.current = "md-view"
                    btn.label = "✏️ Back to Edit"
                    btn.variant = "default"
                else:
                    # Switch back to Edit
                    switcher.current = "paste-area"
                    btn.label = "👁️ TUI Preview"
                    btn.variant = "primary"

        def action_browse_file(self):
            f = open_file_dialog()
            if f:
                self.query_one("#md-input", Input).value = f
                self.update_file_preview(f)

        def action_convert(self):
            self.run_conversion(fmt="pdf")

        def action_convert_docx(self):
            self.run_conversion(fmt="docx")

        def action_show_help(self):
            self.push_screen(HelpScreen())

        def action_open_pdf(self):
            if self.last_output_path and self.last_output_path.exists():
                try:
                    open_file_externally(str(self.last_output_path))
                except Exception as e:
                    self.query_one("#log", RichLog).write(f"[red]Error opening file: {e}[/]")

        def action_browser_preview(self):
            content = ""
            if self.use_paste_source:
                content = self.query_one("#paste-area", TextArea).text
            else:
                path_str = self.query_one("#md-input", Input).value
                if path_str:
                    path = Path(path_str).resolve()
                    if path.exists():
                        content = path.read_text(encoding="utf-8")

            if not content:
                self.query_one("#log", RichLog).write("[yellow]Nothing to preview.[/]")
                return

            self.worker_browser_preview(content)

        @work(thread=True)
        def worker_browser_preview(self, content: str):
             try:
                temp_dir = Path(tempfile.mkdtemp())
                processed_content = process_resources(content, temp_dir)
                html = create_html_content(processed_content, self.settings)
                preview_path = temp_dir / "preview.html"
                preview_path.write_text(html, encoding="utf-8")
                webbrowser.open(f"file://{preview_path.resolve()}")
                self.call_from_thread(lambda: self.query_one("#log", RichLog).write("[green]Browser preview opened.[/]"))
             except Exception as e:
                self.call_from_thread(lambda: self.query_one("#log", RichLog).write(f"[red]Preview Error: {e}[/]"))

        def action_render_tui(self):
            content = ""
            if self.use_paste_source:
                content = self.query_one("#paste-area", TextArea).text
            else:
                path_str = self.query_one("#md-input", Input).value
                if path_str:
                    path = Path(path_str).resolve()
                    if path.exists():
                        content = path.read_text(encoding="utf-8")

            if not content:
                 self.query_one("#log", RichLog).write("[yellow]Nothing to render.[/]")
                 return

            # Check if there are mermaid blocks
            if "mermaid" not in content and "```" not in content:
                 self.query_one("#log", RichLog).write("[yellow]No code blocks found to render.[/]")
                 return

            self.query_one("#log", RichLog).write("[cyan]Rendering diagrams for TUI... please wait.[/]")

            # Switch to preview view if not already
            if self.use_paste_source:
                switcher = self.query_one("#preview-switcher", ContentSwitcher)
                switcher.current = "md-view"
                self.query_one("#toggle-view-btn", Button).label = "✏️ Back to Edit"
                self.query_one("#toggle-view-btn", Button).variant = "default"

            self.worker_render_tui(content)

        @work(thread=True)
        def worker_render_tui(self, content: str):
             try:
                temp_dir = Path(tempfile.mkdtemp())
                processed_content = process_resources(content, temp_dir)

                # Identify mermaid blocks
                parts = MERMAID_PATTERN.split(processed_content)

                # If only 1 part, no mermaid
                if len(parts) < 2:
                    self.call_from_thread(lambda: self.query_one("#log", RichLog).write("[yellow]No mermaid blocks found to render.[/]"))
                    return

                # Render ALL to get images
                html = create_html_content(processed_content, self.settings)
                tmp_h = temp_dir / "render.html"
                tmp_h.write_text(html, encoding="utf-8")

                images = []

                async def capture():
                     async with async_playwright() as p:
                        browser = await p.chromium.launch()
                        page = await browser.new_page(device_scale_factor=2)
                        await page.goto(f"file://{tmp_h.resolve()}", wait_until="load")

                        try:
                            await page.wait_for_selector(".mermaid svg", timeout=5000)
                            await page.wait_for_timeout(500)
                        except: pass

                        elements = await page.locator(".mermaid").all()
                        for i, el in enumerate(elements):
                            p = temp_dir / f"diag_{i}.png"
                            await el.screenshot(path=str(p))
                            images.append(p)
                        await browser.close()

                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(capture())

                def update_ui():
                    container = self.query_one("#md-view", VerticalScroll)
                    container.remove_children()

                    img_idx = 0
                    for i, part in enumerate(parts):
                        if i % 2 == 0:
                            # Text
                            if part.strip():
                                container.mount(Markdown(part))
                        else:
                            # Mermaid Code - replace with image if available
                            if img_idx < len(images):
                                img_path = images[img_idx]
                                try:
                                    img = Image.open(img_path)

                                    # Calculate resize dimensions to fit in terminal
                                    # Get available width (console width - padding)
                                    console_width = self.app.console.size.width
                                    max_width = max(40, console_width - 10) # 10 chars padding

                                    w, h = img.size
                                    aspect = h / w

                                    target_w = max_width
                                    target_h = int(target_w * aspect)

                                    img.thumbnail((target_w, target_h * 2), Image.Resampling.LANCZOS)
                                    pix = Pixels.from_image(img)

                                    container.mount(Center(Static(pix)))
                                    img_idx += 1
                                except Exception as e:
                                    container.mount(Static(f"[red]Error loading image: {e}[/]"))
                            else:
                                container.mount(Static("[red]Image missing[/]"))

                    self.query_one("#log", RichLog).write("[green]TUI Render Complete![/]")

                self.call_from_thread(update_ui)

             except Exception as e:
                self.call_from_thread(lambda: self.query_one("#log", RichLog).write(f"[red]TUI Render Error: {e}[/]"))

        @work(exclusive=True, thread=True)
        def run_conversion(self, fmt="pdf") -> None:
            log_w = self.query_one("#log", RichLog)
            def log(m): self.call_from_thread(lambda: log_w.write(m))
            def prog(v): self.call_from_thread(lambda: self.query_one("#progress-bar", ProgressBar).update(progress=v))
            def enable_btn(): self.query_one("#open-btn", Button).disabled = False

            try:
                if self.use_paste_source:
                    text_content = self.query_one("#paste-area", TextArea).text
                    if not text_content.strip():
                        log("[yellow]⚠️  Paste area is empty![/]")
                        return

                    if text_content.strip().startswith("graph T"):
                         if not text_content.strip().startswith("```"):
                             text_content = f"```mermaid\n{text_content}\n```"

                    # Determine Output Path
                    out_dir_str = self.query_one("#out-input", Input).value.strip()
                    if out_dir_str:
                        out_dir = Path(out_dir_str)
                    else:
                        out_dir = Path(self.settings.get("output_folder", str(Path.home() / "Documents")))
                    out_dir.mkdir(parents=True, exist_ok=True)

                    filename = f"pasted_export_{uuid.uuid4().hex[:8]}.{fmt}"
                    opath = out_dir / filename

                    # Create temp dir for resources
                    with tempfile.TemporaryDirectory() as temp_dir:
                        temp_path = Path(temp_dir)
                        log(f"Processing resources in temporary env...")
                        processed_text = process_resources(text_content, temp_path)

                        # Write processed markdown to temp file
                        tmp_md = temp_path / f"source_{uuid.uuid4()}.md"
                        tmp_md.write_text(processed_text, encoding="utf-8")

                        ipath = tmp_md

                        if fmt == "docx":
                            loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(loop)
                            loop.run_until_complete(generate_docx_core(ipath, opath, log, prog, settings=self.settings))
                            log(f"[green]✓ DOCX Export Done: {str(opath)}[/]")
                        else:
                            loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(loop)
                            # Check for pure mermaid
                            if is_pure_mermaid(processed_text) and fmt != "docx":
                                # We can export to PNG if pure mermaid, but if user asked for PDF, give PDF.
                                # However, user said "we can offer a png".
                                # For now we stick to requested format.
                                pass

                            loop.run_until_complete(generate_pdf_core(ipath, opath, self.settings, log, prog))
                            log(f"[green]✓ PDF Export Done: {str(opath)}[/]")

                        self.last_output_path = opath
                        self.call_from_thread(enable_btn)

                else:
                    inp = self.query_one("#md-input", Input).value.strip()
                    if not inp:
                        log("[yellow]⚠️  Please select a markdown file first![/]")
                        self.call_from_thread(self.query_one("#md-input", Input).focus)
                        return
                    ipath = Path(inp).resolve()

                    # Determine output path
                    out_dir_str = self.query_one("#out-input", Input).value.strip()
                    if out_dir_str:
                        out_dir = Path(out_dir_str)
                        out_dir.mkdir(parents=True, exist_ok=True)
                        opath = out_dir / (ipath.stem + ("." + fmt))
                    else:
                        opath = ipath.with_suffix("." + fmt)

                    if fmt == "docx":
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        # Pass self.settings to ensure theme is used
                        loop.run_until_complete(generate_docx_core(ipath, opath, log, prog, settings=self.settings))
                        log(f"[green]✓ DOCX Export Done: {str(opath)}[/]")
                    else:
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        loop.run_until_complete(generate_pdf_core(ipath, opath, self.settings, log, prog))
                        log(f"[green]✓ PDF Export Done: {str(opath)}[/]")

                    self.last_output_path = opath
                    self.call_from_thread(enable_btn)
            except Exception as e: log(f"[red]Error: {e}[/]")

async def run_gallery_mode(md_path: Path) -> None:
    print("--- Gallery Mode: Generating for all themes ---")
    settings = load_settings()

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        for theme in THEMES.keys():
            settings["theme"] = theme
            gallery_path = md_path.parent / f"{md_path.stem}_{theme.lower().replace(' ', '_')}.png"
            # Pass the shared browser instance
            await generate_png_core(md_path, gallery_path, settings, browser=browser)
        await browser.close()
    print("Gallery generation complete.")

# --- Entry Point ---
def main():
    content_arg = None
    if "--content" in sys.argv:
        try:
            idx = sys.argv.index("--content")
            if idx + 1 < len(sys.argv):
                content_arg = sys.argv[idx + 1]
                del sys.argv[idx:idx+2]
        except ValueError:
            pass

    if len(sys.argv) > 1 or content_arg:
        if len(sys.argv) > 1 and sys.argv[1] in ["--help", "-h"]:
            print("Usage: python md_to_pdf_tui.py [input.md] [output] [flags]")
            print("Flags: --headless, --docx, --png, --gallery, --open, --light, --dark, --content 'markdown text'")
            return
        
        if "--headless" in sys.argv:
            print("--- MDPDFM Background Engine starting ---")
            
            temp_dir = None
            md_path = None

            try:
                if content_arg:
                    temp_dir = tempfile.mkdtemp()
                    temp_path = Path(temp_dir)
                    print("Processing content resources...")
                    processed_text = process_resources(content_arg, temp_path)
                    md_path = temp_path / f"content_{uuid.uuid4().hex[:8]}.md"
                    md_path.write_text(processed_text, encoding="utf-8")
                elif len(sys.argv) > 1 and not sys.argv[1].startswith("--"):
                    md_path = Path(sys.argv[1]).resolve()
                    if not md_path.exists():
                        print(f"Error: {md_path} not found")
                        sys.exit(1)
                else:
                    print("Error: No input file or content provided.")
                    sys.exit(1)

                pdf_path = None
                # Determine output path logic considering content_arg shifting
                potential_args = [a for a in sys.argv[1:] if not a.startswith("--")]

                if content_arg:
                    if potential_args:
                        pdf_path = Path(potential_args[0]).resolve()
                else:
                    if len(potential_args) > 1:
                         pdf_path = Path(potential_args[1]).resolve()

                is_docx = "--docx" in sys.argv or (pdf_path and pdf_path.suffix.lower() == ".docx")
                is_png = "--png" in sys.argv or "--gallery" in sys.argv or (pdf_path and pdf_path.suffix.lower() == ".png")

                # theme gallery mode
                if "--gallery" in sys.argv:
                    asyncio.run(run_gallery_mode(md_path))
                    return

                if not pdf_path:
                    ext = ".docx" if is_docx else (".png" if is_png else ".pdf")
                    if content_arg:
                        pdf_path = Path(f"output_{uuid.uuid4().hex[:8]}{ext}").resolve()
                    else:
                        pdf_path = md_path.with_suffix(ext)

                settings = load_settings()
                chosen_theme = None
                for t in THEMES.keys():
                    slug = "--" + t.lower().replace(" ", "-")
                    if slug in sys.argv:
                        chosen_theme = t
                        break

                if chosen_theme:
                    settings["theme"] = theme_name = chosen_theme

                if is_docx:
                    asyncio.run(generate_docx_core(md_path, pdf_path, settings=settings))
                elif is_png:
                    asyncio.run(generate_png_core(md_path, pdf_path, settings=settings))
                else:
                    asyncio.run(generate_pdf_core(md_path, pdf_path, settings))

                print(f"Success: {pdf_path}")

                if "--open" in sys.argv:
                    print(f"Opening: {pdf_path}")
                    os.startfile(str(pdf_path.resolve()))
            finally:
                if temp_dir:
                    try: shutil.rmtree(temp_dir)
                    except: pass
                
            return

        if HAS_TEXTUAL:
            file_arg = None
            if len(sys.argv) > 1 and not sys.argv[1].startswith("--"):
                file_arg = sys.argv[1]
            MarkdownToPdfApp(cli_file=file_arg, paste_content=content_arg).run()
        else:
            print("Error: Textual not installed. Use --headless.")
    elif HAS_TEXTUAL:
        MarkdownToPdfApp(paste_content=content_arg).run()
    else:
        print("Usage: python md_to_pdf_tui.py [input.md] --headless")

if __name__ == "__main__":
    main()
