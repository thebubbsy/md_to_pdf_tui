
import time
import tempfile
from pathlib import Path
from md_to_pdf_tui import process_resources

def benchmark():
    # Text with no images to avoid file I/O overhead, isolating regex compilation cost
    md_text = """
    This is a markdown text without any images.
    It has some text, but no image tags.
    We want to measure the overhead of compiling regexes.
    """ * 10

    iterations = 100000

    start_time = time.time()

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        for _ in range(iterations):
            process_resources(md_text, temp_path)

    end_time = time.time()
    print(f"Time taken for {iterations} iterations: {end_time - start_time:.4f} seconds")

if __name__ == "__main__":
    benchmark()
