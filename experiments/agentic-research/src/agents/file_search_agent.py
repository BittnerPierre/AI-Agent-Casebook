from agents import Agent, FileSearchTool
from agents.model_settings import ModelSettings

from ..config import get_config
from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX
from agents.mcp import MCPServer
from agents import RunContextWrapper
from .schemas import ResearchInfo, FileSearchResult
from .utils import load_prompt_from_file


INSTRUCTIONS = (
    f"{RECOMMENDED_PROMPT_PREFIX}"
    """You are a research assistant. 
    
    Given a search topic, you search through vectorized files and produce a COMPREHENSIVE summary of the results. 

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

INSTRUCTIONS_V2 = (
    f"{RECOMMENDED_PROMPT_PREFIX}"
    """You are a research assistant.  

    Given a search topic, your task is to search through vectorized files and produce a clear, CONCISE and RELEVANT summary of the results.

    Focus on the KEY points only:
    - Main concepts (1–2 sentences per concept)
    - Only essential technical details
    - 1–2 practical examples or use cases maximum
    - One paragraph on clear advantages and limitations
    - Skip generic background if not directly useful
    - NO unnecessary repetition or filler phrases

    Write a single well-structured text, 200–300 words maximum.  
    Use bullet points sparingly if they clarify the ideas.

    Your goal is to produce a **sharp, dense, actionable summary** — not a lecture.  
    This will be consumed by someone synthesizing a final report, so capture the essence **clearly**, but do not overload with every possible detail.

    Write in the same language as the search topic.
   """
)

INSTRUCTIONS_V3 = (
    f"{RECOMMENDED_PROMPT_PREFIX}"
    """You are a research assistant.

    Given a search term, search the web or vector store for that term and produce a **clear, concise, relevant summary**.

    Your summary must follow these rules:
    - **2–3 short paragraphs maximum**
    - **Max 300 words**
    - Use bullet points only if needed for clarity.
    - No unnecessary background — focus only on the main facts.
    - No filler or redundant phrases.
    - No commentary, disclaimers or explanations — only the raw summary.

    **Delivery rule:**  
    - When done, you MUST store the entire summary using the `write_file` function.
    - DO NOT print the summary directly in your reply — only call `write_file`.
    - The `filename` must be the search term.
    - The `content` must be your summary text.
    - If you do not use `write_file`, your task is incomplete and will be rejected.
    - In your final reply, return only the following JSON object between code markdown blocks: 
    ```json
    {
        "file_written": "<filename>.txt"
    }
    ```
    Do not include any other text.

    ## FILENAME RULES

    When you use `write_file`:
    - Always convert the search topic to lowercase.
    - Replace spaces with underscores `_`.
    - Remove special characters (keep only letters, numbers, underscores).
    - Limit filename length to 50 characters maximum.
    - Always add `.txt` at the end.

    Example:  
    Search term: "Multi Agent Orchestration" → Filename: `multi_agent_orchestration.txt`

    Write in the same language as the search term.

   """
)

prompt_file = "file_search_prompt.md"

def dynamic_instructions(
    context: RunContextWrapper[ResearchInfo], agent: Agent[ResearchInfo]
) -> str:
    
    prompt_template = load_prompt_from_file("prompts", prompt_file)

    if prompt_template is None:
        raise ValueError(f"{prompt_file} is None")

    dynamic_prompt = prompt_template.format(
        RECOMMENDED_PROMPT_PREFIX=RECOMMENDED_PROMPT_PREFIX
    )

    return (f"{dynamic_prompt}"
            f"The absolute path to **temporary filesystem** is `{context.context.temp_dir}`."
              " You MUST use it to write and read temporary data.\n\n"
            # f"The absolute path to **output filesystem** is `{context.context.output_dir}`."
            #   " You MUST use it to write and read output final content.\n\n"
        )



def create_file_search_agent(mcp_servers:list[MCPServer]=None, vector_store_id:str=None):

    mcp_servers = mcp_servers if mcp_servers else []

    config = get_config()

    model = config.models.search_model

    file_search_agent = Agent(
        name="file_search_agent",
        handoff_description="Given a search topic, search through vectorized files and produce a clear, CONCISE and RELEVANT summary of the results.",
        instructions=dynamic_instructions,
        tools=[FileSearchTool(vector_store_ids=[vector_store_id])],
        model=model,
        model_settings=ModelSettings(tool_choice="required"),
        mcp_servers=mcp_servers,
        output_type=FileSearchResult,   
    )

    return file_search_agent    
