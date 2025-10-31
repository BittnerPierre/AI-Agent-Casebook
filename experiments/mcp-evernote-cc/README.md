# Evernote AI Chatbot

An intelligent terminal chatbot powered by OpenAI Agents SDK that connects to a Docker-hosted Evernote MCP server to search, query, and interact with your Evernote notes using natural language.

## Features

- **🤖 AI-Powered Agent**: Uses OpenAI Agents SDK to intelligently interpret natural language queries
- **🔌 MCP Integration**: Connects to Evernote MCP server via Docker stdio for reliable communication
- **🗒️ Evernote Tools**: Full access to `createSearch`, `getSearch`, `getNote`, and `getNoteContent` MCP tools
- **💬 Conversational Interface**: Natural language interaction with contextual conversation memory
- **📝 Session Management**: Maintains conversation history across sessions
- **🎨 Rich Formatting**: Beautiful terminal output with markdown support
- **🔧 Extensible Architecture**: Easy to add additional agents for summarization, analysis, and more

## Installation

```bash
cd experiments/mcp-evernote-cc
poetry install
```

## Prerequisites

1. **Docker**: Ensure Docker is installed and running
2. **Evernote MCP Server**: Have the Evernote MCP server running in a Docker container
3. **OpenAI API Key**: Set `OPENAI_API_KEY` in your environment or `.env` file

## Usage

### Interactive Chat

```bash
# Start the AI-powered chatbot
poetry run evernote-chat
```

### Example Queries

The AI agent understands natural language queries such as:

- "Find all my notes about machine learning"
- "Show me notes I created last month about project planning"
- "What did I write about LLMs?"
- "Search for notes tagged with 'quarterly-review' and summarize them"

## Configuration

Configuration can be provided via command-line flags or environment variables:

- `OPENAI_API_KEY`: Your OpenAI API key (required)
- `CONTAINER_NAME`: Docker container name for Evernote MCP server (default: `evernote-mcp-server-evernote-mcp-server-1`)
- `ALLOWED_NOTEBOOKS`: Comma-separated list of allowed notebooks
- `MAX_NOTES_PER_QUERY`: Maximum notes to retrieve per query
- `PREFER_HTML`: Whether to prefer HTML content over text
- `SAVE_HISTORY`: Enable conversation history persistence (default: `true`)
- `HISTORY_FILE`: Path to conversation history file

## Architecture

The chatbot uses a modern AI agent architecture:

```
User Query → AI Agent (OpenAI Agents SDK) → MCP Client → Docker MCP Server → Evernote API
                                                ↓
                                        Intelligent Query Planning
                                        Tool Selection & Execution
                                        Natural Language Response
```

The AI agent:
1. Interprets your natural language query
2. Plans which Evernote MCP tools to use
3. Executes searches and retrieves notes
4. Formats and presents results conversationally

## Extending with Additional Agents

The architecture supports adding specialized agents for:
- **Summarization**: Automatic note summarization
- **Analysis**: Content analysis and insights
- **Organization**: Smart tagging and categorization
- **Export**: Custom export formats and reports

See `src/evernote_chatbot/agents.py` for implementation details.