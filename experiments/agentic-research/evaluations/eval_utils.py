import re

from typing import List, Dict, Any

def validate_trajectory_spec(
    messages: List[Dict[str,Any]], 
    spec: List[Dict[str,Any]]
) -> Dict[str,Any]:
    """
    Parcourt spec dans l'ordre, et pour chaque étape :
    - essaye de trouver un match dans messages à partir de la position courante
    - collecte found / not found
    - s'arrête si une étape required est manquante
    """
    # convertir messages en une liste d'événements simplifiés
    events = []
    for m in messages:
        if m.get("type") == "function_call":
            events.append({"type":"function_call", "name": m["name"], "msg": m})
        elif m.get("role")=="assistant" and isinstance(m.get("content"), str):
            events.append({"type":"generation", "content": m["content"], "msg": m})
        else:
            # on ignore user/system etc.
            continue

    results = []
    pos = 0
    for step in spec:
        matched = False
        for idx in range(pos, len(events)):
            ev = events[idx]
            if step["type"] == "function_call":
                # match exact name or prefix
                if ev["type"]=="function_call" and (
                   ev["name"] == step.get("name") or
                   (step.get("name_prefix") and ev["name"].startswith(step["name_prefix"]))
                ):
                    matched = True
            else:  # generation
                if ev["type"] == "generation" and re.search(step["match_regex"], ev["content"], re.MULTILINE):
                    matched = True

            if matched:
                results.append({
                    "id": step["id"],
                    "found": True,
                    "event": ev,
                    "index": idx
                })
                pos = idx + 1
                break

        if not matched:
            results.append({
                "id": step["id"],
                "found": False,
                "required": step["required"]
            })
            if step["required"]:
                # on peut arrêter la vérification dès qu'une required manque
                break

    # ok si toutes les required ont found=True
    ok = all(r.get("found", False) or not next(s for s in spec if s["id"]==r["id"])["required"]
             for r in results)
    return {"results": results, "ok": ok}

def extract_full_trajectory(msgs):
    traj = []
    for m in msgs:
        typ = m.get("type")
        # **On teste d’abord le type, quel que soit le role :**
        if typ == "function_call":
            traj.append(f"FUNC_CALL({m.get('name')})")
        elif typ == "function_call_output":
            traj.append("FUNC_OUT")
        # Puis on gère les rôles “user” / “assistant” / “system” / “developer”
        elif m.get("role") == "user":
            traj.append("USER")
        elif m.get("role") == "assistant":
            traj.append("ASSISTANT")
        elif m.get("role") == "system":
            traj.append("SYSTEM")
        elif m.get("role") == "developer":
            traj.append("DEVELOPER")
        else:
            traj.append("UNKNOWN")
    return traj

def extract_tool_trajectory(full_traj):
    """
    Filtre la trajectoire complète pour ne garder que les FUNC_CALL.
    """
    return [ev for ev in full_traj if ev.startswith("FUNC_CALL")]

def evaluate_tools_trajectory(actual_tools, expected_tools):
    """
    Compare la liste des tool calls réels à la référence.
    """
    # on retire le préfixe FUNC_CALL(...)
    clean_actual = [re.match(r"FUNC_CALL\((.*)\)", ev).group(1) for ev in actual_tools]
    missing = [t for t in expected_tools if t not in clean_actual]
    parasites = [t for t in clean_actual if t not in expected_tools]
    return {
        "actual_tools": clean_actual,
        "missing": missing,
        "parasites": parasites,
        "ok": (not missing)
    }

# === Exemple d'utilisation ===


if __name__ == "__main__":
    messages = [
        # ... ta liste de dicts ...
    ]

    # 1) extraire toutes les étapes (USER, ASSISTANT, FUNC_CALL, FUNC_OUT, …)
    full_traj = extract_full_trajectory(messages)

    # 2) n'en garder que les tool calls
    tool_traj = extract_tool_trajectory(full_traj)

    # 3) comparer à la référence
    reference = ["read_multiple_files", "save_final_report"]
    report = evaluate_tools_trajectory(tool_traj, reference)

    import json
    print(json.dumps({
        "full_trajectory": full_traj,
        "tool_trajectory": tool_traj,
        "evaluation": report
    }, indent=2, ensure_ascii=False))
