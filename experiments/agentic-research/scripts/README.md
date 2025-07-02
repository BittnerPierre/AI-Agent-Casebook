# Scripts d'inspection du Vector Store

Ce dossier contient des outils pour inspecter le contenu de votre vector store OpenAI.

## 🔍 inspect_vector_store.py

Ce script vous permet d'inspecter et télécharger le contenu réel de votre vector store, ce qui est très utile pour le debug.

### Utilisation de base

```bash
# Télécharger tout le contenu dans le dossier par défaut (debug_output)
python scripts/inspect_vector_store.py

# Télécharger dans un dossier spécifique
python scripts/inspect_vector_store.py -o mon_dossier_debug

# Lister seulement les fichiers sans les télécharger
python scripts/inspect_vector_store.py --list-only
```

### Ce que fait le script

1. **Trouve votre vector store** en utilisant le nom configuré dans `config.yaml`
2. **Liste tous les fichiers** attachés au vector store
3. **Télécharge le contenu** de chaque fichier
4. **Sauvegarde les fichiers** avec leurs métadonnées
5. **Génère un rapport** JSON avec toutes les informations

### Structure des fichiers téléchargés

```
debug_output/
├── file-abc123_01_Agent_Systems.md           # Contenu du fichier
├── file-abc123_01_Agent_Systems.md.metadata.json  # Métadonnées
├── file-def456_02_Prompt_Engineering.md
├── file-def456_02_Prompt_Engineering.md.metadata.json
└── download_report.json                      # Rapport complet
```

### Exemples de sortie

#### Mode listing (--list-only)

```
🔍 Listing vector store files...

📁 Found 3 files in vector store vs_12345:

1. File ID: file-abc123
   Status: completed
   Created: 1703123456
   Filename: 01_Agent_Systems.md
   Size: 15420 bytes
   Purpose: assistants

2. File ID: file-def456
   Status: completed
   Created: 1703123789
   Filename: 02_Prompt_Engineering.md
   Size: 12890 bytes
   Purpose: assistants
```

#### Mode téléchargement complet

```
🔍 Inspecting and downloading vector store content...

📊 Download Report:
Vector Store ID: vs_12345
Output Directory: debug_output
Files Found: 3
Files Downloaded: 3
Failures: 0
Total Downloaded: 45230 bytes

📁 Downloaded Files:
  ✅ 01_Agent_Systems.md (15420 bytes)
     -> debug_output/file-abc123_01_Agent_Systems.md
  ✅ 02_Prompt_Engineering.md (12890 bytes)
     -> debug_output/file-def456_02_Prompt_Engineering.md

📋 Full report saved to: debug_output/download_report.json

💡 Tip: You can now inspect the downloaded .md files to see what's in your vector store!
```

## 🛠️ Configuration

Le script utilise la configuration dans `config.yaml`:

```yaml
debug:
  enabled: false
  output_dir: "debug_output" # Dossier par défaut
  save_reports: true
```

## 🚨 Variables d'environnement

Vous pouvez override la configuration via des variables d'environnement:

```bash
# Activer le mode debug
export DEBUG=true

# Changer le nom du vector store
export VECTOR_STORE_NAME="mon-autre-vector-store"

# Puis lancer le script
python scripts/inspect_vector_store.py
```

## 💡 Cas d'usage

### Debug du contenu

Quand vous voulez savoir exactement ce qui est stocké dans votre vector store:

```bash
python scripts/inspect_vector_store.py
# Puis inspectez les fichiers .md téléchargés
```

### Vérification rapide

Pour vérifier le nombre et l'état des fichiers sans télécharger:

```bash
python scripts/inspect_vector_store.py --list-only
```

### Backup du contenu

Pour sauvegarder le contenu de votre vector store:

```bash
python scripts/inspect_vector_store.py -o "backup_$(date +%Y%m%d)"
```

## ⚠️ Notes importantes

- Le script nécessite que `OPENAI_API_KEY` soit définie
- Les fichiers sont téléchargés avec leur ID OpenAI en préfixe pour éviter les conflits
- Le rapport JSON contient toutes les métadonnées pour référence future
- Les gros fichiers peuvent prendre du temps à télécharger
