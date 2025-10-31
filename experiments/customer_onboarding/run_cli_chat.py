#!/usr/bin/env python3
"""
Script principal pour lancer le CLI Chat avec l'agent Customer Onboarding.

Usage:
    poetry run python experiments/customer_onboarding/run_cli_chat.py
"""

from agents import gen_trace_id, trace
from cli_chat import ChatCLI
from agent_wrapper import customer_onboarding_agent


def main():
    """Lance le CLI avec l'agent customer onboarding."""
    print("🚀 CLI Chat - Agent Customer Onboarding")
    print("📋 Génération de datasets d'évaluation avec annotations")
    print()
    
    try:
        trace_id = gen_trace_id()
        with trace("Customer Onboarding", trace_id=trace_id):
            print(f"View trace: https://platform.openai.com/traces/trace?trace_id={trace_id}\n")
            # Lancer le CLI avec l'agent customer onboarding
            cli = ChatCLI(
                agent_callback=customer_onboarding_agent,
                output_dir="conversations"
            )
            
            cli.run()
        
    except KeyboardInterrupt:
        print("\n👋 Arrêt demandé par l'utilisateur")
    except Exception as e:
        print(f"❌ Erreur: {e}")
        print("💡 Vérifiez que les dépendances sont installées et l'authentification configurée")


if __name__ == "__main__":
    main()
