"""
Base Agent Wrapper

Classe abstraite pour créer des wrappers d'agents compatibles avec le CLI Chat.
Fournit une interface standardisée pour intégrer différents types d'agents.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional


class BaseAgentWrapper(ABC):
    """
    Classe abstraite pour les wrappers d'agents.
    
    Cette classe définit l'interface standard que tous les wrappers d'agents
    doivent implémenter pour être compatibles avec le CLI Chat.
    """
    
    def __init__(self):
        """Initialise le wrapper."""
        self.initialized = False
    
    @abstractmethod
    def setup(self) -> None:
        """
        Configure et initialise l'agent.
        
        Cette méthode doit être implémentée pour configurer l'agent
        (authentification, connexions, etc.).
        
        Raises:
            Exception: Si l'initialisation échoue
        """
        pass
    
    @abstractmethod
    def call_agent(self, conversation: List[Dict[str, str]]) -> str:
        """
        Appelle l'agent avec l'historique de conversation.
        
        Args:
            conversation: Historique de conversation au format
                         [{"role": "user/assistant", "content": "..."}]
        
        Returns:
            str: Réponse de l'agent
            
        Raises:
            Exception: Si l'appel à l'agent échoue
        """
        pass
    
    def cleanup(self) -> None:
        """
        Nettoie les ressources utilisées par l'agent.
        
        Cette méthode peut être surchargée pour nettoyer les connexions,
        fermer les sessions, etc.
        """
        pass
    
    def __call__(self, conversation: List[Dict[str, str]]) -> str:
        """
        Interface principale pour le CLI.
        
        Cette méthode gère l'initialisation automatique et les erreurs.
        
        Args:
            conversation: Historique de conversation
            
        Returns:
            str: Réponse de l'agent
        """
        try:
            # Initialisation automatique si nécessaire
            if not self.initialized:
                self.setup()
                self.initialized = True
            
            # Appel à l'agent
            return self.call_agent(conversation)
            
        except Exception as e:
            return self.handle_error(e)
    
    def handle_error(self, error: Exception) -> str:
        """
        Gère les erreurs de l'agent.
        
        Cette méthode peut être surchargée pour personnaliser
        la gestion d'erreurs.
        
        Args:
            error: L'exception qui s'est produite
            
        Returns:
            str: Message d'erreur pour l'utilisateur
        """
        error_msg = f"Désolé, une erreur s'est produite: {str(error)}"
        print(f"❌ Erreur dans l'agent: {error}")
        return error_msg
    
    def __enter__(self):
        """Support du context manager."""
        self.setup()
        self.initialized = True
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Nettoyage automatique avec context manager."""
        self.cleanup()


class SimpleAgentWrapper(BaseAgentWrapper):
    """
    Exemple d'implémentation simple d'un wrapper d'agent.
    
    Cette classe peut servir de modèle pour créer des wrappers personnalisés.
    """
    
    def __init__(self, agent_function: callable):
        """
        Initialise avec une fonction d'agent simple.
        
        Args:
            agent_function: Fonction qui prend une conversation et retourne une réponse
        """
        super().__init__()
        self.agent_function = agent_function
    
    def setup(self) -> None:
        """Configuration simple (rien à faire pour une fonction)."""
        if self.agent_function is None:
            raise ValueError("Agent function is required")
    
    def call_agent(self, conversation: List[Dict[str, str]]) -> str:
        """Appelle la fonction d'agent."""
        return self.agent_function(conversation)
