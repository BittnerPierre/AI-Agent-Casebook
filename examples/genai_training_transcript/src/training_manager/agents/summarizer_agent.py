from agents import Agent
from pydantic import BaseModel

PROMPT = (
    "You are a course assistant. Given a course transcript file accessible via file tool, "
    "produce a concise markdown summary highlighting key concepts."
)


class Summary(BaseModel):
    summary: str
    """Markdown summary of the transcript content."""


summarizer_agent = Agent(
    name="SummarizerAgent",
    instructions=PROMPT,
    model="gpt-4o",
    output_type=Summary,
)