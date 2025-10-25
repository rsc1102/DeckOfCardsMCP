#!/usr/bin/env bash
# A simple script to run tests with uv + pytest

set -e  # Exit immediately on error

if [[ "$1" == "server" ]]; then
    echo "Starting the FastMCP server..."
    uv run python -m src.main
elif [[ "$1" == "tests" ]]; then
    echo "Running tests with uv + pytest..."
    uv run python -m pytest tests/
else
    echo "Invalid argument. Usage: $0 [server|tests]"
    exit 1
fi
