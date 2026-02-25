
import unittest
import tempfile
import shutil
import os
from pathlib import Path
from md_to_pdf_tui import process_resources, sanitize_mermaid_code, _process_alerts

class TestAlertsProcessing(unittest.TestCase):
    def setUp(self):
        # Mock alert styles
        self.alert_styles = {
            "NOTE": {"color": "#blue", "bg": "#lightblue", "icon": "ℹ️"},
            "WARNING": {"color": "#orange", "bg": "#lightorange", "icon": "⚠️"}
        }
        self.text_color = "#black"

    def test_no_alerts(self):
        md = "This is a normal paragraph.\n\nAnother paragraph."
        result = _process_alerts(md, self.alert_styles, self.text_color)
        self.assertEqual(md, result)

    def test_single_alert(self):
        md = "> [!NOTE]\n> This is a note."
        # Verify transformation to HTML table
        result = _process_alerts(md, self.alert_styles, self.text_color)
        self.assertIn('<table', result)
        self.assertIn('ℹ️ NOTE - ', result)
        self.assertIn('This is a note.', result)

    def test_multiline_alert(self):
        md = "> [!WARNING]\n> Line 1\n> Line 2"
        result = _process_alerts(md, self.alert_styles, self.text_color)
        self.assertIn('⚠️ WARNING - ', result)
        self.assertIn('Line 1<br/>Line 2', result)

    def test_mixed_content(self):
        md = "Text before.\n> [!NOTE]\n> Note content.\nText after."
        result = _process_alerts(md, self.alert_styles, self.text_color)
        self.assertIn("Text before.", result)
        self.assertIn("Text after.", result)
        self.assertIn("Note content", result)
        self.assertIn("<table", result)

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

if __name__ == "__main__":
    unittest.main()
