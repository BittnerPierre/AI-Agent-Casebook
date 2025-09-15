import os
from agents import Agent, RunContextWrapper, function_tool
from .schemas import ResearchInfo, ReportData, FileFinalReport
from agents.mcp import ToolFilterContext



def load_prompt_from_file(folder_path: str, file_path: str) -> str:
    """
    Charge un prompt depuis un fichier
    """
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        prompt_path = os.path.join(current_dir, folder_path, file_path)
        with open(prompt_path, "r", encoding="utf-8") as file:
            return file.read()
    except FileNotFoundError:
        print(f"Attention: Le fichier de prompt {file_path} n'a pas été trouvé.")
        return None
    


def get_vector_store_id_by_name(client, vector_store_name):
    # Récupérer la liste des vector stores
    vector_stores = client.vector_stores.list()

    # Rechercher le vector store par nom
    for vector_store in vector_stores:
        if vector_store.name == vector_store_name:
            return vector_store.id
    
    # Si le vector store n'est pas trouvé, retourner None
    return None


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


def generate_final_report_filename(research_topic: str) -> str:
    """
    Génère un nom de fichier pour le rapport final selon les règles de nommage.
    """
    import re
    import datetime
    # Appliquer les règles de nommage
    topic = research_topic.lower()
    topic = re.sub(r'\s+', '_', topic)
    topic = re.sub(r'[^a-z0-9_]', '', topic)
    topic = topic[:50]
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{topic}_final_report_{timestamp}.md"

@function_tool
async def save_report(wrapper: RunContextWrapper[ResearchInfo],
                            research_topic: str,
                            markdown_report: str,
                            short_summary: str,
                            follow_up_questions: list[str],
                            ) -> ReportData:  
    """
    Sauvegarde le rapport .
    Appelez cet outil pour sauvegarder le rapport.
    """
    return await save_final_report_function(wrapper.context.output_dir, research_topic, markdown_report, short_summary, follow_up_questions)


async def save_final_report_function(output_dir: str,
                            research_topic: str,
                            markdown_report: str,
                            short_summary: str,
                            follow_up_questions: list[str],
                            ) -> ReportData:  
    """
    Écrit le rapport final.
    Appelez cette fonction pour écrire le rapport final.
    """
    file_name = generate_final_report_filename(research_topic)
    file_path = os.path.join(output_dir, file_name)
    with open(file_path, "w", encoding="utf-8") as file:
        file.write(markdown_report)
        # Remplacer print par logger si le framework de logging est en place
        # print(f"File written: {file_path}")
    return ReportData(file_name=file_name,
                      markdown_report=markdown_report,
                      research_topic=research_topic,
                      short_summary=short_summary,
                      follow_up_questions=follow_up_questions)

MS_FS_TOOLS = [
    "read_file",
    "read_multiple_files",
    "write_file",
    "edit_file",
    "create_directory",
    "list_directory",
    "list_directory_with_sizes",
    "directory_tree",
    "move_file",
    "search_files",
    "get_file_info",
    "list_allowed_directories"
]

MS_DATAPREP_TOOLS = [
    "download_and_store_url_tool",
    "upload_files_to_vectorstore_tool",
    "get_knowledge_entries_tool",
    "check_vectorstore_file_status"
]

WRITER_AGENT_TOOLS = [
    "save_report",
    "read_file",
    "read_multiple_files",
    "list_directory",
]


def some_filtering_logic(agent_name, server_name, tool) -> bool:
    tool_name = tool.name
    if agent_name == "writer_agent":
        if tool_name in WRITER_AGENT_TOOLS:
            return True
        else:
            return False
    else:
        return True


# Context-aware filter
def context_aware_filter(context: ToolFilterContext, tool) -> bool:
    """Filter tools based on context information."""
    # Access agent information
    agent_name = context.agent.name

    # Access server information  
    server_name = context.server_name

    # Implement your custom filtering logic here
    return some_filtering_logic(agent_name, server_name, tool)

