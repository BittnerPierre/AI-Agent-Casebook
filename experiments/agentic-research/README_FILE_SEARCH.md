# Recherche dans les Fichiers Vectorisés

Ce projet utilise maintenant la recherche dans les fichiers vectorisés au lieu de la recherche web.

## Architecture Simplifiée

- **FilePlannerAgent** : Planifie les requêtes de recherche basées sur la requête utilisateur
- **FileSearchAgent** : Effectue les recherches dans le vector store OpenAI avec `FileSearchTool`
- **ResearchManager** : Orchestre le workflow de recherche et génère le rapport final

## Utilisation

### Test rapide

```bash
cd experiments/agentic-research
python test_file_search.py
```

### Utilisation normale

```bash
cd experiments/agentic-research
python -m src.main
```

## Configuration

Le vector store est configuré dans `config.yaml`:

```yaml
vector_store:
  name: "agentic-research-vector-store"
  description: "Vector store for agentic research experiments"
  expires_after_days: 30
```

## Ajout de documents au vector store

Pour ajouter des documents au vector store:

```bash
cd experiments/agentic-research
python -m src.dataprep.core
```

Assurez-vous d'avoir un fichier `urls.txt` avec les URLs à traiter.

## Architecture des Agents

### FilePlannerAgent

- **Input** : Requête utilisateur (ex: "Agents")
- **Output** : Liste de `FileSearchItem` avec queries et raisons
- **Outil** : Aucun (pure génération de plan)

### FileSearchAgent

- **Input** : Terme de recherche + raison
- **Output** : Résumé concis des résultats trouvés
- **Outil** : `FileSearchTool(vector_store_ids=[...])`

### Workflow

1. Utilisateur saisit une requête
2. FilePlannerAgent génère 5-20 requêtes de recherche
3. FileSearchAgent effectue chaque recherche en parallèle
4. WriterAgent synthétise tous les résultats en rapport final

## Avantages

- **Simple** : Utilise directement `FileSearchTool` d'OpenAI
- **Efficace** : Recherches en parallèle
- **Scalable** : Fonctionne avec tout vector store OpenAI
- **Flexible** : Facile d'ajouter ou modifier les agents
