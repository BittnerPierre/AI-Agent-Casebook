# Histoire de l'Intégration GPT-5 dans Agentic Research

## Vue d'ensemble

Ce document trace l'historique des modifications apportées pour intégrer le support GPT-5 dans le système agentic-research, les problèmes de compatibilité rencontrés, et les solutions mises en place.

## Chronologie des Commits

### Commit Initial GPT-5: `1d2d9bc`
**Titre:** feat: Integrate GPT-5 support and comprehensive model enhancements with bug fixes

### Commit Final: `c31d5e7`
**Titre:** feat: Integrate GPT-5 support and comprehensive model enhancements with bug fixes (#135)

## Configuration des Modèles

### Configuration Avant GPT-5 (commit `2669ca0`)
```yaml
models:
  research_model: "openai/gpt-4.1-mini"
  planning_model: "litellm/anthropic/claude-3-7-sonnet-20250219"
  search_model: "openai/gpt-4.1-mini"
  writer_model: "litellm/mistral/mistral-medium-latest"
  knowledge_preparation_model: "litellm/mistral/mistral-medium-latest"
  reasoning_model: "litellm/anthropic/claude-3-7-sonnet-20250219"
```

### Configuration Première Intégration GPT-5 (commit `1d2d9bc`)
```yaml
models:
  research_model: "openai/gpt-5-mini"
  planning_model: "openai/gpt-5-mini"
  search_model: "openai/gpt-5-mini"
  writer_model: "openai/gpt-5-mini"
  knowledge_preparation_model: "openai/gpt-5-mini"
  reasoning_model: "openai/gpt-5-mini"
```

### Configuration Actuelle
```yaml
models:
  research_model: "openai/gpt-5-mini"
  planning_model: "openai/gpt-5-mini"
  search_model: "oopenai/gpt-5-mini"  # Note: typo détecté
  writer_model: "openai/gpt-5-mini"
  knowledge_preparation_model: "openai/gpt-5-mini"
```

## Modifications Techniques Spécifiques à GPT-5

### 1. Sélection d'Outils Automatique

**Problème:** Les anciens modèles nécessitaient des configurations `tool_choice` spécifiques.
**Solution:** Passage à `tool_choice="auto"` pour GPT-5.

**Fichiers modifiés:**
- `src/agents/agentic_research_agent.py:109`
- `src/agents/file_search_agent.py:50` 
- `src/agents/knowledge_preparation_agent.py:50`

```python
model_settings=ModelSettings(tool_choice="auto")
```

### 2. Suppression du Filtre d'Historique pour Mistral

**Fichier:** `src/agents/agentic_research_agent.py:78-81`

**Problème:** Mistral avait des problèmes avec le format des IDs d'appels d'outils (erreur `invalid_function_call`).
**Solution pour Mistral:** Filtre `remove_all_tools` était appliqué.
**Changement pour GPT-5:** Filtre retiré car GPT-5 supporte mieux le format.

```python
# no need to pass the history to the writer agent as it is handle via file, and it will failed with mistral due to the call id format (invalid_function_call error)
# TRY TO PASS THE HISTORY TO THE WRITER AGENT TO CHECK ISSUE WITH GPT-5
# input_filter=handoff_filters.remove_all_tools,
```

### 3. Configuration Writer Agent

**Fichier:** `src/agents/file_writer_agent.py:107`

**Changement:** `tool_choice="required"` commenté pour permettre plus de flexibilité avec GPT-5.

```python
model_settings = ModelSettings(
    #tool_choice="required",  # Commenté pour GPT-5
    metadata={"agent_type": "sub-agent", "trace_type": "agent"}
)
```

### 4. Ajustement des Paramètres de Recherche

**Changement:** `max_search_plan` réduit de `"5-7"` à `"2-3"` pour optimiser les performances avec GPT-5.

## Problèmes de Compatibilité Identifiés

### 1. Compatibilité Multi-Modèles
- **Problème:** Configuration hardcodée sur GPT-5 empêche l'utilisation d'autres modèles
- **Impact:** `tool_choice="auto"` n'est pas supporté par tous les modèles
- **Solution nécessaire:** Paramétrage conditionnel selon le modèle

### 2. Gestion des Filtres d'Historique
- **Problème:** Suppression du filtre `remove_all_tools` casse Mistral
- **Impact:** Format incompatible des IDs d'appels d'outils avec Mistral
- **Solution nécessaire:** Application conditionnelle du filtre selon le modèle

### 3. Configuration Tool Choice
- **Problème:** Configurations différentes selon les capacités des modèles
- **Impact:** Certains modèles ne supportent pas `tool_choice="auto"`
- **Solution nécessaire:** Configuration adaptative

## Recommendations pour la Compatibilité

### 1. Configuration Conditionnelle des Modèles
```python
def get_model_settings(model_name: str) -> ModelSettings:
    if "mistral" in model_name.lower():
        return ModelSettings(tool_choice="required")
    elif "gpt-5" in model_name.lower():
        return ModelSettings(tool_choice="auto")
    else:
        return ModelSettings()  # Default
```

### 2. Filtres Adaptatifs
```python
def get_handoff_filter(model_name: str):
    if "mistral" in model_name.lower():
        return handoff_filters.remove_all_tools
    return None  # Pas de filtre pour GPT-5
```

### 3. Paramètres de Recherche Adaptatifs
```python
def get_search_plan_count(model_name: str) -> str:
    if "gpt-5" in model_name.lower():
        return "2-3"  # Optimisé pour GPT-5
    return "5-7"  # Default pour autres modèles
```

## Status Actuel

- ✅ GPT-5 fonctionne correctement
- ❌ Compatibilité avec Mistral cassée
- ❌ Compatibilité avec Claude cassée  
- ❌ Configuration hardcodée sur GPT-5

## Actions Nécessaires

1. Implémenter la configuration conditionnelle des modèles
2. Restaurer les filtres adaptatifs pour Mistral
3. Tester la compatibilité avec tous les modèles précédents
4. Créer des configurations par défaut robustes

---
*Document généré le $(date) - Commit de référence: c31d5e7*