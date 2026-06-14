#!/bin/bash
set -e

# AI Code Debugger Agent - Runner Script
# Ensures environment is synced and starts the agent.

# Ensure we are in the project root
cd "$(dirname "$0")"

# Check for uv
if ! command -v uv &> /dev/null; then
    echo "Error: 'uv' not found. Please install it: https://astral.sh/uv"
    exit 1
fi

# Environment Configuration
export UV_CACHE_DIR="/tmp/uv-cache-$(whoami)"
export UV_LINK_MODE=copy
export UV_PROJECT_ENVIRONMENT=".venv"

echo "==> Syncing dependencies..."
uv sync --quiet

# Add current directory to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

echo "==> Starting AI Code Debugger Agent..."
echo "------------------------------------------------------------"

# Execute the agent
exec uv run python src/main.py "$@"
