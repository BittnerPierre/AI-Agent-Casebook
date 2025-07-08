import os
from agents import Agent, RunContextWrapper

def load_prompt_from_file(file_path):
    """
    Charge un prompt depuis un fichier
    """
    try:
        with open(file_path, "r", encoding="utf-8") as file:
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

