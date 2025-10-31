# Package CLI Chat

Package générique, configurable et portable pour créer des CLI de test d'agents conversationnels avec génération de datasets d'évaluation.

## 🎯 Objectif

Ce package permet de tester manuellement des agents conversationnels et de générer des datasets annotés pour l'évaluation automatisée. Il est conçu pour être **copié/collé** dans d'autres projets avec un minimum de modifications.

## 📁 Structure

```
cli_chat/
├── __init__.py         # Exports du package
├── core.py             # ChatSession, ChatCLI
├── config.py           # Configuration externalisée
├── base_wrapper.py     # Wrapper générique pour agents
├── tests.py            # Tests unitaires
└── README.md           # Cette documentation
```

## 🚀 Usage rapide

### Installation

Copiez le dossier `cli_chat/` dans votre projet.

### Usage basique

```python
from cli_chat import ChatCLI

def my_agent(conversation):
    # Votre logique d'agent
    return "Ma réponse"

cli = ChatCLI(agent_callback=my_agent)
cli.run()
```

### Usage configurable

```python
from cli_chat import ChatCLI, DEFAULT_CONVERSATION_STARTERS

# Configuration personnalisée
custom_starters = [
    "Hello, how can I help you?",
    "What services do you offer?",
    "I need technical support"
]

cli = ChatCLI(
    agent_callback=my_agent,
    output_dir="my_conversations",
    conversation_starters=custom_starters
)
cli.run()
```

## 🔧 Composants

### Core (`core.py`)

- **`ChatSession`** : Gestion des sessions avec sauvegarde JSON
- **`ChatCLI`** : Interface CLI interactive avec annotations

### Configuration (`config.py`)

- **`DEFAULT_CONVERSATION_STARTERS`** : Questions prédéfinies
- **`DEFAULT_OUTPUT_DIR`** : Répertoire de sauvegarde
- **`INTERFACE_MESSAGES`** : Messages d'interface personnalisables

### Wrappers (`base_wrapper.py`)

- **`BaseAgentWrapper`** : Classe abstraite pour agents
- **`SimpleAgentWrapper`** : Wrapper simple pour fonctions

### Tests (`tests.py`)

- Tests unitaires du package
- 3 tests essentiels : Session, CLI, Intégration

## 🎨 Personnalisation

### Conversation Starters

```python
from cli_chat import ChatCLI

my_starters = [
    "Bonjour, comment allez-vous ?",
    "Quel est votre problème ?",
    "Avez-vous besoin d'aide ?"
]

cli = ChatCLI(
    agent_callback=my_agent,
    conversation_starters=my_starters
)
```

### Messages d'interface

```python
from cli_chat import INTERFACE_MESSAGES

# Modifier les messages (optionnel)
INTERFACE_MESSAGES["welcome"] = "🎉 Mon CLI Personnalisé"
INTERFACE_MESSAGES["thinking"] = "🧠 Mon agent réfléchit..."
```

## 🔌 Wrapper d'agent

### Utilisation simple

```python
from cli_chat import SimpleAgentWrapper

def my_function(conversation):
    return "Ma réponse"

wrapper = SimpleAgentWrapper(my_function)
cli = ChatCLI(agent_callback=wrapper)
```

### Wrapper personnalisé

```python
from cli_chat import BaseAgentWrapper

class MyAgentWrapper(BaseAgentWrapper):
    def setup(self):
        # Configuration de votre agent
        self.api_key = "your-api-key"

    def call_agent(self, conversation):
        # Logique d'appel à votre agent
        return "Réponse de mon agent"

wrapper = MyAgentWrapper()
cli = ChatCLI(agent_callback=wrapper)
```

## 🧪 Tests

```bash
# Depuis le répertoire parent
python -m cli_chat.tests

# Ou directement
python cli_chat/tests.py
```

## 📊 Format de sauvegarde

```json
{
  "session_id": "uuid",
  "timestamp": "2024-10-10T15:30:00",
  "conversation": [
    {
      "turn": 1,
      "user_input": "Bonjour",
      "agent_response": "Bonjour ! Comment puis-je vous aider ?",
      "annotation": {
        "quality": "good",
        "explanation": "Réponse appropriée"
      }
    }
  ]
}
```

## ✨ Fonctionnalités

- **🔧 Configurable** : Conversation starters, messages, répertoires
- **📦 Portable** : Aucune dépendance externe, facilement copiable
- **🎯 Générique** : Compatible avec tout type d'agent
- **📝 Annotations** : Système d'évaluation intégré (good/bad + explication)
- **💾 Sauvegarde** : Export JSON automatique pour datasets
- **🧪 Testable** : Tests unitaires inclus
- **🔌 Extensible** : Système de wrappers pour différents agents

## 🚀 Exemples d'intégration

### API OpenAI

```python
import openai
from cli_chat import BaseAgentWrapper

class OpenAIWrapper(BaseAgentWrapper):
    def setup(self):
        self.client = openai.OpenAI(api_key="your-key")

    def call_agent(self, conversation):
        response = self.client.chat.completions.create(
            model="gpt-4",
            messages=conversation
        )
        return response.choices[0].message.content
```

### API REST

```python
import requests
from cli_chat import BaseAgentWrapper

class RestAPIWrapper(BaseAgentWrapper):
    def setup(self):
        self.base_url = "https://api.example.com"

    def call_agent(self, conversation):
        response = requests.post(
            f"{self.base_url}/chat",
            json={"messages": conversation}
        )
        return response.json()["response"]
```

Ce package est conçu pour être **autonome** et **réutilisable** dans n'importe quel projet ! 🎉
