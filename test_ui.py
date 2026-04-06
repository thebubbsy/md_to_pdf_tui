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
            self.assertEqual(str(btn.tooltip), "Close help dialog")

            # Simulate button press to ensure no crash (though dismissing modal in test app might be tricky)
            await pilot.click("#dismiss-btn")
            await pilot.pause()

class TestTooltips(unittest.IsolatedAsyncioTestCase):
    async def test_dynamic_tooltips(self):
        from textual.widgets import Switch, Button
        from md_to_pdf_tui import MarkdownToPdfApp

        app = MarkdownToPdfApp()
        async with app.run_test() as pilot:
            # Wait for app to initialize
            await pilot.pause()

            btn = pilot.app.query_one("#toggle-view-btn", Button)

            # Initial state (File Mode)
            self.assertEqual(str(btn.tooltip), "Preview not available in File Mode")
            self.assertTrue(btn.disabled)

            # Switch to Paste Mode
            switch = pilot.app.query_one("#source-switch", Switch)
            switch.value = True
            await pilot.pause()

            # State after switching to Paste Mode
            self.assertEqual(str(btn.tooltip), "Switch to preview mode")
            self.assertFalse(btn.disabled)

            # To click a widget that isn't focused/active properly, textual needs us to interact with it carefully or set the state directly.
            # However, we can just trigger the action or set the value directly in tests.
            # Instead of pilot.click, let's call the action/event handler directly to ensure it runs

            # Switch to Paste & Preview tab first to make elements active
            app.query_one('TabbedContent').active = 'tab-2'
            await pilot.pause()

            # Click to switch to Preview Mode
            await pilot.click("#toggle-view-btn")
            await pilot.pause()
            await asyncio.sleep(0.5)
            await pilot.pause()

            # State after switching to Preview Mode
            self.assertEqual(str(btn.tooltip), "Return to markdown editor")

            # Click to return to Edit Mode
            await pilot.click("#toggle-view-btn")
            await pilot.pause()

            # Additional pause to let Textual catch up on the message queue
            await asyncio.sleep(0.5)
            await pilot.pause()

            # State after returning to Edit Mode
            self.assertEqual(str(btn.tooltip), "Switch to preview mode")

if __name__ == "__main__":
    unittest.main()
