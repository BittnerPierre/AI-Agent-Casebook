from agents import Agent, FileSearchTool
from agents.model_settings import ModelSettings

from ..config import get_config
from ..vector_store_manager import VectorStoreManager
from openai import OpenAI

from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX

INSTRUCTIONS = (
    f"{RECOMMENDED_PROMPT_PREFIX}"
    "You are a research assistant. Given a search topic, you search through vectorized files "
    "and produce a concise summary of the results. The summary must be 2-3 paragraphs and less than 300 "
    "words. Capture the main points. Write concisely, no need for complete sentences or perfect "
    "grammar. This will be consumed by someone synthesizing a report, so it's vital to capture "
    "the essence and ignore the superfluous. Do not include any additional commentary other than the summary itself."
)

# Récupérer l'ID du vector store
config = get_config()
client = OpenAI()
manager = VectorStoreManager(client, config.vector_store)
vector_store_id = manager.get_or_create_vector_store()

file_search_agent = Agent(
    name="File search agent",
    instructions=INSTRUCTIONS,
    tools=[FileSearchTool(vector_store_ids=[vector_store_id])],
    model_settings=ModelSettings(tool_choice="required"),
) 