
import unittest
from unittest.mock import MagicMock, patch
from textual.app import App, ComposeResult
from textual.widgets import Select, Button, Input
from md_to_pdf_tui import MarkdownToPdfApp, THEMES
from pathlib import Path
import sys
import shutil

class TestUI(unittest.IsolatedAsyncioTestCase):
    async def test_compose_runs_without_error(self):
        """Verify that the app can be instantiated and composed without TypeError"""
        app = MarkdownToPdfApp()
        async with app.run_test() as pilot:
            pass

    async def test_select_widget_properties(self):
        """Verify the theme select widget is configured correctly"""
        app = MarkdownToPdfApp()
        async with app.run_test() as pilot:
            theme_select = app.query_one("#theme-select", Select)
            self.assertEqual(theme_select.tooltip, "Select color theme for PDF/DOCX output")
            self.assertTrue(len(theme_select._options) > 0)

    async def test_open_folder_button_exists(self):
        """Verify the new Open Folder button exists"""
        app = MarkdownToPdfApp()
        async with app.run_test() as pilot:
            btn = app.query_one("#btn-open-folder", Button)
            self.assertIsNotNone(btn)
            self.assertTrue("icon-btn" in btn.classes)
            self.assertEqual(str(btn.label), "📂")

if __name__ == "__main__":
    unittest.main()
