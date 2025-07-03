import os

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