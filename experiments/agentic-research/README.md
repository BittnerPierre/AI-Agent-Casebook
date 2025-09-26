# Research bot

This is a simple example of a multi-agent research assistant with local MCP. To run it:

```bash
poetry install
poetry run dataprep_server
poetry run agentic-research
```

## Architecture

The flow is:

1. User enters their research topic
2. `planner_agent` comes up with a plan to search the knowlege_base for information. The plan is a list of search queries, with a search term and a reason for each query.
3. For each search item, we run a `search_agent`, which uses the knowlege_base tool to search for that term and summarize the results. These all run in parallel.
4. Finally, the `writer_agent` receives the search summaries, and creates a written report.

## Utilisation du CLI

L'outil agentic-research peut être utilisé via Poetry avec différentes options :

### Options disponibles

- `--syllabus` : Chemin vers un fichier syllabus à utiliser comme requête
- `--manager` : Implémentation du manager à utiliser (options : `agentic_manager`, `manager`, ou chemin personnalisé)
- `--query` : Requête de recherche (alternative à l'entrée interactive)

### Exemples d'utilisation

```bash
# Mode interactif avec le manager par défaut
poetry run agentic-research

# Utiliser un fichier syllabus comme requête
poetry run agentic-research --syllabus syllabus.md

# Spécifier un manager particulier
poetry run agentic-research --syllabus syllabus.md --manager manager

# Spécifier un manager personnalisé
poetry run agentic-research --manager custom_module.CustomManager

# Passer directement une requête en ligne de commande
poetry run agentic-research --query "Retrieval Augmented Generation"

# Combiner plusieurs options
poetry run agentic-research --query "Agents in LLM" --manager agentic_manager
```

### Configuration

Le manager par défaut peut être configuré dans le fichier `config.yaml` :

```yaml
manager:
  default_manager: "agentic_manager" # Options: agentic_manager (Supervisor with CoT), deep_manager (Deep Agents approach), manager (simple example), ou chemin.vers.ClasseManager
```

Vous pouvez également définir le manager par défaut via la variable d'environnement `DEFAULT_MANAGER`.
