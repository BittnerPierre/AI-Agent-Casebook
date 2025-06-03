"""
Stub for the Research Team node to aggregate cross-course content for each module.
"""

def aggregate_research(agenda, transcripts, config):
    """
    For each module in the agenda, gather context (stub returns empty content).
    """
    print("[research_team] Aggregating research notes (stub)")
    return {module: transcripts.get(module, "") for module in agenda}