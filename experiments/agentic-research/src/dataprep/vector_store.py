"""
Module de gestion des vector stores OpenAI.
Ce module centralise l'accès au VectorStoreManager pour éviter
la création multiple de vector stores.
"""

import logging
from openai import OpenAI

from ..vector_store_manager import VectorStoreManager
from ..config import get_config

logger = logging.getLogger(__name__)

# Créer une instance unique du VectorStoreManager qui sera utilisée dans toute l'application
client = OpenAI()
vector_store_manager = VectorStoreManager(client, get_config().vector_store)
vector_store_id = vector_store_manager.get_or_create_vector_store()

logger.info(f"Vector store initialisé: {vector_store_id}")

# Exporter les variables pour qu'elles soient accessibles depuis l'extérieur
__all__ = ['vector_store_manager', 'vector_store_id'] 