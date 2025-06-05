"""
LLM-based metadata extractor: summary, keywords, and tags for cleaned transcripts.
"""

from pydantic import BaseModel
from agents import Agent, Runner

PROMPT = (
    "You are a course assistant. Given the cleaned transcript content, produce a JSON object with keys 'summary', 'keywords', and 'tags'. "
    "'summary' should be a concise Markdown summary highlighting key concepts. "
    "'keywords' should include specific topic-related terms mentioned. "
    "'tags' should be high-level topic tags for quick reference."
)


class ModuleMetadata(BaseModel):
    summary: str
    keywords: list[str]
    tags: list[str]


async def extract_metadata(
    module_filename: str,
    cleaned_transcript: str,
    mcp_server=None,
) -> ModuleMetadata:
    """
    Use an LLM-based agent to extract a summary, keywords, and tags for a cleaned transcript via MCP filesystem.
    """
    agent_kwargs = {
        "name": "MetadataAgent",
        "instructions": PROMPT,
        "model": "gpt-4o",
        "output_type": ModuleMetadata,
    }
    if mcp_server:
        agent_kwargs["mcp_servers"] = [mcp_server]
    agent = Agent(**agent_kwargs)

    prompt = (
        f"Transcript file: {module_filename}\n\n```markdown\n"
        f"{cleaned_transcript}\n```"
    )
    result = await Runner.run(
        starting_agent=agent,
        input=prompt,
    )
    return result.final_output_as(ModuleMetadata)