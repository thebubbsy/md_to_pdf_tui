import unittest
from textual.app import App, ComposeResult
from textual.widgets import Button, Footer
from textual.pilot import Pilot
import asyncio

# Import the class to test
try:
    from md_to_pdf_tui import HelpScreen, MarkdownToPdfApp, HAS_PIXELS
except ImportError:
    # If dependencies are missing, this will fail
    raise

class TestHelpScreen(unittest.IsolatedAsyncioTestCase):
    async def test_help_screen_structure(self):
        class TestApp(App):
            def compose(self) -> ComposeResult:
                yield HelpScreen()

        app = TestApp()
        async with app.run_test() as pilot:
            # Check for Footer
            footer = pilot.app.query("Footer")
            self.assertTrue(len(footer) > 0, "Footer should be present in HelpScreen")

            # Check for Close button
            close_btn = pilot.app.query("#dismiss-btn")
            self.assertTrue(len(close_btn) > 0, "Close button (#dismiss-btn) should be present")

            # Verify button properties
            btn = close_btn.first()
            self.assertEqual(str(btn.label), "Close")
            self.assertEqual(str(btn.tooltip), "Dismiss this help dialog")

            # Simulate button press to ensure no crash (though dismissing modal in test app might be tricky)
            await pilot.click("#dismiss-btn")
            await pilot.pause()

from textual.widgets import Switch

class TestTooltips(unittest.IsolatedAsyncioTestCase):
    async def test_dynamic_tooltips(self):
        app = MarkdownToPdfApp()
        async with app.run_test(size=(120, 40)) as pilot:
            # Wait for app to be ready
            await pilot.pause(1)

            # Switch to Paste & Preview tab
            app.query_one("TabbedContent").active = "tab-2"
            await pilot.pause(0.5)

            # Test initial tooltips
            if HAS_PIXELS:
                render_btn = app.query_one("#tui-render-btn", Button)
                self.assertEqual(str(render_btn.tooltip), "Render Mermaid diagrams in the terminal preview")

            browser_btn = app.query_one("#browser-preview-btn", Button)
            self.assertEqual(str(browser_btn.tooltip), "Open markdown preview in a web browser")

            # Test dynamic tooltips
            toggle_btn = app.query_one("#toggle-view-btn", Button)
            self.assertEqual(str(toggle_btn.tooltip), "Preview markdown rendering in the terminal")

            # Enable paste source
            app.query_one("#source-switch", Switch).value = True
            await pilot.pause(0.5)

            # Switch to preview mode
            await pilot.click("#toggle-view-btn")
            await pilot.pause(0.5)
            self.assertEqual(str(toggle_btn.tooltip), "Return to markdown editor")

            # Switch back to edit mode
            await pilot.click("#toggle-view-btn")
            await pilot.pause(0.5)
            self.assertEqual(str(toggle_btn.tooltip), "Preview markdown rendering in the terminal")

if __name__ == "__main__":
    unittest.main()
