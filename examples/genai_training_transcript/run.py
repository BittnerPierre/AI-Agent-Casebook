"""
Entry point for the GenAI Training Transcript Generator (Local v1).
"""
import argparse
import os

import yaml

from tools.transcript_preprocessor import preprocess_transcript
from tools.syllabus_loader import load_syllabus
from tools.file_client_loader import load_transcripts
from tools.planner import refine_syllabus
from tools.research_team import aggregate_research
from tools.editing_team import edit_chapters
from tools.transcript_generator import generate_transcript


def main(config_path: str):
    with open(config_path) as f:
        config = yaml.safe_load(f)

    preprocess_transcript(config)
    modules = load_syllabus(config["syllabus_path"])
    transcripts = load_transcripts(config)
    agenda = refine_syllabus(modules, config)
    research_notes = aggregate_research(agenda, transcripts, config)
    drafts = edit_chapters(research_notes, config)

    # Generate final scripts per module
    outputs = {}
    for module, draft in drafts.items():
        outputs[module] = generate_transcript(module, draft, config)

    # Write outputs to files
    output_dir = config.get("output_dir", "output")
    os.makedirs(output_dir, exist_ok=True)
    for module, content in outputs.items():
        filename = f"{module.replace(' ', '_')}.md"
        path = os.path.join(output_dir, filename)
        with open(path, "w") as f:
            f.write(content)

    print(f"Generated {len(outputs)} module scripts in {output_dir}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run GenAI Training Transcript Generator")
    parser.add_argument("--config", default="config.yaml", help="Path to the config file")
    args = parser.parse_args()
    main(args.config)