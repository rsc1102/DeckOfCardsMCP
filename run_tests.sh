#!/usr/bin/env bash
# A simple script to run tests with uv + pytest

set -e  # Exit immediately on error

echo "Running tests with uv + pytest..."
uv run python -m pytest tests/
