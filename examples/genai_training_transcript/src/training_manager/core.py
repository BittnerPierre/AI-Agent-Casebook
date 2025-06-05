#!/usr/bin/env python3
"""
TrainingManager orchestrates transcript cleaning and metadata index generation (Sprint 0).
"""

import os
import json

from rich.console import Console
from agents.mcp import MCPServer

from utils.transcript_preprocessor import preprocess_transcript
from utils.metadata_extractor import extract_metadata


class TrainingManager:
    def __init__(self, overwrite: bool = False) -> None:
        self.overwrite = overwrite
        self.console = Console()

    async def run(self, mcp_server: MCPServer, course_path: str) -> None:
        # Determine course_id and course_title from folder name
        base = os.path.basename(course_path)
        try:
            course_id, course_title = base.split(" - ", 1)
        except ValueError:
            course_id = base
            course_title = base

        # Prepare output directories
        transcripts_dir = os.path.join(course_path, "transcripts")
        output_base = os.path.join("output", course_id)
        cleaned_dir = os.path.join(output_base, "cleaned_transcripts")
        metadata_dir = os.path.join(output_base, "metadata")
        os.makedirs(cleaned_dir, exist_ok=True)
        os.makedirs(metadata_dir, exist_ok=True)

        # List raw transcript files
        modules = sorted(
            f for f in os.listdir(transcripts_dir) if f.endswith(".txt")
        )
        metadata_list = []
        for module_file in modules:
            module_id = os.path.splitext(module_file)[0]
            cleaned_path = os.path.join(cleaned_dir, f"{module_id}.md")
            # Skip existing cleaned transcripts unless overwrite is set
            if os.path.exists(cleaned_path) and not self.overwrite:
                self.console.log(f"Skipping existing cleaned transcript: {cleaned_path}")
            else:
                self.console.log(f"Preprocessing transcript: {module_file}")
                cleaned = await preprocess_transcript(module_file, mcp_server)
                with open(cleaned_path, "w", encoding="utf-8") as f:
                    f.write(cleaned)

            # Extract metadata (summary, keywords, tags)
            self.console.log(f"Extracting metadata for: {module_id}.md")
            meta = await extract_metadata(f"{module_id}.md", cleaned, mcp_server)
            metadata_list.append(
                {
                    "module_id": module_id,
                    "title": module_id,
                    "summary": meta.summary,
                    "keywords": meta.keywords,
                    "tags": meta.tags,
                }
            )

        # Write index.json
        index = {"course_id": course_id, "course_title": course_title, "modules": metadata_list}
        index_path = os.path.join(metadata_dir, "index.json")
        if os.path.exists(index_path) and not self.overwrite:
            self.console.log(f"Skipping existing index file: {index_path}")
        else:
            with open(index_path, "w", encoding="utf-8") as f:
                json.dump(index, f, indent=2)
            self.console.log(f"Wrote index: {index_path}")