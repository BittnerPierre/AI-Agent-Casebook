"""
Stub for loading and parsing the course syllabus from Markdown.
"""

def load_syllabus(path):
    """
    Load syllabus Markdown and extract module titles.
    """
    print(f"[syllabus_loader] Loading syllabus from {path}")
    modules = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.strip().startswith("### Module"):
                title = line.strip()[len("### Module"):].strip(': ').strip()
                modules.append(title)
    return modules