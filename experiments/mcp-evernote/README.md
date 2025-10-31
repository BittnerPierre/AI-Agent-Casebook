# Evernote MCP Chat Experiment

Simple command-line chat that uses the OpenAI Agents SDK to talk with the local `evernote-mcp-server`. The assistant issues MCP tool calls (createSearch, getSearch, getNote, getNoteContent) to answer questions like “Summarize all my Evernotes regarding LLMs,” without relying on any vector store.

## Prerequisites
- `evernote-mcp-server` installed locally (see [brentmid/evernote-mcp-server](https://github.com/brentmid/evernote-mcp-server) for setup instructions)
- Evernote developer token or OAuth credentials configured as expected by the server (e.g. `EVERNOTE_PERSONAL_TOKEN`, `EVERNOTE_PERSONAL_SECRET`, or saved profile)
- Docker (or another runtime) running the Evernote MCP server and exposing `https://localhost:3443/mcp`
- This repository dependencies installed (`poetry install`)
- (Optional) `uv` or another launcher if you plan to run the server locally via stdio

## Running the chat
With the Evernote MCP server running in Docker and exposed on `https://localhost:3443/mcp`, launch the chat from the repository root:
```bash
poetry run python experiments/mcp-evernote/chat.py
```

The CLI connects over Streamable HTTP to `https://localhost:3443/mcp`, matching the Docker setup. No SSE or stdio transports are supported.

Additional useful switches:
- `--model gpt-4.1` (or any Agents SDK compatible model)
- `--notebook Research --notebook Meetings` to bias searches
- `--max-notes 10` to limit how many notes the agent should review
- `--prefer-html` to let the agent request HTML content when summarizing rich notes
- `--show-tools` to print the tool call log after each turn

Type `exit` or press `Ctrl+D` to stop the chat.

## Basic smoke tests
Once your Evernote MCP server is reachable, try the following prompts:
- `Search my Evernote for notes about project planning`
- `Find my most recent meeting notes in Evernote`
- `Show me all Evernote notes tagged with 'important'`
- `Summarize all my Evernote notes about LLMs`

The assistant should report which notes it inspected, cite relevant metadata (titles, timestamps, tags), and explain when no matches are found or additional criteria are needed.

## Notes
- The assistant never uses embeddings or external vector stores—only the Evernote MCP tools.
- The chat reuses conversation history in-memory, so multi-turn refinement works within a single run.
- If the CLI fails with “Failed to launch Evernote MCP server,” verify the executable path and that your Evernote credentials are present in the environment.
