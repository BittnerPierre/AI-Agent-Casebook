# Team Coordination: 3-Agent Collaboration Framework

## Team Composition

### Current Agents
- **Claude Code (moi)** - Code review, testing, GitHub coordination, LLM evaluation
- **Codex** - Code generation, implementation, following AGENTS.md guidelines
- **Cursor Agent** - Architecture analysis, planning, system design

## Current Collaboration Patterns

### Established Workflows
1. **Spec-First Policy**: All features must be documented in `specifications/plan_*.md` before implementation
2. **PR Review Process**: Cross-agent review before merging to main
3. **GitHub Coordination**: Issues, PRs, and project tracking via GitHub CLI
4. **Testing Standards**: Comprehensive unit and integration testing required

### Role Boundaries (Current)
- **Codex**: Generates code, follows specifications, creates implementations
- **Claude Code**: Reviews code, creates tests, manages GitHub workflows, evaluates LLM performance
- **Cursor Agent**: Analyzes architecture, identifies improvements, strategic planning

## Evolution Towards Feature-Based Collaboration

### Proposed Transition
Based on Issue #28 discussion, moving from module-based to feature-based collaboration:

#### Current Model (Module-Based)
- Each agent owns specific modules
- Sequential handoffs between agents
- Risk of silos and bottlenecks

#### Target Model (Feature-Based)
- Agents collaborate on complete features
- Any agent can pick up next sprint item
- Collective sprint planning and review

### Open Questions for Team Discussion

#### Architecture & Design (Issue #28)
1. **Adaptive Planner Structure**: How to implement truly adaptive planning that revises objectives mid-course?
2. **Execution Plan Caching**: Strategy for template-based plans per content type (video, training, podcasts)?
3. **Interface Management**: Clean boundaries between planning, execution, and evaluation phases?

#### Technical Implementation
1. **LLM Strategy**: Selection/fallback approach for different models per task?
2. **Quality Measurement**: Automated content quality evaluation metrics?
3. **Timeout Management**: Preventing infinite revision loops while maintaining quality?

#### Collaboration Process
1. **Sprint Organization**: Concrete process for collegial sprint planning?
2. **Review Workflow**: Cross-agent PR review process and conflict resolution?
3. **Decision Making**: Who arbitrates technical disagreements?

## Immediate Coordination Needs

### Current Project State
- **PR #20, #21, #22**: Ready for final review and merge post-revisions
- **PR #25**: Awaiting review for broken import fixes
- **Architecture Issues**: Import path inconsistencies identified by Cursor Agent

### Proposed Next Steps
1. **Address Cursor Agent's findings** from Issue #27 (import paths, JSON schema)
2. **Define feature-based sprint process** based on Issue #28 vision
3. **Implement adaptive planning architecture** for content generation

## Communication Protocols

### GitHub Integration
- **Issue Creation**: Use `gh issue create` for bug reports and feature discussions
- **PR Reviews**: All agents review before merge, identify as agent in comments
- **Agent Identification**: Always sign contributions to distinguish agents
- **Example signature**: `---\n*Created by Claude Code*`

### Decision Making
- **Technical Disputes**: Use GitHub issues for transparent discussion
- **Specification Changes**: Require consensus before implementation
- **Architecture Decisions**: Document rationale in specifications

## Future Evolution

### Vision Alignment (Issue #28)
Working towards **Adaptive Content Generation Platform**:
- Multi-format support (videos, training, podcasts, reports)
- Intelligent planning with dynamic adaptation
- Continuous improvement via feedback loops
- Quality/time balance with automatic timeouts

### Role Evolution Possibilities
As discussed in Issue #28, potential specializations:
- **Codex**: GenAI workflows and advanced generation
- **Claude Code**: MCP knowledge base and evaluation systems  
- **Cursor Agent**: Architecture and intelligent planning

## Action Items

### Immediate (Next Sprint)
1. **Cursor Agent**: Define JSON schema and naming conventions (Issue #27)
2. **Claude Code**: Address import path harmonization
3. **Codex**: Review and merge ready PRs
4. **All Agents**: Contribute architecture suggestions to Issue #28

### Medium Term
1. **Implement feature-based sprint process**
2. **Design adaptive planner architecture**
3. **Create content quality evaluation framework**

---

*Living document - Updated as team collaboration evolves*
*Last updated by Claude Code*