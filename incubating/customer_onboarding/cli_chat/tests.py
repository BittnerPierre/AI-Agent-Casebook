"""
Tests unitaires pour le package CLI Chat.

Tests des composants core du CLI.
"""

import json
import tempfile
from .core import ChatSession, ChatCLI


def simple_test_agent(conversation):
    """Agent de test simple."""
    if not conversation:
        return "Bonjour !"
    last_msg = conversation[-1]['content'].lower()
    if 'bonjour' in last_msg:
        return "Bonjour ! Comment puis-je vous aider ?"
    return "Je comprends votre demande."


def test_chat_session():
    """Test 1: Sauvegarde et structure des données."""
    print("🧪 Test 1: ChatSession")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        session = ChatSession(output_dir=temp_dir)
        
        # Ajouter un tour de conversation
        session.add_turn(
            "Bonjour",
            "Bonjour ! Comment puis-je vous aider ?",
            {"quality": "good", "explanation": "Réponse appropriée"}
        )
        
        # Sauvegarder et vérifier
        filepath = session.save_conversation()
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        assert len(data['conversation']) == 1
        assert data['conversation'][0]['turn'] == 1
        assert 'session_id' in data
        assert 'timestamp' in data
        
        print("✅ Session sauvegardée et structure validée")


def test_cli_initialization():
    """Test 2: Initialisation du CLI."""
    print("\n🧪 Test 2: Initialisation CLI")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        cli = ChatCLI(simple_test_agent, output_dir=temp_dir)
        
        # Vérifications de base
        assert cli.agent_callback is not None
        assert len(cli.CONVERSATION_STARTERS) == 4
        assert cli.session.turn_counter == 0
        
        print("✅ CLI initialisé correctement")


def test_agent_integration():
    """Test 3: Intégration agent + CLI."""
    print("\n🧪 Test 3: Intégration agent")
    
    # Test de l'agent
    conversation = [{"role": "user", "content": "Bonjour"}]
    response = simple_test_agent(conversation)
    
    assert len(response) > 5
    assert "bonjour" in response.lower()
    
    print(f"✅ Agent répond: '{response[:40]}...'")


def run_tests():
    """Lance les 3 tests essentiels."""
    print("🚀 Tests unitaires CLI Chat Package")
    print("=" * 45)
    
    try:
        test_chat_session()
        test_cli_initialization()
        test_agent_integration()
        
        print("\n" + "=" * 45)
        print("✅ Tous les tests du package sont passés !")
        
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        raise


if __name__ == "__main__":
    run_tests()
