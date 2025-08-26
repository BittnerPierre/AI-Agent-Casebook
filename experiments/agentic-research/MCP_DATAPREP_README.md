# Module MCP DataPrep

Système de gestion de base de connaissances locale avec upload optimisé vers OpenAI Vector Store.

## 🎯 Fonctionnalités

### 1. Gestion de Base de Connaissances Locale

- **Base JSON thread-safe** avec verrous de fichiers (portalocker)
- **Stockage local** des fichiers `.md` avec métadonnées
- **Extraction de mots-clés** intelligente via LLM
- **Lookup rapide** par URL ou nom de fichier

### 2. Upload Optimisé vers OpenAI

- **Réutilisation** des fichiers déjà uploadés (OpenAI File ID)
- **Upload en parallèle** avec gestion d'erreurs
- **Vector Store** temporaire (expiration 1 jour)
- **Métriques détaillées** des opérations

### 3. Interface MCP

- **3 outils MCP** pour les agents
- **Serveur FastMCP** intégré
- **Configuration YAML** centralisée

## 📦 Installation

```bash
cd experiments/agentic-research
poetry install
```

### Dépendances ajoutées

- `portalocker` : Verrous de fichiers thread-safe

## ⚙️ Configuration

### `config.yaml`

```yaml
data:
  urls_file: "urls.txt" # URLs existantes (lecture seule)
  knowledge_db_path: "data/knowledge_db.json" # Base de connaissances
  local_storage_dir: "data/" # Stockage fichiers .md
```

## 🚀 Utilisation

### 1. Script de Workflow (Compatible avec l'existant)

```bash
# Reproduit dataprep.core:main avec les nouvelles fonctionnalités
poetry run mcp-dataprep-workflow
```

### 2. Serveur MCP

```bash
# Démarrer le serveur MCP DataPrep
poetry run dataprep_server
```

Le serveur sera accessible sur `http://localhost:8001` avec transport SSE.

### 3. Utilisation Directe des Fonctions

```python
from src.dataprep.mcp_functions import download_and_store_url, upload_files_to_vectorstore, get_knowledge_entries
from src.config import get_config

config = get_config()

# 1. Télécharger une URL
filename = download_and_store_url("https://example.com/article", config)

# 2. Consulter la base de connaissances
entries = get_knowledge_entries(config)
print(f"Entrées disponibles: {len(entries)}")

# 3. Upload vers vector store
result = upload_files_to_vectorstore(
    inputs=["https://example.com/article"],  # URLs ou noms de fichiers
    config=config,
    vectorstore_name="my-research"
)
print(f"Vector Store ID: {result.vectorstore_id}")
print(f"Fichiers réutilisés: {result.reuse_count}")
```

## 🔧 Outils MCP Disponibles

### `download_and_store_url_tool(url: str) -> str`

Télécharge et stocke une URL dans la base de connaissances locale.

**Paramètres:**

- `url`: URL à télécharger

**Retour:** Nom du fichier local créé

**Comportement:**

- Lookup dans la base existante
- Si trouvé → retourne le nom de fichier
- Sinon → télécharge, convertit en Markdown, extrait mots-clés LLM, stocke

### `upload_files_to_vectorstore_tool(inputs: List[str], vectorstore_name: str) -> Dict`

Upload optimisé vers OpenAI Vector Store.

**Paramètres:**

- `inputs`: Liste d'URLs ou noms de fichiers
- `vectorstore_name`: Nom du vector store à créer

**Retour:** Résultat détaillé avec métriques

**Optimisations:**

- Réutilise les `openai_file_id` existants
- Upload uniquement les nouveaux fichiers
- Vector store avec expiration 1 jour

### `get_knowledge_entries_tool() -> List[Dict]`

Consulte l'index de la base de connaissances.

**Retour:** Liste des entrées avec URL, nom de fichier, titre, mots-clés, ID OpenAI

## 📊 Structure des Données

### KnowledgeEntry

```python
{
    "url": "https://example.com/article",
    "filename": "article.md",
    "title": "Titre du document",
    "keywords": ["AI", "Machine Learning"],  # Extraits par LLM
    "openai_file_id": "file_123abc",         # Optimisation uploads
    "created_at": "2025-01-07T10:30:00",
    "last_uploaded_at": "2025-01-07T11:00:00"
}
```

### UploadResult

```python
{
    "vectorstore_id": "vs_abc123",
    "total_files_requested": 5,
    "upload_count": 2,           # Nouveaux uploads
    "reuse_count": 3,            # Fichiers réutilisés
    "attach_success_count": 5,
    "attach_failure_count": 0,
    "files_uploaded": [...],
    "files_attached": [...]
}
```

## 🔄 Workflow Agentique Recommandé

### 1. Planner Agent

```python
# Consulter la base de connaissances
entries = mcp_dataprep.get_knowledge_entries_tool()

# Identifier les URLs manquantes
available_urls = {entry['url'] for entry in entries}
syllabus_urls = ["https://...", "https://..."]
urls_to_download = [url for url in syllabus_urls if url not in available_urls]

if urls_to_download:
    print(f"URLs à télécharger: {urls_to_download}")
```

### 2. Documentalist Agent

```python
# Télécharger les URLs manquantes
for url in urls_to_download:
    filename = mcp_dataprep.download_and_store_url_tool(url)
    print(f"Téléchargé: {url} -> {filename}")
```

### 3. Upload vers Vector Store

```python
# Upload optimisé (réutilise les fichiers existants)
result = mcp_dataprep.upload_files_to_vectorstore_tool(
    inputs=syllabus_urls,  # Toutes les URLs (optimisation automatique)
    vectorstore_name="research-session-123"
)

print(f"Vector Store: {result['vectorstore_id']}")
print(f"Optimisation: {result['reuse_count']}/{result['total_files_requested']} fichiers réutilisés")
```

## 🧪 Tests

```bash
# Tests d'intégration
cd experiments/agentic-research
python -m pytest integration_tests/test_mcp_dataprep.py -v

# Test avec mocks
python integration_tests/test_mcp_dataprep.py
```

## 📁 Architecture des Fichiers

```
src/
├── dataprep/
│   ├── models.py              # Schémas Pydantic
│   ├── knowledge_db.py        # Gestionnaire thread-safe
│   ├── mcp_functions.py       # 3 fonctions MCP principales
│   └── core.py               # Fonctions legacy (intactes)
├── mcp/
│   └── dataprep_server.py    # Serveur MCP FastMCP
└── config.py                 # Configuration étendue

scripts/
└── mcp_dataprep_workflow.py  # Script compatible existant

integration_tests/
└── test_mcp_dataprep.py      # Tests d'intégration

data/                          # Stockage local
├── knowledge_db.json          # Base de connaissances
└── *.md                      # Fichiers markdown
```

## 🔒 Sécurité et Performance

### Thread Safety

- **Verrous de fichiers** avec `portalocker`
- **Pattern read-merge-write** atomique
- **Gestion des erreurs** de concurrence

### Optimisation Memory/CPU

- **Streaming upload** pour gros fichiers
- **Réutilisation** des uploads OpenAI
- **Extraction LLM** avec fallback

### Logging Structuré

```python
logger.info("Document téléchargé", extra={
    "url": url,
    "filename": filename,
    "content_length": len(content),
    "keywords_count": len(keywords)
})
```

## 🚀 Migration depuis l'Existant

Le module est **100% compatible** avec l'existant :

- `src.dataprep.core` : **Inchangé**
- `poetry run dataprep` : **Fonctionne toujours**
- Nouvelles fonctionnalités : **Additives uniquement**

### Script de Migration

```bash
# Ancien workflow
poetry run dataprep

# Nouveau workflow avec optimisations
poetry run mcp-dataprep-workflow
```

## 📈 Métriques et Monitoring

Le système fournit des métriques détaillées :

- **Optimisation ratio** : `reuse_count / total_files`
- **Performance upload** : Temps par fichier
- **Base de connaissances** : Croissance, mots-clés fréquents
- **Vector store** : Taux de succès/échec

## 🔄 Roadmap

### Phase Actuelle ✅

- [x] Base de connaissances thread-safe
- [x] Upload optimisé OpenAI
- [x] Interface MCP 3 outils
- [x] Scripts de workflow
- [x] Tests d'intégration

### Améliorations Futures

- [ ] Interface web pour visualiser la base
- [ ] Synchronisation multi-machines
- [ ] Analytics avancées des mots-clés
- [ ] Support d'autres sources (PDF, etc.)

---

**🏆 Le module MCP DataPrep optimise significativement les workflows de recherche agentique en éliminant les téléchargements et uploads redondants !**
