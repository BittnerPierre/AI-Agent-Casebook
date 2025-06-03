"""
Stub for loading preprocessed transcripts from the filesystem.
"""

def load_transcripts(config):
    """
    Load transcripts from the configured directory into a dict.
    """
    print("[file_client_loader] Loading transcripts from local directory (stub)")
    modules = config.get("modules", [])
    # Return empty content for each module as stub
    return {module: "" for module in modules}