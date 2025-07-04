"""
Module de gestion des vector stores OpenAI.
Ce module centralise l'accès au VectorStoreManager pour éviter
la création multiple de vector stores.
"""

import logging
from typing import Optional
from openai import OpenAI

from ..vector_store_manager import VectorStoreManager
from ..config import get_config, VectorStoreConfig

logger = logging.getLogger(__name__)

# Variables globales pour stocker les instances uniques
_vector_store_manager = None
_vector_store_id = None
_client = None

def initialize_vector_store(vector_store_name: Optional[str] = None):
    """
    Initialise le vector store avec le nom spécifié.
    Cette fonction doit être appelée après le parsing des arguments CLI.
    
    Args:
        vector_store_name: Nom du vector store à utiliser (optionnel)
    
    Returns:
        tuple: (vector_store_manager, vector_store_id)
    """
    global _vector_store_manager, _vector_store_id, _client
    
    if _client is None:
        _client = OpenAI()
    
    config = get_config()
    
    # Si un nom personnalisé est fourni, créer une config temporaire
    if vector_store_name and vector_store_name != config.vector_store.name:
        logger.info(f"Utilisation d'un vector store personnalisé: {vector_store_name}")
        temp_config = VectorStoreConfig(
            name=vector_store_name,
            description=f"Vector store personnalisé: {vector_store_name}",
            expires_after_days=config.vector_store.expires_after_days
        )
        _vector_store_manager = VectorStoreManager(_client, temp_config)
    else:
        # Utiliser la config par défaut
        vector_store_name = config.vector_store.name
        logger.info(f"Utilisation du vector store par défaut: {vector_store_name}")
        _vector_store_manager = VectorStoreManager(_client, config.vector_store)
    
    _vector_store_id = _vector_store_manager.get_or_create_vector_store()
    logger.info(f"Vector store initialisé: {_vector_store_id}")
    
    return _vector_store_manager, _vector_store_id

def get_vector_store():
    """
    Récupère le vector store manager et l'ID.
    Si le vector store n'a pas été initialisé, l'initialise avec les valeurs par défaut.
    
    Returns:
        tuple: (vector_store_manager, vector_store_id)
    """
    global _vector_store_manager, _vector_store_id
    
    if _vector_store_manager is None or _vector_store_id is None:
        return initialize_vector_store()
    
    return _vector_store_manager, _vector_store_id

def reset_vector_store():
    """
    Réinitialise les variables globales du vector store.
    Utile pour les tests ou pour forcer une réinitialisation.
    """
    global _vector_store_manager, _vector_store_id
    _vector_store_manager = None
    _vector_store_id = None 