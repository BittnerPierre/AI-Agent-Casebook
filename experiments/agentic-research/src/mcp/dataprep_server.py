"""Serveur MCP pour les fonctions de préparation de données."""

import logging
from typing import Any

from fastmcp import FastMCP

from ..config import get_config
from ..dataprep.mcp_functions import (
    download_and_store_url,
    get_knowledge_entries,
    upload_files_to_vectorstore,
)

logger = logging.getLogger(__name__)


def create_dataprep_server() -> FastMCP:
    """Crée le serveur MCP pour les fonctions dataprep."""

    mcp = FastMCP(
        name="DataPrep MCP Server",
        instructions="""
        Serveur MCP pour la préparation de données et gestion de vector stores.
        
        Outils disponibles:
        - download_and_store_url: Télécharge et stocke une URL dans le système local
        - upload_files_to_vectorstore: Upload des fichiers vers un vector store OpenAI
        - get_knowledge_entries: Liste les entrées de la base de connaissances
        - check_vectorstore_file_status: Vérifie l'état des fichiers dans un vector store
        """,
    )

    @mcp.tool()
    def download_and_store_url_tool(url: str) -> str:
        """
        Télécharge et stocke une URL dans le système de gestion de connaissances local.

        Args:
            url: URL à télécharger et stocker

        Returns:
            str: Nom du fichier local créé (.md)
        """
        config = get_config()
        return download_and_store_url(url, config)

    @mcp.tool()
    def upload_files_to_vectorstore_tool(
        inputs: list[str], vectorstore_name: str
    ) -> dict[str, Any]:
        """
        Upload des fichiers vers un vector store OpenAI avec expiration 1 jour.

        Args:
            inputs: Liste d'URLs (qui seront résolues) ou noms de fichiers locaux
            vectorstore_name: Nom du vector store à créer

        Returns:
            Dict contenant vectorstore_id et informations sur les fichiers uploadés
        """
        config = get_config()
        result = upload_files_to_vectorstore(inputs, config, vectorstore_name)
        return result.model_dump()

    @mcp.tool()
    def get_knowledge_entries_tool() -> list[dict[str, Any]]:
        """
        Liste toutes les entrées de la base de connaissances.

        Returns:
            List[Dict]: Liste des entrées avec url, filename, title, keywords, openai_file_id
        """
        config = get_config()
        return get_knowledge_entries(config)

    # @mcp.tool()
    # def check_vectorstore_file_status(
    #     vectorstore_id: str,
    #     file_ids: List[str]
    # ) -> Dict[str, List[Dict[str, Any]]]:
    #     """
    #     Vérifie l'état de traitement des fichiers dans un vector store.

    #     Args:
    #         vectorstore_id: ID du vector store
    #         file_ids: Liste des IDs de fichiers à vérifier

    #     Returns:
    #         Dict avec statut de chaque fichier
    #     """
    #     client = OpenAI()
    #     results = []

    #     for file_id in file_ids:
    #         try:
    #             vector_store_file = client.vector_stores.files.retrieve(
    #                 vector_store_id=vectorstore_id,
    #                 file_id=file_id
    #             )
    #             results.append({
    #                 'file_id': file_id,
    #                 'status': vector_store_file.status,
    #                 'last_error': vector_store_file.last_error
    #             })
    #         except Exception as e:
    #             results.append({
    #                 'file_id': file_id,
    #                 'status': 'error',
    #                 'error': str(e)
    #             })

    #     return {'files': results}

    return mcp


def start_server(host: str = "0.0.0.0", port: int = 8001):
    """Démarre le serveur MCP dataprep."""
    server = create_dataprep_server()
    logger.info(f"Démarrage du serveur MCP DataPrep sur {host}:{port}")
    server.run(transport="sse", host=host, port=port)


def main():
    """Démarre le serveur MCP dataprep."""
    # Configuration du logging selon les mémoires [[memory:2246951870861751190]]
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    start_server()


if __name__ == "__main__":
    main()
