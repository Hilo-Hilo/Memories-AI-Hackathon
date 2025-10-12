#!/bin/bash
# Focus Guardian Launcher Script
# Makes it easy to start the application

# Navigate to project directory
cd "$(dirname "$0")"

# Add UV to PATH
export PATH="$HOME/.local/bin:$PATH"

# Activate virtual environment
source .venv/bin/activate

# Launch Focus Guardian
echo "Starting Focus Guardian..."
python -m focus_guardian.main

# Note: Press Ctrl+C to stop the application

