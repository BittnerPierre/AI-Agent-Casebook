from agents import Agent, RunContextWrapper
from agents.agent import StopAtTools
from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX
from agents.mcp import MCPServer
from agents.models import get_default_model_settings

from ..config import get_config
from .schemas import ResearchInfo
from .utils import (
    display_agenda,
    extract_model_name,
    fetch_vector_store_name,
    load_prompt_from_file,
)

prompt_file = "knowledge_preparation.md"


def dynamic_instructions(
    context: RunContextWrapper[ResearchInfo], agent: Agent[ResearchInfo]
) -> str:
    prompt_template = load_prompt_from_file("prompts", prompt_file)

    if prompt_template is None:
        raise ValueError(f"{prompt_file} is None")

    dynamic_prompt = prompt_template.format(RECOMMENDED_PROMPT_PREFIX=RECOMMENDED_PROMPT_PREFIX)

    return (
        f"{dynamic_prompt}"
        # f"The absolute path to **temporary filesystem** is `{context.context.temp_dir}`."
        #   " You MUST use it to write and read temporary data.\n\n"
        # f"The absolute path to **output filesystem** is `{context.context.output_dir}`."
        #   " You MUST use it to write and read output final content.\n\n"
    )


def create_knowledge_preparation_agent(mcp_servers: list[MCPServer] = None):
    mcp_servers = mcp_servers if mcp_servers else []

    config = get_config()

    model = config.models.knowledge_preparation_model

    model_name = extract_model_name(model)
    model_settings = get_default_model_settings(model_name)

    knowledge_preparation_agent = Agent(
        name="knowledge_preparation_agent",
        handoff_description=("Given a research topic, prepare the knowledge base and the agenda."),
        instructions=dynamic_instructions,
        model=model,
        model_settings=model_settings,
        mcp_servers=mcp_servers,
        tools=[
            # save_report,
            fetch_vector_store_name,
            display_agenda,
        ],
        tool_use_behavior=StopAtTools(stop_at_tool_names=["display_agenda"]),
    )

    return knowledge_preparation_agent
