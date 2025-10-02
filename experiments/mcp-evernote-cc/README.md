# Evernote Chatbot

A terminal chatbot that connects to a Docker-hosted Evernote MCP server over Streamable HTTP to query and summarize Evernote notes.

## Features

- **Streamable HTTP only**: Connects to MCP server via HTTPS at `https://localhost:3443/mcp`
- **Evernote Tool Integration**: Uses `createSearch`, `getSearch`, `getNote`, and `getNoteContent` tools
- **Rich Response Formatting**: Summaries include note titles, timestamps, and tags
- **Session Memory**: Maintains conversation history for contextual follow-up questions
- **Flexible Configuration**: Customizable MCP URL, HTTP headers, notebook restrictions, and more

## Installation

```bash
cd experiments/mcp-evernote-cc
poetry install
```

## Usage

### Simple Search (Recommended)

```bash
# Basic search
poetry run evernote-search "your search query"

# Search with content preview
poetry run evernote-search "LLM agents" --content

# Limit number of results
poetry run evernote-search "project planning" --limit 5

# Combine options
poetry run evernote-search "meeting notes" --content --limit 3
```

### Interactive Chat (experimental)

```bash
# Start interactive chatbot
poetry run evernote-chat
```

## Configuration

Configuration can be provided via command-line flags or environment variables:

- `MCP_URL`: MCP server endpoint (default: `https://localhost:3443/mcp`)
- `MCP_HEADERS`: Custom HTTP headers as JSON
- `ALLOWED_NOTEBOOKS`: Comma-separated list of allowed notebooks
- `MAX_NOTES_PER_QUERY`: Maximum notes to retrieve per query
- `PREFER_HTML`: Whether to prefer HTML content over text

## Example Queries

- "Summarize all my Evernotes regarding LLMs"
- "Find notes about project planning from last month"
- "Show me meeting notes tagged with 'quarterly-review'"