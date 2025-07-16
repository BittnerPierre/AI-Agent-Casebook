import os
from agents import Agent, RunContextWrapper, function_tool
from .schemas import ResearchInfo, ReportData, FileFinalReport


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


@function_tool
async def write_final_report(wrapper: RunContextWrapper[ResearchInfo], report: ReportData, file_name: str) -> FileFinalReport:  
    """
    Write the file to the output directory.
    Call this function to write the file to the output directory.
    """
    output_dir = wrapper.context.output_dir
    file_path = os.path.join(output_dir, file_name)
    with open(file_path, "w", encoding="utf-8") as file:
        file.write(report.markdown_report)
        print(f"File written: {file_path}")
        print(f"Report: {report.markdown_report}")
        
    absolute_file_path = os.path.abspath(file_path)
    file_final_report = FileFinalReport(absolute_file_path=absolute_file_path,
                                        short_summary=report.short_summary,
                                        follow_up_questions=report.follow_up_questions
                                        )
    return file_final_report