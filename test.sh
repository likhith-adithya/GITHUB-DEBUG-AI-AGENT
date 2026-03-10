#!/bin/bash

# Automatically set up and use the project's virtual environment for testing

# Ensure we are in the project root
cd "$(dirname "$0")"

if ! command -v uv &> /dev/null; then
    echo "uv could not be found. Please install it first."
    exit 1
fi

export UV_CACHE_DIR=/tmp/uv-cache
export UV_LINK_MODE=copy
export UV_PROJECT_ENVIRONMENT=.uv-314-env

echo "Syncing project environment with uv..."
uv sync

# Set PYTHONPATH so 'src' module can be found
export PYTHONPATH=$(pwd)

echo "Running tests in the virtual environment..."
echo "----------------------------------------"

# Run pytest using uv inside the tests directory to avoid root permission errors
cd tests/ && uv run pytest -v .
