import os
import re
import json
from typing import List, Dict, Any

def _extract_assistant_content(message: Dict[str, Any]) -> str:
    """
    Extrait le contenu textuel d'un message assistant, 
    gérant différents formats (string directe ou liste avec objets text).
    CORRIGÉ : Décode correctement les échappements JSON.
    """
    content = message.get("content", "")
    
    if isinstance(content, str):
        # Décoder les échappements JSON si présents
        return _decode_json_escapes(content)
    elif isinstance(content, list):
        # Format avec liste d'objets contenant du text
        text_parts = []
        for item in content:
            if isinstance(item, dict) and "text" in item:
                text_content = item["text"]
                # Si le texte ressemble à du JSON, essayer de le parser
                if text_content.startswith('{"') and text_content.endswith('"}'):
                    try:
                        parsed = json.loads(text_content)
                        # Extraire le markdown_report si disponible
                        if "markdown_report" in parsed:
                            # ✅ CORRECTION : Décoder les échappements dans le markdown_report
                            markdown_content = parsed["markdown_report"]
                            decoded_content = _decode_json_escapes(markdown_content)
                            text_parts.append(decoded_content)
                        else:
                            text_parts.append(_decode_json_escapes(text_content))
                    except json.JSONDecodeError:
                        text_parts.append(_decode_json_escapes(text_content))
                else:
                    text_parts.append(_decode_json_escapes(text_content))
        return "\n".join(text_parts)
    
    return ""

def _decode_json_escapes(text: str) -> str:
    """
    Décode les échappements JSON comme \\n → \n, \\t → \t, etc.
    """
    if not isinstance(text, str):
        return text
    
    # Décoder les échappements JSON courants
    return text.replace('\\n', '\n').replace('\\t', '\t').replace('\\r', '\r').replace('\\"', '"').replace('\\\\', '\\')

def _clean_regex_for_display(regex_pattern: str) -> str:
    """
    Nettoie un pattern regex pour l'affichage (enlève les quotes et prefixes).
    """
    if not regex_pattern:
        return "Pattern"
    
    # Enlever r" au début et " à la fin
    cleaned = regex_pattern
    if cleaned.startswith('r"') and cleaned.endswith('"'):
        cleaned = cleaned[2:-1]
    elif cleaned.startswith('"') and cleaned.endswith('"'):
        cleaned = cleaned[1:-1]
    
    return cleaned

def _is_function_call_successful(messages: List[Dict[str, Any]], call_id: str) -> bool:
    """
    Vérifie si un appel de fonction a réussi en cherchant son function_call_output correspondant.
    Retourne True si l'output ne contient pas d'erreur.
    """
    for msg in messages:
        if (msg.get("type") == "function_call_output" and 
            msg.get("call_id") == call_id):
            output = msg.get("output", "")
            # Si l'output contient une erreur, l'appel a échoué
            return not ("error occurred" in output.lower() or "error:" in output.lower())
    return False

def save_result_input_list_to_json(model_name: str, report_file_name: str, messages: list, output_report_dir: str) -> str:
    """
    Sauvegarde la liste des messages au format JSON dans le répertoire output_dir,
    en adaptant le nom du fichier à partir du nom du rapport (remplace .txt par _messages.json).
    Remplace également les '/' dans le model_name par '-' pour éviter la création de sous-dossiers.
    """
    base_file_name = os.path.basename(report_file_name).rsplit('.md', 1)[0]
    safe_model_name = model_name.replace('/', '-')
    messages_file_name = f"{base_file_name}_{safe_model_name}_messages.json"
    output_path = os.path.join(output_report_dir, messages_file_name)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(messages, f, ensure_ascii=False, indent=2)

    return messages_file_name

def save_trajectory_evaluation_report(model_name: str, output_report_dir: str, report_file_name: str, human_readable_report: str) -> str:
    """
    Sauvegarde le rapport d'évaluation de trajectoire dans un fichier texte détaillé.

    Args:
        report_dir: Répertoire de sortie pour le rapport.
        report_file_name: Nom de base du fichier de rapport (sans extension).
        human_readable_report: Contenu du rapport à écrire.

    Returns:
        Le chemin complet du fichier de rapport sauvegardé.
    """
    base_file_name = os.path.basename(report_file_name).rsplit('.md', 1)[0]
    safe_model_name = model_name.replace('/', '-')
    trajectory_evaluation_file_name = f"{base_file_name}_{safe_model_name}_trajectory_evaluation.txt"
    report_file_path = os.path.join(output_report_dir, trajectory_evaluation_file_name)
    with open(report_file_path, 'w', encoding='utf-8') as f:
        f.write(human_readable_report)
    return report_file_path


def validate_trajectory_spec(
    messages: List[Dict[str,Any]], 
    spec: List[Dict[str,Any]]
) -> Dict[str,Any]:
    """
    Version améliorée qui gère correctement les différents formats de contenu
    et fournit un rapport plus détaillé. Ne s'arrête JAMAIS aux étapes manquantes.
    
    ⚠️ COMPORTEMENT DE VALIDATION D'ORDRE :
    
    • FUNCTION_CALLS : Ordre temporel strict
      - Vérifie que les appels de fonction se succèdent dans l'ordre spécifié
      - Chaque function_call doit apparaître APRÈS la précédente dans la chronologie
      - ✅ NOUVEAU : Vérifie que l'appel a réussi (pas d'erreur dans l'output)
      - Exemple : read_multiple_files PUIS save_report
    
    • GENERATIONS : Ordre dans le contenu final 
      - Vérifie que les patterns apparaissent dans l'ordre spécifié dans le contenu généré
      - Tous les patterns peuvent être dans le MÊME message assistant final
      - ✅ NOUVEAU : Décode correctement les échappements JSON (\\n → \n)
      - ✅ NOUVEAU : Recherche dans les arguments des function_calls (pour handoff workflow)
      - Exemple : "## Raw Notes" PUIS "## Detailed Agenda" PUIS "## Final Report"
    """
    
    # Extraire tous les événements (function_calls et generations) avec métadonnées
    events = []
    
    for i, m in enumerate(messages):
        if m.get("type") == "function_call":
            # Vérifier le succès de l'appel
            call_id = m.get("call_id", "")
            successful = _is_function_call_successful(messages, call_id)
            
            events.append({
                "type": "function_call",
                "name": m.get("name", ""),
                "call_id": call_id,
                "successful": successful,
                "index": i,
                "arguments": m.get("arguments", "")  # ✅ NOUVEAU : Garder les arguments
            })
        elif m.get("role") == "assistant":
            # Extraire le contenu assistant avec décodage des échappements
            content = _extract_assistant_content(m)
            if content.strip():
                events.append({
                    "type": "generation", 
                    "content": content, 
                    "msg": m, 
                    "index": i
                })
    
    results = []
    pos = 0
    
    # ⚠️ IMPORTANT: On teste TOUTES les étapes, sans s'arrêter aux manquantes
    for step in spec:
        matched = False
        matched_event = None
        
        for idx in range(pos, len(events)):
            ev = events[idx]
            
            if step["type"] == "function_call":
                # FUNCTION_CALLS: Ordre temporel strict requis + Vérification de succès
                # match exact name or prefix ET appel réussi
                if (ev["type"] == "function_call" and 
                    ev.get("successful", False) and  # ✅ NOUVEAU : Vérifier le succès
                    (ev["name"] == step.get("name") or
                     (step.get("name_prefix") and ev["name"].startswith(step["name_prefix"])))):
                    matched = True
                    matched_event = ev
                    
            else:  # generation
                # GENERATIONS: Recherche de pattern dans le contenu (peut être dans le même message)
                if ev["type"] == "generation":
                    # ✅ NOUVEAU : Recherche avec contenu décodé
                    match = re.search(step["match_regex"], ev["content"], re.MULTILINE)
                    if match:
                        matched = True
                        matched_event = ev
                
                # ✅ NOUVEAU : Recherche dans les arguments des function_calls (pour handoff workflow)
                elif ev["type"] == "function_call":
                    arguments = ev.get("arguments", "")
                    if arguments:
                        try:
                            # Parser les arguments JSON
                            args_dict = json.loads(arguments)
                            # Chercher dans markdown_report si disponible
                            markdown_content = args_dict.get("markdown_report", "")
                            if markdown_content:
                                # Décoder les échappements JSON
                                decoded_content = _decode_json_escapes(markdown_content)
                                match = re.search(step["match_regex"], decoded_content, re.MULTILINE)
                                if match:
                                    matched = True
                                    matched_event = ev
                        except (json.JSONDecodeError, KeyError):
                            # Si pas de JSON valide, essayer de chercher directement dans les arguments
                            match = re.search(step["match_regex"], arguments, re.MULTILINE)
                            if match:
                                matched = True
                                matched_event = ev
                        
            if matched:
                # Pour les function_calls, on avance la position pour forcer l'ordre temporel
                if step["type"] == "function_call":
                    pos = idx + 1
                # Pour les generations, on garde la position car plusieurs patterns
                # peuvent être dans le même message
                break
        
        # ✅ CORRIGÉ : Si pas trouvé dans la plage actuelle, chercher à partir de la position actuelle
        # pour respecter l'ordre temporel, sauf si c'est la première étape (pas d'étape précédente validée)
        if not matched and step["type"] == "generation":
            # Si c'est la première étape ou si aucune étape précédente n'a été trouvée, repartir du début
            search_start = 0 if pos == 0 else pos
            
            for idx in range(search_start, len(events)):
                ev = events[idx]
                if ev["type"] == "generation":
                    match = re.search(step["match_regex"], ev["content"], re.MULTILINE)
                    if match:
                        matched = True
                        matched_event = ev
                        pos = idx + 1  # Avancer la position pour l'étape suivante
                        break
                
                elif ev["type"] == "function_call":
                    arguments = ev.get("arguments", "")
                    if arguments:
                        try:
                            args_dict = json.loads(arguments)
                            markdown_content = args_dict.get("markdown_report", "")
                            if markdown_content:
                                decoded_content = _decode_json_escapes(markdown_content)
                                match = re.search(step["match_regex"], decoded_content, re.MULTILINE)
                                if match:
                                    matched = True
                                    matched_event = ev
                                    pos = idx + 1  # Avancer la position pour l'étape suivante
                                    break
                        except (json.JSONDecodeError, KeyError):
                            match = re.search(step["match_regex"], arguments, re.MULTILINE)
                            if match:
                                matched = True
                                matched_event = ev
                                pos = idx + 1  # Avancer la position pour l'étape suivante
                                break
        
        # Construire le résultat pour cette étape
        if matched:
            status_text = "TROUVÉ" 
            if step["type"] == "function_call":
                success_indicator = "✅ RÉUSSI" if matched_event.get("successful") else "❌ ÉCHEC"
                found_text = f"Appel de fonction '{matched_event['name']}' ({success_indicator})"
                detail_text = f"Call ID: {matched_event.get('call_id', 'N/A')}"
                expected_display = step.get("name", "fonction inconnue")
            else:
                # ✅ NETTOYÉ : Utiliser seulement le match_regex avec nettoyage
                pattern_display = _clean_regex_for_display(step["match_regex"])
                found_text = f"'{pattern_display}'"
                detail_text = f"Pattern trouvé dans le contenu"
                if matched_event["type"] == "function_call":
                    detail_text += f" (arguments de {matched_event['name']})"
                expected_display = pattern_display
                
            results.append({
                "id": step["id"],
                "required": step.get("required", True),
                "found": True,
                "status": status_text,
                "found_text": found_text,
                "detail_text": detail_text,
                "position": f"Message #{matched_event['index'] + 1}",
                "type": step["type"],
                "expected": expected_display
            })
        else:
            # Déterminer la raison de l'échec
            if step["type"] == "function_call":
                reason = f"Pas trouvé: {step.get('name', 'fonction inconnue')}"
                expected_display = step.get("name", "fonction inconnue")
            else:
                # ✅ NETTOYÉ : Utiliser seulement le match_regex avec nettoyage
                pattern_display = _clean_regex_for_display(step["match_regex"])
                reason = f"Pas trouvé: {pattern_display}"
                expected_display = pattern_display
                
            results.append({
                "id": step["id"],
                "required": step.get("required", True),
                "found": False,
                "status": "MANQUANT (REQUIS)" if step.get("required", True) else "MANQUANT (OPTIONNEL)",
                "found_text": reason,
                "detail_text": f"Raison: {reason}",
                "position": "N/A",
                "type": step["type"],
                "expected": expected_display
            })
    
    # Résumé global
    found_count = sum(1 for r in results if r["found"])
    required_count = len([r for r in results if r.get("required", True)])
    missing_required = [r for r in results if not r["found"] and r.get("required", True)]
    
    success = found_count == len(results)
    
    return {
        "success": success,
        "found_steps": found_count,
        "total_steps": len(results),
        "required_steps": required_count,
        "missing_required": len(missing_required),
        "results": results,
        "missing_required_list": [r["id"] for r in missing_required]
    }

def format_trajectory_report(model_name: str, evaluation: Dict[str, Any], title: str = "Agent Trajectory") -> str:
    """
    Formate le rapport d'évaluation de trajectoire de manière lisible et professionnelle.
    
    Args:
        evaluation: Résultat de validate_trajectory_spec
        title: Titre du rapport (par défaut "Agent Trajectory")
    """
    
    report = []
    report.append(f"🔍 RAPPORT D'ÉVALUATION - {title} - {model_name}")
    report.append("=" * 60)
    report.append("")
    
    # Résumé global avec emoji de statut
    status_emoji = "✅ SUCCÈS" if evaluation["success"] else "❌ ÉCHEC"
    report.append(f"📊 RÉSUMÉ GLOBAL: {status_emoji}")
    report.append(f"   • Étapes trouvées: {evaluation['found_steps']}/{evaluation['total_steps']}")
    report.append(f"   • Étapes requises: {evaluation['required_steps']}")
    if evaluation['missing_required'] > 0:
        report.append(f"   • Étapes requises manquantes: {evaluation['missing_required']}")
    report.append("")
    
    # Détail des étapes
    report.append("📋 DÉTAIL DES ÉTAPES:")
    report.append("-" * 40)
    report.append("")
    
    for i, result in enumerate(evaluation["results"], 1):
        status_emoji = "✅" if result["found"] else "❌"
        report.append(f"{i}. {status_emoji} {result['id'].upper()}")
        report.append(f"   Type: {result['type']}")
        report.append(f"   Attendu: {result['expected']}")
        report.append(f"   Statut: {result['status']}")
        report.append(f"   Trouvé: {result['found_text']}")
        if result.get('detail_text'):
            report.append(f"   {result['detail_text']}")
        if result.get('position') and result['position'] != 'N/A':
            report.append(f"   Position: {result['position']}")
        report.append("")
    
    # Recommandations
    if not evaluation["success"]:
        report.append("💡 RECOMMANDATIONS:")
        report.append("-" * 20)
        if evaluation['missing_required'] > 0:
            report.append("• Vérifier que l'agent exécute toutes les étapes requises")
            for missing_id in evaluation['missing_required_list']:
                missing_result = next(r for r in evaluation["results"] if r["id"] == missing_id)
                report.append(f"  - {missing_id}: {missing_result['expected']}")
        report.append("• Vérifier les patterns regex et noms de fonctions dans TRAJECTORY_SPEC_MODEL")
        report.append("• Examiner les messages générés pour s'assurer qu'ils contiennent les patterns attendus")
        report.append("• ✅ NOUVEAU : Vérifier que les function_calls ne retournent pas d'erreurs")
    
    return "\n".join(report)

def test_trajectory_from_existing_files(messages_file: str, spec: List[Dict[str, Any]]) -> str:
    """
    ✨ NOUVELLE FONCTIONNALITÉ : 
    Teste la trajectoire sur des fichiers de messages existants sans refaire la génération.
    Parfait pour itérer sur les validations sans payer les coûts de génération !
    """
    try:
        with open(messages_file, 'r', encoding='utf-8') as f:
            messages = json.load(f)
        
        evaluation = validate_trajectory_spec(messages, spec)
        return format_trajectory_report("dummy_model", evaluation, "Test Trajectory")
        
    except FileNotFoundError:
        return f"❌ ERREUR: Fichier {messages_file} introuvable."
    except json.JSONDecodeError as e:
        return f"❌ ERREUR: Impossible de parser le JSON: {e}"
    except Exception as e:
        return f"❌ ERREUR: {e}"
