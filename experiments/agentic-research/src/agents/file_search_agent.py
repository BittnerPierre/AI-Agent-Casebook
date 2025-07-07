from agents import Agent, FileSearchTool
from agents.model_settings import ModelSettings

from ..config import get_config
from openai import OpenAI
#from .utils import get_vector_store_id_by_name
from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX

INSTRUCTIONS = (
    f"{RECOMMENDED_PROMPT_PREFIX}"
    """You are a research assistant. Given a search topic, you search through vectorized files and produce a COMPREHENSIVE summary of the results. 

    Your summary should be DETAILED and THOROUGH, capturing ALL relevant information found. Aim for 300-500 words per search result, including:
    - Complete explanations of concepts
    - Technical details when available
    - Specific examples and use cases
    - Advantages and limitations
    - Practical applications
    - Any relevant context or background

    Write in complete sentences with proper structure. This will be consumed by someone synthesizing a report, so it's vital to capture EVERYTHING relevant, not just the essence.

    The summary must be in the same language as the search topic."""
)

# Récupérer l'ID du vector store
config = get_config()
client = OpenAI()

def create_file_search_agent(vector_store_id:str=None):
    # vector_store_name = config.vector_store.name
    # vector_store_id = get_vector_store_id_by_name(client, vector_store_name)
    if vector_store_id is None:
        vector_store_id = config.vector_store.vector_store_id
    model = config.models.search_model

    file_search_agent = Agent(
        name="file_search_agent",
        instructions=INSTRUCTIONS,
        tools=[FileSearchTool(vector_store_ids=[vector_store_id])],
        model=model,
        model_settings=ModelSettings(tool_choice="required"),
    ) 

    return file_search_agent