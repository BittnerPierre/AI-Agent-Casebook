#!/usr/bin/env bash
# Exit on error
set -euo pipefail

# Run unit tests for the Training Course Manager (scoped to this directory)
cd "$(dirname "${BASH_SOURCE[0]}")"
poetry run python run.py