
import unittest
import tempfile
import shutil
import os
from pathlib import Path
from md_to_pdf_tui import process_resources, sanitize_mermaid_code

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

class TestMermaidSanitization(unittest.TestCase):
    def test_sanitize_mermaid_code_list_markers(self):
        # Case 1: Unordered list marker inside quotes
        code = 'graph TD\nA["- Item 1"]'
        expected = 'graph TD\nA["-&#8203; Item 1"]'
        self.assertEqual(sanitize_mermaid_code(code), expected)

        # Case 2: Ordered list marker inside quotes
        code = 'graph TD\nB["1. Item 2"]'
        expected = 'graph TD\nB["1.&#8203; Item 2"]'
        self.assertEqual(sanitize_mermaid_code(code), expected)

        # Case 3: Asterisk list marker inside quotes
        code = "graph TD\nC['* Item 3']"
        expected = "graph TD\nC['*&#8203; Item 3']"
        self.assertEqual(sanitize_mermaid_code(code), expected)

        # Case 4: Multiple lines inside quotes
        code = 'graph TD\nD["Line 1\n- Line 2"]'
        expected = 'graph TD\nD["Line 1\n-&#8203; Line 2"]'
        self.assertEqual(sanitize_mermaid_code(code), expected)

    def test_sanitize_mermaid_code_no_change(self):
        # Case 5: No list markers
        code = 'graph TD\nA["Just text"]'
        self.assertEqual(sanitize_mermaid_code(code), code)

        # Case 6: Markers not at start of line (inside text)
        code = 'graph TD\nA["Text - not a list"]'
        self.assertEqual(sanitize_mermaid_code(code), code)

if __name__ == "__main__":
    unittest.main()
