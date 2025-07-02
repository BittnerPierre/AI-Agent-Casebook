#!/usr/bin/env python3
"""
Script de test pour la recherche dans les fichiers vectorisés.
"""
import asyncio
import sys
from pathlib import Path

# Ajouter le répertoire src au path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.manager import ResearchManager


async def test_file_search():
    """Test de la recherche dans les fichiers."""
    
    print("🔍 Test de la recherche dans les fichiers vectorisés")
    print("=" * 50)
    
    # Créer le manager de recherche
    manager = ResearchManager()
    
    # Requête de test
    query = "Agents"
    print(f"Requête de test: {query}")
    print()
    
    try:
        # Lancer la recherche
        await manager.run(query)
        print("\n✅ Test terminé avec succès!")
        
    except Exception as e:
        print(f"\n❌ Erreur lors du test: {e}")
        raise


async def main():
    """Fonction principale."""
    await test_file_search()


if __name__ == "__main__":
    asyncio.run(main()) 