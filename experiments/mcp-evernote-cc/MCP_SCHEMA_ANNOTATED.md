# Schémas MCP Annotés pour Vidéo

> Versions améliorées du schéma original avec annotations, couleurs et build-up progressif

---

## 📐 Version 1 : Schéma Complet Annoté

### Légende des Couleurs

```
🟦 BLEU   = Monde LOCAL (stdio uniquement)
🟧 ORANGE = Monde CLOUD (HTTP/SSE avec OAuth)
🟩 VERT   = Application Layer (votre code)
🟥 ROUGE  = Points de friction / incompatibilités
⚠️ JAUNE  = Avertissements / complexité
```

### Schéma Principal

```
╔═══════════════════════════════════════════════════════════════════════════════════════╗
║                              POURQUOI MCP EXISTE ?                                    ║
╠═══════════════════════════════════════════════════════════════════════════════════════╣
║  Sans MCP : Agent → 20 APIs différentes + 20 formats de docs différents              ║
║  Avec MCP : Agent → MCP (interface standardisée) → N'importe quelle API              ║
╚═══════════════════════════════════════════════════════════════════════════════════════╝

┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                                    MIDDLEWARE LAYER                                     │
└─────────────────────────────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────┬────────────────────────────────────────────────────┐
│  🟦 SERVER / BACKEND (Data)        │  🟧 MIDDLEWARE                                     │
│     MONDE LOCAL                    │     MONDE CLOUD                                    │
└────────────────────────────────────┴────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                                                                                         │
│  ┌──────────────────┐                          ┌──────────────────────────────────┐   │
│  │  ☁️ Cloud        │                          │  ☁️ Cloud / Hosted MCP           │   │
│  │                  │                          │                                  │   │
│  │  ┌────────────┐  │                          │  ┌────────────────────────────┐ │   │
│  │  │ HubSpot    │◄─┼──── oAuth ──────────────┼──┤  🔧 MCP                    │ │   │
│  │  │ API        │  │      (pointillés)        │  │  HubSpot Server            │ │   │
│  │  │    🔒      │  │                          │  │                            │ │   │
│  │  └────────────┘  │                          │  │  ⚠️ HTTP + OAuth           │ │   │
│  │                  │                          │  │  ⚠️ URL publique requise   │ │   │
│  └──────────────────┘                          │  └────────────────────────────┘ │   │
│                                                │                                  │   │
│                                                │  📱 Streamable HTTP              │   │
│  ┌──────────────────┐                          └──────────────────────────────────┘   │
│  │  ☁️ Cloud        │                                         │                        │
│  │                  │                                         │ MCP Flow               │
│  │  ┌────────────┐  │                                         │ (trait plein)          │
│  │  │ Evernote   │◄─┼──── oAuth ────────┐                    ▼                        │
│  │  │ API        │  │      (pointillés)  │                                            │
│  │  │    🔒      │  │                    │    ┌──────────────────────────────────┐   │
│  │  └────────────┘  │                    │    │  🟩 AI APPLICATION               │   │
│  └──────────────────┘                    │    │                                  │   │
│           ▲                               │    │  ┌────────────────────────┐     │   │
│           │                               │    │  │  Application Process   │     │   │
│           │ API (pointillés)              │    │  │  • Authentication      │     │   │
│           │                               └────┼──│  • Agentic SDK        │     │   │
│  ┌────────────────────────────────┐           │  │  • 🤖 AI Agent        │     │   │
│  │  📄 Desktop / Intranet          │           │  └────────────────────────┘     │   │
│  │                                 │           │                                  │   │
│  │  ┌──────────────────┐           │           │  ┌────────────────────────┐     │   │
│  │  │  Evernote SDK    │           │           │  │  🔧 MCP                │     │   │
│  │  │  (API local)     │           │           │  │  HubSpot Client        │     │   │
│  │  └──────────────────┘           │           │  └────────────────────────┘     │   │
│  │           ▲                     │           │                                  │   │
│  │           │                     │           │  ┌────────────────────────┐     │   │
│  │           │ stdio               │           │  │  🔧 MCP                │     │   │
│  │           │ (trait plein)       │           │  │  Evernote Client       │     │   │
│  │  ┌────────┴──────────┐          │           │  └────────────────────────┘     │   │
│  │  │  🐳 Desktop /      │          │           └──────────────────────────────────┘   │
│  │  │  Local MCP         │          │                          │                       │
│  │  │                    │          │                          │ streamable http       │
│  │  │  ┌──────────────┐  │          │                          │                       │
│  │  │  │ 🔧 MCP       │  │          │                          ▼                       │
│  │  │  │ Evernote     │  │          │   ┌──────────────────────────────────────────┐  │
│  │  │  │ Server       │  │          │   │  🟧 CLIENT / FRONTEND (Usage)            │  │
│  │  │  │              │  │          │   │      MONDE CLOUD (HTTP/SSE)              │  │
│  │  │  │ 🐳 Docker    │  │          │   │                                          │  │
│  │  │  │              │  │          │   │  ☁️ Cloud / SaaS                         │  │
│  │  │  │ ⚠️ stdio     │  │          │   │  ✅ ChatGPT   ✅ Claude   🌐 Web         │  │
│  │  │  │ LOCAL ONLY   │  │          │   │  ✅ Le Chat   Native connectors          │  │
│  │  │  └──────────────┘  │          │   │  📧 Gmail   📅 Calendar                 │  │
│  │  └────────────────────┘          │   │  👔 Teams   💼 Outlook                  │  │
│  └─────────────────────────────────┘   │  🔵 Dropbox 📦 Box                       │  │
│                                         └──────────────────────────────────────────┘  │
│  ┌─────────────────────────────────┐   ┌──────────────────────────────────────────┐  │
│  │  🟦 Desktop / Local MCP          │   │  🟦 HOSTED MCP (Dev)                     │  │
│  │      MONDE LOCAL (stdio)         │   │      MONDE LOCAL (stdio)                 │  │
│  │                                  │   │                                          │  │
│  │  ✅ Playwright   ✅ Figma        │   │  ✅ Product    ✅ Business               │  │
│  │  ✅ Claude+Code  ✅ Anthropic    │   │  ✅ Figma      ✅ Intercom               │  │
│  │  ✅ GitHub       ✅ Snowflake    │   │  ✅ Atlassian  ✅ Notion                 │  │
│  │  🔺 Cloudflare   🌊 Neon         │   │  ✅ Azure      ✅ GitHub                 │  │
│  │  ❌ ChatGPT      ❌ Le Chat      │   │  🔵 Snowflake  💎 Morningstar            │  │
│  │                                  │   │  💼 S&P        🛡️ Brex                   │  │
│  └─────────────────────────────────┘   └──────────────────────────────────────────┘  │
│                                                                                       │
│  ┌──────────────────────────────────────────────────────────────────────────────┐   │
│  │  📱 Chat Interface and Code Editors                                          │   │
│  │      MONDE LOCAL (desktop apps)                                              │   │
│  │                                                                               │   │
│  │  ✅ ChatGPT+Codex   ✅ Claude+Code                                            │   │
│  │  🦀 Cursor          🏄 Windsurf                                               │   │
│  │  ❌ ChatGPT (web)   ❌ Le Chat (web)                                          │   │
│  └──────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                       │
└───────────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                                      LEGEND                                             │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│  ······► Authentication (oAuth)                  🐳 Docker Container                    │
│  ━━━━━► MCP Flow (resources or tools)            🤖 AI Agent (LLM)                      │
│  ─ ─ ─► API (ex: OpenAPI)                        📱 Web Application                     │
│  🔒 oAuth Server  </> API (ex: OpenAPI)          ☁️ Cloud Hosted                        │
│  🔧 MCP Server    🔧 MCP Client                  📄 Local host                          │
└─────────────────────────────────────────────────────────────────────────────────────────┘

╔═══════════════════════════════════════════════════════════════════════════════════════╗
║                        🚨 POINTS DE FRICTION CRITIQUES                                ║
╠═══════════════════════════════════════════════════════════════════════════════════════╣
║  1. ⛔ PAS DE PONT LOCAL ↔️ CLOUD                                                     ║
║     Les outils locaux (Docker stdio) ne peuvent pas être utilisés par les SaaS cloud  ║
║                                                                                        ║
║  2. ⚠️ OAUTH COMPLEXE (286 lignes de code)                                            ║
║     Serveur local + Token refresh + Persistance requis pour chaque service            ║
║                                                                                        ║
║  3. ⚠️ SETUP NON-TRIVIAL                                                              ║
║     • HubSpot : CLIENT_ID, SECRET, redirect URI, scopes                               ║
║     • Evernote : Docker container, exec transport, error handling                     ║
║                                                                                        ║
║  4. 🐛 CYCLE DE VIE ASYNC                                                             ║
║     Context managers obligatoires (async with) - 166 lignes supprimées sur Evernote   ║
╚═══════════════════════════════════════════════════════════════════════════════════════╝
```

---

## 🎬 Version 2 : Build-up Progressif (Animation)

### Frame 1 - "Le Rêve" (0:30)

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│                   "Le Rêve MCP"                             │
│                                                             │
│              ┌──────────────────────┐                       │
│              │  🟩 AI Application   │                       │
│              │                      │                       │
│              │  "Je veux accéder à  │                       │
│              │   tous mes outils"   │                       │
│              │                      │                       │
│              └──────────────────────┘                       │
│                                                             │
│              Interface standardisée MCP                     │
│              ↓       ↓       ↓       ↓                      │
│           [Evernote][HubSpot][Notion][...]                  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Frame 2 - "Cas 1 : Outil Local" (1:00)

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│           🟦 CAS 1 : OUTIL LOCAL (stdio)                    │
│                                                             │
│              ┌──────────────────────┐                       │
│              │  🟩 AI Application   │                       │
│              └──────────┬───────────┘                       │
│                         │                                   │
│                         │ stdio                             │
│                         ▼                                   │
│              ┌──────────────────────┐                       │
│              │ 🐳 MCP Evernote      │                       │
│              │    (Docker Local)    │                       │
│              └──────────────────────┘                       │
│                         │                                   │
│                         ▼                                   │
│              ┌──────────────────────┐                       │
│              │  📦 Evernote API     │                       │
│              └──────────────────────┘                       │
│                                                             │
│  ✅ Marche avec :                                           │
│     • Claude Code (desktop)                                 │
│     • Cursor (desktop)                                      │
│                                                             │
│  ❌ NE marche PAS avec :                                    │
│     • ChatGPT (web)                                         │
│     • Le Chat (web)                                         │
│     • Tout SaaS cloud                                       │
│                                                             │
│  💡 Pourquoi ? stdio = processus local uniquement           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Frame 3 - "Cas 2 : Service Cloud" (1:30)

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│      🟧 CAS 2 : SERVICE CLOUD (HTTP + OAuth)                │
│                                                             │
│              ┌──────────────────────┐                       │
│              │  🟩 AI Application   │                       │
│              └──────────┬───────────┘                       │
│                         │                                   │
│                         │ HTTP/SSE                          │
│                         ▼                                   │
│              ┌──────────────────────┐                       │
│              │ 🔧 MCP HubSpot       │                       │
│              │    (Cloud/Hosted)    │                       │
│              │                      │                       │
│              │ ⚠️ Requiert :        │                       │
│              │  • URL publique      │                       │
│              │  • OAuth setup       │                       │
│              │  • Token refresh     │                       │
│              └──────────┬───────────┘                       │
│                         │                                   │
│                         │ OAuth                             │
│                         ▼                                   │
│              ┌──────────────────────┐                       │
│              │  ☁️ HubSpot API      │                       │
│              └──────────────────────┘                       │
│                                                             │
│  ✅ Marche avec :                                           │
│     • ChatGPT (web)                                         │
│     • Le Chat (web)                                         │
│     • Claude Code (desktop + web)                           │
│     • N'importe quel client                                 │
│                                                             │
│  ⚠️ Mais... Setup complexe :                                │
│     • 286 lignes de code OAuth                              │
│     • CLIENT_ID, SECRET à configurer                        │
│     • Serveur local pour callback                           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Frame 4 - "Le Dilemme" (2:00)

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│              🚨 LE DILEMME MCP 🚨                           │
│                                                             │
│   🟦 MONDE LOCAL              🟧 MONDE CLOUD                │
│   (stdio)                     (HTTP/SSE + OAuth)            │
│                                                             │
│   ✅ Simple à setup           ❌ Setup complexe             │
│   ✅ Pas d'auth               ✅ OAuth robuste              │
│   ✅ Faible latence           ✅ Accessible partout         │
│   ❌ Desktop uniquement        ✅ SaaS compatible           │
│   ❌ Pas scalable             ✅ Production-ready           │
│                                                             │
│              ⛔ PAS DE PONT SIMPLE                          │
│           entre les deux mondes                             │
│                                                             │
│  💡 Vous devez CHOISIR votre architecture                   │
│     selon votre use case                                    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎨 Version 3 : Schéma Simplifié (Thumbnail YouTube)

```
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║          MCP : LES 2 MONDES QUI NE SE PARLENT PAS            ║
║                                                               ║
╠═══════════════════════════════════════════════════════════════╣
║                                                               ║
║  ┌────────────────────┐      ⛔      ┌────────────────────┐  ║
║  │   🟦 LOCAL 🖥️      │              │   🟧 CLOUD ☁️      │  ║
║  │                    │    FAIL      │                    │  ║
║  │  🐳 Docker         │              │  🌐 OAuth + HTTP   │  ║
║  │  stdio             │              │  Streamable HTTP   │  ║
║  │                    │              │                    │  ║
║  │  ✅ Claude Code    │              │  ❌ Claude Code    │  ║
║  │  ✅ Cursor         │              │  ❌ Cursor         │  ║
║  │  ❌ ChatGPT        │              │  ✅ ChatGPT        │  ║
║  │  ❌ Le Chat        │              │  ✅ Le Chat        │  ║
║  │                    │              │                    │  ║
║  │  Exemple :         │              │  Exemple :         │  ║
║  │  Evernote (Docker) │              │  HubSpot (OAuth)   │  ║
║  └────────────────────┘              └────────────────────┘  ║
║                                                               ║
║  💡 Il n'existe pas (encore) de solution universelle          ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝

           👇 3 PIÈGES QUI VONT VOUS COÛTER DES JOURS 👇
```

**Style pour thumbnail** :
- Fond : Dégradé bleu (local) vers orange (cloud)
- Texte : Blanc, gras, très lisible
- ⛔ rouge vif au centre
- Votre photo en coin bas droit avec expression frustrée

---

## 🎯 Version 4 : Flow Utilisateur (User Journey)

```
╔═══════════════════════════════════════════════════════════════════════════════╗
║                      EXEMPLE : RECHERCHE EVERNOTE                             ║
╚═══════════════════════════════════════════════════════════════════════════════╝

    👤 USER
    │
    │ "Find my notes about AI"
    ▼
┌───────────────────────┐
│  💬 Claude Code       │  ← Desktop app (local)
│  (Chat Interface)     │
└───────┬───────────────┘
        │
        │ User input
        ▼
┌───────────────────────┐
│  🤖 AI Agent          │  ← Interprète la requête
│  (OpenAI Agents SDK)  │
└───────┬───────────────┘
        │
        │ Découvre MCP tools
        ▼
┌───────────────────────┐
│  🔧 MCP Evernote      │  ← Client MCP (dans l'app)
│  Client               │
└───────┬───────────────┘
        │
        │ stdio (local process)
        ▼
┌───────────────────────┐
│  🐳 MCP Evernote      │  ← Docker container
│  Server               │
│                       │
│  ⚠️ stdio uniquement  │
│  ❌ Pas accessible    │
│     depuis le web     │
└───────┬───────────────┘
        │
        │ API call
        ▼
┌───────────────────────┐
│  📦 Evernote API      │  ← Backend Evernote
│  (www.evernote.com)   │
└───────┬───────────────┘
        │
        │ Response
        ▼
    👤 USER
       "Voici vos notes sur l'AI..."


╔═══════════════════════════════════════════════════════════════════════════════╗
║                      EXEMPLE : RECHERCHE HUBSPOT                              ║
╚═══════════════════════════════════════════════════════════════════════════════╝

    👤 USER
    │
    │ "Find contact 'Marc Lefevre'"
    ▼
┌───────────────────────┐
│  💬 ChatGPT           │  ← SaaS cloud
│  (Web Interface)      │
└───────┬───────────────┘
        │
        │ User input
        ▼
┌───────────────────────┐
│  🤖 AI Agent          │  ← Interprète la requête
│  (OpenAI GPT-4)       │
└───────┬───────────────┘
        │
        │ Appelle MCP tool
        ▼
┌───────────────────────┐
│  🔧 MCP HubSpot       │  ← Client MCP (cloud)
│  Client               │
└───────┬───────────────┘
        │
        │ HTTPS + Auth header
        ▼
┌───────────────────────┐
│  ☁️ MCP HubSpot       │  ← Serveur MCP hosted
│  Server               │
│  (mcp.hubspot.com)    │
│                       │
│  ⚠️ OAuth requis      │
│  ⚠️ Token refresh     │
│  ⚠️ URL publique      │
└───────┬───────────────┘
        │
        │ OAuth + API call
        ▼
┌───────────────────────┐
│  ☁️ HubSpot API       │  ← Backend HubSpot
│  (api.hubapi.com)     │
└───────┬───────────────┘
        │
        │ Response
        ▼
    👤 USER
       "Contact trouvé : Marc Lefevre..."
```

---

## 📊 Version 5 : Comparaison Côte à Côte

```
╔════════════════════════════════════════════════════════════════════════════╗
║              LOCAL (stdio) vs CLOUD (HTTP/SSE) - COMPARAISON              ║
╚════════════════════════════════════════════════════════════════════════════╝

┌───────────────────────────┬──────────────────────────────────────────────┐
│  CRITÈRE                  │  🟦 LOCAL          │  🟧 CLOUD               │
├───────────────────────────┼────────────────────┼─────────────────────────┤
│  Transport                │  stdio             │  HTTP/SSE               │
│  Authentification         │  ❌ Aucune         │  ✅ OAuth 2.0           │
│  Latence                  │  ⚡ Très faible    │  🐌 Dépend réseau       │
│  Setup                    │  ✅ Simple         │  ⚠️ Complexe (286 LOC)  │
│  Scalabilité              │  ❌ Limitée        │  ✅ Production-ready    │
│  Debugging                │  ✅ Facile (logs)  │  ⚠️ Plus complexe       │
│  SaaS Compatible          │  ❌ Non            │  ✅ Oui                 │
│  Desktop Apps             │  ✅ Oui            │  ✅ Oui                 │
│  Sécurité                 │  🔒 Sandbox local  │  🔐 OAuth + HTTPS       │
│  Déploiement              │  🖥️ Local          │  ☁️ Cloud infra         │
│  Coût                     │  💵 Gratuit        │  💰 Infra + auth        │
├───────────────────────────┼────────────────────┼─────────────────────────┤
│  USE CASE IDÉAL           │                    │                         │
│                           │  • Outils locaux   │  • Services SaaS        │
│                           │  • Dev/Prototyping │  • Production           │
│                           │  • Desktop apps    │  • Multi-tenant         │
│                           │  • Pas de cloud    │  • Accès universel      │
├───────────────────────────┼────────────────────┼─────────────────────────┤
│  EXEMPLES                 │                    │                         │
│                           │  • Evernote+Docker │  • HubSpot              │
│                           │  • Filesystem      │  • Slack                │
│                           │  • Local DB        │  • Notion               │
└───────────────────────────┴────────────────────┴─────────────────────────┘

╔════════════════════════════════════════════════════════════════════════════╗
║                    💡 RECOMMANDATION                                       ║
╠════════════════════════════════════════════════════════════════════════════╣
║  Prototyping/Dev   →  Local (stdio)    → Plus rapide                      ║
║  Production/SaaS   →  Cloud (HTTP/SSE) → Scalable                         ║
║                                                                            ║
║  ⚠️ Pas de migration simple entre les deux !                              ║
║     Planifiez votre architecture dès le début                             ║
╚════════════════════════════════════════════════════════════════════════════╝
```

---

## 🚀 Version 6 : Roadmap MCP (Vision Future)

```
╔═══════════════════════════════════════════════════════════════════════════════╗
║                          AUJOURD'HUI (2025)                                   ║
╠═══════════════════════════════════════════════════════════════════════════════╣
║                                                                               ║
║    🟦 LOCAL                  ⛔                  🟧 CLOUD                     ║
║    (stdio)                  ISOLÉS              (HTTP/SSE)                    ║
║                                                                               ║
║    • Claude Code            Pas de pont         • ChatGPT                    ║
║    • Cursor                 universel           • Le Chat                    ║
║    • Docker local                               • OAuth complexe             ║
║                                                                               ║
║    ❌ Pas scalable                              ✅ Scalable                  ║
║    ✅ Simple setup                              ❌ Setup complexe            ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
                                    │
                                    │ Évolution
                                    ▼
╔═══════════════════════════════════════════════════════════════════════════════╗
║                          FUTUR (2026 ?)                                       ║
╠═══════════════════════════════════════════════════════════════════════════════╣
║                                                                               ║
║                       🌉 MCP GATEWAY UNIVERSEL                                ║
║                    (Bridge Local ↔️ Cloud)                                    ║
║                                                                               ║
║    🟦 LOCAL                                         🟧 CLOUD                  ║
║    ├─── stdio ───┐                         ┌─── HTTP/SSE ───                 ║
║    │             │                         │                                 ║
║    │             ├──► 🌉 Gateway ◄─────────┤                                 ║
║    │             │                         │                                 ║
║    └─────────────┘                         └─────────────────                ║
║                                                                               ║
║    ✅ Tunnel sécurisé local → cloud                                          ║
║    ✅ OAuth standardisé (one-time setup)                                     ║
║    ✅ Auto-discovery des MCP servers                                         ║
║    ✅ Load balancing + failover                                              ║
║    ✅ Monitoring + observability                                             ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝

╔═══════════════════════════════════════════════════════════════════════════════╗
║                          CE QUI ARRIVE                                        ║
╠═══════════════════════════════════════════════════════════════════════════════╣
║  2025 Q2 : MCP v2.0 - Breaking changes pour stabilité                        ║
║  2025 Q3 : OAuth standardisé (spec commune)                                  ║
║  2025 Q4 : Gateway beta (Anthropic/OpenAI)                                   ║
║  2026 Q1 : Bridge local ↔️ cloud GA                                          ║
║                                                                               ║
║  💡 Positionnez-vous TÔT sur MCP pour être prêt !                            ║
╚═══════════════════════════════════════════════════════════════════════════════╝
```

---

## 🎬 Instructions pour Animation (Excalidraw / PowerPoint)

### Outils Recommandés

1. **Excalidraw** (gratuit, open source)
   - Importez le schéma comme texte
   - Utilisez les formes rectangulaires avec arrondis
   - Couleurs : Bleu #3B82F6, Orange #F97316, Vert #10B981, Rouge #EF4444

2. **Figma** (gratuit pour usage personnel)
   - Plus professionnel
   - Animations natives
   - Export MP4 direct

3. **PowerPoint / Keynote**
   - Transitions "Morph" pour build-up
   - Export vidéo 1080p

### Palette de Couleurs

```
🟦 Bleu Local   : #3B82F6 (Tailwind blue-500)
🟧 Orange Cloud : #F97316 (Tailwind orange-500)
🟩 Vert App     : #10B981 (Tailwind emerald-500)
🟥 Rouge Alert  : #EF4444 (Tailwind red-500)
⚠️ Jaune Warning: #F59E0B (Tailwind amber-500)
```

### Timeline Animation (12 min vidéo)

```
0:30-1:00 : Frame 1 "Le Rêve"          (fade in)
1:00-1:30 : Frame 2 "Local"            (slide left)
1:30-2:00 : Frame 3 "Cloud"            (slide right)
2:00-2:30 : Frame 4 "Dilemme"          (split screen)
...
10:30     : Schéma Roadmap             (zoom out)
11:45     : Call to action             (fade to outro)
```

### Annotations à Animer

- ⛔ "Pas de pont" : Apparaît avec shake
- ⚠️ Warnings : Pulse (battement)
- ✅ Checkmarks : Pop-in avec son
- ❌ Crosses : Slide-in rouge

---

## 📝 Notes pour le Montage Vidéo

### Overlay Code Timing

**2:00-2:30** - Pendant explication cycle de vie :
```python
# ❌ AVANT (mauvais pattern)
class CustomMCPClient:
    def connect(self): ...

# ✅ APRÈS (bon pattern)
async with MCPServerStdio(...) as server:
    agent = Agent(mcp_servers=[server])
```

**5:00-5:30** - Pendant explication OAuth :
```python
# Pattern singleton OAuth
token = await oauth()  # Auto-refresh
mcp_server = MCPServerStreamableHttp(
    headers={"Authorization": f"Bearer {token['access_token']}"}
)
```

**8:00-8:30** - Pendant explication performance :
```python
# Optimisation : stocker l'ID
entry.openai_file_id = "file_abc123"  # ♻️ Réutilise
# Résultat : 35s → 12s (-65%)
```

### B-roll Suggestions

- Screen recording terminal avec erreurs
- Browser OAuth flow en accéléré
- Logs défilant avec métriques
- GitHub repo navigation
- Documentation MCP officielle

---

## ✅ Checklist Création Visuels

- [ ] Schéma complet annoté (version finale)
- [ ] Build-up progressif (4 frames)
- [ ] Thumbnail simplifié (YouTube)
- [ ] Flow utilisateur (2 exemples)
- [ ] Tableau comparaison (Local vs Cloud)
- [ ] Roadmap future (vision)
- [ ] Palette de couleurs exportée
- [ ] Animations timeline définies
- [ ] Code overlays préparés
- [ ] B-roll list complétée

---

**Prochaines étapes** :
1. Importer dans Excalidraw/Figma
2. Appliquer la palette de couleurs
3. Animer selon timeline
4. Exporter PNG (thumbnail) + MP4 (animations)
5. Intégrer dans montage vidéo final

Besoin d'aide pour un des schémas en particulier ?
