"""Serveur MCP pour les fonctions de préparation de données."""

import logging
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional
from agents.mcp import MCPServer
from ..config import get_config
from ..dataprep.vector_store import initialize_vector_store
from ..dataprep.mcp_functions import (
    download_and_process_url,
    upload_files_to_vectorstore,
    search_vector_store
)

logger = logging.getLogger(__name__)

def main():
    """
    Fonction principale pour démarrer le serveur MCP pour les fonctions de préparation de données.
    """
    # Parsing des arguments CLI
    parser = argparse.ArgumentParser(description="Serveur MCP pour les fonctions de préparation de données")
    parser.add_argument("--port", type=int, default=8000, help="Port du serveur MCP")
    parser.add_argument("--host", default="127.0.0.1", help="Host du serveur MCP")
    parser.add_argument("--vector-store", help="Nom du vector store à utiliser")
    args = parser.parse_args()
    
    # Configuration du logging
    config = get_config()
    logging.basicConfig(
        level=getattr(logging, config.logging.level),
        format=config.logging.format
    )
    
    # Initialiser le vector store avec le nom spécifié (si fourni)
    if args.vector_store:
        logger.info(f"Initialisation du vector store personnalisé: {args.vector_store}")
        initialize_vector_store(args.vector_store)
    
    # Création et démarrage du serveur MCP
    logger.info(f"Démarrage du serveur MCP sur {args.host}:{args.port}")
    server = MCPServer(
        host=args.host,
        port=args.port,
        functions=[
            download_and_process_url,
            upload_files_to_vectorstore,
            search_vector_store
        ]
    )
    
    try:
        server.start()
    except KeyboardInterrupt:
        logger.info("Arrêt du serveur MCP")
    except Exception as e:
        logger.error(f"Erreur lors du démarrage du serveur MCP: {e}")
        raise

if __name__ == "__main__":
    main()