"""
Markdown to PDF Converter TUI v2.8.2 Pro - Forensic Suite
The most feature-rich version ever. Zero-bullshit logic.
Now with background CLI mode for automated exports and high-contrast light-mode.
Added themes and png output to docx
"""

import asyncio
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

# Textual imports (only if needed)
try:
    from textual.app import App, ComposeResult, events
    from textual.containers import Container, Horizontal, Vertical, ScrollableContainer, VerticalScroll
    from textual.widgets import (
        Button, Footer, Header, Input, Label, RichLog, Static, 
        Select, Switch, ProgressBar, Rule, TabbedContent, TabPane, Markdown
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
        "a4_fixed_width": True
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

# --- Core Conversion Logic (Decoupled from TUI) ---
# --- Core Conversion Logic (Decoupled from TUI) ---
def create_html_content(md_text: str, settings: dict) -> str:
    theme_name = settings.get("theme", "GitHub Light")
    # Fallback if theme name not found
    if theme_name not in THEMES: theme_name = "GitHub Light"
    
    t_data = THEMES[theme_name]
    c_width = int(settings.get("content_width", 800))
    m_enabled = settings.get("mermaid_enabled", True)
    
    def mf(tokens, idx, options, env):
        t = tokens[idx]
        if t.info.strip() == "mermaid" and m_enabled:
            return f'<div class="m-wrap"><div class="mermaid">{t.content}</div></div>'
        return f"<pre><code>{t.content}</code></pre>"
    
    it = markdown_it.MarkdownIt().use(front_matter_plugin).use(footnote_plugin).enable("table")
    it.renderer.rules["fence"] = mf
    body = it.render(md_text)
    
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
        md_text = md_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        raise ValueError(f"The file '{md_path.name}' is not a valid text file. Please ensure you are converting a Markdown (.md) file, not a binary file like PDF.")
    if prog_fn: prog_fn(20)
    
    html_content = create_html_content(md_text, settings)
    if prog_fn: prog_fn(30)
    
    tmp_h = md_path.with_suffix(".tmp.html")
    with open(tmp_h, "w", encoding="utf-8") as f:
        f.write(html_content)
    if prog_fn: prog_fn(40)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        v_w = 800 if a4_width else 1200
        page = await browser.new_page(viewport={"width": v_w, "height": 1000})
        abs_url = f"file:///{str(tmp_h.resolve()).replace(os.sep, '/')}"
        await page.goto(abs_url, wait_until="networkidle")
        
        if log_fn: log_fn("Waiting for diagrams to render...")
        await page.wait_for_timeout(6000)
        if prog_fn: prog_fn(70)
        
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

async def generate_png_core(md_path: Path, png_path: Path, settings: dict, log_fn=print, prog_fn=None) -> None:
    theme_name = settings.get("theme", "GitHub Light")
    if log_fn: log_fn(f"Rendering PNG ({theme_name}): {md_path.name}")
    
    md_text = md_path.read_text(encoding="utf-8")
    html_content = create_html_content(md_text, settings)
    
    tmp_h = md_path.with_suffix(".tmp.html")
    with open(tmp_h, "w", encoding="utf-8") as f:
        f.write(html_content)
        
    async with async_playwright() as p:
        browser = await p.chromium.launch()
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
        await page.goto(abs_url, wait_until="networkidle")
        
        # Wait for mermaid to finish rendering
        try:
            if log_fn: log_fn("Waiting for Mermaid SVG (60s timeout)...")
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
                
                await browser.close()
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
                await browser.close()
                sys.exit(1)
        
        # Get the first mermaid diagram
        element = await page.query_selector(".mermaid")
        if element:
            # Clip to the element size
            await element.screenshot(path=str(png_path.resolve()), scale="device", omit_background=False)
            if log_fn: log_fn(f"Created: {png_path.name}")
        else:
            if log_fn: log_fn("Error: No Mermaid diagram found to capture.")
            
        await browser.close()
    
    # KEEP tmp_h for debugging in gallery mode
    if "--gallery" not in sys.argv:
        try: os.remove(tmp_h)
        except: pass

async def generate_docx_core(md_path: Path, docx_path: Path, log_fn=print, prog_fn=None, settings: dict=None) -> None:
    if log_fn: log_fn(f"Converting to DOCX: {md_path.name}")
    if prog_fn: prog_fn(10)
    
    # Check for pandoc
    try:
        subprocess.run(["pandoc", "--version"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except FileNotFoundError:
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
        md_text = md_path.read_text(encoding="utf-8")
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
        match = re.match(r"^\s*>\s*\[!(NOTE|TIP|IMPORTANT|WARNING|CAUTION)\]", line, re.IGNORECASE)
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
    
    # Update regex since we modified md_text
    mermaid_pattern = re.compile(r"^(?:`{3,}|~{3,})mermaid\s*\n(.*?)\n(?:`{3,}|~{3,})", re.DOTALL | re.MULTILINE)
    mermaid_blocks = list(mermaid_pattern.finditer(md_text))
    
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
            await page.goto(abs_url, wait_until="networkidle")
            
            # Wait specifically for mermaid to render
            try:
                await page.wait_for_selector(".mermaid svg", timeout=10000)
                # Extra safety buffer for animations/layout
                await page.wait_for_timeout(1500)
            except:
                if log_fn: log_fn("Warning: Timeout waiting for diagrams")

            elements = await page.locator(".mermaid").all()
            
            if len(elements) != len(mermaid_blocks):
                 if log_fn: log_fn(f"Warning: Block count ({len(mermaid_blocks)}) != Element count ({len(elements)})")
            
            for i, (block, element) in enumerate(zip(mermaid_blocks, elements)):
                 img_path = md_path.parent / f"diagram_{uuid.uuid4()}.png"
                 await element.screenshot(path=str(img_path))
                 temp_images.append(img_path)
                 temp_files_to_cleanup.append(img_path)
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
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    # Cleanup
    for p in temp_files_to_cleanup:
        try:
            if p.exists(): os.remove(p)
        except: pass
    
    if result.returncode != 0:
        raise RuntimeError(f"Pandoc failed: {result.stderr}")
        
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
        .section { background: #161b22; border: solid #30363d; padding: 1 2; margin-bottom: 1; }
        .row { height: 3; align: left middle; }
        .row Label { width: 18; }
        .row Input { width: 1fr; border: solid #30363d; }
        #log-area { height: 10; background: #010409; border-top: solid #30363d; }
        #button-bar { dock: bottom; height: 3; align: center middle; background: #161b22; }
        #convert-btn { background: #238636; color: white; width: 22; margin-left: 1; }
        #docx-btn { background: #1f6feb; color: white; width: 22; margin-left: 1; }
        """
        BINDINGS = [Binding("ctrl+o", "browse_file"), Binding("ctrl+r", "convert"), Binding("ctrl+d", "convert_docx"), Binding("ctrl+p", "open_pdf"), Binding("f1", "show_help")]

        def __init__(self, cli_file=None):
            super().__init__(); self.cli_file = cli_file; self.settings = load_settings(); self.recent_files = load_recent_files(); self.last_output_path = None

        def compose(self) -> ComposeResult:
            yield Static("MDPDFM PRO v3.0 - FORENSIC EDITION", id="app-header")
            with TabbedContent():
                with TabPane("🛠️ SETTINGS"):
                    with VerticalScroll():
                        with Container(classes="section"):
                            yield Static("📁 FILES")
                            with Horizontal(classes="row"):
                                yield Label("Input:"); yield Input(id="md-input", placeholder="Select file or enter path..."); yield Button("Browse", id="browse-btn")
                            with Horizontal(classes="row"):
                                yield Label("Output Folder:"); yield Input(value=self.settings.get("output_folder", ""), id="out-input", placeholder="Leave empty to save alongside input file"); yield Button("Browse", id="browse-out-btn")
                        with Container(classes="section"):
                            yield Static("🎨 AESTHETICS")
                            with Horizontal(classes="row"):
                                yield Label("Theme:"); yield Select.from_values(list(THEMES.keys()), allow_blank=False, value=self.settings.get("theme", "GitHub Light"), id="theme-select")
                        with Container(classes="section"):
                            yield Static("⚙️ OPTIONS")
                            with Horizontal(classes="row"):
                                yield Label("A4 Lock:"); yield Switch(value=self.settings.get("a4_fixed_width", True), id="a4-width-switch")
                            with Horizontal(classes="row"):
                                yield Label("Single Pg:"); yield Switch(value=self.settings.get("unlimited_height", True), id="unlimited-height-switch")
                    with Vertical(id="log-area"):
                        yield ProgressBar(id="progress-bar", show_eta=False); yield RichLog(id="log")
                with TabPane("👁️ PREVIEW"): yield Markdown(id="md-preview")
            with Horizontal(id="button-bar"): 
                yield Button("📄 Open PDF", id="open-btn")
                yield Button("📝 Export DOCX", id="docx-btn")
                yield Button("▶ GENERATE PDF", id="convert-btn")

        def on_mount(self):
            if self.cli_file: self.query_one("#md-input", Input).value = str(Path(self.cli_file).resolve())
        
        def on_select_changed(self, event: Select.Changed):
            if event.select.id == "theme-select":
                self.settings["theme"] = str(event.value)
                save_settings(self.settings)

        def on_switch_changed(self, event: Switch.Changed):
            if event.switch.id == "a4-width-switch": self.settings["a4_fixed_width"] = event.value
            elif event.switch.id == "unlimited-height-switch": self.settings["unlimited_height"] = event.value
            save_settings(self.settings)

        def on_input_changed(self, event: Input.Changed):
             if event.input.id == "out-input":
                 self.settings["output_folder"] = event.value
                 save_settings(self.settings)

        async def on_button_pressed(self, event: Button.Pressed):
            if event.button.id == "convert-btn": self.run_conversion(fmt="pdf")
            elif event.button.id == "docx-btn": self.run_conversion(fmt="docx")
            elif event.button.id == "open-btn": self.action_open_pdf()
            elif event.button.id == "browse-btn":
                f = open_file_dialog()
                if f: self.query_one("#md-input", Input).value = f
            elif event.button.id == "browse-out-btn":
                d = open_folder_dialog()
                if d: self.query_one("#out-input", Input).value = d

        def action_open_pdf(self):
            if self.last_output_path and self.last_output_path.exists(): os.startfile(str(self.last_output_path))

        @work(exclusive=True, thread=True)
        def run_conversion(self, fmt="pdf") -> None:
            log_w = self.query_one("#log", RichLog)
            def log(m): self.call_from_thread(lambda: log_w.write(m))
            def prog(v): self.call_from_thread(lambda: self.query_one("#progress-bar", ProgressBar).update(progress=v))
            try:
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
                    log(f"[green]✓ DOCX Export Done: {opath.name}[/]")
                else:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(generate_pdf_core(ipath, opath, self.settings, log, prog))
                    log(f"[green]✓ PDF Export Done: {opath.name}[/]")
                
                self.last_output_path = opath
            except Exception as e: log(f"[red]Error: {e}[/]")

# --- Entry Point ---
def main():
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        if arg in ["--help", "-h"]:
            print("Usage: python md_to_pdf_tui.py [input.md] [output] [flags]")
            print("Flags: --headless, --docx, --png, --gallery, --open, --light, --dark")
            return
        
        if "--headless" in sys.argv:
            print("--- MDPDFM Background Engine starting ---")
            md_path = Path(arg).resolve()
            if not md_path.exists():
                print(f"Error: {md_path} not found")
                sys.exit(1)
            
            pdf_path = None
            if len(sys.argv) > 2 and not sys.argv[2].startswith("--"):
                pdf_path = Path(sys.argv[2]).resolve()
            
            is_docx = "--docx" in sys.argv or (pdf_path and pdf_path.suffix.lower() == ".docx")
            is_png = "--png" in sys.argv or "--gallery" in sys.argv or (pdf_path and pdf_path.suffix.lower() == ".png")
            
            # theme gallery mode
            if "--gallery" in sys.argv:
                print("--- Gallery Mode: Generating for all themes ---")
                settings = load_settings()
                for theme in THEMES.keys():
                    settings["theme"] = theme
                    gallery_path = md_path.parent / f"{md_path.stem}_{theme.lower().replace(' ', '_')}.png"
                    asyncio.run(generate_png_core(md_path, gallery_path, settings))
                print("Gallery generation complete.")
                return

            if not pdf_path:
                ext = ".docx" if is_docx else (".png" if is_png else ".pdf")
                pdf_path = md_path.with_suffix(ext)

            settings = load_settings()
            # Try to match a theme from CLI args, otherwise fallback to settings or default
            chosen_theme = None
            if len(sys.argv) > 1:
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
                
            return

        if HAS_TEXTUAL:
            MarkdownToPdfApp(cli_file=arg).run()
        else:
            print("Error: Textual not installed. Use --headless.")
    elif HAS_TEXTUAL:
        MarkdownToPdfApp().run()
    else:
        print("Usage: python md_to_pdf_tui.py [input.md] --headless")

if __name__ == "__main__":
    main()
