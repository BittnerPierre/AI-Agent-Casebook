# Remaining Questions for PBI - Sprint 1 Resolution

## Outstanding Questions Requiring PBI Input

Based on team reviews from Codex and Cursor, the following questions need PBI clarification before Sprint 1 can proceed:

### 1. **RAG Evaluation Thresholds** *(High Priority)*
**Context:** Cursor implementing US-008 (RAG Triad - Context Relevance) needs quantitative guidance
**Question:** What are acceptable threshold scores for Context Relevance evaluation?
- Minimum acceptable score (e.g., 0.7/1.0)?
- Score ranges for quality categories (excellent/good/poor)?
- Should thresholds be configurable or hard-coded?

**Impact:** Without thresholds, evaluation system cannot determine pass/fail for content quality

### 2. **Prompt Templates for Content Synthesis** *(Medium Priority)*
**Context:** Codex implementing US-004 (Response API Content Synthesis) needs consistency guidance
**Question:** Are there preferred prompt templates or guidelines for chapter synthesis?
- Standard prompt structure for educational content?
- Required sections/format for training chapters?
- Specific tone/style requirements beyond the narrative signature?

**Impact:** May result in inconsistent content format across different modules

### 3. **JSON Schema File Format** *(Low Priority)*
**Context:** Codex asking about schema implementation approach
**Question:** Should data schemas be in separate JSON schema files vs inline documentation?
- Create `schemas/` directory with `.json` files?
- Keep schemas in `Inter_Module_Architecture.md` as documentation?
- Use both approaches (files for validation, docs for reference)?

**Impact:** Minor - affects code organization but not functionality

## Proposed Default Decisions (If No PBI Input)

If PBI input is not available, we recommend proceeding with these defaults:

### RAG Evaluation Thresholds:
- **Minimum Context Relevance:** 0.6/1.0 (configurable)
- **Quality Categories:** 
  - Excellent: 0.8-1.0
  - Good: 0.6-0.79
  - Poor: <0.6
- **Implementation:** Configurable thresholds in evaluation config

### Prompt Templates:
- **Use Response API example patterns** from US-011 implementation
- **Follow narrative signature guidelines** from US-000
- **Standard educational structure:** Introduction → Concepts → Examples → Exercises → Summary

### Schema Format:
- **Keep schemas in documentation** for Sprint 1 simplicity
- **Add JSON validation** in future sprints if needed
- **Use TypedDict** for Python type hints (already implemented)

## Sprint 1 Readiness Decision

**Recommendation:** 🟢 **Proceed with Sprint 1 using proposed defaults**

**Rationale:**
1. **Core architecture resolved** - Both teams understand the technical approach
2. **Major blockers addressed** - Interface alignment and example code completed
3. **Remaining questions are refinements** - Not Sprint 1 blockers
4. **Defaults are reasonable** - Can be adjusted based on Sprint 1 results

## Next Steps

1. **Immediate:** Proceed with Sprint 1 using proposed defaults
2. **Week 1:** Test defaults during implementation and gather feedback
3. **Week 2:** Adjust thresholds/templates based on initial results
4. **Future sprints:** Refine based on PBI feedback and Sprint 1 learnings

**Sprint 1 can start immediately** - Outstanding questions are optimization concerns, not implementation blockers.

---

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>