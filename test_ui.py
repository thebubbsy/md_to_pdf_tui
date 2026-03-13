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

            # Verify tooltip
            self.assertEqual(str(btn.tooltip), "Dismiss this help dialog")

            # Simulate button press to ensure no crash (though dismissing modal in test app might be tricky)
            await pilot.click("#dismiss-btn")
            await pilot.pause()

if __name__ == "__main__":
    unittest.main()
