"""
Module de préparation des données pour la recherche agentique.

Ce module contient les fonctionnalités pour:
- Télécharger et traiter des documents web
- Gérer une base de connaissances locale
- Interagir avec les vector stores OpenAI
- Fournir des outils MCP pour les agents

Structure:
- core.py: Fonctions principales de traitement des documents
- knowledge_db.py: Gestion de la base de connaissances locale
- mcp_functions.py: Fonctions exposées via MCP
- models.py: Modèles de données Pydantic
- vector_store.py: Accès au vector store OpenAI
- web_loader_improved.py: Chargement et traitement des documents web
"""

from .vector_store import vector_store_manager, vector_store_id
