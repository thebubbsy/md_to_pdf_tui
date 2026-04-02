import re
import time

ALERT_PATTERN = re.compile(r"^\s*>\s*\[!(NOTE|TIP|IMPORTANT|WARNING|CAUTION)\]", re.IGNORECASE)

md_text = """
# Header
Some text that does not have an alert but is very long and has many lines.
""" * 100000

def original():
    lines = md_text.split('\n')
    processed_lines = []
    in_alert = False
    alert_type = None
    alert_content = []

    for line in lines:
        if not in_alert and '>' not in line:
            processed_lines.append(line)
            continue
        match = ALERT_PATTERN.match(line)
        if match:
            in_alert = True
            alert_type = match.group(1).upper()
            continue
        if in_alert:
            pass
        else:
            processed_lines.append(line)
    return "\n".join(processed_lines)

def optimized():
    # Only process alerts if "[!" is present
    if "[!" not in md_text or not re.search(r"^\s*>\s*\[!", md_text, re.MULTILINE):
        return md_text

    lines = md_text.split('\n')
    processed_lines = []
    in_alert = False
    alert_type = None
    alert_content = []

    for line in lines:
        if not in_alert and '>' not in line:
            processed_lines.append(line)
            continue
        match = ALERT_PATTERN.match(line)
        if match:
            in_alert = True
            alert_type = match.group(1).upper()
            continue
        if in_alert:
            pass
        else:
            processed_lines.append(line)
    return "\n".join(processed_lines)

start = time.perf_counter()
for _ in range(10):
    original()
print("Original:", time.perf_counter() - start)

start = time.perf_counter()
for _ in range(10):
    optimized()
print("Optimized:", time.perf_counter() - start)
