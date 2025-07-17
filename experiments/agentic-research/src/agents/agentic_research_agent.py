
from agents import Agent, RunContextWrapper, RunResult, ToolCallOutputItem, function_tool
from agents import Agent, ModelSettings, handoff
from openai import OpenAI
from agents.mcp import MCPServer

from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX
from .utils import load_prompt_from_file, fetch_vector_store_name, display_agenda
from ..config import get_config
from .schemas import FileFinalReport, ResearchInfo, ReportData
from agents.extensions import handoff_filters
from .writer_agent import WriterDirective

ORCHESTRATOR_PROMP_V1 = """
    You are a helpful lead research assistant. 

    Given a user input (query or syllabus), come up with a set of file searches
    to perform to best answer the query. Output between 5 and 20 search items to query for.

    You are the lead researcher and you are responsible for the overall research process.
    You are the one who will decide which files to look after and which topics to cover in the report.
    You are the one who will aggregate the search results and write the report.

    To achieve your goals, follow strictly the steps define below. Each step is separated by a ####

    First ####, look at the user input to see if it already specifies files to look after in the reference section and extract all filenames.
    Second ####, identify all topics and research areas that need to be covered in the report by the user in its request.
    Third ####, look at the knowledge entries and identify the relevant files matching the topics or research areas or user input
    with summary and keywords of the knowledge entries. Write down the list of filenames to look into.

    Fourth ####, prepare a FileSearchPlan by delegating to file_planner_agent based on the list of filenames.
    Fifth ####, delegate each file search item to file_search_agent that will perform the search and come back with a summary.
    Finally ####, you aggregate the summaries and ask writer_agent to write a report.

    Use the tools and agents to achieve the task.
    """

config = get_config()
client = OpenAI()
# manager = VectorStoreManager(client, config.vector_store)
#vector_store_id = manager.get_or_create_vector_store()
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