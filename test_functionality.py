
import unittest
import tempfile
import shutil
import os
import sys
from unittest.mock import MagicMock, patch
from pathlib import Path
from md_to_pdf_tui import process_resources, MarkdownToPdfApp

class TestProcessResources(unittest.TestCase):
    def test_process_resources_local_images(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create a dummy image file in the temp dir (representing a source file)
            src_img = temp_path / "source.png"
            src_img.touch()

            # Create another temp dir for the output of process_resources
            out_dir = temp_path / "output"
            out_dir.mkdir()

            # Markdown text referencing the image using absolute path to ensure it's found
            src_abs_path = src_img.resolve()
            md_text = f"![alt]({src_abs_path})\n<img src='{src_abs_path}'>"

            # Run process_resources
            new_text = process_resources(md_text, out_dir)

            # Verify that the image was NOT copied to out_dir
            dest_img = out_dir / "source.png"
            self.assertFalse(dest_img.exists(), "Image should NOT be copied to destination directory")

            # Verify that the markdown text points to the absolute path
            expected_path = src_abs_path.as_posix()
            expected_link = f"![alt]({expected_path})"
            self.assertIn(expected_link, new_text)

            # Verify HTML tag replacement
            expected_html = f"src='{expected_path}'"
            self.assertIn(expected_html, new_text)

class TestOpenPdfAction(unittest.TestCase):
    def setUp(self):
        self.app = MarkdownToPdfApp()
        self.app.notify = MagicMock()
        # Set up a fake output path
        self.app.last_output_path = Path("test_output.pdf")

        # Create dummy file
        with open("test_output.pdf", "w") as f:
            f.write("dummy")

    def tearDown(self):
        if os.path.exists("test_output.pdf"):
            os.remove("test_output.pdf")

    @patch('sys.platform', 'linux')
    @patch('subprocess.run')
    def test_open_linux(self, mock_run):
        self.app.action_open_pdf()
        self.app.notify.assert_called()
        mock_run.assert_called_with(["xdg-open", str(self.app.last_output_path.resolve())], check=True)

    @patch('sys.platform', 'darwin')
    @patch('subprocess.run')
    def test_open_mac(self, mock_run):
        self.app.action_open_pdf()
        mock_run.assert_called_with(["open", str(self.app.last_output_path.resolve())], check=True)

    @patch('sys.platform', 'win32')
    @patch('os.startfile', create=True)
    def test_open_win(self, mock_startfile):
        self.app.action_open_pdf()
        mock_startfile.assert_called_with(str(self.app.last_output_path.resolve()))

if __name__ == "__main__":
    unittest.main()
