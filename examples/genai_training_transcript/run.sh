#!/usr/bin/env bash
set -euo pipefail

# Change to script directory
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

# Launch the Training Course Manager (Sprint 0)
poetry run python run_training_manager.py \
  --course-path "data/training_courses/CHROMA - Chroma Course" \
  --mcp-endpoint stdio:// \
  "$@"