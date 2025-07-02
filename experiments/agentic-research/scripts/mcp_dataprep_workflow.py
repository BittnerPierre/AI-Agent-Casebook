"""
Script utilisant le MCP DataPrep pour reproduire la fonctionnalité de src.dataprep.core:main
"""
import logging
from pathlib import Path
from typing import List

# Import direct des fonctions (pas via MCP pour ce script)
from src.dataprep.mcp_functions import download_and_store_url, upload_files_to_vectorstore, get_knowledge_entries
from src.dataprep.knowledge_db import KnowledgeDBManager
from src.config import get_config

logger = logging.getLogger(__name__)


def load_urls_from_file(config) -> List[str]:
    """Charge les URLs depuis le fichier configuré."""
    urls_file_path = config.data.urls_file
    current_dir = Path(__file__).parent.parent
    urls_file = current_dir / urls_file_path
    
    if not urls_file.exists():
        raise FileNotFoundError(f"Fichier URLs non trouvé: {urls_file}")
    
    urls = []
    with open(urls_file, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            url = line.strip()
            if url and not url.startswith('#'):
                if url.startswith(('http://', 'https://')):
                    urls.append(url)
                else:
                    logger.warning(f"URL invalide ignorée (ligne {line_num}): {url}")
    
    if not urls:
        raise ValueError(f"Aucune URL valide trouvée dans le fichier: {urls_file}")
    
    return urls


def analyze_knowledge_base(config):
    """Analyse l'état actuel de la base de connaissances."""
    logger.info("=== ANALYSE DE LA BASE DE CONNAISSANCES ===")
    
    # État général
    entries = get_knowledge_entries(config)
    
    logger.info(f"📊 Total d'entrées: {len(entries)}")
    
    # Compter les fichiers avec openai_file_id
    openai_files_count = sum(1 for entry in entries if entry.get('openai_file_id'))
    logger.info(f"☁️  Fichiers uploadés sur OpenAI: {openai_files_count}")
    
    # Vérifier les fichiers locaux
    local_dir = Path(config.data.local_storage_dir)
    local_files_count = 0
    if local_dir.exists():
        for entry in entries:
            local_file = local_dir / entry['filename']
            if local_file.exists():
                local_files_count += 1
    
    logger.info(f"📁 Fichiers locaux disponibles: {local_files_count}")
    
    # Détails par entrée
    if entries:
        logger.info("\n=== DÉTAILS DES ENTRÉES ===")
        for entry in entries:
            status_icons = []
            local_file = local_dir / entry['filename'] if local_dir.exists() else None
            if local_file and local_file.exists():
                status_icons.append("📁")
            if entry.get('openai_file_id'):
                status_icons.append("☁️")
            if not status_icons:
                status_icons.append("❌")
            
            status_str = " ".join(status_icons)
            title = entry.get('title', 'Titre non disponible')
            logger.info(f"{status_str} {entry['filename']} - {title}")
    
    return entries


def main():
    """
    Fonction principale reproduisant le comportement de dataprep.core:main
    mais utilisant les nouvelles fonctions MCP optimisées.
    """
    config = get_config()
    
    # Configuration du logging selon les mémoires [[memory:2246951870861751190]]
    logging.basicConfig(
        level=getattr(logging, config.logging.level),
        format=config.logging.format
    )
    
    try:
        # 1. Analyser l'état actuel de la base
        analyze_knowledge_base(config)
        
        # 2. Charger les URLs
        urls = load_urls_from_file(config)
        logger.info(f"\nDébut du traitement de {len(urls)} URLs")
        
        # 3. Télécharger et stocker chaque URL
        filenames = []
        for url in urls:
            try:
                filename = download_and_store_url(url, config)
                filenames.append(filename)
                logger.info(f"✅ URL traitée: {url} -> {filename}")
            except Exception as e:
                logger.error(f"❌ Erreur pour {url}: {e}")
        
        if not filenames:
            logger.error("Aucun fichier n'a pu être traité")
            return
        
        # 4. Mode debug ou upload
        if config.debug.enabled:
            logger.info(f"\nMode debug activé - {len(filenames)} fichiers stockés localement")
            
            # Afficher le contenu de la base de connaissances
            entries = get_knowledge_entries(config)
            
            logger.info("\n=== BASE DE CONNAISSANCES FINALE ===")
            for entry in entries:
                openai_status = "📤 Uploadé" if entry.get('openai_file_id') else "📥 Local"
                logger.info(f"📄 {entry['filename']} ({openai_status})")
                logger.info(f"🔗 Source: {entry['url']}")
                keywords = entry.get('keywords', [])
                if keywords:
                    logger.info(f"🏷️  Mots-clés LLM: {', '.join(keywords[:5])}")
                if entry.get('openai_file_id'):
                    logger.info(f"🆔 OpenAI File ID: {entry['openai_file_id']}")
                logger.info("---")
                
        else:
            # Mode normal: upload vers vector store avec optimisations
            logger.info("\nMode normal - upload optimisé vers vector store")
            
            try:
                result = upload_files_to_vectorstore(
                    inputs=urls,  # Utiliser les URLs qui seront résolues
                    config=config,
                    vectorstore_name="agentic-research-batch"
                )
                
                logger.info("\n=== RAPPORT D'UPLOAD OPTIMISÉ ===")
                logger.info(f"Vector Store ID: {result.vectorstore_id}")
                logger.info(f"Total de fichiers demandés: {result.total_files_requested}")
                logger.info(f"Nouveaux uploads vers OpenAI: {result.upload_count}")
                logger.info(f"Fichiers réutilisés (déjà sur OpenAI): {result.reuse_count}")
                logger.info(f"Attachements réussis au vector store: {result.attach_success_count}")
                logger.info(f"Échecs d'attachement: {result.attach_failure_count}")
                
                logger.info("\n=== DÉTAILS DES FICHIERS ===")
                logger.info("📤 Uploads vers OpenAI Files API:")
                for file_info in result.files_uploaded:
                    status_icons = {
                        'uploaded': '🆕',
                        'reused': '♻️',
                        'failed': '❌'
                    }
                    icon = status_icons.get(file_info['status'], '❓')
                    logger.info(f"  {icon} {file_info['filename']} -> {file_info.get('file_id', 'N/A')}")
                
                logger.info("\n📎 Attachements au Vector Store:")
                for file_info in result.files_attached:
                    status_icon = "✅" if file_info['status'] == 'attached' else "❌"
                    logger.info(f"  {status_icon} {file_info['filename']}")
                    
            except Exception as e:
                logger.error(f"Erreur lors de l'upload: {e}")
                
    except Exception as e:
        logger.error(f"Erreur critique: {e}")
        raise


if __name__ == "__main__":
    main() 