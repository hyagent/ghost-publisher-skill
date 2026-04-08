#!/bin/sh
# Helper: load GHOST_HOST and GHOST_ADMIN_API_KEY from ../.env and run ghost_publish.py
# Usage: ./ghost-publisher/run.sh [ghost_publish.py args...]
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ENV_FILE="$SCRIPT_DIR/../.env"

if [ -f "$ENV_FILE" ]; then
  GHOST_HOST=$(grep '^GHOST_HOST=' "$ENV_FILE" | head -1 | cut -d= -f2-)
  GHOST_ADMIN_API_KEY=$(grep '^GHOST_ADMIN_API_KEY=' "$ENV_FILE" | head -1 | cut -d= -f2-)
  export GHOST_HOST GHOST_ADMIN_API_KEY
fi

exec "$SCRIPT_DIR/.venv/bin/python" "$SCRIPT_DIR/scripts/ghost_publish.py" "$@"
