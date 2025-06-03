# MCP Evernote JS POC

This POC demonstrates OAuth 2.0 PKCE authentication with Evernote and simple note read/write using the Evernote JavaScript SDK (Node.js).

For OAuth authentication, see the Evernote OAuth guide:
https://dev.evernote.com/doc/articles/authentication.php

## Prerequisites
- Node.js >=12
- A registered Evernote OAuth 2.0 application with a client ID and configured redirect URI (see https://dev.evernote.com/doc/articles/authentication.php)

## Setup
```bash
cd examples/genai_training_transcript/mcp-evernote-js-poc
npm install
```

## Usage
Set your Evernote OAuth2 client ID and (optional) redirect URI in the environment:
```bash
export EVERNOTE_CLIENT_ID=<your_client_id>
# Optional. Defaults to out-of-band redirect URI.
export EVERNOTE_REDIRECT_URI=<your_redirect_uri>
```

Then run the POC script:
```bash
npm start
```

The script will:
1. Generate a code verifier and code challenge (PKCE)
2. Prompt you to visit the authorization URL and grant access
3. Prompt for the OAuth2 authorization code
4. Exchange the code for an access token
5. Create a new note titled "POC Test Note - TIMESTAMP" in your default notebook
6. Retrieve and print the content of the created note