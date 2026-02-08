#!/usr/bin/env python3
"""
Process raw captured traces and convert to ClaudeTrace format.

This is called automatically by the CLI wrapper to process captured interactions.
"""

import sys
import json
import logging
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from claude_trace_schema import ClaudeTrace, ToolCall, TraceStorage
from reasoning_extractor import ReasoningSignalExtractor

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def process_raw_trace(raw_file: str):
    """Process a raw trace file and convert to ClaudeTrace."""
    try:
        # Load raw trace
        with open(raw_file, 'r') as f:
            raw_data = json.load(f)

        # Extract tool calls from response
        tool_calls = extract_tool_calls_from_text(raw_data['claude_response'])

        # Create ClaudeTrace
        trace = ClaudeTrace(
            trace_id=raw_data['trace_id'],
            session_id=raw_data['trace_id'].split('_')[0],
            timestamp=datetime.fromisoformat(raw_data['timestamp']),
            user_prompt=raw_data['user_prompt'],
            claude_response=raw_data['claude_response'],
            tool_calls=tool_calls,
            working_directory=raw_data.get('working_directory', '/home/rohith'),
            response_time_ms=raw_data.get('response_time_ms', 0),
            task_completed=raw_data.get('task_completed', True)
        )

        # Extract reasoning signals
        extractor = ReasoningSignalExtractor()
        trace.reasoning_signals = extractor.extract_signals(trace)

        # Save to storage
        storage = TraceStorage()
        storage.save_trace(trace)

        logger.info(f"✅ Processed trace: {trace.trace_id}")
        logger.info(f"   Tools: {' → '.join(trace.reasoning_signals.tool_sequence)}")
        logger.info(f"   Steps: {trace.reasoning_signals.reasoning_steps}")

        # Delete raw file
        Path(raw_file).unlink()

        return True

    except Exception as e:
        logger.error(f"Failed to process {raw_file}: {e}")
        return False


def extract_tool_calls_from_text(text: str) -> list:
    """Extract tool calls from Claude's response text."""
    import re

    tool_calls = []

    # Patterns for different tools
    patterns = {
        'Read': r'(?:read|reading|viewing)\s+(?:file\s+)?`?([^`\n]+)`?',
        'Edit': r'(?:edit|editing|modifying)\s+(?:file\s+)?`?([^`\n]+)`?',
        'Write': r'(?:writ(?:e|ing)|creat(?:e|ing))\s+(?:file\s+)?`?([^`\n]+)`?',
        'Bash': r'(?:run|running|execut(?:e|ing))\s+`([^`]+)`',
        'Grep': r'(?:search|searching|grep)\s+for\s+["\']([^"\']+)["\']',
    }

    for tool, pattern in patterns.items():
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            tool_call = ToolCall(
                tool=tool,
                args={'target': match.group(1)},
                output="",
                timestamp=datetime.now(),
                reasoning=f"Auto-extracted: {match.group(0)}"
            )
            tool_calls.append(tool_call)

    return tool_calls


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: process_raw_trace.py <raw_trace_file>")
        sys.exit(1)

    raw_file = sys.argv[1]
    success = process_raw_trace(raw_file)
    sys.exit(0 if success else 1)
