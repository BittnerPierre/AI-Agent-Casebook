from agents import Agent, FileSearchTool, RunContextWrapper
from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX
from agents.mcp import MCPServer
from agents.models import get_default_model_settings

from ..config import get_config
from .schemas import FileSearchResult, ResearchInfo
from .utils import extract_model_name, load_prompt_from_file

prompt_file = "file_search_prompt.md"


def dynamic_instructions(
    context: RunContextWrapper[ResearchInfo], agent: Agent[ResearchInfo]
) -> str:
    prompt_template = load_prompt_from_file("prompts", prompt_file)

    if prompt_template is None:
        raise ValueError(f"{prompt_file} is None")

    dynamic_prompt = prompt_template.format(RECOMMENDED_PROMPT_PREFIX=RECOMMENDED_PROMPT_PREFIX)

    return (
        f"{dynamic_prompt}"
        f"The absolute path to **temporary filesystem** is `{context.context.temp_dir}`."
        " You MUST use it to write and read temporary data.\n\n"
        # f"The absolute path to **output filesystem** is `{context.context.output_dir}`."
        #   " You MUST use it to write and read output final content.\n\n"
    )


def create_file_search_agent(mcp_servers: list[MCPServer] = None, vector_store_id: str = None):
    mcp_servers = mcp_servers if mcp_servers else []

    config = get_config()

    model = config.models.search_model
    model_name = extract_model_name(model)
    model_settings = get_default_model_settings(model_name)

    file_search_agent = Agent(
        name="file_search_agent",
        handoff_description="Given a search topic, search through vectorized files and produce a clear, CONCISE and RELEVANT summary of the results.",
        instructions=dynamic_instructions,
        tools=[FileSearchTool(vector_store_ids=[vector_store_id])],
        model=model,
        model_settings=model_settings,
        mcp_servers=mcp_servers,
        output_type=FileSearchResult,
    )

    return file_search_agent
