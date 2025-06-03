# Sprint 1 (POC v0): Evernote OAuth 2.0 PKCE Integration (On Hold)

**Goal:** Proof-of-concept for Evernote integration via OAuth 2.0 PKCE, enabling basic read/write operations against an Evernote account without using a client secret.

**Note:** This sprint is currently on hold pending receipt of `EVERNOTE_CLIENT_ID` from Evernote support.

**Refer to** `plan_mcp_evernote.md` (sections “Itération 1” and “Itération 2”) for the full MCP Evernote integration plan.

## Acceptance Criteria
- A Node.js POC script (`index.js` in `mcp-evernote-js-poc/`) implements the OAuth 2.0 PKCE flow (code verifier/challenge), requests an authorization code, and exchanges it for an access token using Evernote’s `/oauth2/token` endpoint.
- The POC script can successfully create a new note in Evernote with a sample ENML body.
- The POC script can read back and display the content of the newly created note.
- Environment variables `EVERNOTE_CLIENT_ID` and (optional) `EVERNOTE_REDIRECT_URI` are used, with out-of-band fallback if no redirect URI is specified.
- The `README.md` in `mcp-evernote-js-poc/` documents setup steps, required variables, and commands to run the POC.

## Tasks
- [ ] Finalize POC script in `examples/genai_training_transcript/mcp-evernote-js-poc/index.js`.
- [ ] Implement PKCE utilities for generating `code_verifier` and `code_challenge`.
- [ ] Add CLI prompt to input the OAuth authorization code.
- [ ] Exchange authorization code for an access token and handle token storage or display.
- [ ] Implement Evernote read/write test calls: `createNote()` and `getNoteContent()`.
- [ ] Update `README.md` with clear instructions and mark this sprint as on hold until credentials are available.