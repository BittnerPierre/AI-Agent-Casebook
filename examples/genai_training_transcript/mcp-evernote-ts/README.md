# MCP Evernote Plugin (TypeScript)

This folder contains the TypeScript implementation of the MCP Filesystem plugin for Evernote, adapted from the core filesystem plugin.

## Setup

```bash
cd mcp-evernote-ts
npm install
```

## Authentication

Evernote requires either a developer token or OAuth credentials to access the API.

### Developer Token

For development and testing, generate a developer token on the Evernote developer site:

https://dev.evernote.com/doc/articles/dev_tokens.php

Pass the token using the `--token` flag. To use the Evernote sandbox environment, include the optional `--sandbox` flag.

### OAuth

For production use with full OAuth authentication, follow the OAuth flow described in the Evernote documentation:

https://dev.evernote.com/doc/articles/authentication.php

## Build and Run

```bash
npm run build
npm start -- --plugin evernote --token "$EVERNOTE_TOKEN" [--sandbox]
```

## Tests

```bash
npm test
```