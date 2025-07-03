from pydantic import BaseModel

from agents import Agent
from .schemas import FileSearchPlan  
from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX
from ..config import get_config
from openai import OpenAI

config = get_config()
client = OpenAI()
# manager = VectorStoreManager(client, config.vector_store)
#vector_store_id = manager.get_or_create_vector_store()
model = config.openai.model


PROMPT = (
    f"{RECOMMENDED_PROMPT_PREFIX}"
    "You are a helpful research assistant. Given a query and a list of knowledge entries, generate a set of "
    "semantic searches to perform in vectorized files to better answer the query. "
    "Generate between 3 and 5 searches per domain identified in the query."
    "Prepare a FileSearchPlan with the `query`, the `filename` and the `reason` why you think this file is relevant."
    "Look at the knowledge entries summary and keywords to identify the reason why you think this file is relevant for the query."

    "Use the tools to achieve the task."
)

def create_file_planner_agent(mcp_server=None):
    mcp_servers = [mcp_server] if mcp_server else []
    return Agent(
        name="FilePlannerAgent",
        instructions=PROMPT,
        model=model,
        mcp_servers=mcp_servers,  
        output_type=FileSearchPlan,
    )
