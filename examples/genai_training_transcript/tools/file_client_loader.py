"""
Stub for loading preprocessed transcripts from the filesystem.
"""

def load_transcripts(config):
    """
    Load transcripts from the configured directory into a dict.
    """
    import os

    raw_dir = config.get("raw_transcripts_dir")
    print(f"[file_client_loader] Loading transcripts from directory: {raw_dir}")
    transcripts: dict[str, str] = {}
    if raw_dir:
        for root, _, files in os.walk(raw_dir):
            for filename in files:
                if filename.endswith(".txt"):
                    path = os.path.join(root, filename)
                    module_id = os.path.splitext(filename)[0]
                    # Map file-based module_id (underscores) to human title (spaces)
                    human_title = module_id.replace("_", " ")
                    with open(path, encoding="utf-8") as f:
                        transcripts[human_title] = f.read()
    else:
        print("[file_client_loader] Warning: 'raw_transcripts_dir' not set in config")
    return transcripts