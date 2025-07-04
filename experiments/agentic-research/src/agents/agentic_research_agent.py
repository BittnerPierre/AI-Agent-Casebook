from pydantic import BaseModel
from agents import Agent
from agents.mcp import MCPServer
from .schemas import FileSearchPlan 
from .file_search_agent import file_search_agent
from .web_search_agent import web_search_agent
from .file_planner_agent import create_file_planner_agent
from agents import Agent, FileSearchTool, WebSearchTool, ModelSettings
from openai import OpenAI
from ..vector_store_manager import VectorStoreManager
from ..config import get_config
from .writer_agent import writer_agent, ReportData

from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX
from .utils import load_prompt_from_file
import os

# Chemin vers le fichier de prompt
# Utiliser un chemin relatif par rapport au fichier actuel
current_dir = os.path.dirname(os.path.abspath(__file__))
RESEARCH_LEAD_PROMPT_PATH = os.path.join(current_dir, "prompts", "research_lead_agent.md")

# Chargement du prompt depuis le fichier
ORCHESTRATOR_PROMPT = load_prompt_from_file(RESEARCH_LEAD_PROMPT_PATH)

if ORCHESTRATOR_PROMPT is None:
    raise ValueError("ORCHESTRATOR_PROMPT is None")


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
model = config.openai.model   

# Factory function pour créer l'agent avec le serveur MCP
def create_research_supervisor_agent(mcp_server=None):
    mcp_servers = [mcp_server] if mcp_server else []

    file_planner_agent = create_file_planner_agent(mcp_server)
    
    return Agent(
        name="ResearchSupervisorAgent",
        instructions=ORCHESTRATOR_PROMPT,
        model="gpt-4.1",
        # handoffs=[
        #     file_planner_agent, file_search_agent, writer_agent
        # ],
        tools=[
            file_planner_agent.as_tool(
                tool_name="plan_file_search",
                tool_description="Plan the file search",
            ),
            file_search_agent.as_tool(
                tool_name="file_search",
                tool_description="Search for relevant information in the knowledge base",
            ),
            writer_agent.as_tool(
                tool_name="write",
                tool_description="Write the report based on the search results",
            ),
    ],
        output_type=ReportData,
        mcp_servers=mcp_servers,
        model_settings=ModelSettings(tool_choice="required"),
    ) 