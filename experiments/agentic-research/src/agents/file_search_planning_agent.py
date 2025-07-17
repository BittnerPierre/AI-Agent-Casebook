import os
from pydantic import BaseModel

from agents import Agent
from .schemas import FileSearchPlan  
from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX
from ..config import get_config
from openai import OpenAI
from agents.mcp import MCPServer
from agents import RunContextWrapper
from .schemas import ResearchInfo
from .utils import load_prompt_from_file


prompt_file = "file_search_planning_prompt.md"

def dynamic_instructions(
    context: RunContextWrapper[ResearchInfo], agent: Agent[ResearchInfo]
) -> str:
    
    search_count = context.context.max_search_plan if hasattr(context.context, 'max_search_plan') else "8-12"

    prompt_template = load_prompt_from_file("prompts", prompt_file)

    if prompt_template is None:
        raise ValueError(f"{prompt_file} is None")

    dynamic_prompt = prompt_template.format(
        search_count=search_count,
        RECOMMENDED_PROMPT_PREFIX=RECOMMENDED_PROMPT_PREFIX
    )

    return (
            f"{dynamic_prompt}"
            # f"The absolute path to **temporary filesystem** is `{context.context.temp_dir}`. "
            #  " You MUST use it to write and read temporary data.\n\n"
            # f"The absolute path to **output filesystem** is `{context.context.output_dir}`."
            #  " You MUST use it to write and read output final content.\n\n"
        )

def create_file_planner_agent(mcp_servers:list[MCPServer]=None):
    mcp_servers = mcp_servers if mcp_servers else []

    config = get_config()
    model = config.models.planning_model


    return Agent(
        name="file_planner_agent",
        instructions=dynamic_instructions,
        model=model,
        # mcp_servers=mcp_servers,  
        output_type=FileSearchPlan,
    )
