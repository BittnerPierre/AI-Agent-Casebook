"""
Configuration du CLI Chat.

Fichier de configuration externalisé pour faciliter la réutilisation du package
dans différents projets avec un minimum de modifications.
"""

# Conversation starters par défaut (modifiables)
DEFAULT_CONVERSATION_STARTERS = [
    "Bonjour, je voudrais ouvrir un compte bancaire. Pouvez-vous m'aider ?",
    "Quelle est la différence entre une carte de CREDIT et une carte de DEBIT ?",
    "Je n'arrive pas à recevoir l'email de confirmation pour mon compte",
    "Je suis étudiant étranger, puis-je ouvrir un compte ?",
    "Bonjour, je suis Marc Lefévre. J'essaye d'ouvrir un compte bancaire via l'application mobile. Mais je ne recois pas l'email de confirmation. Mon email est 'marc.lefevre+test2@example.com'. Comment puis-je résoudre ce problème ?"
]

# Répertoire de sauvegarde par défaut
DEFAULT_OUTPUT_DIR = "conversations"

# Messages d'interface
INTERFACE_MESSAGES = {
    "welcome": "🤖 CLI Chat Interactif",
    "commands_help": """Commandes spéciales:
  /quit    - Quitter et sauvegarder
  /save    - Sauvegarder la conversation
  /restart - Redémarrer une nouvelle session""",
    "starters_prompt": "📝 Conversation Starters:",
    "starters_instruction": "0. Saisir votre propre message",
    "choice_prompt": "\nChoisissez une option (0-{max_choice}): ",
    "annotation_prompt": "\n📊 Évaluez cette réponse (g=good, b=bad, s=skip): ",
    "explanation_prompt": "💬 Explication optionnelle: ",
    "thinking": "\n🤔 Agent réfléchit...",
    "user_prefix": "\n➡️ Vous: ",
    "agent_prefix": "\n⬅️ Agent: ",
    "save_success": "💾 Conversation sauvegardée: {filename}",
    "goodbye": "\n👋 Au revoir !",
    "restart": "🔄 Nouvelle session démarrée",
    "error_input": "❌ Erreur: Impossible de lire l'entrée utilisateur",
    "error_non_interactive": "❌ Erreur: Ce CLI nécessite un environnement interactif (terminal)",
    "error_non_interactive_help": "💡 Lancez le script directement dans un terminal, pas en arrière-plan"
}

# Messages d'erreur et validation
VALIDATION_MESSAGES = {
    "invalid_choice": "❌ Choix invalide. Veuillez choisir entre 0 et {max_choice}.",
    "invalid_number": "❌ Veuillez entrer un nombre valide.",
    "invalid_annotation": "❌ Veuillez choisir 'g' (good), 'b' (bad), ou 's' (skip)"
}

# Configuration du formatage
FORMATTING = {
    "separator": "=" * 60,
    "section_separator": "=" * 40
}
