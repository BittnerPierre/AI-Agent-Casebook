# Consolidated Sprint 1 Questions for Decision

## Critical Questions Requiring Your Input

### 1. Data Schemas ✅ RESOLVED

**✅ COMPLETE:** Full schema definitions created in `Inter_Module_Architecture.md`

**Schemas defined:**
- SyllabusInput, KnowledgeQuery/Response  
- ResearchNotes, ChapterDraft, QualityIssues
- FinalTranscript, EvaluationMetadata
- MCP operations specification

**✅ Editorial Finalizer Misconduct Categories DEFINED:**
- **Critical:** Content ↔ Syllabus alignment, Inadequate level
- **High:** Duration violations, Groundedness, Training course principles
- **Medium:** Content repetition without new angle

### 2. LangSmith Configuration ✅ RESOLVED

**✅ CONFIRMED:**
- New LangSmith project: "story-ops"
- Naming convention: kebab-case
- Platform: Free tier with dataset download capability
- Integration: Agent SDK built-in tracing (no custom API client)

### 3. Response API Configuration ✅ RESOLVED

**✅ CONFIRMED:**
- Environment variable: `OPENAI_API_KEY`
- Project ID: `proj_UWuOPp9MOKrOCtZABSCTY4Um`
- Requirements: Fully functional end-to-end implementation
- Location: `examples/genai_training_transcript/examples/response_api_file_search_example.py`

### 4. Timeline Adjustments ✅ RESOLVED

**✅ DECISIONS:**
- US-012 moved to Week 2 (added to sprint_1.md)
- US-008 simplified to Context Relevance only for Sprint 1
- Created US-013 (Answer Relevance) and US-014 (Grounding) for Sprint 2
- Updated weekly priorities with integration testing milestones

### 5. Quality Standards for Sprint 1 ✅ RESOLVED

**✅ ACCEPTANCE CRITERIA:**
1. Agenda/Research notes aligned with syllabus + knowledge base + educational structure
2. Training course transcript respects agenda/research notes
3. Agent execution logged in LangSmith + evaluation metadata generated
4. End-to-end processing of "AI Engineer Basic Course Syllabus"

**✅ TEST CASES:**
- Week 1: API/schema validation tests
- Week 2: Simple syllabus generation test  
- Week 3: Full "AI Engineer Basic Course Syllabus" processing

## Scope Clarifications

### Items to DROP (too vague/long-term per your instruction):

**From Issue 38:**
- ❌ "Observability and monitoring strategy" - too broad for Sprint 1
- ❌ "Scalability and concurrent processing" - explicitly single workflow
- ❌ "Advanced debugging tools" - Sprint 2 concern

**From Issue 39:**  
- ❌ "Event-driven architecture alternatives" - over-engineering for Sprint 1
- ❌ "Microservices approach" - against single workflow decision
- ❌ "Advanced workflow orchestration tools" - LangGraph is sufficient

**From Issue 43:**
- ❌ "Complex recovery patterns and circuit breakers" - simplified fallback decided
- ❌ "Dashboard and web interface" - CLI only for Sprint 1
- ❌ "Advanced caching and optimization" - stateless components decided

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

## Recommended Decisions

Based on architecture discussion and codebase analysis:

1. **Accept simplified scope** - MVP over complete features
2. **MCP file operations** - ALL data access via MCP (research_notes/, chapter_drafts/, quality_issues.json)
3. **Agent SDK coordination** - Simple multi-agent orchestration (not LangGraph)
4. **Simple error handling** - MCP retry logic and graceful degradation
5. **Clean API separation** - MCP-first design for Evernote migration readiness

## Next Steps

1. **Your decisions on schemas and timeline adjustments**
2. **Create GitHub milestone for confirmed Sprint 1 scope**  
3. **Start Week 1 implementation with confirmed decisions**

---

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>