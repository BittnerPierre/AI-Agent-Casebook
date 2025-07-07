
from agents import Agent, RunContextWrapper, function_tool
from .file_search_agent import create_file_search_agent
from .file_search_planning_agent import create_file_planner_agent
from agents import Agent, ModelSettings, handoff
from openai import OpenAI
from .writer_agent import writer_agent, ReportData

from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX
from .utils import load_prompt_from_file
import os
from ..config import get_config
from .schemas import ResearchInfo

# Chemin vers le fichier de prompt
# Utiliser un chemin relatif par rapport au fichier actuel
current_dir = os.path.dirname(os.path.abspath(__file__))
RESEARCH_LEAD_PROMPT_PATH = os.path.join(current_dir, "prompts", "research_lead_agent_revised.md")

# Chargement du prompt depuis le fichier
ORCHESTRATOR_PROMPT = load_prompt_from_file(RESEARCH_LEAD_PROMPT_PATH)

if ORCHESTRATOR_PROMPT is None:
    raise ValueError("ORCHESTRATOR_PROMPT is None")

INSTRUCTIONS = (
    f"{RECOMMENDED_PROMPT_PREFIX}"
    f"{ORCHESTRATOR_PROMPT}"
)

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


@function_tool
async def fetch_vector_store_name(wrapper: RunContextWrapper[ResearchInfo]) -> str:  
    """
    Fetch the name of the vector store.
    Call this function to get the vector store name to upload file.
    """
    return f"The name of vector store is '{wrapper.context.vector_store_name}'."


@function_tool
async def display_agenda(wrapper: RunContextWrapper[ResearchInfo], agenda: str) -> str:  
    """
    Display the agenda in the conversation.
    Call this function to display the agenda in the conversation.
    """
    return f"#### Cartographie des concepts à explorer\n\n{agenda}"

# Factory function pour créer l'agent avec le serveur MCP
def create_research_supervisor_agent(mcp_server=None, research_info: ResearchInfo=None):
    mcp_servers = [mcp_server] if mcp_server else []

    file_planner_agent = create_file_planner_agent(mcp_server)
    file_search_agent = create_file_search_agent(research_info.vector_store_id)
    

    def on_handoff(ctx: RunContextWrapper[None]):
        print("Writer agent called")

    handoff_obj = handoff(
        agent=writer_agent,
        on_handoff=on_handoff,
        # tool_name_override="custom_handoff_tool",
        # tool_description_override="Custom description",
    )


    return Agent[ResearchInfo](
        name="ResearchSupervisorAgent",
        instructions=ORCHESTRATOR_PROMPT,
        model=model,
        handoffs=[
            writer_agent
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
            #     tool_name="write",
            #     tool_description="Write the full report based on the search results",
            # ),
            fetch_vector_store_name,
            display_agenda,
    ],
        # output_type=ReportData,
        mcp_servers=mcp_servers,
        model_settings=ModelSettings(tool_choice="required"),
    ) 