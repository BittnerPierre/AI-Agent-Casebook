import re
from datetime import datetime
from IPython.display import display, Markdown

def pretty_print_agent_response(response_obj):
    print(f"\n\033[1mID de la conversation :\033[0m {getattr(response_obj, 'conversation_id', '?')}\n")

    # Parcours des outputs
    for entry in getattr(response_obj, 'outputs', []):
        entry_type = getattr(entry, 'type', None)

        if entry_type == 'agent.handoff':
            print("\033[1mTransfert d'agent (Handoff) :\033[0m")
            print(f"  De : {getattr(entry, 'previous_agent_name', '?')}")
            print(f"  Vers : {getattr(entry, 'next_agent_name', '?')}")
            print(f"  Date : {getattr(entry, 'created_at', '?')}")
            print()
        elif entry_type == 'tool.execution':
            print("\033[1mExécution d'outil :\033[0m")
            print(f"  Outil : {getattr(entry, 'name', '?')}")
            print(f"  Début : {getattr(entry, 'created_at', '?')}")
            print(f"  Fin : {getattr(entry, 'completed_at', '?')}")
            print(f"  ID : {getattr(entry, 'id', '?')}")
            print()
        elif entry_type == 'message.output':
            print("\033[1mRéponse finale de l'agent :\033[0m")
            content = getattr(entry, 'content', [])
            # Gérer tous les cas de content
            if isinstance(content, str):
                print(f"  {content.strip()}")
                #display(Markdown(c ontent.strip()))
            elif isinstance(content, list):
                # Si l'agent est calculator-agent, on cherche reasoning et result
                if getattr(entry, 'agent_id', None) == 'calculator-agent':
                    for chunk in content:
                        chunk_type = getattr(chunk, 'type', None)
                        if chunk_type == 'json':
                            reasoning = chunk.get('reasoning', None)
                            result = chunk.get('result', None)
                            if reasoning:
                                print(f"  \033[94mRaisonnement :\033[0m {reasoning}")
                            if result:
                                print(f"  \033[92mRésultat :\033[0m {result}")
                            filename = chunk.get('filename', None)
                            if filename:
                                print(f"  \033[93mNom de fichier :\033[0m {filename}")
                        elif chunk_type == 'text':
                            # Affichage du texte
                            text = getattr(chunk, 'text', None)
                            if text and isinstance(text, str):
                                print(f"  {text.strip()}")
                                # display(Markdown(data=text))
                            # Affichage du nom de fichier si disponible
                            filename = getattr(chunk, 'filename', None)
                            if filename is None and isinstance(chunk, dict):
                                filename = chunk.get('filename', None)
                            if filename:
                                print(f"  \033[93mNom de fichier :\033[0m {filename}")
                else:
                    for chunk in content:
                        chunk_type = getattr(chunk, 'type', None)
                        if chunk_type == 'text':
                            # Affichage du texte
                            text = getattr(chunk, 'text', None)
                            if text and isinstance(text, str):
                                print(f"  {text.strip()}")
                                # display(Markdown(data=text))
                            # Affichage du nom de fichier si disponible
                            filename = getattr(chunk, 'filename', None)
                            if filename is None and isinstance(chunk, dict):
                                filename = chunk.get('filename', None)
                            if filename:
                                print(f"  \033[93mNom de fichier :\033[0m {filename}")
                # Affichage des sources
                sources = [
                    chunk for chunk in content
                    if getattr(chunk, 'type', None) == 'tool_reference'
                ]
                if sources:
                    print("\n  \033[4mSources citées :\033[0m")
                    for chunk in sources:
                        print(f"    - [{getattr(chunk, 'title', '?')}]({getattr(chunk, 'url', '?')}) via {getattr(chunk, 'tool', '?')}")
            else:
                # Cas inattendu (ex: dict), on affiche tout de même quelque chose
                print(f"  {str(content).strip()}")
            print()


def download_and_display_agent_images(response, client):
    """
    Télécharge et affiche toutes les images générées par un agent Mistral
    à partir d'une réponse contenant des ToolFileChunk.

    Args:
        response: La réponse de l'agent (contenant potentiellement des ToolFileChunk dans outputs[-1].content)
        client: Le client Mistral utilisé pour télécharger les fichiers
    """
    from mistralai.models import ToolFileChunk
    from IPython.display import Image, display

    for i, chunk in enumerate(response.outputs[-1].content):
        if isinstance(chunk, ToolFileChunk):
            # Télécharger le fichier image
            file_bytes = client.files.download(file_id=chunk.file_id).read()
            # Sauvegarder localement
            filename = f"plot_generated_{i}.png"
            with open(filename, "wb") as file:
                file.write(file_bytes)
            # Afficher l'image
            display(Image(filename=filename))