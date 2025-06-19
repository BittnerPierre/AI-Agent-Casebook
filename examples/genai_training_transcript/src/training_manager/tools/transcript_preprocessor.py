"""
Stub for preprocessing raw transcript files into formatted Markdown and metadata.
"""

from agents import Agent, Runner
from pydantic import BaseModel

PROMPT = (
    "You are a course assistant. Given a transcript file accessible via file tool, "
    "add proper punctuation, fix sentence boundaries, resolve misspellings, "
    "and segment the content into coherent paragraphs. "
    "Output only the cleaned transcript as Markdown text."
)


class PreprocessedTranscript(BaseModel):
    content: str


async def preprocess_transcript(
    module_filename: str,
    mcp_server=None,
) -> str:
    """
    Use an LLM-based agent to preprocess the raw transcript file via MCP filesystem.
    """
    agent_kwargs = {
        "name": "PreprocessorAgent",
        "instructions": PROMPT,
        "model": "gpt-4o",
        "output_type": PreprocessedTranscript,
    }
    if mcp_server:
        agent_kwargs["mcp_servers"] = [mcp_server]
    agent = Agent(**agent_kwargs)

    result = await Runner.run(
        starting_agent=agent,
        input=f"Transcript file: {module_filename}",
    )
    return result.final_output.content