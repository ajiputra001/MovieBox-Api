#!/usr/bin/env bash
# Production Start Script for Ajiputra-Project MovieBox API
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

if [ -d "venv" ]; then
    source venv/bin/activate
fi

export PORT="${PORT:-8000}"
export WORKERS="${WORKERS:-4}"
echo "Starting Ajiputra-Project MovieBox API on port $PORT with $WORKERS workers..."
exec python main.py

