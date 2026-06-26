#!/bin/bash
# Self-contained launcher for Sancho ACP Mobile client.
# This script sets up the virtual environment, installs dependencies, and runs the client.

set -e

# Ensure we operate in the script's directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Initialize virtual environment if missing
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment (.venv)..."
    python3 -m venv .venv
fi

# Activate the virtual environment
source .venv/bin/activate

# Install/verify dependencies
echo "Verifying dependencies..."
pip install -r requirements.txt --quiet

# Launch Sancho Mobile app, forwarding all arguments
echo "Launching Sancho ACP Mobile..."
python3 -m sancho_mobile "$@"
