from agents import Agent, RunContextWrapper, RunResult, ToolCallOutputItem, handoff
from agents.extensions import handoff_filters
from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX
from agents.mcp import MCPServer
from agents.models import get_default_model_settings

from ..config import get_config
from .file_writer_agent import WriterDirective
from .schemas import ReportData, ResearchInfo
from .utils import (
    display_agenda,
    extract_model_name,
    fetch_vector_store_name,
    load_prompt_from_file,
    should_apply_tool_filter,
)

# Plus de variables globales - utilisation directe de get_config() dans les fonctions

prompt_file = "research_lead_agent_revised.md"

# Chargement du prompt depuis le fichier
ORCHESTRATOR_PROMPT = load_prompt_from_file("prompts", prompt_file)

if ORCHESTRATOR_PROMPT is None:
    raise ValueError(f"{prompt_file} is None")

INSTRUCTIONS = f"{RECOMMENDED_PROMPT_PREFIX}" f"{ORCHESTRATOR_PROMPT}"


async def extract_json_payload(run_result: RunResult) -> str:
    # Scan the agent’s outputs in reverse order until we find a JSON-like message from a tool call.
    print(f"run_result: {run_result}")
    for item in reversed(run_result.new_items):
        if isinstance(item, ToolCallOutputItem) and item.output.strip().startswith("{"):
            return item.output.strip()
    # Fallback to an empty JSON object if nothing was found
    return "{}"


# Factory function pour créer l'agent avec le serveur MCP
def create_research_supervisor_agent(
    mcp_servers: list[MCPServer],
    file_planner_agent: Agent,
    file_search_agent: Agent,
    writer_agent: Agent,
):
    def on_handoff(ctx: RunContextWrapper[ResearchInfo], directive: WriterDirective):
        print(f"Writer agent called with directive: {directive}")
        ctx.context.search_results = directive.search_results

    config = get_config()
    writer_model = config.models.writer_model

    # Déterminer le filtre à appliquer selon le modèle du writer_agent
    input_filter = None
    if should_apply_tool_filter(writer_model):
        input_filter = handoff_filters.remove_all_tools
    # Si should_apply_tool_filter retourne False (GPT-5), input_filter reste None

    writer_handoff = handoff(
        agent=writer_agent,
        on_handoff=on_handoff,
        input_type=WriterDirective,
        tool_name_override="write_report",
        tool_description_override="Write the full report based on the search results",
        input_filter=input_filter,  # Application conditionnelle du filtre selon le modèle
    )

    model_name = extract_model_name(config.models.research_model)
    model_settings = get_default_model_settings(model_name)

    return Agent[ResearchInfo](
        name="ResearchSupervisorAgent",
        instructions=ORCHESTRATOR_PROMPT,
        model=config.models.research_model,
        handoffs=[writer_handoff],
        tools=[
            file_planner_agent.as_tool(
                tool_name="plan_file_search",
                tool_description="Plan the file search",
            ),
            file_search_agent.as_tool(
                tool_name="file_search",
                tool_description="Search for relevant information in the knowledge base",
            ),
            fetch_vector_store_name,
            display_agenda,
        ],
        output_type=ReportData,
        mcp_servers=mcp_servers,
        model_settings=model_settings,
    )
