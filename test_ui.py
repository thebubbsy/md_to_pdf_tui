import unittest
from textual.app import App, ComposeResult
from textual.widgets import Button, Footer, Switch, ContentSwitcher, TextArea
from textual.pilot import Pilot
import asyncio

try:
    from md_to_pdf_tui import HelpScreen, MarkdownToPdfApp
except ImportError:
    raise

class TestHelpScreen(unittest.IsolatedAsyncioTestCase):
    async def test_help_screen_structure(self):
        class TestApp(App):
            def compose(self) -> ComposeResult:
                yield HelpScreen()

        app = TestApp()
        async with app.run_test() as pilot:
            footer = pilot.app.query("Footer")
            self.assertTrue(len(footer) > 0, "Footer should be present in HelpScreen")

            close_btn = pilot.app.query("#dismiss-btn")
            self.assertTrue(len(close_btn) > 0, "Close button (#dismiss-btn) should be present")

            btn = close_btn.first()
            self.assertEqual(str(btn.label), "Close")

            await pilot.click("#dismiss-btn")
            await pilot.pause()

class TestTooltips(unittest.IsolatedAsyncioTestCase):
    async def test_dynamic_tooltips(self):
        app = MarkdownToPdfApp()
        async with app.run_test() as pilot:
            # Check initial state (File Mode)
            toggle_btn = app.query_one("#toggle-view-btn", Button)
            self.assertEqual(str(toggle_btn.tooltip), "Preview only available in Paste Mode")

            # Switch to Paste Mode
            switch = app.query_one("#source-switch", Switch)
            switch.value = True # Trigger on_switch_changed
            await pilot.pause()

            self.assertEqual(str(toggle_btn.tooltip), "Preview Markdown in terminal")

            # Trigger via action instead of raw event if possible
            btn = app.query_one("#toggle-view-btn", Button)
            class MockEvent:
                button = btn
            await app.on_button_pressed(MockEvent())
            await pilot.pause()

            self.assertEqual(str(toggle_btn.tooltip), "Return to markdown editor")

            # Click it again to go to edit
            await app.on_button_pressed(MockEvent())
            await pilot.pause()

            self.assertEqual(str(toggle_btn.tooltip), "Preview Markdown in terminal")

            # Put something in the text area so it doesn't return early
            ta = app.query_one("#paste-area", TextArea)
            ta.text = "test```mermaid\ngraph TD;\nA-->B;\n```"
            await pilot.pause()

            # Render TUI switches back to view
            app.action_render_tui()
            await pilot.pause()

            self.assertEqual(str(toggle_btn.tooltip), "Return to markdown editor")

if __name__ == "__main__":
    unittest.main()
