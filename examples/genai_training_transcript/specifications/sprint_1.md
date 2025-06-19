# Sprint 1: Operational Content Creation Workflow

## Critical Gaps Analysis

**IMPLEMENTED:** Training Manager preprocessing, Knowledge Bridge, Agent SDK framework, CLI structure, MCP framework  
**STUBS NEEDING IMPLEMENTATION:** Research Team, Editing Team, Planner, Reviewer, Evaluation system  
**MISSING:** Multi-agent coordination, narrative signature for training courses, training course guidelines, automatic LangSmith post-execution metadata, Response API file_search patterns

## Restructured Sprint 1 User Stories with Dependencies & Module Interfaces

### P0: Foundation Dependencies (Week 1)

**US-000: Training Course Narrative Signature** *(All developers collaboration)*
- **Module:** `transcript_generator/guidelines/training_course_guidelines.md`
- **Interface:** Guidelines document + few-shot prompt templates
- **As a** Content Creator
- **I want** training course narrative signature with pedagogical guidelines and few-shot examples
- **So that** Editing Team produces educational content with consistent voice and structure
- **Acceptance:** Training course guidelines document + example prompts for course structure, learning objectives, engagement patterns
- **Integration Point:** Used by all content generation agents for consistent output
- **Reference:** Examine `app/video_script/` for narrative signature patterns (storytelling_guidebook.md, script_guidelines.md)

### P0: Foundation Dependencies (Week 1) - Core Infrastructure

**US-001: Knowledge Database MCP Interface** *(Claude Code)*
- **Module:** `knowledge_bridge/mcp_interface.py`
- **Interface:** `KnowledgeMCPServer` class
- **As a** Research Agent
- **I want** MCP interface with `lookup_content(keywords)`, `read_content(content_id)` operations
- **So that** I can access structured course content via MCP protocol
- **Acceptance:** MCP server exposes `lookup_content()`, `read_content()` methods with proper schemas
- **Integration Point:** Exports `KnowledgeMCPServer` for training_manager connection

**US-002: Operational Training Manager Content Access** *(Claude Code)*  
- **Module:** `training_manager/content_accessor.py`
- **Interface:** `ContentAccessor` class with `get_by_keywords()`, `get_content()` methods
- **As a** Knowledge Bridge
- **I want** training_manager to provide searchable, accessible processed content
- **So that** MCP interface can serve structured knowledge queries
- **Acceptance:** Training manager content indexed and accessible via ContentAccessor API
- **Integration Point:** ContentAccessor used by KnowledgeMCPServer

**US-003: Research Team Knowledge Integration** *(Codex)*
- **Module:** `transcript_generator/research_team.py` 
- **Interface:** `ResearchTeam` class with `research_topic(syllabus_section)` method
- **As a** Content Creator
- **I want** Research Team to query Knowledge Bridge and produce structured research notes
- **So that** editing has knowledge-grounded input for content creation
- **Acceptance:** ResearchTeam outputs `research_notes.json` with knowledge references and structured content
- **Integration Point:** Uses `KnowledgeMCPServer.lookup_content()`, outputs to `research_notes/` for editing team
- **Implementation Notes:** Include robust error handling, semantic key-point extraction, narrative synthesis, and configurable parameters for extraction/summarization

### P1: Core Workflow Components (Week 2)

**US-011: Response API File_Search Integration Pattern** *(Codex)*
- **Module:** `examples/response_api_file_search_example.py`
- **Interface:** Working example of Response API file_search usage
- **As a** Developer
- **I want** reference implementation of Response API file_search with research notes
- **So that** US-004 has concrete patterns to follow for content synthesis
- **Acceptance:** Working code example demonstrating file_search on structured research notes
- **Integration Point:** Pattern used by EditingTeam for research note synthesis

### P1: Core Workflow Components (Week 2) - Main Pipeline

**US-004: Response API Content Synthesis** *(Codex)*
- **Module:** `transcript_generator/editing_team.py`
- **Interface:** `EditingTeam` class with `synthesize_chapter(research_notes)` method  
- **As a** Content Creator
- **I want** Editing Team to use Response API file_search on research notes for chapter synthesis
- **So that** content generation leverages structured research effectively
- **Acceptance:** EditingTeam uses Response API file_search on research_notes/ and outputs draft chapters
- **Integration Point:** Consumes `research_notes/` from Research Team, outputs to `chapter_drafts/`

**US-005: Editorial Finalizer Misconduct Tracking** *(Cursor)*
- **Module:** `transcript_generator/editorial_finalizer.py`
- **Interface:** `EditorialFinalizer` class with `finalize_content(chapters)`, `track_issues()` methods
- **As a** Quality Manager
- **I want** Editorial Finalizer to detect and track agentic workflow misconduct
- **So that** final content quality is maintained and issues are logged for evaluation
- **Acceptance:** EditorialFinalizer outputs `final_transcript.md` + `quality_issues.json` with misconduct tracking
- **Integration Point:** Consumes `chapter_drafts/`, exports quality metadata for evaluation module

**US-006: Component Integration Orchestrator** *(Claude Code)*
- **Module:** `transcript_generator/workflow_orchestrator.py`
- **Interface:** `WorkflowOrchestrator` class with `execute_pipeline(syllabus)` method
- **As a** System Administrator  
- **I want** orchestrated execution of Research Team → Editing Team → Editorial Finalizer
- **So that** components interact seamlessly with proper error handling
- **Acceptance:** Single orchestrator manages component lifecycle and data flow
- **Integration Point:** Main pipeline entry point using all component interfaces

### P2: Evaluation & Enhancement (Week 3)

**US-012: LangSmith Post-Execution Metadata Integration** *(Cursor)*
- **Module:** `evaluation/langsmith_integration.py`
- **Interface:** `LangSmithIntegration` class with `send_execution_metadata()` method
- **As a** Quality Manager
- **I want** automatic sending of execution metadata to LangSmith after workflow completion
- **So that** I can analyze performance data without manual evaluation setup
- **Acceptance:** Workflow execution automatically sends traces, performance metrics, and quality data to LangSmith
- **Integration Point:** Used by WorkflowOrchestrator for automatic trace collection
- **Reference:** Examine `tests/` folder for existing LangSmith evaluation patterns

### P2: Evaluation & Enhancement (Week 3) - Quality Systems

**US-007: LangSmith Evaluation Logging** *(Cursor)*
- **Module:** `evaluation/langsmith_logger.py`
- **Interface:** `EvaluationLogger` class with `log_workflow()`, `collect_metrics()` methods
- **As a** Quality Manager
- **I want** agent conversations and quality metadata logged to LangSmith  
- **So that** I can perform post-execution evaluation and analysis
- **Acceptance:** All agent interactions + quality_issues.json logged with execution metadata
- **Integration Point:** Used by WorkflowOrchestrator and EditorialFinalizer

**US-008: RAG Triad Knowledge Evaluation** *(Cursor)*
- **Module:** `evaluation/rag_evaluator.py`
- **Interface:** `RAGEvaluator` class with `evaluate_knowledge_usage()` method
- **As a** Quality Manager
- **I want** RAG Triad evaluation (Context relevance only for Sprint 1) for knowledge queries
- **So that** I can measure knowledge integration quality
- **Acceptance:** Context relevance metrics calculated for each knowledge lookup with LLM-as-judge
- **Integration Point:** Consumes knowledge query logs from Research Team via EvaluationLogger
- **Sprint 1 Scope:** Context relevance only, Answer relevance and Grounding deferred to Sprint 2

**US-012: LangSmith Post-Execution Metadata Integration** *(Cursor)*
- **Module:** `evaluation/langsmith_integration.py`
- **Interface:** `LangSmithIntegration` class with `send_execution_metadata()` method
- **As a** Quality Manager
- **I want** automatic sending of execution metadata to LangSmith after workflow completion
- **So that** I can analyze performance data without manual evaluation setup
- **Acceptance:** Workflow execution automatically sends traces, performance metrics, and quality data to LangSmith
- **Integration Point:** Used by WorkflowOrchestrator for automatic trace collection
- **LangSmith Setup:** Project "story-ops", kebab-case naming, Agent SDK built-in tracing

**US-013: Answer Relevance RAG Evaluation** *(Future - Sprint 2)*
- **Module:** `evaluation/rag_evaluator.py` (extension)
- **As a** Quality Manager
- **I want** Answer relevance evaluation for generated content
- **So that** I can measure how well content answers the learning objectives
- **Dependencies:** US-008 completion

**US-014: Grounding RAG Evaluation** *(Future - Sprint 2)*
- **Module:** `evaluation/rag_evaluator.py` (extension)  
- **As a** Quality Manager
- **I want** Grounding evaluation to ensure content is based on source knowledge
- **So that** I can measure factual accuracy and source attribution
- **Dependencies:** US-008 completion

### P3: Integration & Testing (Week 4)

**US-009: End-to-End CLI Integration** *(All developers)*
- **Module:** `cli/transcript_generator_cli.py`
- **Interface:** CLI command `transcript-generator --syllabus <file>`
- **As a** Content Creator
- **I want** single CLI command orchestrating complete workflow
- **So that** I can test end-to-end syllabus → transcript generation
- **Acceptance:** CLI command produces final transcript with all evaluation metadata
- **Integration Point:** Uses WorkflowOrchestrator as main pipeline

**US-010: Example Syllabus Validation** *(All developers)*
- **Module:** `tests/integration_test.py`
- **Interface:** Test suite validating example syllabus processing
- **As a** Developer
- **I want** shared example syllabus to process successfully through entire pipeline  
- **So that** V1 demonstrates working end-to-end generation
- **Acceptance:** Example syllabus produces complete transcript with evaluation metrics
- **Integration Point:** End-to-end validation of all module interfaces

## Module Interface Dependencies

```
KnowledgeMCPServer ← ContentAccessor ← Training Manager
         ↓ (MCP)
ResearchTeam → (MCP: research_notes/) → EditingTeam → (MCP: chapter_drafts/) → EditorialFinalizer
         ↓ (MCP)                              ↓ (MCP)                              ↓ (MCP)
EvaluationLogger ← RAGEvaluator    EvaluationLogger           quality_issues.json
         ↓ (Agent SDK)
WorkflowOrchestrator → CLI
```

**Key Architecture Principles:**
- **Agent SDK:** Multi-agent coordination and communication
- **MCP Protocol:** ALL file and data access operations (research_notes/, chapter_drafts/, quality_issues.json)
- **Response API:** Content synthesis with file_search capabilities
- **Clean API Separation:** Prepares for MCP Evernote migration

## Developer Allocation & Integration Points

**Claude Code:** Knowledge infrastructure (US-001, US-002, US-006)  
**Codex:** Content generation workflow (US-003, US-004, US-011)  
**Cursor:** Evaluation and quality systems (US-005, US-007, US-008, US-012)  
**All:** Integration testing (US-009, US-010) + Narrative signature collaboration (US-000)

## Architecture Decisions (Claude Code Responses)

### ContentMatch/ContentData Schemas (US-001)
- **Status:** Not implemented yet in current knowledge_bridge.py
- **Sprint 1 Implementation:**
```python
class ContentMatch(TypedDict):
    content_id: str
    title: str  
    relevance_score: float
    preview: str

class ContentData(TypedDict):
    content_id: str
    full_content: str
    metadata: Dict[str, Any]
```

### Concurrent Access Strategy (US-002)
- **Decision:** Single workflow execution, READ-ONLY knowledge access
- **Rationale:** Authoring domain is read-only during content creation phases
- **Implementation:** No concurrent access controls needed for Sprint 1

### Orchestrator Resilience (US-006)  
- **Decision:** Simple Agent SDK coordination with basic retry logic
- **Implementation:** Agent SDK error handling patterns, no complex state management needed
- **Retry Strategy:** MCP operation retries and graceful degradation on failures

### US-000 Narrative Signature Strategy
- **Decision:** Implement basic version (not mock)
- **Deliverable:** `transcript_generator/guidelines/training_course_guidelines.md`
- **Pedagogical Patterns:** Learning scaffolding, active learning, knowledge anchoring, engagement patterns
- **Reference:** Adapt from existing `app/video_script/storytelling_guidebook.md` for educational content

### Editorial Finalizer Misconduct Categories  
**Critical Issues:**
- Content ↔ Syllabus alignment (missing modules, off-topic content, missing syllabus details)
- Inadequate level (content too difficult/simple for target audience)

**High Priority Issues:**
- Duration violations (generated content timing vs syllabus requirements)
- Groundedness violations (content not based on provided knowledge base)
- Training course principles violations (tone, style, structure)

**Medium Priority Issues:**
- Content repetition (topics addressed twice without new angle/deep dive)

### LangSmith Configuration
- **Project:** "story-ops" 
- **Naming Convention:** kebab-case
- **Platform:** Free tier with dataset download capability
- **Integration:** Agent SDK built-in tracing

### Response API Configuration
- **Environment:** `OPENAI_API_KEY` environment variable
- **Project ID:** `proj_UWuOPp9MOKrOCtZABSCTY4Um`
- **Requirements:** Fully functional end-to-end implementation

### Test Syllabus
- **Source:** `examples/genai_training_transcript/syllabus.md` - "AI Engineer Basic Course Syllabus"
- **Content Files:** Mock for Week 1-2, full content needed for final integration testing
- **Required Files:** Prompt_Engineering_for_Developers.txt, Advanced_Retrieval_for_AI.txt, Multi_AI_Agent_Systems.txt, Building_Systems_with_the_ChatGPT_API.txt

## Sub-iteration Integration Tests

- **Week 1 end:** Knowledge Bridge → Research Team integration + Training course guidelines established
- **Week 2 end:** Research Team → Editing Team → Editorial Finalizer pipeline + Response API patterns working  
- **Week 3 end:** Evaluation logging capturing complete workflow + Automatic LangSmith metadata sending
- **Week 4:** Full end-to-end validation with narrative signature

## Critical References for Developers

**Existing Patterns to Study:**
- **`app/video_script/`** - Working LangGraph multi-agent pipeline with narrative signature implementation
- **`tests/`** - LangSmith evaluation patterns and dataset management
- **`storytelling_guidebook.md`** and **`script_guidelines.md`** - Narrative signature examples in video_script

**New Integration Patterns Needed:**
- Training course pedagogical guidelines (different from video script guidelines)
- Response API file_search for research note synthesis
- Automatic LangSmith trace collection during execution (not just evaluation)

This structure eliminates blocking dependencies and provides clear interface contracts for parallel development.

## Detailed Architecture & Data Contracts

**📋 See `Inter_Module_Architecture.md` for:**
- Complete sequence diagram of inter-module interactions
- JSON schemas for all data exchange between business domains
- MCP operations specification for Knowledge_Management and File_Operations
- Clear separation of Business Domains: Knowledge_Management, Authoring_Content, Evaluation_Optimization

**Key Integration Points:**
- All file operations (research_notes/, chapter_drafts/, quality_issues.json) via MCP
- Knowledge queries via Knowledge_Bridge MCP interface  
- Agent SDK for intra-domain component coordination
- Clean API contracts for MCP Evernote migration readiness