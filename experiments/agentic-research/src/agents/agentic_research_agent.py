from pydantic import BaseModel

from agents import Agent
from .schemas import FileSearchPlan 
from .file_search_agent import file_search_agent
from .web_search_agent import web_search_agent
from .file_planner_agent import file_planner_agent
from agents import Agent, FileSearchTool, WebSearchTool, ModelSettings
from openai import OpenAI
from ..vector_store_manager import VectorStoreManager
from ..config import get_config
from .writer_agent import writer_agent, ReportData

ORCHESTRATOR_PROMPT = """
{RECOMMENDED_PROMPT_PREFIX  }

Analyze this task and break it down into 2-3 distinct approaches:

Task: {task}

Return your response in this format:

<analysis>
Explain your understanding of the task and which variations would be valuable.
Focus on how each approach serves different aspects of the task.
</analysis>

<tasks>
    <task>
    <type>formal</type>
    <description>Write a precise, technical version that emphasizes specifications</description>
    </task>
    <task>
    <type>conversational</type>
    <description>Write an engaging, friendly version that connects with readers</description>
    </task>
</tasks>
"""

WORKER_PROMPT = """
Generate content based on:
Task: {original_task}
Style: {task_type}
Guidelines: {task_description}

Return your response in this format:

<response>
Your content here, maintaining the specified style and fully addressing requirements.
</response>
"""

config = get_config()
client = OpenAI()
manager = VectorStoreManager(client, config.vector_store)
vector_store_id = manager.get_or_create_vector_store()

sub_agent = Agent(
        name="SubAgent",
        instructions=WORKER_PROMPT,
        model="gpt-4o",
    )


research_agent = Agent(
    name="ResearchAgent",
    instructions=ORCHESTRATOR_PROMPT,
    model="gpt-4o",
    handoffs=[
        file_search_agent, writer_agent, file_planner_agent, web_search_agent
    ],
    output_type=ReportData
) 