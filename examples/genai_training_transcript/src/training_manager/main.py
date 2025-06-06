#!/usr/bin/env python3
"""
Entrypoint for Training Course Manager (Sprint 0): preprocess transcripts and generate metadata index.
"""

import argparse
import os
import sys
import asyncio
import shutil

# allow running as module
if __name__ == "__main__" and __package__ is None:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, script_dir)
    __package__ = "genai_training_transcript"

from agents import gen_trace_id, trace
from agents.mcp import MCPServerStdio
from training_manager import TrainingManager


async def main() -> None:
    parser = argparse.ArgumentParser(
        description="Training Course Manager (Sprint 0): preprocess transcripts and generate metadata index"
    )
    parser.add_argument(
        "--course-path",
        required=True,
        help="Path to course directory or single .txt file (e.g., data/training_courses/Course_Name.txt or data/training_courses/<course_id> - <course_name>)",
    )
    parser.add_argument(
        "--mcp-endpoint",
        default=os.environ.get("MCP_ENDPOINT", "stdio://"),
        help="MCP filesystem URI (default: stdio://)",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing outputs; skip when False",
    )
    args = parser.parse_args()

    if args.mcp_endpoint.startswith("stdio"):
        if not shutil.which("npx"):
            raise RuntimeError(
                "npx is required for stdio MCP filesystem server (npm install -g npx)"
            )
        mcp_params = {
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-filesystem", args.course_path],
        }
        mcp_server = MCPServerStdio(params=mcp_params, name="Training Courses Filesystem")
    elif args.mcp_endpoint.startswith("evernote://"):
        if not shutil.which("npx"):
            raise RuntimeError("npx is required for the TypeScript MCP Evernote server")
        evernote_token = os.environ.get("EVERNOTE_TOKEN")
        if not evernote_token:
            raise RuntimeError(
                "Environment variable EVERNOTE_TOKEN must be set for Evernote MCP"
            )

        mcp_params = {
            "command": "npx",
            "args": [
                "-y", "@modelcontextprotocol/server-filesystem",
                "--plugin", "evernote",
                "--token", evernote_token,
            ],
        }
        mcp_server = MCPServerStdio(params=mcp_params, name="Evernote MCP Server")
    else:
        raise ValueError(f"Unsupported MCP endpoint: {args.mcp_endpoint}")

    trace_id = gen_trace_id()
    with trace("MCP GenAI training transcripts", trace_id=trace_id):
        print(
            f"View trace: https://platform.openai.com/traces/trace?trace_id={trace_id}\n"
        )
        async with mcp_server:
            await TrainingManager(overwrite=args.overwrite).run(
                mcp_server, args.course_path
            )


def cli_main():
    """Sync entrypoint for Poetry scripts."""
    asyncio.run(main())


if __name__ == "__main__":
    cli_main()