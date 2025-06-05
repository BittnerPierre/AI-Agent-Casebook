# Evernote MCP Integration Specification

This document preserves the Evernote MCP integration details for future development when the Evernote application key becomes available.

## Current Status

**⚠️ DEVELOPMENT FROZEN** - Waiting for Evernote application key from Evernote support.

The Evernote MCP server implementation is incomplete and non-operational. The project currently works only with the MCP filesystem server.

## Planned Evernote Integration

### MCP Evernote Server Implementation

The project includes two Evernote MCP implementations:

#### TypeScript Implementation (Primary)
- **Location**: `mcp-evernote-ts/`
- **Status**: Development frozen
- **Dependencies**: Requires valid Evernote developer token

#### JavaScript Proof-of-Concept
- **Location**: `mcp-evernote-js-poc/`
- **Status**: Proof-of-concept only

### Environment Setup (When Available)

```bash
# Set Evernote developer token
export EVERNOTE_TOKEN=your_token_here
```

### Starting the Evernote MCP Server (When Available)

```bash
# Option 1: Direct npm start
cd mcp-evernote-ts
npm install
npm start

# Option 2: Shell script
bash run_mcp_evernote.sh
```

### Training Manager Usage with Evernote (When Available)

```bash
# Basic usage with Evernote endpoint
poetry run run_training_manager --course-path "data/training_courses/<course_id> - <course_name>" --mcp-endpoint evernote://

# With overwrite option
poetry run run_training_manager --course-path "data/training_courses/<course_id> - <course_name>" --mcp-endpoint evernote:// --overwrite
```

### Usage Parameters (When Available)

- **`--mcp-endpoint evernote://`**: Use Evernote MCP server for note storage
- **Environment**: Requires `EVERNOTE_TOKEN` to be set
- **Functionality**: Store cleaned transcripts and metadata as Evernote notes

### Testing Evernote Implementation (When Available)

```bash
# Test TypeScript implementation
cd mcp-evernote-ts
npm test
```

## Integration Benefits (Planned)

1. **Note Management**: Store processed transcripts as organized Evernote notes
2. **Cross-Platform Access**: Access training materials from any Evernote client
3. **Search Capabilities**: Leverage Evernote's search functionality
4. **Collaboration**: Share training notes and materials easily
5. **Backup**: Automatic cloud backup of processed content

## Technical Requirements (When Resuming Development)

1. **Evernote Developer Account**: Valid application key from Evernote
2. **Authentication**: Proper OAuth flow implementation
3. **API Integration**: Complete Evernote API client implementation
4. **Error Handling**: Robust error handling for API failures
5. **Rate Limiting**: Respect Evernote API rate limits

## Files Related to Evernote Integration

```
mcp-evernote-ts/              # Primary TypeScript implementation
├── src/index.ts              # Main server implementation
├── package.json              # Dependencies and scripts
├── jest.config.js            # Test configuration
└── tests/index.test.ts       # Test suite

mcp-evernote-js-poc/          # JavaScript proof-of-concept
├── index.js                  # POC implementation
└── package.json              # Dependencies

run_mcp_evernote.sh           # Launch script for Evernote server
```

## Resume Development Checklist

When Evernote application key becomes available:

- [ ] Obtain valid Evernote developer token
- [ ] Complete MCP Evernote server implementation
- [ ] Implement proper authentication flow
- [ ] Add comprehensive error handling
- [ ] Complete test suite
- [ ] Update README.md with Evernote instructions
- [ ] Update training manager to support Evernote endpoints
- [ ] Test end-to-end integration
- [ ] Document Evernote-specific features

## Contact Information

For Evernote application key status, contact Evernote Developer Support regarding the pending application.