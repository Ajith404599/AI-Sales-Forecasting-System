#!/usr/bin/env bash
# Single command launcher for Backend + Frontend in Bash / macOS / Linux
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

if [ -f "$DIR/.venv/bin/python" ]; then
    PYTHON_EXE="$DIR/.venv/bin/python"
else
    PYTHON_EXE="python3"
fi

exec "$PYTHON_EXE" "$DIR/run.py" "$@"
