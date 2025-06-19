"""
Stub for generating module scripts via LLM (Completions API) based on draft content.
"""

import asyncio

from pydantic import BaseModel

try:
    import inspect
    import os

    from agents import Agent, Runner

    _AGENTS_SDK_AVAILABLE = (
        inspect.iscoroutinefunction(getattr(Runner, "run", None))
        and os.environ.get("OPENAI_API_KEY")
    )
except ImportError:
    _AGENTS_SDK_AVAILABLE = False

PROMPT = (
    "You are a course assistant. Given a draft chapter transcript in Markdown, "
    "perform a global quality pass: smooth transitions, eliminate repetition, "
    "and ensure all syllabus objectives are covered. Output the final transcript in Markdown."
)


class FinalTranscript(BaseModel):
    content: str


def generate_transcript(module: str, draft: str, mcp_server=None) -> str:
    """
    Generate the final transcript for a module via a Course Authoring Agent.
    Falls back to a placeholder stub if the Agents SDK is not available.
    """
    if not _AGENTS_SDK_AVAILABLE:
        header = f"# {module}\n"
        return header + f"\nThis is a generated script for module: {module}."

    async def _run_authoring():
        agent_kwargs = {
            "name": "CourseAuthoringAgent",
            "instructions": PROMPT,
            "model": "gpt-4o",
            "output_type": FinalTranscript,
        }
        if mcp_server:
            agent_kwargs["mcp_servers"] = [mcp_server]
        agent = Agent(**agent_kwargs)

        prompt_input = (
            f"Module: {module}\n\n```markdown\n{draft}\n```"
        )
        result = await Runner.run(starting_agent=agent, input=prompt_input)
        return result.final_output_as(FinalTranscript).content

    return asyncio.run(_run_authoring())