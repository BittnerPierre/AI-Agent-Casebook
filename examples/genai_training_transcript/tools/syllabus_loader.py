"""
Stub for loading and parsing the course syllabus from Markdown.
"""

def load_syllabus(path):
    """
    Load syllabus Markdown and extract module titles and objectives.
    """
    print(f"[syllabus_loader] Loading syllabus from {path}")
    modules: list[dict[str, list[str]]] = []
    current: dict[str, list[str]] | None = None
    with open(path, encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()
            if stripped.startswith("### Module"):
                # Save previous module
                if current:
                    modules.append(current)
                # Parse module title after '### Module <n>:'
                parts = stripped.split(":", 1)
                title = parts[1].strip() if len(parts) == 2 else stripped
                current = {"title": title, "objectives": []}
            elif stripped.startswith("* ") and current:
                # Objective under current module
                current["objectives"].append(stripped[2:].strip())
    if current:
        modules.append(current)
    return modules