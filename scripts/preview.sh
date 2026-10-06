#!/usr/bin/env bash
# Serve the invitation from the repository root.
set -euo pipefail
cd "$(dirname "$0")/.."
port="${1:-8000}"
exec python3 -m http.server "$port"
