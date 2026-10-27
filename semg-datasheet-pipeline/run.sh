#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
exec python3 "$SCRIPT_DIR/doc_pipeline.py" --manifest "$SCRIPT_DIR/documents.json" --root "$REPO_ROOT" "$@"
