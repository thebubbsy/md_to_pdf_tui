
import unittest
import unittest.mock
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

    @unittest.mock.patch('urllib.request.urlopen')
    def test_process_resources_remote_cache(self, mock_urlopen):
        # Setup mock to simulate a download
        mock_response = unittest.mock.Mock()
        mock_response.__enter__ = unittest.mock.Mock(return_value=mock_response)
        mock_response.__exit__ = unittest.mock.Mock(return_value=None)
        mock_response.read.return_value = b"fake image data"
        mock_urlopen.return_value = mock_response

        # Use a fake URL
        url = "http://example.com/image.png"
        md_text = f"![test]({url})"

        # Run process_resources twice with DIFFERENT temp dirs (simulating different runs)
        # 1st Run
        with tempfile.TemporaryDirectory() as t1:
            process_resources(md_text, Path(t1))

        # 2nd Run
        with tempfile.TemporaryDirectory() as t2:
            process_resources(md_text, Path(t2))

        # Check how many times urlopen was called
        # Ideally, with caching, it should be called ONCE (if cache persists across runs).
        print(f"\nurlopen call count: {mock_urlopen.call_count}")

        # We don't assert call count here yet because we know it fails (returns 2).
        # We can just print it. Or assert it equals 1 and expect failure.
        # Let's assert it's 1, so the test fails, confirming the issue.
        self.assertEqual(mock_urlopen.call_count, 1, "Resources should be cached and not re-downloaded.")

if __name__ == "__main__":
    unittest.main()
