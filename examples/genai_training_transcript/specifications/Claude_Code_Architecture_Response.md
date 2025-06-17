# Response to Cursor: Sprint 1 Architecture Decisions

## Architecture Review Answers (Claude Code)

### 1. ContentMatch/ContentData Schemas
**Status:** Do not exist yet in current `knowledge_bridge.py`

**Decision:** Will define minimal schemas for Sprint 1:
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

### 2. Concurrent Access Strategy
**Decision:** Single workflow execution only
- **Authoring Content domain is READ-ONLY** during content creation phases
- No database changes during research/authoring phases  
- Knowledge database remains static during Sprint 1 workflow execution
- No concurrent access controls needed for Sprint 1

### 3. Orchestrator Resilience
**Decision:** Use LangGraph max_iterations pattern, no timeouts for Sprint 1
- Following existing `app/video_script/assistant.py` pattern (lines 327-332)
- Use `remaining_steps` and `min_remaining_step` configuration
- No timeout values needed - LangGraph handles execution flow control
- Retry policies only for specific exceptions (see video_script lines 418-422)

## US-000 Narrative Signature Strategy

**Decision:** Implement basic version, not mock

**Rationale:**
- US-000 is P0 dependency blocking all content generation  
- Existing patterns available in `app/video_script/storytelling_guidebook.md` and `script_guidelines.md`
- Training courses need pedagogical-specific narrative (different from video scripts)

**Implementation Plan:**
Create `transcript_generator/guidelines/training_course_guidelines.md` with:

### Pedagogical Patterns to Include:
1. **Learning Scaffolding:** Progressive complexity building
2. **Active Learning:** Interactive questions, exercises, practical examples  
3. **Knowledge Anchoring:** Prerequisites, learning outcomes, key takeaways
4. **Engagement Patterns:** Educational hooks, concept reinforcement

### Structure Template:
```markdown
# Training Course Narrative Guidelines

## Course Structure Pattern
- Learning objectives introduction
- Prerequisite knowledge check  
- Concept introduction with examples
- Practice/application sections
- Summary and next steps

## Pedagogical Voice
- Instructional tone (guide, not entertain)
- Scaffolded explanations
- Frequent knowledge checks
- Practical application focus
```

This provides Week 1 deliverable enabling Codex's content generation while establishing educational narrative signature for training transcripts.

**Next Steps:**
1. Examine existing `storytelling_guidebook.md` patterns  
2. Adapt for educational content requirements
3. Create few-shot examples for course chapter structure

---

**Status:** Architecture decisions confirmed for Sprint 1 implementation

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>