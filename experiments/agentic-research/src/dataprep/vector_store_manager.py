"""Gestionnaire intelligent pour les vector stores OpenAI."""

import logging

from openai import OpenAI

logger = logging.getLogger(__name__)


class VectorStoreManager:
    """Gère automatiquement les vector stores par nom."""

    def __init__(self, vector_store_name: str = None, client: OpenAI = None):
        self._vector_store_name = vector_store_name
        self._client = client or OpenAI()
        self._vector_store_id: str | None = None

    def get_or_create_vector_store(self) -> str:
        """
        Trouve un vector store existant par nom ou en crée un nouveau.

        Returns:
            str: L'ID du vector store
        """
        if self._vector_store_id:
            return self._vector_store_id

        # 1. Chercher un vector store existant avec ce nom
        existing_id = self._find_existing_vector_store()
        if existing_id:
            logger.info(f"Vector store trouvé: {existing_id}")
            self._vector_store_id = existing_id
            return existing_id

        # 2. Créer un nouveau vector store si aucun trouvé
        new_id = self._create_new_vector_store()
        logger.info(f"Nouveau vector store créé: {new_id}")
        self._vector_store_id = new_id
        return new_id

    def _find_existing_vector_store(self) -> str | None:
        """Cherche un vector store existant par nom."""
        try:
            # Lister tous les vector stores
            response = self._client.vector_stores.list(limit=100)

            target_name = self._vector_store_name
            for vs in response.data:
                if vs.name == target_name:
                    logger.info(f"Vector store existant trouvé: {vs.id}")
                    return vs.id

            logger.info(f"Aucun vector store trouvé avec le nom: {target_name}")
            return None

        except Exception as e:
            logger.error(f"Erreur lors de la recherche: {e}")
            return None

    def _create_new_vector_store(self) -> str:
        """Crée un nouveau vector store."""
        try:
            logger.info(f"Création d'un nouveau vector store: {self._vector_store_name}")
            response = self._client.vector_stores.create(
                name=self._vector_store_name,
                expires_after={
                    "anchor": "last_active_at",
                    "days": 30,
                },  # Assuming a default expires_after_days
            )
            logger.info(f"Vector store créé avec succès: {response.id}")
            return response.id

        except Exception as e:
            logger.error(f"Erreur lors de la création: {e}")
            raise
