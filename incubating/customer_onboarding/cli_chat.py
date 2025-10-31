#!/usr/bin/env python3
"""
CLI Chat Interactif Minimal

Un CLI simple pour tester des agents conversationnels et générer des datasets d'évaluation.

Usage:
    cd incubating/customer_onboarding
    uv run python run_cli_chat.py

Le CLI prend uniquement une fonction callback qui accepte une conversation 
au format [{"role": "user/assistant", "content": "..."}] et retourne une réponse.
"""

import json
import os
import sys
import uuid
from datetime import datetime
from typing import Callable, List, Dict, Optional


class ChatSession:
    """Gère une session de chat avec sauvegarde et annotations."""
    
    def __init__(self, output_dir: str = "conversations"):
        self.session_id = str(uuid.uuid4())
        self.timestamp = datetime.now().isoformat()
        self.conversation = []
        self.turn_counter = 0
        self.output_dir = output_dir
        
        # Créer le dossier de sortie s'il n'existe pas
        os.makedirs(output_dir, exist_ok=True)
    
    def add_turn(self, user_input: str, agent_response: str, annotation: Optional[Dict[str, str]] = None):
        """Ajoute un tour de conversation."""
        self.turn_counter += 1
        turn = {
            "turn": self.turn_counter,
            "user_input": user_input,
            "agent_response": agent_response,
            "annotation": annotation
        }
        self.conversation.append(turn)
    
    def save_conversation(self) -> str:
        """Sauvegarde la conversation dans un fichier JSON."""
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"conversation_{timestamp_str}.json"
        filepath = os.path.join(self.output_dir, filename)
        
        data = {
            "session_id": self.session_id,
            "timestamp": self.timestamp,
            "conversation": self.conversation
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        return filepath
    
    def get_conversation_history(self) -> List[Dict[str, str]]:
        """Retourne l'historique de conversation au format attendu par les agents."""
        history = []
        for turn in self.conversation:
            history.append({"role": "user", "content": turn["user_input"]})
            history.append({"role": "assistant", "content": turn["agent_response"]})
        return history


class ChatCLI:
    """Interface CLI pour chat interactif avec annotations."""
    
    CONVERSATION_STARTERS = [
        "Bonjour, je voudrais ouvrir un compte bancaire. Pouvez-vous m'aider ?",
        "Quelle est la différence entre une carte de CREDIT et une carte de DEBIT ?",
        "Je n'arrive pas à recevoir l'email de confirmation pour mon compte",
        "Je suis étudiant étranger, puis-je ouvrir un compte ?"
    ]
    
    def __init__(self, agent_callback: Callable[[List[Dict[str, str]]], str], output_dir: str = "conversations"):
        """
        Initialise le CLI.
        
        Args:
            agent_callback: Fonction qui prend l'historique de conversation et retourne la réponse de l'agent
            output_dir: Dossier où sauvegarder les conversations
        """
        self.agent_callback = agent_callback
        self.session = ChatSession(output_dir)
        self.running = True
    
    def display_welcome(self):
        """Affiche le message de bienvenue."""
        print("=" * 60)
        print("🤖 CLI Chat Interactif")
        print("=" * 60)
        print("Commandes spéciales:")
        print("  /quit    - Quitter et sauvegarder")
        print("  /save    - Sauvegarder la conversation")
        print("  /restart - Redémarrer une nouvelle session")
        print("=" * 60)
    
    def display_conversation_starters(self) -> Optional[str]:
        """Affiche les conversation starters et retourne le choix de l'utilisateur."""
        print("\n📝 Conversation Starters:")
        print("0. Saisir votre propre message")
        
        for i, starter in enumerate(self.CONVERSATION_STARTERS, 1):
            print(f"{i}. {starter}")
        
        while True:
            try:
                choice = input("\nChoisissez une option (0-4): ").strip()
                
                if choice == "0":
                    return None  # L'utilisateur saisira son propre message
                
                choice_num = int(choice)
                if 1 <= choice_num <= len(self.CONVERSATION_STARTERS):
                    return self.CONVERSATION_STARTERS[choice_num - 1]
                else:
                    print("❌ Choix invalide. Veuillez choisir entre 0 et 4.")
            
            except ValueError:
                print("❌ Veuillez entrer un nombre valide.")
            except KeyboardInterrupt:
                print("\n👋 Au revoir !")
                return "/quit"
            except EOFError:
                print("\n❌ Erreur: Impossible de lire l'entrée utilisateur")
                return "/quit"
    
    def get_user_input(self) -> str:
        """Récupère l'input de l'utilisateur."""
        try:
            user_input = input("\n➡️ Vous: ").strip()
            return user_input
        except KeyboardInterrupt:
            return "/quit"
        except EOFError:
            print("\n❌ Erreur: Impossible de lire l'entrée utilisateur")
            return "/quit"
    
    def handle_special_commands(self, user_input: str) -> bool:
        """
        Gère les commandes spéciales.
        
        Returns:
            True si une commande spéciale a été traitée, False sinon
        """
        if user_input == "/quit":
            filepath = self.session.save_conversation()
            print(f"\n💾 Conversation sauvegardée: {filepath}")
            print("👋 Au revoir !")
            self.running = False
            return True
        
        elif user_input == "/save":
            filepath = self.session.save_conversation()
            print(f"💾 Conversation sauvegardée: {filepath}")
            return True
        
        elif user_input == "/restart":
            filepath = self.session.save_conversation()
            print(f"💾 Session précédente sauvegardée: {filepath}")
            self.session = ChatSession(self.session.output_dir)
            print("🔄 Nouvelle session démarrée")
            return True
        
        return False
    
    def get_annotation(self) -> Optional[Dict[str, str]]:
        """Demande à l'utilisateur d'annoter la réponse de l'agent."""
        while True:
            try:
                evaluation = input("\n📊 Évaluez cette réponse (g=good, b=bad, s=skip): ").strip().lower()
                
                if evaluation == "s":
                    return None
                
                elif evaluation in ["g", "b"]:
                    quality = "good" if evaluation == "g" else "bad"
                    
                    try:
                        explanation = input("💬 Explication optionnelle: ").strip()
                    except EOFError:
                        explanation = ""
                    
                    annotation = {"quality": quality}
                    if explanation:
                        annotation["explanation"] = explanation
                    
                    return annotation
                
                else:
                    print("❌ Veuillez choisir 'g' (good), 'b' (bad), ou 's' (skip)")
            
            except KeyboardInterrupt:
                return None
            except EOFError:
                print("\n❌ Erreur: Impossible de lire l'entrée utilisateur")
                return None
    
    def run(self):
        """Lance la boucle principale du CLI."""
        # Vérifier si nous sommes dans un environnement interactif
        if not sys.stdin.isatty():
            print("❌ Erreur: Ce CLI nécessite un environnement interactif (terminal)")
            print("💡 Lancez le script directement dans un terminal, pas en arrière-plan")
            return
        
        self.display_welcome()
        
        # Premier message avec conversation starters
        first_message = self.display_conversation_starters()
        
        if first_message == "/quit":
            return
        
        if first_message is None:
            first_message = self.get_user_input()
        
        if not first_message or self.handle_special_commands(first_message):
            return
        
        # Boucle principale de chat
        current_input = first_message
        
        while self.running:
            if not current_input:
                current_input = self.get_user_input()
                if self.handle_special_commands(current_input):
                    continue
            
            # Appel à l'agent
            print("\n🤔 Agent réfléchit...")
            
            try:
                conversation_history = self.session.get_conversation_history()
                conversation_history.append({"role": "user", "content": current_input})
                
                agent_response = self.agent_callback(conversation_history)
                
                print(f"\n⬅️ Agent: {agent_response}")
                
                # Annotation de la réponse
                annotation = self.get_annotation()
                
                # Sauvegarder le tour
                self.session.add_turn(current_input, agent_response, annotation)
                
                # Préparer pour le prochain tour
                current_input = None
                
            except Exception as e:
                print(f"\n❌ Erreur lors de l'appel à l'agent: {e}")
                current_input = None
        
        # Sauvegarde finale si pas déjà fait
        if self.session.conversation:
            filepath = self.session.save_conversation()
            print(f"\n💾 Conversation finale sauvegardée: {filepath}")


# Le CLI ne contient plus d'agent de démonstration
# Il doit être utilisé avec un wrapper externe
