from agents import Agent, FileSearchTool
from agents.model_settings import ModelSettings

from ..config import get_config
from ..dataprep.vector_store import vector_store_id
from openai import OpenAI

from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX

INSTRUCTIONS = (
    f"{RECOMMENDED_PROMPT_PREFIX}"
    "You are a research assistant. Given a search topic, you search through vectorized files "
    "and produce a concise summary of the results. The summary must be 2-3 paragraphs and less than 300 "
    "words. Capture the main points. Write concisely, no need for complete sentences or perfect grammar. "
    "This will be consumed by someone synthesizing a report, so it's vital to capture the essence and ignore the superfluous. "
    "Do not include any additional commentary other than the summary itself. "
    "The summary must be in the same language as the search topic."
)

# Récupérer l'ID du vector store depuis le module vector_store
config = get_config()
client = OpenAI()
model = config.openai.model

file_search_agent = Agent(
    name="file_search_agent",
    instructions=INSTRUCTIONS,
    tools=[FileSearchTool(vector_store_ids=[vector_store_id])],
    model=model,
    model_settings=ModelSettings(tool_choice="required"),
) 