# Agent used to synthesize a final report from the individual summaries.
from pydantic import BaseModel
from ..config import get_config
from openai import OpenAI
from agents import Agent

PROMPT = (
   """You are a senior researcher tasked with writing a COMPREHENSIVE and DETAILED report for a research inquiry.

    You will be provided with the original inquiry and extensive research done by research assistants.

    Your task:
    1. Create a detailed outline covering all aspects of the topic
    2. Write a thorough, exhaustive report that serves as a complete reference

    The final output should be:
    - In markdown format
    - Minimum 3000-5000 words
    - Highly detailed with technical depth when appropriate
    - Include all relevant information gathered
    - Structured with clear sections and subsections
    - Comprehensive enough to serve as a complete reference on the topic

    This report should be so complete that it could serve as the basis for any future use: training materials, articles, presentations, or technical documentation."""
)

config = get_config()
client = OpenAI()
model = config.openai.model

class ReportData(BaseModel):
    short_summary: str
    """A short 2-3 sentence summary of the findings."""

    markdown_report: str
    """The final report"""

    follow_up_questions: list[str]
    """Suggested topics to research further"""


writer_agent = Agent(
    name="writer_agent",
    instructions=PROMPT,
    model=model,
    output_type=ReportData,
)
