#!/bin/bash
# Quick start script for Claude RL Agent

set -e

AGENT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC_DIR="$AGENT_DIR/src"

cd "$SRC_DIR"

# Show banner (unless running status/engine commands)
if [[ "$1" != "status" && "$1" != "engine" ]]; then
    echo "=================================================="
    echo " Claude Behavioral Replication Agent"
    echo "=================================================="
    echo ""
fi

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3.11+"
    exit 1
fi

# Run agent
python3 agent.py "$@"
