"""
Stub for reviewing final transcripts for alignment with syllabus and research notes.
"""

def review_transcript(module, content, syllabus_item, research_note):
    """
    Check that the final transcript covers syllabus objectives and integrates research.
    Raises RuntimeError on misalignment.
    """
    print(f"[reviewer] Reviewing transcript for module: {module} (stub)")
    # Fail if no research note was provided
    if not research_note.strip():
        raise RuntimeError(f"[reviewer] No research note to review for module: {module}")
    # Determine syllabus title
    title = syllabus_item.get("title") if isinstance(syllabus_item, dict) else syllabus_item
    # Fail if module title not mentioned in transcript
    if title not in content:
        raise RuntimeError(f"[reviewer] Transcript for module '{module}' does not mention the module title.")
    return True