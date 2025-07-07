from pydantic import BaseModel

from agents import Agent
from .schemas import FileSearchPlan  
from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX
from ..config import get_config
from openai import OpenAI

config = get_config()
client = OpenAI()
model = config.models.planning_model


PROMPT = (
    f"{RECOMMENDED_PROMPT_PREFIX}"
    """You are a helpful research assistant. Given a query and a list of knowledge entries, generate a COMPREHENSIVE set of semantic searches to perform in vectorized files to exhaustively answer the query.

    Generate between 8-12 searches covering:
    - Fundamental concepts and definitions
    - Technical details and specifications
    - Practical examples and use cases
    - Current trends and developments
    - Challenges and limitations
    - Future perspectives
    - Comparative analysis
    - Best practices

    For each search, prepare a FileSearchPlan with:
    - `query`: A specific, detailed search query
    - `reason`: Why this search is important and what specific information you expect to find

    Look at the knowledge entries summary and keywords to frame comprehensive queries that will extract maximum relevant information.

    Use the tools to achieve the task."""
)

def create_file_planner_agent(mcp_server=None):
    mcp_servers = [mcp_server] if mcp_server else []
    return Agent(
        name="file_planner_agent",
        instructions=PROMPT,
        model=model,
        # mcp_servers=mcp_servers,  
        output_type=FileSearchPlan,
    )
