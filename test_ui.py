import unittest
from textual.app import App, ComposeResult
from textual.widgets import Button, Footer
from textual.pilot import Pilot
import asyncio

# Import the class to test
try:
    from md_to_pdf_tui import HelpScreen
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

            # Simulate button press to ensure no crash (though dismissing modal in test app might be tricky)
            await pilot.click("#dismiss-btn")
            await pilot.pause()


try:
    from md_to_pdf_tui import MarkdownToPdfApp
except ImportError:
    pass
else:
    from textual.widgets import Switch

    class TestDynamicTooltips(unittest.IsolatedAsyncioTestCase):
        async def test_dynamic_tooltips(self):
            app = MarkdownToPdfApp()
            async with app.run_test() as pilot:
                # Give time to mount
                await pilot.pause(1)

                btn = app.query_one("#toggle-view-btn", Button)

                # Check initial tooltip
                self.assertEqual(str(btn.tooltip), "Preview Markdown rendering in TUI")

                # Switch to paste mode
                switch = app.query_one("#source-switch", Switch)
                switch.value = True
                await pilot.pause(1)

                # Tooltip should remain the same but button enabled
                self.assertEqual(str(btn.tooltip), "Preview Markdown rendering in TUI")
                self.assertFalse(btn.disabled)

                # Switch tab to Paste & Preview
                tabs = app.query_one("TabbedContent")
                tabs.active = "tab-2"
                await pilot.pause(1)

                # Click to switch to preview mode
                await pilot.click("#toggle-view-btn")
                await pilot.pause(1)

                # Tooltip should update
                self.assertEqual(str(btn.tooltip), "Return to editing Markdown text")

                # Click to switch back to edit mode
                await pilot.click("#toggle-view-btn")
                await pilot.pause(1)

                # Tooltip should revert
                self.assertEqual(str(btn.tooltip), "Preview Markdown rendering in TUI")

if __name__ == "__main__":
    unittest.main()
