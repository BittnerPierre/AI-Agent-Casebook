import logging
import tempfile
import re
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional
from openai import OpenAI
from ..config import get_config
from .vector_store import initialize_vector_store, get_vector_store
#from .web_loader import WebDocument, load_documents_from_urls
from .web_loader_improved import WebDocument, load_documents_from_urls

# Configuration du logger
config = get_config()
logger = logging.getLogger(__name__)

client = OpenAI()

# Le vector store sera initialisé plus tard, lors du traitement des arguments CLI


def format_document_as_markdown(doc: WebDocument) -> str:
    """
    Formate un document en markdown avec métadonnées.
    
    Args:
        doc: Document web à formater
        
    Returns:
        Contenu formaté en markdown
    """
    title = doc.metadata.get('title', 'Document sans titre')
    source_url = doc.metadata.get('source', 'URL inconnue')
    
    # Construction du markdown avec métadonnées
    markdown_content = f"""---
title: "{title}"
source: "{source_url}"
content_length: {len(doc.page_content)}
---

# {title}

**Source:** [{source_url}]({source_url})

## Contenu

{doc.page_content}

---
*Document traité automatiquement par le système de recherche agentique*
"""
    
    return markdown_content


def save_docs_to_markdown(docs_list: List[WebDocument], temp_dir: Path) -> List[Path]:
    """
    Sauvegarde les documents en format markdown dans le dossier temporaire.
    
    Args:
        docs_list: Liste des documents web
        temp_dir: Dossier temporaire pour sauvegarder les fichiers
        
    Returns:
        Liste des chemins des fichiers sauvegardés
    """
    saved_files = []
    
    for i, doc in enumerate(docs_list):
        # Générer un nom de fichier à partir du titre ou de l'URL
        title = doc.metadata.get('title', f'document_{i+1}')
        filename = f"{i+1:02d}_{title[:50]}.md"
        
        # Nettoyer le nom de fichier
        filename = re.sub(r'[^a-zA-Z0-9_.-]', '_', filename)
        filename = re.sub(r'_+', '_', filename)  # Supprimer les underscores multiples
        
        file_path = temp_dir / filename
        
        try:
            # Formater et sauvegarder le document
            markdown_content = format_document_as_markdown(doc)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            
            saved_files.append(file_path)
            logger.info(f"Document sauvegardé: {filename}")
            
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde de {filename}: {e}")
            
    return saved_files


def upload_files_to_vector_store(client: OpenAI, file_paths: List[Path], vector_store_id: str) -> Dict[str, Any]:
    """
    Upload les fichiers vers l'API Files OpenAI puis les attache au vector store.
    
    Cette approche en deux étapes permet de télécharger les fichiers ultérieurement,
    contrairement à l'upload direct au vector store.
    
    Args:
        client: Client OpenAI
        file_paths: Liste des chemins de fichiers à uploader
        vector_store_id: ID du vector store
        
    Returns:
        Résultats de l'upload avec statistiques
    """
    upload_results = {
        'success': [],
        'failures': [],
        'total_files': len(file_paths)
    }
    
    for file_path in file_paths:
        try:
            logger.info(f"Upload du fichier vers l'API Files: {file_path.name}")
            
            # Étape 1: Upload du fichier vers l'API Files OpenAI
            with open(file_path, 'rb') as file:
                file_upload_response = client.files.create(
                    file=file,
                    purpose='user_data'
                )
            
            file_id = file_upload_response.id
            logger.info(f"Fichier uploadé vers l'API Files avec l'ID: {file_id}")
            
            # Étape 2: Attacher le fichier au vector store
            logger.info(f"Attachement du fichier au vector store: {file_path.name}")
            
            vector_store_file = client.vector_stores.files.create(
                vector_store_id=vector_store_id,
                file_id=file_id
            )
            
            # Attendre que le fichier soit traité
            while vector_store_file.status == 'in_progress':
                logger.info(f"Traitement en cours pour {file_path.name}...")
                import time
                time.sleep(1)
                vector_store_file = client.vector_stores.files.retrieve(
                    vector_store_id=vector_store_id,
                    file_id=file_id
                )
            
            if vector_store_file.status == 'completed':
                upload_results['success'].append({
                    'filename': file_path.name,
                    'file_id': file_id,
                    'vector_store_file_id': vector_store_file.id
                })
                logger.info(f"Fichier attaché avec succès au vector store: {file_path.name}")
            else:
                raise Exception(f"Échec de l'attachement au vector store. Status: {vector_store_file.status}")
            
        except Exception as e:
            error_msg = f"Erreur lors de l'upload de {file_path.name}: {e}"
            logger.error(error_msg)
            upload_results['failures'].append({
                'filename': file_path.name,
                'error': str(e)
            })
    
    return upload_results


def process_urls_to_vectorstore(
    urls_file: str, 
    dry_run: bool = False, 
    verbose: bool = False,
    vector_store_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Traite une liste d'URLs pour les transformer en documents et les uploader vers un vector store.
    
    Args:
        urls_file: Chemin vers le fichier contenant les URLs (une par ligne)
        dry_run: Si True, n'effectue pas l'upload vers le vector store
        verbose: Si True, affiche plus de détails pendant le traitement
        vector_store_name: Nom du vector store à utiliser (optionnel)
        
    Returns:
        Dict contenant les résultats du traitement
    """
    # 1. Initialiser le vector store avec le nom spécifié (si fourni)
    if vector_store_name:
        vector_store_manager, vector_store_id = initialize_vector_store(vector_store_name)
    else:
        vector_store_manager, vector_store_id = get_vector_store()
    
    # Chargement des URLs depuis le fichier spécifié
    urls_path = Path(urls_file)
    if not urls_path.exists():
        raise FileNotFoundError(f"Le fichier d'URLs '{urls_file}' n'existe pas")
    
    urls = []
    with open(urls_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                urls.append(line)
    
    logger.info(f"{len(urls)} URLs chargées depuis {urls_path}")
    
    # Traitement des URLs
    logger.info(f"Début du traitement de {len(urls)} URLs")
    
    # Chargement des documents
    logger.info("Chargement des documents depuis les URLs...")
    docs_list = load_documents_from_urls(urls)
    logger.info(f"{len(docs_list)} documents chargés avec succès")
    
    # Mode dry-run: ne pas uploader vers le vector store
    if dry_run:
        logger.info("Mode dry-run - pas d'upload vers vector store")
        return {
            'total_urls': len(urls),
            'total_docs': len(docs_list),
            'total_files_saved': 0,
            'upload_results': None
        }
    
    # Mode normal: upload vers le vector store
    logger.info("Mode normal - upload vers vector store")
    
    # Création d'un dossier temporaire pour les fichiers markdown
    temp_dir = tempfile.mkdtemp(prefix="agentic_research_docs_")
    logger.info(f"Dossier temporaire créé: {temp_dir}")
    
    # Conversion des documents en markdown et sauvegarde dans le dossier temporaire
    logger.info("Conversion et sauvegarde des documents en markdown...")
    saved_files = []
    
    for i, doc in enumerate(docs_list):
        # Créer un nom de fichier basé sur le titre ou l'URL
        if doc.title:
            # Nettoyer le titre pour en faire un nom de fichier valide
            clean_title = re.sub(r'[^\w\s-]', '', doc.title)
            clean_title = re.sub(r'[-\s]+', '_', clean_title).strip('-_')
            filename = f"{i+1:02d}_{clean_title[:50]}.md"
        else:
            # Utiliser un nom générique basé sur l'URL
            domain = re.search(r'https?://(?:www\.)?([^/]+)', doc.url)
            domain_str = domain.group(1) if domain else "document"
            filename = f"{i+1:02d}_{domain_str}.md"
        
        # Sauvegarder le contenu markdown
        file_path = Path(temp_dir) / filename
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(doc.content)
        
        saved_files.append((filename, file_path))
        logger.info(f"Document sauvegardé: {filename}")
    
    logger.info(f"{len(saved_files)} fichiers markdown créés")
    
    # Upload des fichiers vers le vector store
    logger.info("Upload vers le vector store OpenAI...")
    
    upload_results = {
        'total': len(saved_files),
        'success': 0,
        'failures': 0,
        'files': []
    }
    
    for filename, file_path in saved_files:
        try:
            # Upload du fichier vers l'API Files
            logger.info(f"Upload du fichier vers l'API Files: {filename}")
            with open(file_path, 'rb') as file:
                response = client.files.create(
                    file=file,
                    purpose="assistants"
                )
            
            file_id = response.id
            logger.info(f"Fichier uploadé vers l'API Files avec l'ID: {file_id}")
            
            # Attachement du fichier au vector store
            logger.info(f"Attachement du fichier au vector store: {filename}")
            vector_store_file = client.vector_stores.files.create(
                vector_store_id=vector_store_id,
                file_id=file_id
            )
            
            # Attendre que le fichier soit traité
            logger.info(f"Traitement en cours pour {filename}...")
            file_status = client.vector_stores.files.retrieve(
                vector_store_id=vector_store_id,
                file_id=file_id
            )
            
            # Vérifier si le traitement a réussi
            if file_status.status == "processed":
                logger.info(f"Fichier attaché avec succès au vector store: {filename}")
                upload_results['success'] += 1
                upload_results['files'].append({
                    'filename': filename,
                    'file_id': file_id,
                    'status': 'success'
                })
            else:
                logger.warning(f"Problème avec le fichier {filename}: {file_status.status}")
                upload_results['failures'] += 1
                upload_results['files'].append({
                    'filename': filename,
                    'file_id': file_id,
                    'status': file_status.status
                })
        
        except Exception as e:
            logger.error(f"Erreur lors de l'upload du fichier {filename}: {e}")
            upload_results['failures'] += 1
            upload_results['files'].append({
                'filename': filename,
                'status': 'error',
                'error': str(e)
            })
    
    # Affichage du rapport d'upload
    logger.info("=== RAPPORT D'UPLOAD ===")
    logger.info(f"Total de fichiers traités: {upload_results['total']}")
    logger.info(f"Uploads réussis: {upload_results['success']}")
    logger.info(f"Échecs: {upload_results['failures']}")
    
    if upload_results['success'] > 0:
        logger.info("Fichiers uploadés avec succès:")
        for file_info in upload_results['files']:
            if file_info['status'] == 'success':
                logger.info(f"  - {file_info['filename']} (ID: {file_info['file_id']})")
    
    # Nettoyage du dossier temporaire
    import shutil
    shutil.rmtree(temp_dir)
    logger.info("Traitement terminé. Dossier temporaire nettoyé automatiquement.")
    
    return {
        'total_urls': len(urls),
        'total_docs': len(docs_list),
        'total_files_saved': len(saved_files),
        'upload_results': upload_results
    }


def create_processing_report(docs_list: List[WebDocument], saved_files: List[Path], report_path: Path) -> None:
    """
    Crée un rapport de synthèse du traitement des documents.
    
    Args:
        docs_list: Liste des documents traités
        saved_files: Liste des fichiers sauvegardés
        report_path: Chemin du fichier de rapport
    """
    import datetime
    
    report_content = f"""# Rapport de Traitement des Documents

**Date de traitement:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Résumé

- **Nombre de documents traités:** {len(docs_list)}
- **Nombre de fichiers créés:** {len(saved_files)}
- **Taille totale du contenu:** {sum(len(doc.page_content) for doc in docs_list):,} caractères

## Documents Traités

"""
    
    for i, doc in enumerate(docs_list, 1):
        title = doc.metadata.get('title', f'Document {i}')
        source = doc.metadata.get('source', 'Source inconnue')
        content_length = len(doc.page_content)
        
        report_content += f"""### {i}. {title}

- **Source:** {source}
- **Taille:** {content_length:,} caractères
- **Aperçu:** {doc.page_content[:150]}...

"""
    
    report_content += f"""
## Fichiers Créés

"""
    
    for file_path in saved_files:
        report_content += f"- `{file_path.name}`\n"
    
    report_content += f"""
---
*Rapport généré automatiquement par le système de recherche agentique*
"""
    
    try:
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report_content)
        logger.info(f"Rapport de synthèse créé: {report_path}")
    except Exception as e:
        logger.error(f"Erreur lors de la création du rapport: {e}")


if __name__ == "__main__":
    # Configuration du logging pour l'exécution directe
    logging.basicConfig(
        level=getattr(logging, config.logging.level),
        format=config.logging.format
    )
    
    # Parsing des arguments CLI
    parser = argparse.ArgumentParser(description="Traitement d'URLs pour vector store")
    parser.add_argument("--urls-file", default="urls.txt", help="Fichier contenant les URLs à traiter")
    parser.add_argument("--dry-run", action="store_true", help="Ne pas uploader vers le vector store")
    parser.add_argument("--verbose", action="store_true", help="Afficher plus de détails")
    parser.add_argument("--vector-store", help="Nom du vector store à utiliser")
    args = parser.parse_args()
    
    # Traitement des URLs
    results = process_urls_to_vectorstore(
        args.urls_file,
        dry_run=args.dry_run,
        verbose=args.verbose,
        vector_store_name=args.vector_store
    )

