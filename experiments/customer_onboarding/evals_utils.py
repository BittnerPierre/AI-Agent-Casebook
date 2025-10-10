from typing import Dict, Any


def format_evaluation_report(simulator_result):
    """Format a concise evaluation report"""
    print("\n" + "="*60)
    print("🔍 RAPPORT D'ÉVALUATION DE L'AGENT")
    print("="*60)
    
    # Extract evaluator results
    evaluator_results = simulator_result.get('evaluator_results', [])
    
    if not evaluator_results:
        print("❌ Aucun résultat d'évaluation trouvé")
        return
    
    # Count successes and failures
    total_tests = len(evaluator_results)
    successes = sum(1 for result in evaluator_results if result.get('score') is True)
    failures = total_tests - successes
    
    # Overall status
    overall_success = successes == total_tests
    status_icon = "✅ SUCCÈS" if overall_success else "❌ ÉCHEC"
    
    print(f"\n📊 RÉSULTAT GLOBAL: {status_icon}")
    print(f"   Tests réussis: {successes}/{total_tests}")
    
    print(f"\n📋 DÉTAIL DES ÉVALUATIONS:")
    print("-" * 40)
    
    for i, result in enumerate(evaluator_results, 1):
        key = result.get('key', f'Test {i}')
        score = result.get('score')
        comment = result.get('comment', 'Pas de commentaire')
        
        # Format the key name
        if key == 'satisfaction':
            test_name = "Satisfaction Client"
        else:
            test_name = key.replace('_', ' ').title()
        
        # Status icon
        icon = "✅" if score is True else "❌"
        status = "RÉUSSI" if score is True else "ÉCHOUÉ"
        
        print(f"{icon} {test_name}: {status}")
        
        # Truncate comment if too long
        if len(comment) > 100:
            comment = comment[:97] + "..."
        
        print(f"   └─ {comment}")
        print()
    
    print("="*60)
    
    return overall_success