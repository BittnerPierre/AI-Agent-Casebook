#!/usr/bin/env python3
"""
TrainingManager orchestrates transcript cleaning and metadata index generation (Sprint 0).
"""

import json
import os

from rich.console import Console
from agents.mcp import MCPServer

from tools.transcript_preprocessor import preprocess_transcript
from tools.metadata_extractor import extract_metadata


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
        
        # Create output directories via MCP (fallback to local for now)
        await self._ensure_directories_exist(mcp_server, [cleaned_dir, metadata_dir])

        # List raw transcript files via MCP
        modules = await self._list_transcript_files(mcp_server, transcripts_dir)
        metadata_list = []
        for module_file in modules:
            module_id = os.path.splitext(module_file)[0]
            cleaned_path = os.path.join(cleaned_dir, f"{module_id}.md")
            # Skip existing cleaned transcripts unless overwrite is set
            if await self._file_exists(mcp_server, cleaned_path) and not self.overwrite:
                self.console.log(f"Skipping existing cleaned transcript: {cleaned_path}")
                # Read existing cleaned transcript for metadata extraction
                cleaned = await self._read_file(mcp_server, cleaned_path)
            else:
                self.console.log(f"Preprocessing transcript: {module_file}")
                cleaned = await preprocess_transcript(module_file, mcp_server)
                await self._write_file(mcp_server, cleaned_path, cleaned)

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

        # Write index.json via MCP
        index = {"course_id": course_id, "course_title": course_title, "modules": metadata_list}
        index_path = os.path.join(metadata_dir, "index.json")
        if await self._file_exists(mcp_server, index_path) and not self.overwrite:
            self.console.log(f"Skipping existing index file: {index_path}")
        else:
            index_content = json.dumps(index, indent=2)
            await self._write_file(mcp_server, index_path, index_content)
            self.console.log(f"Wrote index: {index_path}")

    async def _ensure_directories_exist(self, mcp_server: MCPServer, directories: list[str]) -> None:
        """Ensure output directories exist, using local fallback for MCP limitations."""
        for directory in directories:
            # For now, use local directory creation as MCP filesystem may not support mkdir
            # TODO: Implement proper MCP directory creation when available
            os.makedirs(directory, exist_ok=True)

    async def _list_transcript_files(self, mcp_server: MCPServer, transcripts_dir: str) -> list[str]:
        """List transcript files via MCP, with local fallback."""
        try:
            # Try to use MCP to list files
            # TODO: Implement proper MCP file listing when available
            # For now, fallback to local file listing
            if os.path.exists(transcripts_dir):
                files = [f for f in os.listdir(transcripts_dir) if f.endswith(".txt")]
                return sorted(files)
            return []
        except Exception as e:
            self.console.log(f"Warning: Failed to list files via MCP: {e}")
            return []

    async def _file_exists(self, mcp_server: MCPServer, file_path: str) -> bool:
        """Check if file exists via MCP, with local fallback."""
        try:
            # TODO: Implement proper MCP file existence check when available
            # For now, use local file system
            return os.path.exists(file_path)
        except Exception:
            return False

    async def _read_file(self, mcp_server: MCPServer, file_path: str) -> str:
        """Read file via MCP, with local fallback."""
        try:
            # TODO: Implement proper MCP file reading when available
            # For now, use local file system as fallback
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            self.console.log(f"Error reading file {file_path}: {e}")
            raise

    async def _write_file(self, mcp_server: MCPServer, file_path: str, content: str) -> None:
        """Write file via MCP, with local fallback."""
        try:
            # TODO: Implement proper MCP file writing when available
            # For now, use local file system as fallback
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
        except Exception as e:
            self.console.log(f"Error writing file {file_path}: {e}")
            raise