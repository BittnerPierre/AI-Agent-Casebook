# Claude Code Instructions

## PR Reviews
When reviewing PRs, always include the Claude Code signature at the end of review comments:

```
> Generated with [Claude Code](https://claude.ai/code)

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
   cd src && poetry run python run.py --config ../config.yaml
   ```
4. **Import Validation** - Test that existing functionality works
   ```bash
   poetry run python -c "from key_modules import *; print(' Imports work')"
   ```
5. **Smoke Tests** - Basic end-to-end validation
6. **Only then create PR**

### Code Quality Standards
- Follow existing code conventions in the project
- Check for lint/typecheck commands and run them after changes
- Never assume library availability - always verify imports exist in codebase
- Test backward compatibility - existing code must continue working
- Integration testing is NOT optional - it's mandatory

### Professional Documentation Standards
- Use proper project-specific paths and commands (e.g., `poetry run`, correct test directories)
- Maintain professional tone without informal signatures or personal touches
- Ensure consistency with existing project structure and conventions
- Verify all commands and paths work in the actual project environment
- Follow established formatting and style guidelines

### AI Developer Accountability
- No "tunnel vision" - think holistically about system impact
- No "it works on my machine" - verify in actual application context
- No shortcuts on testing - quality is non-negotiable
- Document any breaking changes or migration requirements

**Violation of testing standards is unacceptable in production development.**