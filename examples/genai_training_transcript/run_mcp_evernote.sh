#!/usr/bin/env bash
#
# Script to launch the MCP Evernote server.
# Requires EVERNOTE_TOKEN env variable set to a valid Evernote developer token.

set -euo pipefail

# Navigate to project directory
cd "$(dirname "${BASH_SOURCE[0]}")"

: "${EVERNOTE_TOKEN:?Environment variable EVERNOTE_TOKEN must be set}"

poetry run python tools/mcp_evernote.py "$@"