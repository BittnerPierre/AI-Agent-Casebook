# MCP Evernote Server Setup (Future Enhancement)

This document describes the setup for MCP Evernote server integration, which is planned for future implementation.

## Prerequisites

- [Node.js](https://nodejs.org/) and [npx](https://www.npmjs.com/package/npx)
- Valid Evernote developer token
- MCP servers repository

## Installation

1. Clone the MCP servers repository and install dependencies:

```bash
git clone https://github.com/modelcontextprotocol/servers.git
cd servers/src/filesystem
npm install
```

2. Set the environment variable `EVERNOTE_TOKEN` to a valid Evernote developer token:

```bash
export EVERNOTE_TOKEN="your_evernote_developer_token_here"
```

## Starting the Evernote MCP Server

Start the Evernote plugin:

```bash
npm run start -- --plugin evernote --token "$EVERNOTE_TOKEN"
```

## Integration with Training Manager

To use Evernote as a knowledge source, specify the Evernote endpoint when running the training manager:

```bash
poetry run python run_training_manager.py \
  --course-path <path/to/data/training_courses/<course_id> - <course_name>> \
  --mcp-endpoint evernote:// \
  [--overwrite]
```

## Configuration

- `--mcp-endpoint evernote://`: Specifies to use the Evernote MCP server
- `EVERNOTE_TOKEN`: Environment variable containing your Evernote developer token

## Status

**Note**: This integration is planned for future implementation and is not currently available in the main codebase.

## Related Files

- `mcp-evernote-js-poc/`: JavaScript proof-of-concept implementation
- `mcp-evernote-ts/`: TypeScript implementation with tests
- `run_mcp_evernote.sh`: Shell script for running Evernote MCP server