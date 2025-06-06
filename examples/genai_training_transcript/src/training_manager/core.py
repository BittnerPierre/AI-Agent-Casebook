#!/usr/bin/env python3
"""
TrainingManager orchestrates transcript cleaning and metadata index generation (Sprint 0).
"""

import os
import json

from rich.console import Console
from agents.mcp import MCPServer

from .tools.transcript_preprocessor import preprocess_transcript
from .tools.metadata_extractor import extract_metadata


class TrainingManager:
    def __init__(self, overwrite: bool = False) -> None:
        self.overwrite = overwrite
        self.console = Console()

    async def run(self, mcp_server: MCPServer, course_path: str) -> None:
        # Check if course_path is a single file or directory
        is_single_file = os.path.isfile(course_path) and course_path.endswith(".txt")
        
        if is_single_file:
            # Handle single-file course
            course_id, course_title, modules, transcripts_dir = self._process_single_file_course(course_path)
        else:
            # Handle multi-module directory course
            course_id, course_title, modules, transcripts_dir = self._process_directory_course(course_path)

        # Prepare output directories
        output_base = os.path.join("output", course_id)
        cleaned_dir = os.path.join(output_base, "cleaned_transcripts")
        metadata_dir = os.path.join(output_base, "metadata")
        os.makedirs(cleaned_dir, exist_ok=True)
        os.makedirs(metadata_dir, exist_ok=True)
        # Process transcript modules
        metadata_list = []
        for module_info in modules:
            if is_single_file:
                module_file = module_info["filename"]
                module_path = module_info["filepath"]
                module_id = module_info["module_id"]
            else:
                module_file = module_info
                module_path = os.path.join(transcripts_dir, module_file)
                module_id = os.path.splitext(module_file)[0]
                
            cleaned_path = os.path.join(cleaned_dir, f"{module_id}.md")
            
            # Skip existing cleaned transcripts unless overwrite is set
            if os.path.exists(cleaned_path) and not self.overwrite:
                self.console.log(f"Skipping existing cleaned transcript: {cleaned_path}")
                # Read existing cleaned transcript for metadata extraction
                with open(cleaned_path, "r", encoding="utf-8") as f:
                    cleaned = f.read()
            else:
                self.console.log(f"Preprocessing transcript: {module_file}")
                cleaned = await preprocess_transcript(module_path, mcp_server)
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

    def _process_single_file_course(self, course_path: str) -> tuple[str, str, list[dict], str]:
        """Process a single .txt file course."""
        # Extract course info from filename
        filename = os.path.basename(course_path)
        course_id = os.path.splitext(filename)[0]
        
        # Convert underscores to spaces for title
        course_title = course_id.replace("_", " ")
        
        # Create module info for the single file
        modules = [{
            "filename": filename,
            "filepath": course_path,
            "module_id": course_id
        }]
        
        # Use parent directory as transcripts_dir (for reference)
        transcripts_dir = os.path.dirname(course_path)
        
        self.console.log(f"Processing single-file course: {course_title}")
        return course_id, course_title, modules, transcripts_dir

    def _process_directory_course(self, course_path: str) -> tuple[str, str, list[str], str]:
        """Process a multi-module directory course."""
        # Determine course_id and course_title from folder name
        base = os.path.basename(course_path)
        try:
            course_id, course_title = base.split(" - ", 1)
        except ValueError:
            course_id = base
            course_title = base
        
        # List raw transcript files in transcripts subdirectory
        transcripts_dir = os.path.join(course_path, "transcripts")
        
        if not os.path.exists(transcripts_dir):
            raise FileNotFoundError(f"Transcripts directory not found: {transcripts_dir}")
            
        modules = sorted(
            f for f in os.listdir(transcripts_dir) if f.endswith(".txt")
        )
        
        if not modules:
            raise ValueError(f"No .txt transcript files found in {transcripts_dir}")
            
        self.console.log(f"Processing multi-module course: {course_title} ({len(modules)} modules)")
        return course_id, course_title, modules, transcripts_dir