"""
Stub for the Research Team node to aggregate cross-course content for each module.
"""

def aggregate_research(agenda, transcripts, config):
    """
    For each module in the agenda, gather context (stub returns empty content).
    """
    print("[research_team] Aggregating research notes (stub)")
    # Build a mapping of module titles (or names) to research content,
    # failing if no transcript source is available for a module.
    notes: dict[str, str] = {}
    for item in agenda:
        # Support agenda entries as dicts or strings
        key = item.get("title") if isinstance(item, dict) else item
        content = transcripts.get(key, "")
        if not content.strip():
            raise RuntimeError(f"[research_team] No transcript source found for module: {key}. Aborting research.")
        notes[key] = content
    return notes