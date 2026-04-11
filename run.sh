#!/bin/sh
# Helper: load GHOST_HOST and GHOST_ADMIN_API_KEY and run ghost_publish.py
# Searches for .env in order: ~/.hermes/.env, $SCRIPT_DIR/../.env
# Usage: ./run.sh [ghost_publish.py args...]
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

_load_env() {
  if [ -f "$1" ]; then
    GHOST_HOST=$(grep '^GHOST_HOST=' "$1" | head -1 | cut -d= -f2-)
    GHOST_ADMIN_API_KEY=$(grep '^GHOST_ADMIN_API_KEY=' "$1" | head -1 | cut -d= -f2-)
    export GHOST_HOST GHOST_ADMIN_API_KEY
    return 0
  fi
  return 1
}

_load_env "$HOME/.hermes/.env" || _load_env "$SCRIPT_DIR/../.env"

exec "$SCRIPT_DIR/.venv/bin/python" "$SCRIPT_DIR/scripts/ghost_publish.py" "$@"
