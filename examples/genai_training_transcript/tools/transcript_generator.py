"""
Stub for generating module scripts via LLM (Completions API) based on draft content.
"""

def generate_transcript(module, draft, config):
    """
    Generate the final script for a module (stub returns placeholder text).
    """
    print(f"[transcript_generator] Generating transcript for '{module}' (stub)")
    header = f"# {module}\n"
    return header + "\nThis is a generated script for module: {}.".format(module)