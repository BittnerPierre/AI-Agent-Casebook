from pydantic import BaseModel

from agents import Agent

PROMPT = (
    "You are a course assistant. Given a directory of course transcript files accessible via file tool, "
    "list all transcript file names to process. "
    "Output JSON with a single key 'modules', whose value is a list of file name strings."
)


class ModuleList(BaseModel):
    modules: list[str]
    """List of transcript file names."""


planner_agent = Agent(
    name="PlannerAgent",
    instructions=PROMPT,
    output_type=ModuleList,
)