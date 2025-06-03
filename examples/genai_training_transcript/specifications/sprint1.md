# Sprint 1 – US-MCP-1 à US-MCP-5 : Intégration MCP Evernote

## User Stories (US-MCP-1 à US-MCP-5)
| ID       | Rôle      | Fonctionnalité                                         | Valeur métier                      |
| -------- | --------- | ------------------------------------------------------ | ---------------------------------- |
| US-MCP-1 | Client AI | Charger un document via `file://` ou `evernote://`     | Accéder au contenu pour traitement |
| US-MCP-2 | Client AI | Enregistrer un document via `file://` ou `evernote://` | Sauvegarder les mises à jour       |
| US-MCP-3 | Client AI | Lister les dossiers dans un URI donné                  | Naviguer dans la structure         |
| US-MCP-4 | Client AI | Rechercher des documents par mot-clé                   | Retrouver rapidement du contenu    |
| US-MCP-5 | Client AI | Récupérer les métadonnées d’un document                | Afficher date de création, taille  |

Référence : `plan_mcp_evernote.md` (section 3 – User Stories)

## Contexte et objectifs
Cette itération vise à implémenter le client/serveur MCP pour Evernote en s’appuyant sur l’architecture existante du MCP Filesystem.
Le code TypeScript du MCP Filesystem (https://github.com/modelcontextprotocol/servers/tree/main/src/filesystem) servira de référence pour la mise en œuvre.
L’objectif est de soutenir le schéma `evernote://` pour les US‑MCP‑1 à US‑MCP‑5, en TypeScript, sans dépendance au SDK Python Evernote.

## Critères d’acceptation
- Le client/serveur MCP Evernote (TypeScript) doit exposer la même API que le MCP Filesystem.
- Les User Stories US-MCP-1 à US-MCP-5 sont fonctionnelles pour la couche `evernote://`.
- Les méthodes doivent passer les tests unitaires TS (mocquage du client Evernote TS) et les tests d’intégration éventuels en sandbox Evernote.
- La documentation doit expliquer la configuration et l’usage du client/serveur MCP Evernote (TS), avec lien vers la documentation Evernote et le code MCP Filesystem TS.

## Tâches
- [x] Initialiser un projet Node.js/TypeScript pour le serveur MCP Evernote (via `npm init`, `tsconfig.json`, `package.json`).
- [x] Faire un POC OAuth 2.0 (PKCE) Evernote en JavaScript (Node.js sans secret) : obtention d'un access token via OAuth 2.0, tests simples de lecture/écriture d'une note (voir https://dev.evernote.com/doc/articles/authentication.php ; sans sandbox).
- [ ] Cloner et adapter le code TypeScript du MCP Filesystem (https://github.com/modelcontextprotocol/servers/tree/main/src/filesystem) pour prendre en charge `evernote://`.
- [ ] Installer les dépendances TS nécessaires (MCP core TS, Evernote JS API ou wrapper HTTP).
- [ ] Implémenter en TypeScript les méthodes MCP Evernote :
  - `read_file(uri)`
  - `write_file(uri, data)`
  - `mkdir(uri)`
  - `list_dirs(uri)`
  - `delete_dir(uri)`
  - `move(src_uri, dest_uri)`
  - `search(uri, query)`
  - `stat(uri)`
- [ ] Écrire des tests unitaires TS (Jest ou équivalent) pour chaque méthode, avec mocquage des appels Evernote.
- [ ] Écrire des tests d’intégration end-to-end contre un environnement sandbox Evernote (ou compte de test).
- [ ] Mettre à jour la documentation (`README.md`) avec les instructions Node.js/TypeScript et l’option `--plugin evernote`.
- [ ] Fournir des fixtures TS pour les tests (GUIDs fictifs, structure de notebooks).
- [ ] Supprimer l’ancienne implémentation Python (`tools/mcp_evernote.py`) et le script `run_mcp_evernote.sh`.
- [ ] Ajouter des liens vers :
  - Code MCP Filesystem TS : https://github.com/modelcontextprotocol/servers/tree/main/src/filesystem
  - Documentation Evernote API : https://dev.evernote.com/doc/

## Références
- Code MCP Filesystem (TypeScript) : https://github.com/modelcontextprotocol/servers/tree/main/src/filesystem
- Documentation Evernote API : https://dev.evernote.com/doc/