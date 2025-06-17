# Consolidated Sprint 1 Questions for Decision

## Critical Questions Requiring Your Input

### 1. Data Schemas (RESOLVED - See Inter_Module_Architecture.md)

**✅ COMPLETE:** Full schema definitions created in `Inter_Module_Architecture.md`

**Schemas defined:**
- SyllabusInput, KnowledgeQuery/Response  
- ResearchNotes, ChapterDraft, QualityIssues
- FinalTranscript, EvaluationMetadata
- MCP operations specification

**Remaining question:** What specific "misconduct" categories should Editorial Finalizer detect?
- Suggested: `content_accuracy`, `pedagogical_structure`, `narrative_consistency`, `length_violation`, `missing_elements`

**PBI Answer:** The misconducts are:

- [Critical] Content --> Syllabus content is not respected in the generated Training Courses. (Example: Modules are missing, Covered topic that is not in the module description, Details that is explictly listed in syllabus is missing...) 
- [High] Duration --> Training courses generated does not cope with the timing (exemple: 1 day (8 hours) training course in syllabus vs 2 - 3 days materials provided)
- [Critical] Inadequate level. Training course material is too difficult or too simple.
- [High] Groundness: The content is not generated based on the Knowlegde Base given in the Syllabus (Source Transcript).
- [High] Tone, Style and Structure: the content does not respect "Training" Course principles for content creation.
- [Medium] Repetition over training course: a topic should not be adressed twice if not for a new angle or deep dive.

### 2. LangSmith Configuration (Week 1-2)

**Questions:**
- Should we create a new LangSmith project for transcript_generator or use existing?
- What project/dataset naming convention do you prefer?
- Any specific retention or cost management requirements?

**PBI Answer:** 
- Yes, yes a new project in LangSmish: "story-ops".
- Let's use "kebab-case" for naming convention within langsmith
- No, we use free langsmith. We should be able to download dataset for integration test.


### 3. Response API Configuration (Week 2)

**Questions:**
- Which OpenAI account/API key configuration should be used?
- Any specific file_search parameters or indices to target?
- Should the example be fully functional or just demonstration code?

**PBI Answer:** 
- OPENAI_API_KEY is define in environment variable.
- I've created a project "story-ops" with ID "proj_UWuOPp9MOKrOCtZABSCTY4Um"
- It should be fully functional end to end. Less or simpler feature if needed but we should be able to generate a training course based on syllabus with Knowledge Retrieval (throught Knowledge bridge MCP) and Evaluation in Langsmith.

### 4. Timeline Adjustments (DECISION NEEDED)

**Cursor's concern about Week 3 overload (4 user stories):**
- Should US-012 (simpler) move to Week 2?
- Should US-008 RAG Triad be simplified to Context Relevance only for Sprint 1?
- Accept the scope reduction suggestions from issues?

**PBI Answer:**
- US-012 is not in the Sprint_1.md file. Should be added. Yes if it make sense, move it into Week 2.
- Ok but when Groundness and Response relevance will be added ?
- it is for US-008 ? Reduce scope of US-008 but create other topic for Groundness and Response relance.

### 5. Quality Standards for Sprint 1

**Questions:**
- What constitutes "acceptable quality" for Sprint 1 deliverables? 
- Should we prioritize working end-to-end over polished components?
- How much error handling vs MVP functionality?

**PBI Answer:**
- 1) Detailed Agenda and Research Note are aligned with syllabus and use content from Knowledge base and structure of a education content (progression, exercice). 2) Training course transcript respect agenda and research note. 3) Run execution of agents are Logged in Langsmith and metadata created with evaluation performed.

## Scope Clarifications

### Items to DROP (too vague/long-term per your instruction):

**From Issue 38:**
- ❌ "Observability and monitoring strategy" - too broad for Sprint 1
- ❌ "Scalability and concurrent processing" - explicitly single workflow
- ❌ "Advanced debugging tools" - Sprint 2 concern

**PBI Answer:**
- "Observability and monitoring strategy" - Accepted but a work (Task) to be done to make a detailed specification (discussed with PBI, make a draft and use References.md for study).
- "Scalability and concurrent processing" - Agreed, not in scope
- "Advanced debugging tools" - Agreed, not in scope

**From Issue 39:**  
- ❌ "Event-driven architecture alternatives" - over-engineering for Sprint 1
- ❌ "Microservices approach" - against single workflow decision
- ❌ "Advanced workflow orchestration tools" - LangGraph is sufficient

**PBI Answer:**
- "Event-driven architecture alternatives" - Confirm, overkill
- "Microservices approach" - Confirm, overkill
- "Advanced workflow orchestration tools" - We use "Agents SDK" only for now. Alternative may be considered when serious limitation is identify. Agentic framework should be no "System" dependant. For example "Swarm" or "handoff" approach could be use for intra-system collaboration (ex: ResearchTeam <-> EditingTeam <-> Finalizer) but between system MCP should be use to cross boundaries (Knowlegde Management <-> Content Authoring <-> Evaluation & Optimization). Access to Data (filesystem, evernote, ...) should also use MCP.

**From Issue 43:**
- ❌ "Complex recovery patterns and circuit breakers" - simplified fallback decided
- ❌ "Dashboard and web interface" - CLI only for Sprint 1
- ❌ "Advanced caching and optimization" - stateless components decided

**PBI Answer:**
- "Complex recovery patterns and circuit breakers": confirm for the simplfied fallback (iteration count), a flag is available to start generation process from scratch (for example clean research note).

### Items to FOCUS ON (Sprint 1 specific):

**Week 1 Priorities:**
1. ✅ Data schemas definition (above)
2. ✅ Narrative signature guidelines creation
3. ✅ Component interface contracts

**Week 2 Priorities:**  
1. ✅ Response API file_search example
2. ✅ MCP file operations for research_notes/, chapter_drafts/
3. ✅ LangSmith logging setup

**Week 3-4 Priorities:**
1. ✅ Component integration testing
2. ✅ End-to-end workflow validation
3. ✅ Documentation and examples

**PBI Answer:**
- Week 1 priorities: should include a first end-to-end integration test to validate API and schema. 
- Week 2 priorities: should include a first end-to-end generation for integration testing on a simple syllabus
- Week 3 priorities: pipeline should fully work on the "AI Engineer Basic Course Syllabus" syllabus. 
- Comment: missing priorities on operational "Knowledge Bridge", operational "content creation" workflow and Log and Evaluation available in LangSmith (passive mode) fed with quality control feedback (see above for misconduct.

## Recommended Decisions

Based on architecture discussion and codebase analysis:

1. **Accept simplified scope** - MVP over complete features
2. **MCP file operations** - ALL data access via MCP (research_notes/, chapter_drafts/, quality_issues.json)
3. **Agent SDK coordination** - Simple multi-agent orchestration (not LangGraph)
4. **Simple error handling** - MCP retry logic and graceful degradation
5. **Clean API separation** - MCP-first design for Evernote migration readiness

**PBI Comment**:
On 3: no planner, no task executor

## Next Steps

1. **Your decisions on schemas and timeline adjustments**
2. **Create GitHub milestone for confirmed Sprint 1 scope**  
3. **Start Week 1 implementation with confirmed decisions**

---

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>