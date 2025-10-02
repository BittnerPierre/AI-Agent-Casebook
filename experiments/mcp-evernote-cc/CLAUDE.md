# Claude Code Instructions - Evernote MCP Chatbot

## API Feasibility Analysis (CRITICAL)
**BEFORE implementing any feature, MUST verify feasibility within available APIs**

### Evernote MCP Server Constraints
- **API Reference**: https://dev.evernote.com/doc/reference/
- **MCP Server**: https://github.com/brentmid/evernote-mcp-server
- **Available MCP Functions ONLY**:
  - `createSearch`: Search notes using natural language queries
  - `getSearch`: Retrieve cached search results
  - `getNote`: Get detailed metadata for a specific note
  - `getNoteContent`: Retrieve full note content in text, HTML, or ENML format

**Key Constraint**: The MCP server does NOT expose `getNotebook()` function, so notebook GUIDs cannot be resolved to readable names. Any feature requiring notebook name resolution is impossible without extending the MCP server itself.

### Mandatory Pre-Implementation Checklist
1. **API Inventory**: List all required API calls for the feature
2. **Availability Check**: Verify each API call exists in MCP server
3. **Feasibility Assessment**: Can the feature be implemented with available APIs?
4. **Scope Limitation**: If not fully feasible, define what's possible vs impossible
5. **Document Constraints**: Clearly state API limitations in code comments

**Rule**: Never implement complex workarounds for missing APIs. Accept limitations and focus on what's achievable with available tools.

## Development Standards

### Testing Protocol
- Run `poetry run pytest tests/ -v` after changes
- Test interactive CLI: `poetry run evernote-chat`
- Test search CLI: `poetry run evernote-search "query"`

### Code Quality
- Follow existing patterns in the codebase
- Keep progress indicators clean and user-friendly
- Suppress technical debug output from MCP server
- Maintain clean separation between MCP client, handlers, and UI components

## Git Operations
When committing changes, use descriptive messages with:
```
🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```