#!/usr/bin/env bash
# Production Start Script for Ajiputra-Project MovieBox API
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

if [ -d "venv" ]; then
    source venv/bin/activate
fi

export PORT="${PORT:-8000}"
echo "Starting Ajiputra-Project MovieBox API on port $PORT..."
exec python main.py
