
import unittest
import tempfile
import shutil
import os
from pathlib import Path
from md_to_pdf_tui import process_resources

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
