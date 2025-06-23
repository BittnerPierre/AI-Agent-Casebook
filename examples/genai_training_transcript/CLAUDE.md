# Claude Code Instructions

## PR Reviews

When reviewing PRs, always include the Claude Code signature at the end of review comments:

```
> Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

## GitHub Contributions

Tag all Claude-generated contributions (PRs, issues, comments) with the 'claude' label for easy search and tracking.

## Git Operations

When merging PRs, use `--squash` flag by default: `gh pr merge <number> --squash`

## Development Standards (MANDATORY)

### Testing Protocol - NO EXCEPTIONS

Every feature implementation MUST follow this sequence:

1. **Implement Feature** - Write the code
2. **Unit Tests** - Comprehensive test coverage
   ```bash
   poetry run pytest tests/ -v
   ```
3. **Integration Tests** - CRITICAL: Verify app still works
   ```bash
   cd src && python run.py --config ../config.yaml
   ```
4. **Import Validation** - Test that existing functionality works
   ```bash
   poetry run python -c "from key_modules import *; print('✅ Imports work')"
   ```
5. **Smoke Tests** - Basic end-to-end validation
6. **Only then create PR**

### Code Quality Standards

- Follow existing code conventions in the project
- Check for lint/typecheck commands and run them after changes
- Never assume library availability - always verify imports exist in codebase
- Test backward compatibility - existing code must continue working
- Integration testing is NOT optional - it's mandatory

### Architecture Compliance (MANDATORY)

**API Governance - NO EXCEPTIONS**

Prohibited APIs (ZERO TOLERANCE):
- OpenAI Assistant API (`client.beta.assistants.*`)
- OpenAI Threads API (`client.beta.threads.*`)
- Any legacy OpenAI APIs not explicitly approved

Required APIs for Agentic Workflows:
- OpenAI Agents SDK (`agents.Agent`, `agents.Runner`)
- FileSearchTool (`agents.FileSearchTool`) for file search functionality
- Approved vector store APIs (`client.vector_stores.*`)

**Architecture Review Checklist**:
- [ ] Uses only approved APIs (Agents SDK for agentic workflows)
- [ ] No Assistant API calls (`client.beta.assistants`)
- [ ] No Thread API calls (`client.beta.threads`)
- [ ] File search uses `FileSearchTool` class
- [ ] Vector store management follows approved patterns
- [ ] Integration tests validate architectural compliance

**Enforcement**: CI/CD will automatically reject PRs containing prohibited API usage.

### AI Developer Accountability

- No "tunnel vision" - think holistically about system impact
- No "it works on my machine" - verify in actual application context
- No shortcuts on testing - quality is non-negotiable
- Document any breaking changes or migration requirements
- **Architecture compliance is mandatory** - verify API usage aligns with standards

**Violation of testing standards OR architecture compliance is unacceptable in production development.**
