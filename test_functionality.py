
import unittest
import tempfile
import shutil
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
from md_to_pdf_tui import process_resources, sanitize_mermaid_code, open_file_externally

class TestSanitizeMermaidCode(unittest.TestCase):
    def test_basic_sanitize(self):
        input_code = 'graph TD\nA["Test"] --> B["123"]'
        expected = 'graph TD\nA["Test"] --> B["123"]'
        self.assertEqual(sanitize_mermaid_code(input_code), expected)

    def test_sanitize_list_markers(self):
        input_code = 'graph TD\nA["- Item 1\n* Item 2"]'
        # Expect zero-width space after markers
        expected = 'graph TD\nA["-&#8203; Item 1\n*&#8203; Item 2"]'
        self.assertEqual(sanitize_mermaid_code(input_code), expected)

    def test_sanitize_numbered_list(self):
        input_code = "graph TD\nA['1. Item 1\n2. Item 2']"
        expected = "graph TD\nA['1.&#8203; Item 1\n2.&#8203; Item 2']"
        self.assertEqual(sanitize_mermaid_code(input_code), expected)

    def test_sanitize_mixed_quotes(self):
        input_code = 'graph TD\nA["- Item 1"] --> B[\'1. Item 2\']'
        expected = 'graph TD\nA["-&#8203; Item 1"] --> B[\'1.&#8203; Item 2\']'
        self.assertEqual(sanitize_mermaid_code(input_code), expected)

    def test_sanitize_escaped_quotes(self):
        input_code = 'graph TD\nA["String with \\"quotes\\" inside"]'
        # Should not touch internal quotes if they are escaped properly
        expected = 'graph TD\nA["String with \\"quotes\\" inside"]'
        self.assertEqual(sanitize_mermaid_code(input_code), expected)

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

class TestOpenFile(unittest.TestCase):
    @patch("platform.system")
    @patch("os.startfile", create=True) # create=True for non-Windows systems
    @patch("subprocess.run")
    def test_open_file_windows(self, mock_run, mock_startfile, mock_system):
        mock_system.return_value = "Windows"
        with tempfile.NamedTemporaryFile() as tmp:
            open_file_externally(tmp.name)
            mock_startfile.assert_called_with(str(Path(tmp.name).resolve()))
            mock_run.assert_not_called()

    @patch("platform.system")
    @patch("subprocess.run")
    def test_open_file_mac(self, mock_run, mock_system):
        mock_system.return_value = "Darwin"
        with tempfile.NamedTemporaryFile() as tmp:
            open_file_externally(tmp.name)
            mock_run.assert_called_with(["open", str(Path(tmp.name).resolve())], check=False)

    @patch("platform.system")
    @patch("subprocess.run")
    def test_open_file_linux(self, mock_run, mock_system):
        mock_system.return_value = "Linux"
        with tempfile.NamedTemporaryFile() as tmp:
            open_file_externally(tmp.name)
            mock_run.assert_called_with(["xdg-open", str(Path(tmp.name).resolve())], check=False)

if __name__ == "__main__":
    unittest.main()
