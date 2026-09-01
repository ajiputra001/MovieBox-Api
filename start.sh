#!/usr/bin/env bash
# Production Start Script for Ajiputra-Project MovieBox API
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

PYTHON_BIN="python3"
if command -v python &> /dev/null; then
    PYTHON_BIN="python"
fi

if [ -d "venv" ]; then
    source venv/bin/activate
    PYTHON_BIN="python"
fi

export PORT="${PORT:-8000}"
export WORKERS="${WORKERS:-1}"
echo "Starting Ajiputra-Project MovieBox API on port $PORT with $WORKERS workers..."
exec $PYTHON_BIN main.py

