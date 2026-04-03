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
            self.assertEqual(str(btn.tooltip), "Close the help dialog")

            # Simulate button press to ensure no crash (though dismissing modal in test app might be tricky)
            await pilot.click("#dismiss-btn")
            await pilot.pause()

class TestDynamicTooltips(unittest.IsolatedAsyncioTestCase):
    async def test_toggle_view_btn_tooltip(self):
        try:
            from md_to_pdf_tui import MarkdownToPdfApp
        except ImportError:
            self.skipTest("Dependencies not met")

        app = MarkdownToPdfApp()
        async with app.run_test(size=(120, 30)) as pilot:
            await pilot.pause(1) # Wait for mount

            # Enable paste mode to activate preview button
            app.query_one("#source-switch").value = True
            await pilot.pause(1)

            btn = app.query_one("#toggle-view-btn", Button)
            self.assertEqual(str(btn.tooltip), "Switch to TUI preview mode")

            # Manually trigger button press to switch to preview mode
            app.post_message(Button.Pressed(btn))
            await pilot.pause(1)

            self.assertEqual(str(btn.tooltip), "Switch back to markdown editor")

            # Trigger again to switch back
            app.post_message(Button.Pressed(btn))
            await pilot.pause(1)

            self.assertEqual(str(btn.tooltip), "Switch to TUI preview mode")

if __name__ == "__main__":
    unittest.main()
