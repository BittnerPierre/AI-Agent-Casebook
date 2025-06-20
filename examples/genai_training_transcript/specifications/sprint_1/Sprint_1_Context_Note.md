# Sprint 1 Planning Context: Operational Content Creation Workflow

## Important: This is NOT a Greenfield Project

**We are NOT starting from scratch.** You will find:
- **Existing codebase** with training_manager preprocessing and knowledge bridge foundations
- **Previous sprint work** and specifications in the repository  
- **GitHub issues** with detailed technical discussions and architecture decisions
- **Working components** that need integration and refactoring, not rewriting

**Your focus:** Complete the gaps between existing components to create the first **working content creation workflow**.

## Business Context & Vision

### What We're Building
We're developing an **Agentic Content Production Platform** for automated content authoring. While our current focus is a **training course transcript generator**, we're architecting a **generic content authoring system** that can eventually support multiple formats (videos, podcasts, research reports, documentation).

**Sprint 1 Goal**: Deliver the first operational workflow where **3 core components work together** - Knowledge Management, Content Creation, and Evaluation - processing a real syllabus into a complete training transcript.

### Architecture Reference
See **"C4 - Architecture - Component.png"** for the complete system architecture showing:
- Knowledge Management components (Training Manager, Knowledge Bridge, MCP Interface)
- Authoring Content components (Research Team, Editing Team, Editorial Finalizer) 
- Production & Optimization components (Evaluation, LangSmith integration)

### Technical References  
See **"References.md"** for comprehensive technical references including:
- Multi-agent research patterns (Anthropic, OpenAI)
- Plan-and-Execute methodologies (LangGraph, ReWOO paper)
- Hierarchical agent coordination patterns
- Industry examples and code samples that inform our architecture

### Existing Implementation References
**CRITICAL**: Study these existing implementations before starting:
- **`app/video_script/`** - Working LangGraph multi-agent pipeline with narrative signature, guidelines integration, and quality control patterns
- **`tests/`** - Comprehensive LangSmith evaluation patterns, dataset creation, and API integration examples
- **`storytelling_guidebook.md`** and **`script_guidelines.md`** in video_script - Examples of narrative signature implementation

### Business Value
- **Content Creators** can generate consistent, knowledge-grounded training content from syllabi
- **Quality Managers** get automated evaluation and misconduct tracking
- **System** demonstrates multi-agent coordination with real knowledge integration

### Success Criteria for Sprint 1
After this sprint, a content creator should be able to:
1. Run `transcript-generator --syllabus example.md` 
2. Get a complete training transcript with evaluation metrics
3. See evidence of knowledge integration from existing training materials
4. Have quality issues tracked and logged for improvement

## Technical Context & Current State

### What Currently Exists ✅
- **Training Manager**: Preprocessing pipeline that extracts metadata from training transcripts
- **Knowledge Bridge**: File-based interface to access processed training content
- **Agent SDK Integration**: Framework for creating and running AI agents with tracing
- **CLI Infrastructure**: Basic command-line structure and configuration
- **MCP Framework**: Model Context Protocol setup (mostly using local fallbacks)

### What Needs Implementation ❌
- **Research Team**: Multi-agent system to query knowledge and produce research notes
- **Editing Team**: Content synthesis using Response API file_search feature
- **Editorial Finalizer**: Quality control and misconduct detection
- **Evaluation System**: RAG Triad metrics and LangSmith logging
- **Workflow Orchestrator**: Component coordination and error handling

### Architecture Overview (Reference C4 Diagram)
The platform follows a **3-module architecture**:

1. **Knowledge Management**: Training Manager + Knowledge Bridge + MCP Interface
2. **Content Creation**: Research Team + Editing Team + Editorial Finalizer  
3. **Evaluation**: LangSmith logging + RAG evaluation + Quality metrics

**Key Innovation**: Research Team uses MCP protocol to access knowledge, Editing Team uses Response API file_search on research notes for content synthesis.

## Sprint 1 User Stories Breakdown

### P0: Foundation Dependencies (Week 1)
*These must be completed first as other components depend on them*

#### US-001: Knowledge Database MCP Interface (Claude Code)
**Context**: Research agents need structured access to training content via MCP protocol, not local file access.

**Technical Details**:
- Create `knowledge_bridge/mcp_interface.py` with `KnowledgeMCPServer` class
- Implement `lookup_content(keywords: List[str]) -> List[ContentMatch]`
- Implement `read_content(content_id: str) -> ContentData` 
- Use proper MCP schemas for data exchange
- Connect to existing training_manager processed content

**Questions for PO/SM**:
- What should ContentMatch schema include? (title, summary, tags, content_id?)
- How should keyword matching work? (exact, fuzzy, semantic?)
- Should we support filtering by course/module?

#### US-002: Operational Training Manager Content Access (Claude Code)
**Context**: The MCP interface needs a programmatic way to access training_manager's processed content.

**Technical Details**:
- Create `training_manager/content_accessor.py` with `ContentAccessor` class
- Implement `get_by_keywords(keywords: List[str]) -> List[ContentItem]`
- Implement `get_content(content_id: str) -> str`
- Build searchable index from existing processed training files
- Ensure thread-safe access for concurrent queries

**Questions for PO/SM**:
- Should we cache search results? For how long?
- What's the expected query volume (concurrent users)?
- How should we handle large content files (>10MB)?

#### US-003: Research Team Knowledge Integration (Codex)
**Context**: Replace current research_team.py stub with actual multi-agent system that queries knowledge and produces structured output.

**Technical Details**:
- Create `ResearchTeam` class with `research_topic(syllabus_section) -> ResearchNotes`
- Use `KnowledgeMCPServer.lookup_content()` for knowledge queries
- Output structured `research_notes.json` with knowledge references
- Include 3 internal agents: Researcher (finds content), Analyst (evaluates relevance), Synthesizer (structures notes)
- Store results in `research_notes/` directory for editing team consumption
- Implement robust error handling for MCP queries and file I/O to allow partial results on failure
- Perform semantic key-point extraction (e.g. using NLP or LLM-driven summarization) rather than fixed word-chunking
- Generate a coherent `research_summary` that avoids repetition and structures insights as a narrative
- Expose parameters (e.g. `max_key_points_per_item`, `max_summary_length`) via configuration for tuning extraction and summarization

**Questions for PO/SM**:
- What structure should research_notes.json have?
- How many knowledge sources should we aim to include per syllabus section?
- Should we prioritize recent content over older content?

### P1: Core Workflow Components (Week 2)
*Main content generation pipeline*

#### US-004: Response API Content Synthesis (Codex)
**Context**: This is the key innovation - using Response API file_search on research notes for content generation.

**Technical Details**:
- Update `EditingTeam` class with `synthesize_chapter(research_notes) -> ChapterDraft`
- Use Response API file_search feature on `research_notes/` directory
- Coordinate Writer, Reviewer, Script Strategist agents
- Output to `chapter_drafts/` with structured content
- Implement agent-to-agent feedback loops within editing team

**Questions for PO/SM**:
- What Response API file_search parameters should we use?
- How should agents communicate within the editing team?
- What's the expected chapter length/structure?

#### US-005: Editorial Finalizer Misconduct Tracking (Cursor)
**Context**: Quality control system that detects when agents don't follow guidelines or produce poor content.

**Technical Details**:
- Create `EditorialFinalizer` class with `finalize_content()`, `track_issues()` methods
- Detect misconduct: off-topic content, guideline violations, factual errors
- Output `final_transcript.md` + `quality_issues.json`
- Implement severity levels: INFO, WARNING, ERROR, CRITICAL
- Track patterns for evaluation system

**Questions for PO/SM**:
- What constitutes "misconduct" vs acceptable creative deviation?
- Should we auto-reject content or just flag issues?
- How should we handle borderline cases?

#### US-006: Component Integration Orchestrator (Claude Code)
**Context**: Main pipeline coordinator that manages the Research → Editing → Finalizer workflow.

**Technical Details**:
- Create `WorkflowOrchestrator` class with `execute_pipeline(syllabus) -> TranscriptResult`
- Handle component lifecycle and data flow
- Implement error handling and recovery
- Manage temporary directories and cleanup
- Provide progress tracking and logging

**Questions for PO/SM**:
- How should we handle partial failures? (retry, skip, abort?)
- What timeout limits should we set for each component?
- Should we support resuming interrupted workflows?

### P2: Evaluation & Enhancement (Week 3)
*Quality measurement and logging infrastructure*

#### US-007: LangSmith Evaluation Logging (Cursor)
**Context**: All agent conversations and quality data must be logged to LangSmith for post-execution analysis.

**Technical Details**:
- Create `EvaluationLogger` class with `log_workflow()`, `collect_metrics()` methods
- Capture agent conversations, decisions, and quality_issues.json
- Tag with execution metadata (timestamp, version, configuration)
- Provide clean interface hiding LangSmith API complexity

**Questions for PO/SM**:
- What LangSmith project/dataset should we use?
- How long should we retain conversation logs?
- What metadata is most important for analysis?

#### US-008: RAG Triad Knowledge Evaluation (Cursor)
**Context**: Measure quality of knowledge integration using RAG Triad metrics (Context relevance, Answer relevance, Grounding).

**Technical Details**:
- Create `RAGEvaluator` class with `evaluate_knowledge_usage() -> RAGMetrics`
- Implement LLM-as-judge for each RAG Triad component
- Evaluate each knowledge query from Research Team
- Store metrics alongside conversation logs
- Generate summary reports per execution

**Questions for PO/SM**:
- What LLM should we use for evaluation? (GPT-4, Claude?)
- What's the threshold for "good" vs "poor" RAG scores?
- Should we weight the three RAG components equally?

### P3: Integration & Testing (Week 4)
*End-to-end validation and CLI completion*

#### US-009: End-to-End CLI Integration (All developers)
**Context**: Single command that demonstrates complete workflow from syllabus to finished transcript.

**Technical Details**:
- Create `cli/transcript_generator_cli.py` with proper argument parsing
- Integrate `WorkflowOrchestrator` as main pipeline
- Handle configuration, logging, output formatting
- Support common CLI patterns (help, verbose, config file)

**Questions for PO/SM**:
- What CLI arguments do we need beyond --syllabus?
- Should we support different output formats? (markdown, PDF, JSON?)
- How should we display progress to users?

#### US-010: Example Syllabus Validation (All developers)
**Context**: Proof that the system works with real data - the example syllabus must process successfully.

**Technical Details**:
- Create `tests/integration_test.py` with end-to-end test suite
- Validate example syllabus produces complete transcript
- Check all evaluation metrics are generated
- Verify quality issues are detected and logged
- Measure performance benchmarks

**Questions for PO/SM**:
- What constitutes "success" for the example syllabus?
- Should we have performance requirements? (time, quality scores?)
- How should we handle test data management?

## Performance & Quality Requirements

### Performance Benchmarks
- **Max 2 iterations per chapter** during editing process
- **Max 2 iterations for final revision** during editorial finalization  
- **Processing time target**: <15 minutes for 1-hour training content
- **Concurrent processing**: Support 3-5 simultaneous workflows

### Quality Measurements
- **Tone & Style**: LLM-as-judge evaluation
- **RAG Triad**: Context relevance, Answer relevance, Grounding scores
- **Final Result**: Overall quality assessment with breakdown
- **Misconduct Detection**: Automated flagging of guideline violations

## Technical Constraints & Assumptions

### Technology Stack
- **Agent Framework**: OpenAI Agents SDK (version 0.0.17)
- **Protocol**: Model Context Protocol (MCP) for knowledge access
- **Response API**: File_search feature for content synthesis
- **Logging**: LangSmith for conversation and evaluation data
- **Configuration**: YAML-based configuration files
- **CLI**: Poetry-managed Python package with entry points

### Development Constraints  
- **No dynamic planning**: Use static execution plans (no replanning mid-workflow)
- **Local development**: All components must work without external service dependencies
- **Existing codebase**: Build on training_manager foundation, don't rewrite
- **Agent SDK patterns**: Follow OpenAI Agents SDK conventions for consistency

## Critical Missing Components Identified

### 1. Training Course Narrative Signature - BLOCKS CONTENT QUALITY
**Problem**: No narrative signature system for training courses (unlike video_script which has comprehensive guidelines)  
**Impact**: Content will lack pedagogical structure, consistent voice, and educational effectiveness  
**Solution**: NEW US-000 creates training course guidelines with few-shot prompting examples

### 2. Response API File_Search Integration - BLOCKS US-004
**Problem**: No existing patterns for Response API file_search usage in codebase  
**Impact**: Editing Team implementation will lack concrete reference patterns  
**Solution**: NEW US-011 creates working example of Response API file_search with research notes

### 3. Automatic LangSmith Post-Execution Integration - BLOCKS EVALUATION
**Problem**: Current LangSmith usage is evaluation/testing only, no automatic execution metadata sending  
**Impact**: Quality monitoring and improvement loops won't work automatically  
**Solution**: NEW US-012 creates automatic trace collection and metadata sending during execution

## Integration Points & Dependencies

### Week 1 Integration Test
Knowledge Bridge → Research Team integration verified with sample knowledge queries

### Week 2 Integration Test  
Research Team → Editing Team → Editorial Finalizer pipeline produces complete chapter

### Week 3 Integration Test
Full workflow with evaluation logging captures all agent conversations and metrics

### Week 4 Integration Test
CLI command processes example syllabus and produces final transcript with all evaluation data

## Updated User Stories Summary

**Added Critical Missing User Stories:**
- **US-000**: Training Course Narrative Signature (P0, All developers collaboration)
- **US-011**: Response API File_Search Integration Pattern (P1, Codex)
- **US-012**: LangSmith Post-Execution Metadata Integration (P2, Cursor)

**Total User Stories**: 13 (original 10 + 3 critical additions)
**Additional Effort**: ~5-7 developer days for missing foundational components

## Questions for Sprint Planning

### For Product Owner
1. What's the acceptable quality threshold for V1? (what scores mean "good enough"?)
2. How should we prioritize speed vs quality when they conflict?
3. What should happen when agents produce unacceptable content?
4. **NEW**: What pedagogical patterns should we include in training course guidelines? (learning objectives structure, knowledge progression, engagement techniques)
5. **NEW**: Should we mock narrative signature or implement basic version for V1?
6. **NEW**: What training course examples should we use for few-shot prompting?

### For Scrum Master
1. How should we handle cross-team dependencies? (Claude Code → Codex → Cursor)
2. What's our definition of done for integration tests?
3. How do we manage shared interfaces when teams work in parallel?
4. What's the escalation path for technical blockers?
5. **NEW**: How do we coordinate the collaborative US-000 (narrative signature) across all developers?
6. **NEW**: Should we front-load the missing foundational components or spread them across weeks?

### For Technical Lead
1. Should we use async/await patterns for agent coordination?
2. How should we handle MCP server failures or timeouts?
3. What's our error handling strategy across the pipeline?
4. How do we ensure thread safety for concurrent knowledge access?

## Success Metrics for Sprint Review

**Demo Ready**: CLI command successfully processes example syllabus  
**Quality Assured**: All evaluation metrics collected and logged  
**Integration Verified**: All components communicate via defined interfaces  
**Performance Met**: Processing completes within time/iteration limits  
**Code Quality**: All modules pass integration tests and code review

This sprint delivers the foundation for adaptive, high-quality content generation while establishing patterns for future sprint iterations.