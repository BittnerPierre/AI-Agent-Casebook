# CLI Chat - Customer Onboarding

CLI interactif pour tester l'agent customer onboarding et générer des datasets d'évaluation avec annotations.

## Usage

### Lancement principal

```bash
cd incubating/customer_onboarding
uv run python run_cli_chat.py
```

### Tests unitaires

```bash
cd incubating/customer_onboarding
uv run python test_cli.py
```

## Fonctionnalités

### Interface

- **Conversation starters** : 4 questions prédéfinies pour démarrer
- **Chat interactif** : Conversation continue avec l'agent
- **Commandes spéciales** : `/quit`, `/save`, `/restart`
- **Annotations** : Évaluation des réponses (good/bad + explication)

### Sauvegarde

- Export automatique en JSON avec timestamp
- Structure adaptée pour évaluations (OpenAI Evals, LangSmith)
- Dossier : `conversations/`

## Format de données

### Conversation

```python
[
    {"role": "user", "content": "Bonjour, je veux ouvrir un compte"},
    {"role": "assistant", "content": "Bonjour ! Êtes-vous majeur ?"}
]
```

### Sauvegarde JSON

```json
{
  "session_id": "uuid",
  "timestamp": "2024-10-10T15:30:00",
  "conversation": [
    {
      "turn": 1,
      "user_input": "Message utilisateur",
      "agent_response": "Réponse agent",
      "annotation": {
        "quality": "good|bad",
        "explanation": "Explication optionnelle"
      }
    }
  ]
}
```

## Architecture

### Structure

```
customer_onboarding/
├── cli_chat/                # Package CLI générique
│   ├── __init__.py         # Exports du package
│   ├── core.py             # ChatSession, ChatCLI
│   ├── tests.py            # Tests du package
│   └── README.md           # Doc du package
├── my_agents/               # Agent definitions
│   ├── __init__.py
│   ├── agents.py           # Main agent logic
│   └── oauth.py            # OAuth configuration
├── agent_wrapper.py        # Wrapper customer onboarding
├── run_cli_chat.py         # Script de lancement
├── evals_simple.py         # Simple evaluations
├── evals_mcp.py            # MCP-based evaluations
├── faq.json                # FAQ database
├── error_db.json           # Error handling database
└── README.md               # Documentation principale
```

### Fichiers

- `cli_chat/` : Package CLI générique réutilisable
- `agent_wrapper.py` : Wrapper pour l'agent customer onboarding
- `run_cli_chat.py` : Script de lancement avec Poetry
- `test_cli.py` : Tests d'intégration (3 tests essentiels)

### Interface agent

Le CLI accepte toute fonction avec cette signature :

```python
def your_agent(conversation: List[Dict[str, str]]) -> str:
    # Votre logique
    return "Réponse de l'agent"
```

## Conversation starters

1. Bonjour, je voudrais ouvrir un compte bancaire. Pouvez-vous m'aider ?
2. Quelle est la différence entre une carte de CREDIT et une carte de DEBIT ?
3. Je n'arrive pas à recevoir l'email de confirmation pour mon compte
4. Je suis étudiant étranger, puis-je ouvrir un compte ?

## Annotation des réponses

Après chaque réponse de l'agent :

- `g` = good (bonne réponse)
- `b` = bad (mauvaise réponse)
- `s` = skip (ignorer l'annotation)

Explication optionnelle pour documenter le choix.

## Objectif

Ce CLI permet de :

1. **Tester manuellement** l'agent avec différents scénarios
2. **Générer des datasets** annotés pour l'évaluation automatisée
3. **Améliorer itérativement** l'agent basé sur les retours

Les fichiers JSON générés peuvent être utilisés directement avec les systèmes d'évaluation d'agents conversationnels.
