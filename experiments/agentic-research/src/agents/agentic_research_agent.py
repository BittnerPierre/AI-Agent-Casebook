
from agents import Agent, RunContextWrapper, RunResult, ToolCallOutputItem, function_tool
from agents import Agent, ModelSettings, handoff
from openai import OpenAI
from agents.mcp import MCPServer

from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX
from .utils import load_prompt_from_file, fetch_vector_store_name, display_agenda
from ..config import get_config
from .schemas import FileFinalReport, ResearchInfo, ReportData
from agents.extensions import handoff_filters
from .file_writer_agent import WriterDirective

config = get_config()
client = OpenAI()

model = config.models.research_model

prompt_file = "research_lead_agent_revised.md"

# Chargement du prompt depuis le fichier
ORCHESTRATOR_PROMPT = load_prompt_from_file("prompts", prompt_file)

if ORCHESTRATOR_PROMPT is None:
    raise ValueError(f"{prompt_file} is None")

INSTRUCTIONS = (
    f"{RECOMMENDED_PROMPT_PREFIX}"
    f"{ORCHESTRATOR_PROMPT}"
)


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
        mcp_servers:list[MCPServer],
        file_planner_agent:Agent,
        file_search_agent:Agent,
        writer_agent:Agent):

    def on_handoff(ctx: RunContextWrapper[ResearchInfo], directive: WriterDirective):
        print(f"Writer agent called with directive: {directive}")
        ctx.context.search_results = directive.search_results


    writer_handoff = handoff(
        agent=writer_agent,
        on_handoff=on_handoff,
        input_type=WriterDirective,
        tool_name_override="write_report",
        tool_description_override="Write the full report based on the search results",
        # no need to pass the history to the writer agent as it is handle via file, and it will failed with mistral due to the call id format (invalid_function_call error)
        input_filter=handoff_filters.remove_all_tools, 
    )

    return Agent[ResearchInfo](
        name="ResearchSupervisorAgent",
        instructions=ORCHESTRATOR_PROMPT,
        model=model,
        handoffs=[
            writer_handoff
        ],
        tools=[
            file_planner_agent.as_tool(
                tool_name="plan_file_search",
                tool_description="Plan the file search",
            ),
            file_search_agent.as_tool(
                tool_name="file_search",
                tool_description="Search for relevant information in the knowledge base",
            ),
            # writer_agent.as_tool(
            #     tool_name="write_report",
            #     tool_description="Write the full report based on the search results",
            #     custom_output_extractor=extract_json_payload
            # ),
            fetch_vector_store_name,
            display_agenda,
    ],
        output_type=ReportData,
        mcp_servers=mcp_servers,
        model_settings=ModelSettings(tool_choice="required"),
    ) 