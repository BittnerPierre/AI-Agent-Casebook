# Présentation des Projets MCP

Ce document présente en détail les deux projets développés pour illustrer les architectures MCP locale et cloud.

---

## 🏠 Projet 1: mcp-evernote-cc (Architecture LOCAL)

### Description
Interface CLI conversationnelle pour interroger mes documents Evernote (chat with doc).

### Motivation
J'utilise Evernote comme outil de prise de note et de capture web. Evernote a intégré des fonctions IA mais je souhaite pouvoir ajouter mes propres fonctions et workflows IA (comme la classification automatique).

Je souhaiterais continuer à utiliser Evernote comme source de mes transcripts et le connecter à mes workflows IA. Actuellement j'utilise MCP Filesystem, mais avec un connecteur MCP Evernote je peux accéder directement à mes notes via leur API sans export intermédiaire.

### Contexte Technique Evernote

**Particularité de l'API Evernote:**
- Evernote ne propose **pas directement d'API Cloud (OpenAPI)** pour manipuler ses notes
- Ils fournissent une **librairie cliente disponible dans plusieurs langages** pour interagir avec les notes
- La communication avec le serveur Evernote se fait (semble-t-il) avec **Thrift** (RPC framework)
- Evernote ne propose **pas son propre serveur MCP**

**Serveur MCP utilisé:**
- J'ai utilisé une **librairie publique disponible sur GitHub**: https://github.com/brentmid/evernote-mcp-server
- Développée par la communauté (pas officiel Evernote)
- Implémentée en **TypeScript**
- Déployée dans un **conteneur Docker** qui tourne en local sur le poste client

### Stack Technique

| Composant | Technologie |
|-----------|-------------|
| **Client MCP** | OpenAI Agents SDK + Python |
| **Serveur MCP** | TypeScript (librairie communautaire GitHub) |
| **Déploiement serveur** | Docker (local) |
| **Transport MCP** | **stdio via Docker exec** |
| **API Evernote** | Thrift (via librairie cliente) |
| **OAuth** | Géré par le serveur MCP |

### Architecture MCP

**Transport: stdio via Docker exec**
```python
docker_cmd = shutil.which("docker")
evernote_mcp_server = MCPServerStdio(
    name="EVERNOTE_MCP_SERVER",
    params={
        "command": docker_cmd,
        "args": [
            "exec", "-i", "--tty=false",
            container_name,
            "sh", "-c", "node mcp-server.js 2>/dev/null"
        ],
    },
    cache_tools_list=True,
)
```

**Pattern de communication:**
```
User → CLI Python → Agents SDK → MCPServerStdio → Docker exec → TypeScript Server → Evernote API
         (client)                  (transport)      (stdin/stdout)   (conteneur)
```

### Gestion OAuth

**OAuth géré PAR le serveur MCP** (transparent pour le client):

1. **Configuration au déploiement:**
   - On déploie l'image Docker avec `EVERNOTE_CONSUMER_KEY` et `EVERNOTE_CONSUMER_SECRET`
   - Ces clés sont demandées auprès du support Evernote (ça prend du temps)

2. **Processus d'authentification:**
   - Le **serveur MCP déclenche** l'authentification OAuth
   - Le **serveur MCP sauvegarde** le token dans le conteneur
   - Le **serveur MCP rafraîchit** automatiquement le token
   - **0 ligne de code OAuth** côté client Python

3. **Conséquence architecturale:**
   - Architecture **1-to-1** (un serveur MCP par client)
   - Le token est lié au conteneur Docker spécifique
   - Pas de mutualisation possible du serveur MCP

**Code client (aucune gestion OAuth):**
```python
async with evernote_mcp_server as server:
    evernote_agent = _create_evernote_agent_with_mcp(server)
    result = await Runner.run_streamed(evernote_agent, conversation)
```

### MCP Client Lifecycle

**Pattern: Long-lived (vit toute la session)**

- Le client MCP est créé **une seule fois** au démarrage
- Il **reste connecté** pendant toute la session conversationnelle
- Connexion **stable** via stdio Docker
- **Pas de problème de token refresh** (géré côté serveur)

**Code pattern:**
```python
async def run_evernote_agent_interactive(
    mcp_server: MCPServerStdio,
    user_input: str,
    conversation_history: list[dict[str, str]] | None = None
):
    # mcp_server passé en paramètre, déjà initialisé
    # Pas de création/destruction à chaque appel

    streamed_result = await run_evernote_agent(
        mcp_server=mcp_server,  # Réutilise la même instance
        conversation=conversation_history,
        stream=True
    )
```

### Agents SDK Architecture

**Agent unique avec MCP integration:**
```python
evernote_agent = Agent(
    name="Evernote Search Agent",
    instructions="""
    You are an AI assistant that helps users search and retrieve
    information from their Evernote notes.

    # Available MCP Tools
    - createSearch: Search for notes using natural language queries
    - getNote: Get note metadata
    - getNoteContent: Retrieve full note content

    # Behavior
    1. Understand user intent
    2. Use appropriate MCP tools
    3. Format results clearly
    4. Be conversational
    """,
    mcp_servers=[mcp_server],
)
```

**Migration CLI direct → AI Agent:**
- **Avant**: CLI direct vers MCP tools (utilisateur devait connaître "createSearch")
- **Après**: Agent interprète langage naturel → sélectionne les bons outils MCP
- **Commit**: `f5eb8e4` - Migration to AI agent architecture

### MCP Tools Disponibles

Le serveur MCP Evernote expose 4 outils:

| Tool | Description | Exemple |
|------|-------------|---------|
| `createSearch` | Rechercher des notes avec requête naturelle | "machine learning notes from last month" |
| `getSearch` | Récupérer résultats de recherche en cache | (utilisé en interne) |
| `getNote` | Obtenir métadonnées détaillées d'une note | GUID → title, dates, tags |
| `getNoteContent` | Récupérer contenu complet d'une note | Formats: text, HTML, ENML |

### Problèmes Rencontrés & Solutions

#### 1. Erreur AI Assistant: Client MCP Custom (2 jours perdus)
**Erreur**: Claude Code a généré un client MCP personnalisé `ProperMCPClient` (166 lignes) au lieu d'utiliser la librairie native.

**Impact**: Erreurs "Server not initialized", debugging complexe, 2 jours perdus

**Solution**:
- **Commit `d9294ac`**: Suppression complète du fichier custom
- Utilisation de `MCPServerStdio` natif avec `async with` context manager
- **Leçon**: Les AI assistants tentent de réimplémenter des protocoles existants au lieu d'utiliser les librairies natives

#### 2. Architecture CLI Direct (sans agent)
**Erreur**: Première version interfaçait directement avec les outils MCP sans couche agent.

**Impact**: UX médiocre, utilisateur devait connaître les noms techniques des outils ("createSearch", "getNoteContent")

**Solution**:
- **Commit `f5eb8e4`**: Migration vers OpenAI Agents SDK
- Agent interprète le langage naturel → sélectionne les outils
- **Leçon**: Toujours ajouter une couche agent pour l'interprétation

#### 3. Logs Techniques Affichés à l'Utilisateur
**Erreur**: Les logs debug du serveur MCP TypeScript étaient affichés à l'utilisateur.

**Impact**: UX confuse avec messages techniques incompréhensibles

**Solution**:
- Suppression stderr: `"sh", "-c", "node mcp-server.js 2>/dev/null"`
- Utilisation de Rich Live avec spinners transients pour les appels d'outils
- **Leçon**: Séparer logs debug vs feedback utilisateur

### Pourquoi ce Projet est Intéressant

1. **Illustre l'architecture locale/on-premise**
   - Transport stdio (pas possible en SaaS)
   - Docker local sur poste client
   - Pas de network, pas de firewall issues

2. **OAuth géré côté serveur (simple pour le client)**
   - 0 ligne de code OAuth côté client
   - Architecture 1-to-1 (trade-off: pas de mutualisation)

3. **Serveur MCP communautaire**
   - Montre qu'on peut utiliser des serveurs non-officiels
   - Utile quand l'API n'a pas de serveur MCP officiel
   - Nécessite compréhension de l'API sous-jacente (Thrift ici)

4. **Client MCP long-lived**
   - Pattern de connexion stable
   - Simplifie la gestion d'état conversationnel
   - Possible grâce à stdio local

5. **Migration CLI → Agent**
   - Montre l'amélioration UX avec couche agent
   - Langage naturel vs commandes techniques

---

## ☁️ Projet 2: customer_onboarding (Architecture CLOUD)

### Description
Workflow agentique pour l'onboarding de prospects d'une banque en ligne.

**Fonctionnalités:**
- Agent conversationnel qui répond aux questions sur produits/services bancaires
- Aide à résoudre les problèmes d'onboarding (web et mobile)
- Vérifie l'éligibilité du prospect avant résolution (inutile de résoudre le problème d'un prospect non-éligible)
- Enrichit le profil utilisateur dans le CRM (HubSpot) via MCP

### Motivation

**Contexte utilisateur:**
- L'utilisateur a déjà réalisé une partie du parcours de création de compte
- Certaines informations sont déjà saisies dans le CRM: banque actuelle, âge, pays de résidence, etc.
- L'utilisateur **ne souhaite pas retransmettre** ces informations de manière non-sécurisée sur un chat

**Solution MCP:**
- Outiller le chat avec un **connecteur MCP HubSpot**
- Permettre à l'agent d'aller **retrouver automatiquement** les informations depuis le CRM
- Utiliser nom + email comme identifiants pour récupérer le profil
- Rend la communication **plus efficace et fluide** (pas de re-saisie)
- L'agent peut **enrichir le profil** avant de vérifier l'éligibilité

**Workflow:**
1. Utilisateur démarre chat avec nom + email
2. Agent principal récupère profil HubSpot via MCP (âge, banque, nationalité)
3. Si question FAQ → délègue à agent FAQ
4. Si problème technique → agent eligibility checker vérifie éligibilité via MCP
5. Si éligible → agent problem solver aide à résoudre
6. Tout au long: guardrails vérifie pas d'info sensible (IBAN, N° de CB etc.)

### Contexte du Projet

**Historique:**
- C'est une **réécriture** du workflow `customer_onboarding` déjà présenté **3 fois** sur la chaîne:
  1. **Première version**: Workflow LangGraph (architecture graphe)
  2. **Deuxième version**: Agents SDK dans un Jupyter notebook
  3. **Troisième version**: Vidéo Jetson Orin Nano (guardrails Agents SDK + appel local avec litellm)

**Pourquoi encore une version?**
- La version LangGraph datait un peu
- Intéressant de refaire en Agents SDK "au propre" (pas dans un notebook)
- Ajouter **intégration MCP HubSpot** (nouvelle fonctionnalité)
- Partir de la version notebook Agents SDK et cleaner

### Stack Technique

| Composant | Technologie |
|-----------|-------------|
| **Client MCP** | OpenAI Agents SDK + Python |
| **Serveur MCP** | **HubSpot MCP officiel** (hébergé par HubSpot) |
| **Transport MCP** | **Streamable HTTP/SSE** |
| **URL Serveur** | `https://mcp.hubspot.com` |
| **OAuth** | Géré par l'application Python (286 lignes) |
| **UI** | CLI simple (créé via Cursor AI) |
| **Eval** | OpenEvals (LLM-as-judge) |

### Architecture Multi-Agents

**1 Superviseur + 3 Agents Experts + 1 Guardrails:**

```
┌─────────────────────────────────────────────────────────────┐
│                    Input Guardrails Agent                    │
│            (vérifie pas d'IBAN/CB/info sensible)                │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                   Main Supervisor Agent                      │
│          (garde la communication avec utilisateur)           │
│              (appelle experts via fonctions)                 │
└───────┬──────────────────┬──────────────────┬───────────────┘
        │                  │                  │
        ▼                  ▼                  ▼
┌──────────────┐  ┌─────────────────┐  ┌────────────────────┐
│  FAQ Agent   │  │ Eligibility     │  │ Problem Solver     │
│              │  │ Checker Agent   │  │ Agent              │
│ (répond aux  │  │ (vérifie avec   │  │ (aide résolution)  │
│  questions)  │  │  MCP HubSpot)   │  │                    │
└──────────────┘  └─────────────────┘  └────────────────────┘
                         │
                         │ MCP HubSpot
                         ▼
                  ┌──────────────┐
                  │   HubSpot    │
                  │   CRM API    │
                  └──────────────┘
```

**Pattern "Ask an Expert":**
- Le superviseur **garde la communication** avec l'utilisateur
- Il **demande de l'aide** aux agents experts via des **fonctions**
- Les experts ne communiquent pas directement avec l'utilisateur
- Le superviseur synthétise et présente les résultats

### Architecture MCP

**Transport: Streamable HTTP/SSE (remote)**

```python
from agents.mcp import MCPServerStreamableHttp

async def run_onboarding_agent_with_mcp(conversation: list[dict[str, str]]):
    # 1. Obtenir token OAuth
    token = await oauth()

    # 2. Créer client MCP avec token dans headers
    mcp_hubspot_server = MCPServerStreamableHttp(
        name="Streamable HTTP Python Server",
        params={
            "url": "https://mcp.hubspot.com",
            "headers": {
                "Authorization": f"Bearer {token['access_token']}"
            },
        },
    )

    # 3. Utiliser dans contexte (short-lived)
    async with mcp_hubspot_server as server:
        customer_onboarding_agent = _create_agents_with_mcp(server)
        result = await Runner.run(customer_onboarding_agent, conversation)
        return result
```

**Pattern de communication:**
```
User → CLI Python → Agents SDK → MCPServerStreamableHttp → HTTPS → HubSpot MCP Server → HubSpot API
         (client)    (superviseur)     (transport)         (internet)   (hébergé)
                        ↓
              3 agents experts
```

### Gestion OAuth

**OAuth géré PAR l'application Python** (complexe):

#### Code OAuth: 286 lignes complètes

**Fichier**: `my_agents/oauth.py` (286 lignes)

**Responsabilités:**
1. ✅ **Token acquisition** (OAuth flow complet)
2. ✅ **Token refresh** (avec marge de 5 minutes)
3. ✅ **Token persistence** (fichier JSON)
4. ✅ **Thread-safety** (asyncio.Lock + portalocker)
5. ✅ **Error handling** (retry, fallback)

**Architecture de l'OAuthManager:**

```python
class OAuthManager:
    def __init__(self):
        self._token: Optional[Dict[str, Any]] = None
        self._lock = asyncio.Lock()  # Thread-safety
        self._token_file = Path("hubspot_token.json")

    async def get_token(self) -> Dict[str, Any]:
        """
        1. Load from file (avec portalocker)
        2. Check validity (avec 5min margin)
        3. Try refresh si expiré
        4. New OAuth flow si refresh échoue
        """
        async with self._lock:
            # Gestion complète du cycle de vie du token
            ...
```

**Processus OAuth complet:**

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Check Token File                                          │
│    ├─ File exists? → Load with portalocker                   │
│    └─ No file? → Go to step 4                                │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. Check Token Validity                                      │
│    ├─ expires_at - now > 5min? → Return token               │
│    └─ Expired or close? → Go to step 3                       │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. Try Token Refresh                                         │
│    ├─ POST /oauth/v1/token (grant_type=refresh_token)       │
│    ├─ Success? → Save + Return new token                     │
│    └─ Fail? → Go to step 4                                   │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. New OAuth Flow                                            │
│    ├─ Lancer navigateur avec authorization URL               │
│    ├─ Utilisateur s'authentifie sur HubSpot                  │
│    ├─ Récupérer authorization code du callback               │
│    ├─ POST /oauth/v1/token (grant_type=authorization_code)   │
│    └─ Save + Return token                                    │
└─────────────────────────────────────────────────────────────┘
```

**Persistence avec thread-safety:**

```python
import portalocker

def _save_token_to_file(self, token: Dict[str, Any]):
    """Save token to file with file locking (thread-safe)"""
    with portalocker.Lock(
        self._token_file,
        mode='w',
        timeout=5
    ) as f:
        json.dump(token, f, indent=2)

def _load_token_from_file(self) -> Optional[Dict[str, Any]]:
    """Load token from file with file locking"""
    if not self._token_file.exists():
        return None

    with portalocker.Lock(
        self._token_file,
        mode='r',
        timeout=5
    ) as f:
        return json.load(f)
```

**Token passé dans headers MCP:**

```python
token = await oauth()  # Obtenir token valide (load/refresh/new)

mcp_hubspot_server = MCPServerStreamableHttp(
    params={
        "url": "https://mcp.hubspot.com",
        "headers": {
            "Authorization": f"Bearer {token['access_token']}"
        },
    },
)
```

#### Comparaison avec Evernote

| Aspect | Evernote (Serveur) | HubSpot (Client) |
|--------|-------------------|------------------|
| **Lignes de code OAuth** | 0 | 286 |
| **Token storage** | Dans conteneur Docker | Fichier JSON avec lock |
| **Token refresh** | Automatique (serveur) | Manuel (application) |
| **Thread-safety** | N/A | asyncio.Lock + portalocker |
| **Margin before expiry** | N/A | 5 minutes |
| **Error handling** | Serveur gère | Application gère |
| **Architecture** | 1-to-1 | N-to-1 (mutualisable) |

### MCP Client Lifecycle

**Pattern: Short-lived (recréé à chaque interaction)**

**Code pattern:**
```python
async def run_onboarding_agent_with_mcp(conversation: list[dict[str, str]]):
    # CHAQUE appel recrée tout
    token = await oauth()  # 1. Get fresh token

    mcp_hubspot_server = MCPServerStreamableHttp(...)  # 2. Create client

    async with mcp_hubspot_server as server:  # 3. Use
        agent = _create_agents_with_mcp(server)
        result = await Runner.run(agent, conversation)
        return result
    # 4. Destroy (exit context manager)
```

**Pourquoi short-lived?**

**Réalisation clé** (insight final de l'utilisateur):
> "Le problème de la durée de vie du client MCP HubSpot est complètement dû au fait qu'il soit distant avec OAuth et le problème de refresh. C'est une décision architecturale."

**Raisons techniques:**
1. **Remote connection**: Connexion HTTP peut être instable (network, timeouts)
2. **OAuth token refresh**: Token expire, besoin de rafraîchir régulièrement
3. **Serverless-friendly**: Design compatible avec fonctions serverless (courte durée)
4. **Stateless**: Chaque requête est indépendante, facilite la scalabilité

**Impact architectural:**
- Impossible de réutiliser le même client MCP entre interactions
- Doit recréer **client MCP + agent** à chaque fois
- Pattern `async with` garantit cleanup proper
- C'est **by design**, pas un bug!

**Contraste avec Evernote:**
- Evernote: stdio local → connexion stable → long-lived OK
- HubSpot: HTTP remote + OAuth → connexion instable → short-lived nécessaire

### MCP Tools Disponibles (HubSpot)

Le serveur MCP HubSpot expose des outils pour manipuler le CRM:

**Utilisés dans ce projet:**
- `contacts_search`: Rechercher des contacts par nom/email
- `contacts_get`: Récupérer les propriétés d'un contact (y compris custom fields)
- `contacts_update`: Mettre à jour les propriétés d'un contact

**Exemple d'utilisation:**
```python
# Agent eligibility checker
tools=[
    "contacts_search",   # Trouver le contact par email
    "contacts_get",      # Récupérer âge, nationalité, banque actuelle
    "contacts_update",   # Enrichir le profil si info manquante
]
```

### Problèmes Rencontrés & Solutions

#### 1. Setup HubSpot Complexe

**Problème**: Configuration initiale très complexe
- Créer une app HubSpot Developer
- Configurer OAuth (client_id, client_secret, redirect_uri, scopes)
- Créer des custom fields (âge, nationalité, banque actuelle)
- **Custom fields invisibles par défaut!**

**Impact**: Temps de setup important, frustration

**Solution partielle**:
- Documentation des étapes
- Scripts d'initialisation (à améliorer)

#### 2. Custom Fields Invisibles par Défaut

**Problème critique**: Les custom fields (âge, nationalité, banque) créés dans HubSpot **ne sont pas visibles par défaut** dans les requêtes MCP.

**Impact**:
- Les appels MCP `contacts_get` ne retournaient pas les champs custom
- L'agent ne pouvait pas vérifier l'éligibilité
- Debugging difficile (pourquoi les champs manquent?)

**Solution**:
- Spécifier **explicitement** les custom fields dans les instructions de l'agent:
  ```python
  instructions="""
  When calling contacts_get, always request these custom fields:
  - age (type: number)
  - nationality (type: string)
  - current_bank (type: string)

  IMPORTANT: Do NOT translate field names to French!
  """
  ```

**Leçon**: Les serveurs MCP n'auto-découvrent pas les custom fields, il faut les documenter explicitement.

#### 3. Traduction Automatique des Noms de Champs

**Problème**: L'agent (GPT-4) traduisait automatiquement les noms de champs en français.

**Exemple:**
- Agent cherche: `"âge"`, `"nationalité"`, `"banque_actuelle"`
- API attend: `"age"`, `"nationality"`, `"current_bank"`
- Résultat: ❌ Échec API

**Solution**:
- Ajouter instruction explicite:
  ```python
  IMPORTANT: HubSpot API requires English field names.
  NEVER translate to French:
  - age (not "âge")
  - nationality (not "nationalité")
  - current_bank (not "banque_actuelle")
  ```

**Leçon**: Avec des LLM multilingues, il faut explicitement contraindre la langue des identifiants techniques.

#### 4. UI Frameworks Incompatibles

**Problème**: Tentative d'intégrer une UI sympathique dans le même processus Python.

**Frameworks testés:**

| Framework | Problème Rencontré |
|-----------|-------------------|
| **Streamlit** | Threading issues avec Agents SDK (async conflicts) |
| **Chainlit** | Trop de dépendances, setup lourd |
| **Gradio** | Trop gros, overhead important |

**Impact**: Impossible d'avoir une UI moderne dans le même processus que les agents

**Solution adoptée**:
- **CLI simple** (créé via Cursor AI)
- Librairie réutilisable pour CLI (`chat_cli` package)
- **Recommandation future**: Séparer avec API
  ```
  Frontend (Streamlit/Gradio/etc.)
         ↓ HTTP
  Backend FastAPI (Agents SDK + MCP)
  ```

**Appel à la communauté:**
> "Si quelqu'un connaît une librairie Python légère pour faire des démos Agents SDK, je suis preneur!"

#### 5. Protocol Confusion (stdio vs HTTP)

**Erreur utilisateur** (admise):
- HubSpot exposait un port Docker
- Utilisateur pensait pouvoir utiliser stdio (comme Evernote)
- Disputes avec Claude Code sur le choix du protocol

**Réalité**:
- HubSpot est un **service SaaS cloud**
- Pas de serveur local possible
- **Obligatoire** d'utiliser streamable HTTP
- Le port Docker était pour autre chose

**Leçon**:
- Local service → stdio possible
- Cloud SaaS → streamable HTTP obligatoire
- "Port exposed" ≠ "MCP via HTTP" (peut être autre service)

### Evaluation avec OpenEvals

**Mise en place d'évaluations automatisées:**

```python
from openevals import LLMAsJudge

# Simulation de conversations
test_cases = [
    {
        "user": "Je suis Pierre, pierre@example.com, j'ai un problème de connexion",
        "expected_behavior": "Check eligibility before solving problem"
    },
    {
        "user": "Mon IBAN est FR76...",
        "expected_behavior": "Guardrails should reject"
    }
]

# LLM-as-judge évalue les réponses
judge = LLMAsJudge(model="gpt-4")
results = judge.evaluate(agent_responses, test_cases)
```

**Métriques évaluées:**
- Respect du workflow (eligibility → problem solving)
- Guardrails efficaces (détection IBAN, N° de CB)
- Utilisation correcte du MCP (récupération profil)
- Qualité des réponses

### Pourquoi ce Projet est Intéressant

1. **Illustre l'architecture cloud/SaaS**
   - Transport streamable HTTP/SSE (seul choix pour cloud)
   - Serveur MCP hébergé par le provider (HubSpot)
   - Network considerations (timeouts, retries)

2. **OAuth géré côté client (complexe mais scalable)**
   - 286 lignes vs 0 pour Evernote
   - Token refresh avec marge de sécurité
   - Thread-safety nécessaire
   - Architecture N-to-1 (plusieurs clients, un serveur)

3. **Serveur MCP officiel**
   - Pas besoin de créer/maintenir le serveur
   - Mais: setup complexe (app, OAuth, custom fields)
   - Pitfall: custom fields invisibles par défaut

4. **Client MCP short-lived (by design)**
   - Pattern serverless-friendly
   - Recréer client+agent à chaque interaction
   - Raison: remote + OAuth + token refresh
   - Décision architecturale, pas un bug

5. **Architecture multi-agents complexe**
   - Superviseur + 3 experts + guardrails
   - Pattern "ask an expert" via fonctions
   - Évaluation avec LLM-as-judge

6. **Challenges d'intégration UI**
   - Threading/async conflicts
   - Recommandation: séparer backend/frontend avec API
   - Appel communauté pour librairie légère

7. **Pitfalls concrets documentés**
   - Custom fields invisibles
   - Traduction automatique des noms de champs
   - Confusion stdio vs HTTP
   - Setup OAuth complexe

---

## 🔄 Contraste des Deux Architectures

### Tableau Comparatif Complet

| Critère | mcp-evernote-cc (LOCAL) | customer_onboarding (CLOUD) |
|---------|-------------------------|------------------------------|
| **Transport MCP** | stdio (Docker exec) | Streamable HTTP/SSE |
| **Déploiement serveur** | Local (conteneur Docker) | Remote (hébergé par HubSpot) |
| **OAuth Management** | Géré PAR serveur MCP | Géré PAR application client |
| **Lignes code OAuth** | 0 | 286 |
| **OAuth flow** | Serveur déclenche | Application déclenche (navigateur) |
| **Token storage** | Dans conteneur Docker | Fichier JSON avec portalocker |
| **Token refresh** | Automatique (serveur) | Manuel (application, 5min margin) |
| **Client MCP lifecycle** | Long-lived (toute session) | Short-lived (par interaction) |
| **Raison lifecycle** | Connexion stdio stable | Remote + OAuth + token refresh |
| **Pattern code** | `async with` une fois au startup | `async with` à chaque interaction |
| **Serveur MCP** | Communautaire (GitHub) | Officiel (HubSpot) |
| **Stack serveur** | TypeScript (custom) | Hébergé (pas d'accès) |
| **Architecture OAuth** | 1-to-1 (serveur par client) | N-to-1 (serveur mutualisé) |
| **Scalabilité** | Limitée (un conteneur par client) | Élevée (serveur mutualisé) |
| **Setup complexity** | Moyenne (Docker + clés API) | Élevée (app, OAuth, custom fields) |
| **Network dependency** | Aucune (local) | Forte (internet requis) |
| **Pitfall principal** | Client MCP custom généré par AI | Custom fields invisibles |
| **Agent architecture** | Agent unique | Superviseur + 3 experts + guardrails |
| **Use case** | Personnel (chat with doc) | Professionnel (customer service) |

### Architecture Visuelle

```
╔═══════════════════════════════════════════════════════════════╗
║                    LOCAL (mcp-evernote-cc)                    ║
╚═══════════════════════════════════════════════════════════════╝

User
  │
  ▼
┌────────────────┐
│  CLI Python    │ ← Agents SDK (1 agent)
└───────┬────────┘
        │ MCPServerStdio
        │ (stdio transport)
        ▼
┌────────────────┐
│ Docker Local   │ ← TypeScript MCP Server
│  (container)   │   + OAuth (géré ici)
└───────┬────────┘
        │ Thrift
        ▼
┌────────────────┐
│  Evernote API  │
└────────────────┘

✅ Long-lived client (stable stdio)
✅ 0 ligne OAuth (serveur gère)
✅ 1-to-1 architecture


╔═══════════════════════════════════════════════════════════════╗
║                  CLOUD (customer_onboarding)                  ║
╚═══════════════════════════════════════════════════════════════╝

User
  │
  ▼
┌─────────────────────┐
│   CLI Python        │ ← Agents SDK
│                     │   (1 superviseur + 3 experts)
│  + OAuthManager     │   + 286 lignes OAuth
│    (286 lines)      │
└─────────┬───────────┘
          │ MCPServerStreamableHttp
          │ (HTTP/SSE transport)
          │ Authorization: Bearer {token}
          │
          │ HTTPS (internet)
          ▼
┌─────────────────────┐
│ HubSpot MCP Server  │ ← Hébergé par HubSpot
│    (hosted)         │
└─────────┬───────────┘
          │ REST API
          ▼
┌─────────────────────┐
│   HubSpot CRM API   │
└─────────────────────┘

⚠️ Short-lived client (remote + OAuth)
⚠️ 286 lignes OAuth (client gère)
✅ N-to-1 architecture (scalable)
```

### Décisions Architecturales Clés

#### 1. Choix du Transport

**Règle:**
- Service local (Docker, native) → **stdio**
- Service cloud (SaaS) → **streamable HTTP/SSE**

**Piège:**
- "Port exposed" ≠ "MCP via HTTP"
- Docker peut exposer port mais MCP utilise quand même stdio (via `docker exec`)

#### 2. Choix de la Gestion OAuth

**Serveur MCP gère OAuth (comme Evernote):**
- ✅ Simple pour le client (0 ligne)
- ✅ Sécurité: token jamais exposé au client
- ❌ Architecture 1-to-1 (pas de mutualisation)
- ❌ Chaque client = un serveur MCP

**Client gère OAuth (comme HubSpot):**
- ❌ Complexe (286 lignes: refresh, persistence, thread-safety)
- ❌ Token géré côté client (risque sécurité)
- ✅ Architecture N-to-1 (serveur mutualisé)
- ✅ Scalabilité élevée

**Trade-off fondamental:**
- Simplicité client vs scalabilité

#### 3. MCP Client Lifecycle

**Insight majeur:**
> Le lifecycle short-lived du client MCP cloud est **by design**, pas un bug.

**Raisons:**
1. Remote connection (instabilité réseau)
2. OAuth token refresh (expiration)
3. Serverless-friendly (fonctions courtes)
4. Stateless (scalabilité)

**Conséquence:**
- Pattern obligatoire pour cloud: créer → utiliser → détruire
- Pattern optionnel pour local: créer une fois → réutiliser

**Code pattern cloud:**
```python
async def handle_user_message(message: str):
    # RECREATE everything each time
    token = await oauth()
    mcp_server = MCPServerStreamableHttp(...)
    async with mcp_server as server:
        agent = create_agent(server)
        result = await Runner.run(agent, conversation)
    # Auto-cleanup on exit
```

### Quand Choisir Quelle Architecture?

| Critère | LOCAL (stdio) | CLOUD (HTTP) |
|---------|---------------|--------------|
| **Service** | Docker local, native app | SaaS cloud |
| **Network** | Pas nécessaire | Internet requis |
| **OAuth** | Préférer serveur gère | Client doit gérer |
| **Scalabilité** | Limitée (1-to-1) | Élevée (N-to-1) |
| **Complexité** | Simple | Complexe |
| **Use case** | Personnel, prototype | Production, multi-users |

---

## 📊 Métriques & Statistiques

### Code Metrics

| Métrique | mcp-evernote-cc | customer_onboarding |
|----------|-----------------|---------------------|
| **Lignes OAuth** | 0 | 286 |
| **Lignes supprimées** (erreurs AI) | 166 (client custom) | ~50 (divers) |
| **Nombre d'agents** | 1 | 5 (1 + 3 + 1) |
| **MCP servers** | 1 (Evernote) | 1 (HubSpot) |
| **Tests** | Unit tests (pytest) | Unit + Eval (OpenEvals) |

### Time Lost to Issues

| Problème | Temps Perdu | Projet |
|----------|-------------|--------|
| Client MCP custom généré | ~2 jours | Evernote |
| Protocol confusion (stdio vs HTTP) | ~0.5 jour | Evernote |
| Custom fields invisibles | ~0.5 jour | HubSpot |
| UI framework integration | ~1 jour | HubSpot |
| Setup OAuth complexe | ~0.5 jour | HubSpot |
| **TOTAL** | **~4.75 jours** | |

### Commits Clés

| Commit | Description | Impact |
|--------|-------------|--------|
| `d9294ac` | Suppression client MCP custom | -166 lignes |
| `f5eb8e4` | Migration to AI agent architecture | +UX |
| `60fc58b` | Suppression logs techniques | +UX |

---

## 🎯 Lessons Learned (Résumé)

### Les 5 Leçons Principales

1. **Transport = fonction du déploiement**
   - Local → stdio
   - Cloud → streamable HTTP
   - Pas d'alternative

2. **OAuth = trade-off simplicité vs scalabilité**
   - Serveur gère: simple mais 1-to-1
   - Client gère: complexe mais N-to-1

3. **Client MCP cloud = short-lived by design**
   - Remote + OAuth + token refresh
   - Pattern: créer → utiliser → détruire
   - Pas un bug, c'est voulu!

4. **AI assistants réimplémentent au lieu de réutiliser**
   - Erreur fréquente: générer client custom
   - Toujours vérifier si librairie native existe
   - Code review critique des suggestions AI

5. **Custom fields = configuration explicite**
   - Serveurs MCP n'auto-découvrent pas
   - Documenter explicitement dans instructions
   - Attention traduction automatique des noms

### Erreurs AI à Éviter

1. ❌ Générer client MCP custom (utiliser librairies natives)
2. ❌ CLI direct vers MCP (ajouter couche agent)
3. ❌ Montrer logs techniques à l'utilisateur (séparer debug/feedback)
4. ❌ Assumer custom fields visibles (documenter explicitement)
5. ❌ UI framework dans même processus (séparer backend/frontend)

---

## 🚀 Extensions Futures

### Pour mcp-evernote-cc
- Fonction de classification automatique des notes
- Agent de résumé (summarization)
- Synchronisation avec autres knowledge bases

### Pour customer_onboarding
- Séparer backend (FastAPI) + frontend (Streamlit/Gradio)
- Ajouter plus de métriques d'évaluation
- Intégrer d'autres CRM via MCP (Salesforce, etc.)

### Écosystème MCP
- Contribuer au catalogue Docker MCP
- Créer des serveurs MCP custom avec FastMCP
- Partager les patterns OAuth trouvés

---

## 📚 Ressources

### Repositories
- **Evernote MCP Server**: https://github.com/brentmid/evernote-mcp-server
- **HubSpot MCP**: https://mcp.hubspot.com
- **OpenAI Agents SDK**: https://github.com/anthropics/agents-sdk
- **FastMCP**: https://github.com/jlowin/fastmcp

### Documentation
- MCP Protocol: https://modelcontextprotocol.io
- OpenAI Agents SDK: https://platform.openai.com/docs/agents
- OpenEvals: https://github.com/openai/evals

### Vidéos Précédentes (customer_onboarding)
1. LangGraph version
2. Agents SDK notebook version
3. Jetson Orin Nano + Guardrails version

---

**Note finale**: Ces deux projets illustrent les **deux faces de MCP** - local/simple vs cloud/scalable. Comprendre les trade-offs entre ces architectures est essentiel pour choisir le bon pattern selon le use case.
