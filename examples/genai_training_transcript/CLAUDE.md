# Claude Code Instructions

## PR Reviews
When reviewing PRs, always include the Claude Code signature at the end of review comments:

```
🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

## GitHub Contributions
Tag all Claude-generated contributions (PRs, issues, comments) with the 'claude' label for easy search and tracking.

## Git Operations
When merging PRs, use `--squash` flag by default: `gh pr merge <number> --squash`

## Testing
Run tests before making changes: `poetry run pytest -q`

## Code Standards
- Follow existing code conventions in the project
- Check for lint/typecheck commands and run them after changes
- Never assume library availability - always verify imports exist in codebase