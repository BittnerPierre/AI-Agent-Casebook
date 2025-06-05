"""
Stub for the Editing Team nodes (Documentalist/Writer/Reviewer) to process chapters.
"""

def edit_chapters(research_notes, config):
    """
    For each module, produce a draft script (stub returns same content).
    """
    print("[editing_team] Editing chapters (stub)")
    drafts: dict[str, str] = {}
    for module, note in research_notes.items():
        if not note.strip():
            raise RuntimeError(f"[editing_team] No research notes provided for module: {module}. Aborting edit.")
        # Stub: echo research note as draft content
        drafts[module] = note
    return drafts