#!/usr/bin/env python3
"""
Agent Wrapper pour Customer Onboarding

Wrapper spécifique qui hérite du BaseAgentWrapper pour l'agent customer onboarding.
"""

import asyncio
from typing import List, Dict

from cli_chat import BaseAgentWrapper
from my_agents import run_onboarding_agent_with_mcp


class CustomerOnboardingWrapper(BaseAgentWrapper):
    """Wrapper pour l'agent customer onboarding utilisant MCP et OAuth."""
    
    def setup(self) -> None:
        """Configuration de l'agent customer onboarding."""
        # Rien à configurer ici, l'authentification se fait dans call_agent
        pass
    
    def call_agent(self, conversation: List[Dict[str, str]]) -> str:
        """
        Appelle l'agent customer onboarding.
        
        Args:
            conversation: Historique de conversation [{"role": "user/assistant", "content": "..."}]
            
        Returns:
            Réponse de l'agent
        """
        # Utiliser la fonction existante qui gère déjà l'asyncio
        result = asyncio.run(run_onboarding_agent_with_mcp(conversation))
        return result.final_output


# Fonction de compatibilité pour l'ancien usage
def customer_onboarding_agent(conversation: List[Dict[str, str]]) -> str:
    """
    Interface simple pour l'agent customer onboarding (compatibilité).
    
    Args:
        conversation: Historique de conversation [{"role": "user/assistant", "content": "..."}]
        
    Returns:
        Réponse de l'agent
    """
    wrapper = CustomerOnboardingWrapper()
    return wrapper(conversation)



def test_agent():
    """Test de l'agent."""
    print("🧪 Test de l'agent customer onboarding...")
    
    # Test avec une conversation simple
    conversation = [
        {"role": "user", "content": "Bonjour, je voudrais ouvrir un compte bancaire. Pouvez-vous m'aider ?"}
    ]
    
    response = customer_onboarding_agent(conversation)
    print(f"✅ Réponse reçue: {response[:100]}...")


if __name__ == "__main__":
    test_agent()
