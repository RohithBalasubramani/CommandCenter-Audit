#!/usr/bin/env python3
"""
DEMONSTRATION: Capturing Claude's Workflow Design Meta-Capability

This shows EXACTLY how we capture the workflow design process Claude uses
when answering: "What's the difference between transformer 1 and transformer 2?"

We capture:
1. WORKFLOW DESIGN: What pipeline did Claude design?
2. EXECUTION: How did Claude execute it step-by-step?
3. SYNTHESIS: How did Claude combine results?

This is the META-CAPABILITY LLaMA needs to learn.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from claude_capture_hook import ClaudeCapturer
from claude_trace_schema import TraceStorage
import json


def demonstrate_workflow_capture():
    """
    Demonstrate capturing Claude's WORKFLOW DESIGN process.

    This simulates a real interaction where Claude designs and executes
    a multi-step pipeline to answer a database query question.
    """

    print("=" * 80)
    print(" DEMONSTRATION: Capturing Claude's Workflow Design Meta-Capability")
    print("=" * 80)
    print()

    # USER'S QUESTION
    user_question = "What's the difference between transformer 1 and transformer 2 in the factory data?"

    print("USER ASKS:")
    print(f"  → {user_question}")
    print()

    # CLAUDE'S INTERNAL WORKFLOW DESIGN (what we're capturing)
    print("CLAUDE'S WORKFLOW DESIGN:")
    print("  1. 🎯 PLANNING PHASE")
    print("     - Identify: Need to compare two database entities")
    print("     - Constraint: Must understand schema first")
    print("     - Design pipeline: Schema → Code search → DB query → Compare")
    print()
    print("  2. 🔧 EXECUTION PHASE")
    print("     Step 1: Read schema to understand transformer table structure")
    print("     Step 2: Search codebase for transformer references")
    print("     Step 3: Query database for transformer 1 data")
    print("     Step 4: Query database for transformer 2 data")
    print()
    print("  3. 🧠 SYNTHESIS PHASE")
    print("     - Compare voltage readings")
    print("     - Compare specifications")
    print("     - Identify key differences")
    print("     - Generate coherent explanation")
    print()
    print("=" * 80)
    print()

    # NOW CAPTURE THIS WORKFLOW
    capturer = ClaudeCapturer()

    print("CAPTURING THE WORKFLOW...")
    print()

    # Start trace
    capturer.start_trace(
        user_prompt=user_question,
        working_directory="/home/rohith/desktop/CommandCenter"
    )

    # PHASE 1: PLANNING (captured through explicit plan extraction)
    # Claude mentions its plan in the response

    # PHASE 2: EXECUTION (captured through tool calls)

    print("📝 Logging Step 1: Read schema (understand data structure)")
    capturer.add_tool_call(
        tool="Read",
        args={"file_path": "/home/rohith/desktop/CommandCenter/rl_training_data/generate_schema.py"},
        output="""
CREATE TABLE trf_substation_main_1 (
    ts TIMESTAMPTZ NOT NULL,
    v_primary_l1 REAL,
    v_primary_l2 REAL,
    v_primary_l3 REAL,
    v_secondary_l1 REAL,
    v_secondary_l2 REAL,
    v_secondary_l3 REAL,
    i_primary_l1 REAL,
    i_primary_l2 REAL,
    i_primary_l3 REAL,
    ...
    kva_rating INTEGER DEFAULT 1500,
    PRIMARY KEY (ts)
);

CREATE TABLE trf_substation_main_2 (
    -- Same structure as trf_substation_main_1
    ...
);
""",
        reasoning="First, I need to understand the transformer table structure to know what data is available"
    )

    print("📝 Logging Step 2: Search for transformer references")
    capturer.add_tool_call(
        tool="Grep",
        args={"pattern": "transformer|trf_", "path": "/home/rohith/desktop/CommandCenter/rl_training_data"},
        output="""
generate_schema.py:45:    CREATE TABLE trf_substation_main_1
generate_schema.py:78:    CREATE TABLE trf_substation_main_2
generate_data_gpu.py:123:    # Generate transformer data
generate_data_gpu.py:145:    transformer_1_data = generate_equipment_data('trf_substation_main_1', ...)
generate_data_gpu.py:146:    transformer_2_data = generate_equipment_data('trf_substation_main_2', ...)
""",
        reasoning="Searching for transformer references to understand how the data is generated and what might differ"
    )

    print("📝 Logging Step 3: Query transformer 1 data")
    capturer.add_tool_call(
        tool="Bash",
        args={
            "command": "psql -U postgres -d command_center_data -c \"SELECT ts, v_primary_l1, v_primary_l2, v_primary_l3, kva_rating FROM trf_substation_main_1 ORDER BY ts LIMIT 5\""
        },
        output="""
          ts                 | v_primary_l1 | v_primary_l2 | v_primary_l3 | kva_rating
---------------------+--------------+--------------+--------------+------------
 2023-02-01 00:00:00 |     11000.23 |     11001.15 |     10999.81 |       1500
 2023-02-01 00:01:00 |     11000.51 |     11000.92 |     11000.08 |       1500
 2023-02-01 00:02:00 |     11000.67 |     11001.03 |     10999.95 |       1500
 2023-02-01 00:03:00 |     11000.42 |     11000.88 |     11000.12 |       1500
 2023-02-01 00:04:00 |     11000.35 |     11001.21 |     10999.76 |       1500
(5 rows)
""",
        reasoning="Querying transformer 1 data to see its actual voltage readings and specifications"
    )

    print("📝 Logging Step 4: Query transformer 2 data")
    capturer.add_tool_call(
        tool="Bash",
        args={
            "command": "psql -U postgres -d command_center_data -c \"SELECT ts, v_primary_l1, v_primary_l2, v_primary_l3, kva_rating FROM trf_substation_main_2 ORDER BY ts LIMIT 5\""
        },
        output="""
          ts                 | v_primary_l1 | v_primary_l2 | v_primary_l3 | kva_rating
---------------------+--------------+--------------+--------------+------------
 2023-02-01 00:00:00 |     11000.38 |     11000.79 |     10999.92 |       1500
 2023-02-01 00:01:00 |     11000.63 |     11001.05 |     11000.01 |       1500
 2023-02-01 00:02:00 |     11000.45 |     11000.96 |     10999.88 |       1500
 2023-02-01 00:03:00 |     11000.57 |     11001.12 |     11000.15 |       1500
 2023-02-01 00:04:00 |     11000.29 |     11000.84 |     10999.97 |       1500
(5 rows)
""",
        reasoning="Querying transformer 2 data for comparison with transformer 1"
    )

    # PHASE 3: SYNTHESIS (captured in Claude's response)
    claude_response = """
Let me analyze the differences between transformer 1 and transformer 2 in the factory data.

**Workflow I designed:**
1. First, I read the schema to understand the transformer table structure
2. Then searched for transformer references in the codebase
3. Queried actual data from both transformer tables
4. Now comparing the results

**Findings:**

Both transformers have **identical specifications**:
- **kVA Rating**: 1500 kVA (both)
- **Primary Voltage**: ~11kV (11000V ±1V variation)
- **Secondary Voltage**: 415V (from schema)
- **Configuration**: 3-phase (L1, L2, L3)

**Voltage Readings Comparison:**

| Metric | Transformer 1 | Transformer 2 |
|--------|--------------|--------------|
| V_primary_L1 | 11000.23-11000.67V | 11000.29-11000.63V |
| V_primary_L2 | 11000.88-11001.21V | 11000.79-11001.12V |
| V_primary_L3 | 10999.76-11000.12V | 10999.88-11000.15V |

**Key Differences:**

1. **Location**:
   - Transformer 1: Substation Main Section 1
   - Transformer 2: Substation Main Section 2

2. **Voltage Stability**:
   - Transformer 1: Slightly higher variance (~0.44V range on L1)
   - Transformer 2: Slightly more stable (~0.34V range on L1)

3. **Load Distribution**:
   - Both operating at similar load levels (voltage readings nearly identical)
   - Serving different factory sections but under comparable electrical conditions

**Conclusion:**
The transformers are electrically **identical in specifications** (1500 kVA, 11kV/415V) but serve **different physical locations** in the factory. The voltage readings show both are operating normally with minimal variation, suggesting balanced load distribution across the facility.

The main difference is **operational location**, not electrical characteristics.
"""

    print("📝 Logging Claude's final response (with synthesis)")
    print()

    # Finish trace
    trace = capturer.finish_trace(
        claude_response=claude_response,
        user_feedback="up",  # User found this helpful
        response_time_ms=3500
    )

    # Save
    capturer.save(trace)

    print("=" * 80)
    print(" CAPTURED WORKFLOW BREAKDOWN")
    print("=" * 80)
    print()

    # Show what was extracted
    signals = trace.reasoning_signals

    print("🎯 WORKFLOW DESIGN CAPTURED:")
    print(f"   Pipeline designed by Claude: {' → '.join(signals.tool_sequence)}")
    print(f"   Workflow type: {extract_workflow_type(trace)}")
    print(f"   Reasoning steps: {signals.reasoning_steps}")
    print(f"   Exploration depth: {signals.exploration_depth.value}")
    print()

    print("🔧 EXECUTION PATTERN:")
    print(f"   Sequential execution: {len(trace.tool_calls)} steps")
    print(f"   Tools used: {set(signals.tool_sequence)}")
    print(f"   Multi-step reasoning: {signals.multi_step_reasoning}")
    print(f"   Used database: {signals.used_terminal}")
    print()

    print("🧠 SYNTHESIS CAPTURED:")
    if signals.explicit_plan:
        print(f"   Explicit plan detected: {signals.explicit_plan[:100]}...")
    print(f"   Constraints detected: {len(signals.constraints_detected)}")
    print(f"   Pruning decisions: {len(signals.tools_pruned)}")
    print()

    print("=" * 80)
    print(" WHAT LLAMA WILL LEARN FROM THIS")
    print("=" * 80)
    print()

    print("1️⃣  META-CAPABILITY: Design multi-step workflows")
    print("    Pattern: Schema → Search → Query DB → Compare → Synthesize")
    print()

    print("2️⃣  TOOL SELECTION: When to use which tool")
    print("    - Read: For understanding schema/code structure")
    print("    - Grep: For finding relevant code references")
    print("    - Bash: For database queries (psql)")
    print()

    print("3️⃣  EXECUTION ORDER: Sequential pipeline execution")
    print("    - Explore BEFORE querying (read schema first)")
    print("    - Query both entities for comparison")
    print("    - Synthesize results into coherent answer")
    print()

    print("4️⃣  REASONING DEPTH: Thorough exploration")
    print("    - Don't jump to conclusions")
    print("    - Gather all relevant data first")
    print("    - Compare systematically")
    print()

    print("5️⃣  SYNTHESIS: Combine results coherently")
    print("    - Structure: Workflow → Findings → Comparison → Conclusion")
    print("    - Use tables for clarity")
    print("    - Highlight key differences")
    print()

    print("=" * 80)
    print()

    # Show the actual JSON structure
    print("📄 TRACE DATA STRUCTURE (saved to disk):")
    print()

    trace_dict = trace.to_dict()
    # Show abbreviated version
    print(json.dumps({
        "trace_id": trace_dict["trace_id"],
        "user_prompt": trace_dict["user_prompt"][:60] + "...",
        "tool_calls": [
            {"tool": tc["tool"], "reasoning": tc["reasoning"][:50] + "..." if tc["reasoning"] else None}
            for tc in trace_dict["tool_calls"]
        ],
        "reasoning_signals": {
            "tool_sequence": trace_dict["reasoning_signals"]["tool_sequence"],
            "reasoning_steps": trace_dict["reasoning_signals"]["reasoning_steps"],
            "exploration_depth": trace_dict["reasoning_signals"]["exploration_depth"],
            "multi_step_reasoning": trace_dict["reasoning_signals"]["multi_step_reasoning"],
            "used_terminal": trace_dict["reasoning_signals"]["used_terminal"],
        },
        "claude_response": trace_dict["claude_response"][:100] + "...",
    }, indent=2))

    print()
    print("=" * 80)
    print(f" ✅ Trace saved: {trace.trace_id}")
    print(f" 📂 Location: /home/rohith/desktop/CommandCenter/rl_training_data/claude_traces/traces.jsonl")
    print("=" * 80)
    print()

    return trace


def extract_workflow_type(trace):
    """Extract the workflow type from trace."""
    from reasoning_extractor import WorkflowExtractor
    extractor = WorkflowExtractor()
    workflow = extractor.extract_workflow_graph(trace)
    return workflow["workflow_type"]


def show_training_impact():
    """Show how this will impact LLaMA training."""
    print()
    print("=" * 80)
    print(" TRAINING IMPACT: What LLaMA Learns from 500+ Traces Like This")
    print("=" * 80)
    print()

    print("After training on 500-1000 similar traces, LLaMA will learn to:")
    print()

    print("1. DESIGN WORKFLOWS (Meta-Capability)")
    print("   ✓ Given: 'What's the difference between X and Y?'")
    print("   ✓ LLaMA learns: Schema → Search → Query X → Query Y → Compare")
    print("   ✓ NOT memorized, but LEARNED as a pattern")
    print()

    print("2. SELECT APPROPRIATE TOOLS")
    print("   ✓ Database questions → Use Bash + psql")
    print("   ✓ Code questions → Use Read + Grep")
    print("   ✓ File modifications → Use Edit (not Write)")
    print()

    print("3. REASON BEFORE ACTING")
    print("   ✓ Claude explores first (Read schema, Search code)")
    print("   ✓ Then queries (Bash psql)")
    print("   ✓ LLaMA learns: Exploration depth = 'thorough'")
    print()

    print("4. SYNTHESIZE COHERENTLY")
    print("   ✓ Structure answers clearly (Findings → Comparison → Conclusion)")
    print("   ✓ Use tables when comparing data")
    print("   ✓ Highlight key differences")
    print()

    print("5. ADAPT TO CONSTRAINTS")
    print("   ✓ If Claude detected 'must preserve X', LLaMA learns to check for X")
    print("   ✓ If Claude avoided tool Y, LLaMA learns why")
    print()

    print("=" * 80)
    print()

    print("🎯 BEHAVIORAL REPLICATION (Not Text Similarity)")
    print()
    print("Standard Fine-Tuning:")
    print("  ❌ Trains on: Claude's final answer text")
    print("  ❌ LLaMA learns: How to sound like Claude")
    print("  ❌ Result: Similar text, but random tool usage")
    print()
    print("Our Behavioral Replication:")
    print("  ✅ Trains on: Claude's workflow design + execution")
    print("  ✅ LLaMA learns: How to THINK like Claude")
    print("  ✅ Result: Same workflow, same tools, same reasoning depth")
    print()

    print("=" * 80)
    print()


if __name__ == "__main__":
    # Run the demonstration
    trace = demonstrate_workflow_capture()

    # Show training impact
    show_training_impact()

    # Next steps
    print("🚀 NEXT STEPS:")
    print()
    print("1. Capture 500-1000 diverse traces like this")
    print("   → Use: python -m claude_capture_hook")
    print()
    print("2. Build SFT dataset from traces")
    print("   → Run: behavioral_cloning_builder.py (Week 2)")
    print()
    print("3. Train LLaMA with behavioral cloning")
    print("   → Run: sft_trainer.py (Week 2)")
    print()
    print("4. PPO alignment to close behavioral gaps")
    print("   → Run: ppo_trainer.py (Weeks 3-6)")
    print()
    print("5. Deploy and test indistinguishability")
    print("   → Goal: Users can't tell Claude from LLaMA")
    print()
    print("Start capturing now! Every trace brings LLaMA closer to Claude's workflow design capability.")
    print()
