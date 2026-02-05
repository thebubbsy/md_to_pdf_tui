
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
            # In real usage, source file might be elsewhere, but for simplicity let's put it here
            src_img = temp_path / "source.png"
            src_img.touch()

            # Create another temp dir for the output of process_resources
            out_dir = temp_path / "output"
            out_dir.mkdir()

            # Markdown text referencing the image using absolute path to ensure it's found
            md_text = f"![alt]({src_img.resolve()})\n<img src='{src_img.resolve()}'>"

            # Run process_resources
            new_text = process_resources(md_text, out_dir)

            # Verify that the image was copied to out_dir
            dest_img = out_dir / "source.png"
            self.assertTrue(dest_img.exists(), "Image should be copied to destination directory")

            # Verify that the markdown text was updated to point to the new file name (relative path)
            # process_resources returns links as just the filename for local files in the same dir
            expected_link = f"![alt]({dest_img.name})"
            self.assertIn(expected_link, new_text)

            # Verify HTML tag replacement
            # <img src="source.png">
            # The regex replacement for HTML might be slightly different depending on implementation
            # process_resources: return full_tag.replace(url, dest_path.name)
            expected_html = f"src='{dest_img.name}'"
            self.assertIn(expected_html, new_text)

if __name__ == "__main__":
    unittest.main()
