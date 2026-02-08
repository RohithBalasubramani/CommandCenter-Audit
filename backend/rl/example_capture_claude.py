#!/usr/bin/env python3
"""
Example: How to Capture Claude Code Interactions for Training Data

This demonstrates how to manually capture Claude's problem-solving workflow
to build a training dataset for LLaMA.

Run this script to see how the capture system works, then use it to log
real interactions with Claude Code.
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from claude_capture_hook import ClaudeCapturer, quick_capture


def example_1_simple_query():
    """
    Example 1: Capturing a simple query

    User asks: "What's the difference between transformer 1 and transformer 2?"
    Claude uses RAG + database queries to answer.
    """
    print("=" * 70)
    print("Example 1: Capturing Claude's workflow for a database query")
    print("=" * 70)

    capturer = ClaudeCapturer()

    # 1. Start capture (this is what you ask Claude)
    capturer.start_trace(
        user_prompt="What's the difference between transformer 1 and transformer 2 in the factory data?",
        working_directory="/home/rohith/desktop/CommandCenter"
    )

    # 2. Log each tool Claude uses (in the order it uses them)

    # Claude first reads the schema to understand the data structure
    capturer.add_tool_call(
        tool="Read",
        args={"file_path": "/home/rohith/desktop/CommandCenter/rl_training_data/generate_schema.py"},
        output="... schema definition showing transformer table structure ...",
        reasoning="I'll read the schema to understand the transformer table structure"
    )

    # Claude searches for transformer-related code
    capturer.add_tool_call(
        tool="Grep",
        args={"pattern": "transformer", "path": "/home/rohith/desktop/CommandCenter/rl_training_data"},
        output="Found references in generate_data_gpu.py, generate_schema.py",
        reasoning="Searching for transformer references to understand the data model"
    )

    # Claude queries the database
    capturer.add_tool_call(
        tool="Bash",
        args={
            "command": "psql -U postgres -d command_center_data -c \"SELECT * FROM trf_substation_main_1 LIMIT 5\""
        },
        output="""
          ts                 | v_primary_l1 | v_primary_l2 | v_primary_l3 | ...
        ---------------------+--------------+--------------+--------------+-----
         2023-02-01 00:00:00 |     11000.2  |     11001.1  |     10999.8  | ...
         2023-02-01 00:01:00 |     11000.5  |     11000.9  |     11000.1  | ...
        """,
        reasoning="Querying transformer 1 data to see its actual values"
    )

    capturer.add_tool_call(
        tool="Bash",
        args={
            "command": "psql -U postgres -d command_center_data -c \"SELECT * FROM trf_substation_main_2 LIMIT 5\""
        },
        output="""
          ts                 | v_primary_l1 | v_primary_l2 | v_primary_l3 | ...
        ---------------------+--------------+--------------+--------------+-----
         2023-02-01 00:00:00 |     11000.4  |     11000.8  |     10999.9  | ...
         2023-02-01 00:01:00 |     11000.6  |     11001.0  |     11000.2  | ...
        """,
        reasoning="Querying transformer 2 data for comparison"
    )

    # 3. Log Claude's final response
    claude_response = """
Based on the database queries and schema, here are the key differences between transformer 1 and transformer 2:

**Transformer 1** (trf_substation_main_1):
- Primary voltage: ~11kV (11000V ±1V variation)
- Secondary voltage: ~415V
- Capacity: 1500 kVA
- Located in substation main section 1

**Transformer 2** (trf_substation_main_2):
- Primary voltage: ~11kV (11000V ±1V variation)
- Secondary voltage: ~415V
- Capacity: 1500 kVA
- Located in substation main section 2

Both transformers have identical specifications (1500 kVA, 11kV/415V) but serve different sections of the factory. The voltage readings are nearly identical, suggesting they're operating under similar load conditions.

The main difference is their **physical location** and the **factory sections they serve**, not their electrical specifications.
"""

    trace = capturer.finish_trace(claude_response, user_feedback="up")

    # 4. Save to disk
    capturer.save(trace)

    print(f"\n✓ Captured trace: {trace.trace_id}")
    print(f"  - Tools used: {len(trace.tool_calls)}")
    print(f"  - Tool sequence: {trace.reasoning_signals.tool_sequence}")
    print(f"  - Reasoning steps: {trace.reasoning_signals.reasoning_steps}")
    print(f"  - Exploration depth: {trace.reasoning_signals.exploration_depth.value}")
    print(f"  - Used database: {trace.reasoning_signals.used_terminal}")

    if trace.reasoning_signals.constraints_detected:
        print(f"  - Constraints detected: {len(trace.reasoning_signals.constraints_detected)}")
        for constraint in trace.reasoning_signals.constraints_detected[:2]:
            print(f"    * {constraint.constraint[:80]}...")

    print()


def example_2_complex_workflow():
    """
    Example 2: Capturing a complex multi-step workflow

    User asks: "Refactor the config.py file to improve readability"
    Claude reads → analyzes → plans → edits → verifies
    """
    print("=" * 70)
    print("Example 2: Capturing Claude's multi-step refactoring workflow")
    print("=" * 70)

    capturer = ClaudeCapturer()

    capturer.start_trace(
        user_prompt="Refactor the config.py file to improve readability",
        working_directory="/home/rohith/desktop/CommandCenter/backend/rl"
    )

    # Step 1: Read to understand
    capturer.add_tool_call(
        tool="Read",
        args={"file_path": "/home/rohith/desktop/CommandCenter/backend/rl/config.py"},
        output="... 176 lines of config code ...",
        reasoning="First, I'll read the entire file to understand its current structure"
    )

    # Step 2: Analyze structure
    capturer.add_tool_call(
        tool="Grep",
        args={"pattern": "^def |^class ", "path": "config.py"},
        output="def get_config(config_name: str = 'default') -> dict:",
        reasoning="Checking for functions and classes to understand code organization"
    )

    # Step 3: Check for tests (constraint detection)
    capturer.add_tool_call(
        tool="Bash",
        args={"command": "find . -name '*test*config*' -o -name 'config*test*'"},
        output="./tests/test_config.py",
        reasoning="Checking if there are tests to ensure I don't break existing functionality"
    )

    claude_response = """
I'll refactor config.py to improve readability. First, let me understand the constraints:

**Constraints identified:**
- Must preserve backward compatibility (existing code imports from this file)
- Cannot modify the function signatures (would break tests)
- Need to maintain all existing configuration keys

**Refactoring approach:**
1. Add docstrings to explain each configuration section
2. Group related settings together
3. Add type hints for better clarity
4. Extract magic numbers into named constants

Let me make these changes:

[Uses Edit tool to make the changes]

The refactoring maintains all existing functionality while improving:
- **Documentation**: Added comprehensive docstrings
- **Organization**: Grouped related configs together
- **Type safety**: Added type hints
- **Maintainability**: Extracted magic numbers to constants

All tests should still pass since we haven't changed any exported values or function signatures.
"""

    trace = capturer.finish_trace(claude_response, user_feedback="up")
    capturer.save(trace)

    print(f"\n✓ Captured trace: {trace.trace_id}")
    print(f"  - Tools used: {len(trace.tool_calls)}")
    print(f"  - Constraints detected: {len(trace.reasoning_signals.constraints_detected)}")

    if trace.reasoning_signals.explicit_plan:
        print(f"  - Explicit plan found: {trace.reasoning_signals.explicit_plan[:100]}...")

    print()


def example_3_quick_capture():
    """
    Example 3: Quick one-liner capture for simple interactions
    """
    print("=" * 70)
    print("Example 3: Quick capture for simple queries")
    print("=" * 70)

    # Simple one-liner for quick captures
    trace = quick_capture(
        prompt="How many tables are in the command_center_data database?",
        claude_response="""
Let me check the database schema:

[Runs: psql -U postgres -d command_center_data -c "\\dt" | wc -l]

There are **367 tables** in the command_center_data database:
- 357 equipment tables
- 10 system tables

These tables store 3 years of sensor data for the factory monitoring system.
""",
        tool_calls=[
            ("Bash", {"command": "psql -U postgres -d command_center_data -c \"\\\\dt\" | wc -l"}, "367")
        ]
    )

    print()


def main():
    """Run all examples."""
    print("\n" + "=" * 70)
    print(" Claude Code Capture System - Examples")
    print("=" * 70)
    print()
    print("This demonstrates how to capture Claude's problem-solving workflow")
    print("to build training data for LLaMA behavioral replication.")
    print()

    # Run examples
    example_1_simple_query()
    example_2_complex_workflow()
    example_3_quick_capture()

    # Show summary
    capturer = ClaudeCapturer()
    total_traces = capturer.get_trace_count()

    print("=" * 70)
    print(f" Total traces captured: {total_traces}")
    print("=" * 70)
    print()
    print("Next steps:")
    print("1. Use the interactive session: python -m claude_capture_hook")
    print("2. Or use ClaudeCapturer in your own scripts")
    print("3. Aim for 500-1000 diverse traces before training")
    print("4. Once you have enough traces, run the SFT trainer")
    print()
    print("Training data stored at:")
    print("  /home/rohith/desktop/CommandCenter/rl_training_data/claude_traces/")
    print()


if __name__ == "__main__":
    main()
