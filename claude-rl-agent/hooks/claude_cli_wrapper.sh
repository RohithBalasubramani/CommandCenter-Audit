#!/bin/bash
#
# Claude CLI Wrapper with Automatic Capture
#
# This wrapper intercepts all Claude Code CLI interactions and automatically
# logs them for training.
#
# Installation:
#   1. Add to ~/.bashrc or ~/.zshrc:
#      alias claude="/home/rohith/desktop/CommandCenter/claude-rl-agent/hooks/claude_cli_wrapper.sh"
#
#   2. Or symlink:
#      sudo ln -s /home/rohith/desktop/CommandCenter/claude-rl-agent/hooks/claude_cli_wrapper.sh /usr/local/bin/claude-rl
#
# Usage:
#   claude "your prompt here"  # Automatically captured!
#

set -e

# Paths
CAPTURE_DIR="/home/rohith/desktop/CommandCenter/claude-rl-agent/data/traces/raw"
LOG_DIR="/home/rohith/desktop/CommandCenter/claude-rl-agent/logs"
CLAUDE_BIN="/usr/local/bin/claude"  # Adjust to your Claude CLI location

# Create directories
mkdir -p "$CAPTURE_DIR" "$LOG_DIR"

# Generate session ID
SESSION_ID=$(date +%Y%m%d_%H%M%S)_$$
CAPTURE_FILE="$CAPTURE_DIR/${SESSION_ID}.jsonl"

# Log the command
echo "[$(date -Iseconds)] Claude CLI invoked with $# arguments" >> "$LOG_DIR/cli_wrapper.log"

# Capture the prompt
USER_PROMPT="$*"

# Record start time
START_TIME=$(date +%s)

# Run Claude and capture output
echo "🎯 Running Claude Code CLI (auto-capturing)..."
echo ""

# Create temporary file for output
TEMP_OUTPUT=$(mktemp)

# Run Claude, capturing both stdout and stderr
if "$CLAUDE_BIN" "$@" 2>&1 | tee "$TEMP_OUTPUT"; then
    CLAUDE_RESPONSE=$(cat "$TEMP_OUTPUT")
    SUCCESS=true
else
    CLAUDE_RESPONSE=$(cat "$TEMP_OUTPUT")
    SUCCESS=false
fi

# Calculate duration
END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

# Build trace JSON
cat > "$CAPTURE_FILE" << TRACE_JSON
{
  "trace_id": "${SESSION_ID}",
  "timestamp": "$(date -Iseconds)",
  "user_prompt": $(echo "$USER_PROMPT" | jq -Rs .),
  "claude_response": $(cat "$TEMP_OUTPUT" | jq -Rs .),
  "working_directory": "$(pwd)",
  "response_time_ms": $((DURATION * 1000)),
  "task_completed": $SUCCESS,
  "captured_by": "cli_wrapper"
}
TRACE_JSON

# Clean up
rm -f "$TEMP_OUTPUT"

# Notify
echo ""
echo "✅ Interaction auto-captured: $CAPTURE_FILE"
echo "📊 Duration: ${DURATION}s"
echo ""

# Trigger processing (async)
(
  python3 "/home/rohith/desktop/CommandCenter/claude-rl-agent/engine/process_raw_trace.py" "$CAPTURE_FILE" &
) 2>/dev/null

exit 0
