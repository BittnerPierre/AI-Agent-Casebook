# Plan de Migration EditingTeam : Assistant API vers Agents SDK

## Contexte et Justification

### Problème Identifié
Le module `editing_team.py` utilise actuellement l'OpenAI Assistant API (`client.beta.assistants.*` et `client.beta.threads.*`) qui sera dépréciée en 2026. L'architecture actuelle viole les règles de compliance définies dans `CLAUDE.md` qui interdisent l'usage de ces APIs legacy.

### Objectif de Migration
Migrer vers OpenAI Agents SDK en préservant la fonctionnalité existante et en permettant une coexistence temporaire des deux implémentations pour une migration sans risque.

## Architecture Cible

### Pattern Factory/Interface
```
BaseEditingTeam (Abstract)
├── Fonctions communes (60% réutilisable)
├── AssistantAPIEditingTeam (Legacy - préservé)
└── AgentsSDKEditingTeam (Nouveau - conforme)

EditingTeamFactory
├── create("assistant_api") → AssistantAPIEditingTeam  
└── create("agents_sdk") → AgentsSDKEditingTeam
```

### Workflow Editorial Explicite
```
Phase 1: Setup & Preparation
├── _create_research_files() [COMMUNE]
├── _upload_files_to_vector_store() [COMMUNE]  
└── _setup_agents() [SPÉCIFIQUE]

Phase 2: Multi-Agent Editorial Process
├── _execute_documentalist_step() [SPÉCIFIQUE]
├── _execute_writer_step() [SPÉCIFIQUE]
├── _execute_reviewer_step() [SPÉCIFIQUE]
└── _execute_strategist_step() [SPÉCIFIQUE]

Phase 3: Cleanup
└── _cleanup_resources() [COMMUNE + SPÉCIFIQUE]
```

## Plan de Refactoring

### Étape 1: Extraction Interface et Classes Abstraites

#### 1.1 Créer `EditorialContext`
```python
@dataclass
class EditorialContext:
    """Context partagé entre agents avec gestion d'état conversation"""
    research_notes: Dict[str, Any]
    target_section: str
    vector_store_id: str | None = None
    documented_content: str | None = None
    draft_content: str | None = None
    review_feedback: str | None = None
    
    # Gestion état conversation pour Agents SDK
    conversation_history: list[Dict[str, str]] = field(default_factory=list)
    last_agent_result: Any = None  # Résultat du dernier agent pour continuité
```

#### 1.2 Créer `EditingTeamWorkflow` (Interface)
```python
class EditingTeamWorkflow(ABC):
    def synthesize_chapter(self, research_notes: Dict[str, Any]) -> ChapterDraft:
        """Orchestration principale avec workflow explicite"""
    
    @abstractmethod
    def _setup_research_environment(self, context: EditorialContext) -> None: pass
    
    @abstractmethod  
    def _execute_documentalist_step(self, context: EditorialContext) -> None: pass
    
    @abstractmethod
    def _execute_writer_step(self, context: EditorialContext) -> None: pass
    
    @abstractmethod
    def _execute_reviewer_step(self, context: EditorialContext) -> None: pass
    
    @abstractmethod
    def _execute_strategist_step(self, context: EditorialContext) -> None: pass
    
    @abstractmethod
    def _finalize_chapter(self, context: EditorialContext) -> ChapterDraft: pass
    
    @abstractmethod
    def _cleanup_resources(self) -> None: pass
```

#### 1.3 Créer `BaseEditingTeam` (Classe Abstraite)
```python
class BaseEditingTeam(EditingTeamWorkflow):
    """Fonctions communes réutilisables (~60% du code)"""
    
    # === FONCTIONS COMMUNES ===
    def _create_research_files(self, research_notes: Dict[str, Any]) -> list[str]:
        """Code actuel lignes 191-261 - identique"""
    
    def _upload_files_to_vector_store(self, file_paths: list[str]) -> str:
        """Code actuel lignes 263-302 - identique"""
    
    def _get_training_guidelines(self) -> str:
        """Code actuel lignes 489-509 - identique"""
    
    # === QUERY BUILDERS COMMUNES ===
    def _create_documentalist_query(self, target_section: str, research_notes: Dict[str, Any]) -> str:
        """Code actuel lignes 403-414 - même logique métier"""
    
    def _create_writer_query(self, target_section: str, documented_content: str, research_notes: Dict[str, Any]) -> str:
        """Code actuel lignes 416-431 - même logique métier"""
    
    def _create_reviewer_query(self, target_section: str, draft_content: str) -> str:
        """Code actuel lignes 433-448 - même logique métier"""
    
    def _create_final_revision_query(self, target_section: str, draft_content: str, review_feedback: str) -> str:
        """Code actuel lignes 450-468 - même logique métier"""
    
    # === TEMPLATE METHOD PATTERN ===
    def _setup_research_environment(self, context: EditorialContext) -> None:
        file_paths = self._create_research_files(context.research_notes)
        context.vector_store_id = self._upload_files_to_vector_store(file_paths)
        self._setup_agents(context)  # Méthode abstraite
    
    @abstractmethod
    def _setup_agents(self, context: EditorialContext) -> None:
        """Spécifique à chaque implémentation"""
    
    def _finalize_chapter(self, context: EditorialContext) -> ChapterDraft:
        """Finalisation commune"""
        return ChapterDraft(
            section_id=context.target_section,
            content=context.draft_content or "Error: No content generated"
        )
```

### Étape 2: Refactoring AssistantAPIEditingTeam

#### 2.1 Migrer Code Existant
```python
class AssistantAPIEditingTeam(BaseEditingTeam):
    """Implémentation Assistant API avec workflow explicite"""
    
    def _setup_agents(self, context: EditorialContext) -> None:
        """Setup Assistant API"""
        self.assistant_id = self._create_research_assistant(context.vector_store_id)
        thread = self.client.beta.threads.create()
        self.thread_id = thread.id
    
    def _execute_documentalist_step(self, context: EditorialContext) -> None:
        """Documentalist via Assistant API"""
        query = self._create_documentalist_query(context.target_section, context.research_notes)
        context.documented_content = self._synthesize_content_step(
            self.thread_id, self.assistant_id, query, "documentalist"
        )
    
    # ... autres étapes similaires
    
    def _synthesize_content_step(self, thread_id: str, assistant_id: str, query: str, agent_role: str) -> str:
        """Code actuel lignes 359-401 - préservé tel quel"""
```

#### 2.2 Tests Non-Régression
- Valider que l'implémentation refactorisée produit les mêmes résultats
- Tests d'intégration avec le workflow complet
- Validation de la compatibilité backward

### Étape 3: Implémentation AgentsSDKEditingTeam

#### 3.1 Setup Multi-Agent Architecture
```python
class AgentsSDKEditingTeam(BaseEditingTeam):
    """Implémentation Agents SDK conforme"""
    
    def _setup_agents(self, context: EditorialContext) -> None:
        """Setup Agents SDK avec FileSearchTool"""
        self.documentalist = Agent(
            name="Documentalist",
            instructions=self._get_documentalist_instructions(),
            tools=[FileSearchTool(vector_store_ids=[context.vector_store_id])]
        )
        
        self.writer = Agent(
            name="Writer", 
            instructions=self._get_writer_instructions(),
            handoffs=[self.reviewer]  # Pattern handoff
        )
        
        self.reviewer = Agent(
            name="Reviewer",
            instructions=self._get_reviewer_instructions(), 
            handoffs=[self.strategist]
        )
        
        self.strategist = Agent(
            name="ScriptStrategist",
            instructions=self._get_strategist_instructions()
        )
```

#### 3.2 Workflow Execution avec Agents SDK et Context Management
```python
def _execute_documentalist_step(self, context: EditorialContext) -> None:
    """Documentalist via Agents SDK avec context management"""
    query = self._create_documentalist_query(context.target_section, context.research_notes)
    
    # Utilisation du context management pour état conversation
    input_messages = self._build_input_from_context(context, query)
    
    # Exécution asynchrone recommandée
    result = await Runner.run(self.documentalist, input_messages)
    
    # Mise à jour context avec résultat
    context.documented_content = self._extract_content(result)
    context.last_agent_result = result
    self._update_conversation_context(context, query, result)

def _execute_writer_step(self, context: EditorialContext) -> None:
    """Writer via Agents SDK avec continuité conversation"""
    query = self._create_writer_query(
        context.target_section, 
        context.documented_content, 
        context.research_notes
    )
    
    # Continuité avec résultat agent précédent
    input_messages = self._build_input_from_context(context, query)
    
    result = await Runner.run(self.writer, input_messages)
    
    context.draft_content = self._extract_content(result)
    context.last_agent_result = result
    self._update_conversation_context(context, query, result)

# Pattern similaire pour reviewer et strategist
```

#### 3.3 Context Management Implementation
```python
def _build_input_from_context(self, context: EditorialContext, new_query: str) -> list:
    """Construction input avec état conversation via context management"""
    # Si premier agent, commencer nouvelle conversation
    if not context.last_agent_result:
        return [{"role": "user", "content": new_query}]
    
    # Utiliser result.to_input_list() pour continuité (recommandation OpenAI)
    conversation_history = context.last_agent_result.to_input_list()
    conversation_history.append({"role": "user", "content": new_query})
    return conversation_history

def _update_conversation_context(self, context: EditorialContext, query: str, result) -> None:
    """Mise à jour contexte conversation pour agent suivant"""
    # Ajouter échange dans l'historique local pour debugging
    context.conversation_history.extend([
        {"role": "user", "content": query},
        {"role": "assistant", "content": self._extract_content(result)}
    ])
    
    # Le result.to_input_list() sera utilisé pour l'agent suivant
    context.last_agent_result = result

def _extract_content(self, result) -> str:
    """Extraction contenu du résultat agent"""
    # Adaptation selon structure retour Agents SDK
    if hasattr(result, 'content'):
        return result.content
    elif hasattr(result, 'text'):
        return result.text
    else:
        return str(result)
```

### Étape 4: Factory Implementation

#### 4.1 EditingTeamFactory
```python
class EditingTeamFactory:
    @staticmethod
    def create(implementation: str = "assistant_api", **kwargs) -> EditingTeamWorkflow:
        """Factory pour création EditingTeam"""
        if implementation == "assistant_api":
            return AssistantAPIEditingTeam(**kwargs)
        elif implementation == "agents_sdk":
            return AgentsSDKEditingTeam(**kwargs)
        else:
            raise ValueError(f"Unknown implementation: {implementation}")

# Usage
editing_team = EditingTeamFactory.create("agents_sdk")
chapter = editing_team.synthesize_chapter(research_notes)
```

#### 4.2 Configuration YAML (Fonction Masquée de Transition)
```yaml
# config.yaml - Configuration editing team (NOT exposed in CLI)
editing_team:
  # Paramètre masqué pour transition - pas d'auto-fallback
  implementation: "agents_sdk"  # ou "assistant_api" - YAML config only
  
  # Paramètres visibles (configuration métier)
  max_revisions: 2  # Paramètre visible dans config métier
  poll_interval_secs: 1.0
  expires_after_days: 1
  
  # Agents SDK specific config
  agents_sdk:
    use_async: true
    context_management: true
    
  # Assistant API specific config  
  assistant_api:
    model: "gpt-4o-mini"
    project_id: "proj_UWuOPp9MOKrOCtZABSCTY4Um"
```

```python
# Utilisation avec config YAML
def load_editing_team_from_config(config_path: str) -> EditingTeamWorkflow:
    """Chargement depuis config YAML - pas de fallback automatique"""
    with open(config_path) as f:
        config = yaml.safe_load(f)
    
    implementation = config['editing_team']['implementation']
    team_config = config['editing_team']
    
    try:
        return EditingTeamFactory.create(
            implementation=implementation,
            **team_config
        )
    except Exception as e:
        # PAS de fallback - arrêt si échec selon config
        logger.error(f"Failed to create EditingTeam with {implementation}: {e}")
        raise RuntimeError(f"EditingTeam creation failed for {implementation}. Check configuration.") from e

# Usage
editing_team = load_editing_team_from_config("../config.yaml")
```

### Étape 5: Integration et Tests

#### 5.1 Tests Configuration-Based (Pas de Tests A/B Automatiques)
- Test d'une implémentation selon config YAML
- Validation fonctionnelle pour implementation configurée
- Métriques de performance spécifiques à l'implementation active
- **Pas d'exécution parallèle automatique** - choix via configuration

#### 5.2 Backward Compatibility
- Fonction legacy `edit_chapters()` maintenue
- Interface publique inchangée
- Pas de breaking changes

#### 5.3 Compliance Validation
- Aucun usage de `client.beta.assistants.*`
- Aucun usage de `client.beta.threads.*`
- Utilisation exclusive de Agents SDK pour nouvelle implémentation

## Critères d'Acceptation

### Fonctionnels
- [ ] Les deux implémentations produisent des résultats équivalents
- [ ] Workflow multi-agent (Documentalist → Writer → Reviewer → Strategist) préservé
- [ ] FileSearch functionality maintenue avec vector stores
- [ ] Cleanup automatique des ressources OpenAI
- [ ] Fonction legacy `edit_chapters()` compatible

### Techniques  
- [ ] Factory pattern implémenté et fonctionnel
- [ ] Interface commune respectée par les deux implémentations
- [ ] Code commun factorisé dans BaseEditingTeam (~60%)
- [ ] Tests unitaires et d'intégration passants
- [ ] Aucune violation des règles CLAUDE.md

### Qualité
- [ ] Documentation complète des nouvelles classes
- [ ] Gestion d'erreurs robuste
- [ ] Logging approprié pour debugging
- [ ] Performance acceptable (pas de régression significative)

## Risques et Mitigation

### Risques Techniques
- **State Management Complexity**: Context management manuel avec `result.to_input_list()`
  - *Mitigation*: Tests extensifs, logging détaillé, validation avec exemples OpenAI
- **API Maturity**: Agents SDK relativement nouveau
  - *Mitigation*: Validation avec exemples OpenAI, tests robustes
- **Configuration Errors**: Échec selon implementation choisie dans YAML
  - *Mitigation*: Validation config au démarrage, messages d'erreur clairs

### Risques Opérationnels  
- **Breaking Changes**: Risque de casser l'existant
  - *Mitigation*: Factory pattern permet coexistence, tests non-régression
- **Performance Impact**: Overhead possible avec orchestration manuelle
  - *Mitigation*: Benchmarking, optimisation si nécessaire

## Timeline et Dépendances

### Dépendances
- Installation `openai-agents` SDK
- Validation environnement de développement
- Tests avec clés API OpenAI valides

### Checkpoints
1. **Checkpoint 1**: Interface et classes abstraites créées
2. **Checkpoint 2**: AssistantAPIEditingTeam refactorisé et validé
3. **Checkpoint 3**: AgentsSDKEditingTeam implémenté
4. **Checkpoint 4**: Factory et tests d'intégration
5. **Checkpoint 5**: Documentation et compliance validation

## Post-Migration

### Transition Path (Fonction Masquée)
- Maintenir Assistant API version comme option YAML (fonction masquée)
- Configuration par défaut basculée vers Agents SDK dans YAML
- **Pas d'exposition CLI** du choix d'implémentation - configuration interne uniquement
- Documentation interne pour équipe de développement

### Monitoring
- Métriques d'usage des deux implémentations
- Monitoring erreurs et performance
- Feedback utilisateur pour validation qualité

---

**Statut**: Spécification approuvée
**Version**: 1.0
**Date**: 2025-06-25