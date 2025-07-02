from pydantic import BaseModel

from agents import Agent
from .schemas import FileSearchPlan 

PROMPT = (
    "You are a helpful research assistant. Given a query, generate a set of "
    "semantic searches to perform in vectorized files to better answer the query. "
    "Generate between 3 and 5 searches per domain identified in the query."
)

file_planner_agent = Agent(
    name="FilePlannerAgent",
    instructions=PROMPT,
    model="gpt-4o",
    output_type=FileSearchPlan,
) 