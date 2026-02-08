#!/usr/bin/env python3
"""
Fast-Track Bootstrap - Generate Synthetic Training Data

Instead of waiting 6 months for real traces, bootstrap with:
1. Synthetic Claude-like workflows (generated from templates)
2. Command Center RL system's existing feedback data
3. Demonstrations and examples
4. Aggressive immediate training

This compresses 6 months → NOW.
"""

import json
import random
from pathlib import Path
from datetime import datetime
from typing import List, Dict
import sys

sys.path.insert(0, str(Path(__file__).parent))

from claude_trace_schema import ClaudeTrace, ToolCall, ReasoningSignals, ConstraintDetection, SelfCorrection, ExplorationDepth
from claude_trace_schema import TraceStorage

# Template workflows that Claude typically uses
# COMMAND CENTER SPECIFIC - Industrial Equipment Database Queries
WORKFLOW_TEMPLATES = {
    "equipment_analysis": {
        "prompts": [
            "What's the average power consumption of chiller_001 vs chiller_002 in June 2024?",
            "Show me the daily energy pattern for transformer trf_001",
            "Compare efficiency of all DG sets (dg_001 to dg_006)",
            "Find cooling tower ct_001 performance degradation over time",
            "Analyze AHU runtime patterns across all 23 units",
            "What's the power factor trend for lt_mcc_001 in the last month?",
        ],
        "reasoning_chain": [
            "First, I'll query the equipment table to understand the schema",
            "Then I'll aggregate the data by time period",
            "Next, I'll calculate the metrics (averages, totals, trends)",
            "Finally, I'll compare across equipment or time periods",
        ],
        "tool_sequence": ["Bash", "Read", "Bash"],
        "exploration": ExplorationDepth.MODERATE,
    },

    "anomaly_detection": {
        "prompts": [
            "Find anomalies in chiller_003 temperature readings for last week",
            "Detect unusual power spikes in transformer trf_002",
            "Identify motor_005 vibration anomalies",
            "Show me when DG set dg_001 had abnormal runtime",
            "Find cooling tower ct_002 failures in maintenance_records",
            "Detect energy meter em_010 communication errors",
        ],
        "reasoning_chain": [
            "First, I'll query the equipment data with time filters",
            "Then I'll calculate statistical thresholds (mean ± 3σ)",
            "Next, I'll identify outliers beyond thresholds",
            "Finally, I'll correlate with alerts and maintenance records",
        ],
        "tool_sequence": ["Bash", "Bash", "Read", "Bash"],
        "exploration": ExplorationDepth.THOROUGH,
    },

    "database_schema": {
        "prompts": [
            "Show me the schema of lt_mcc_001 table",
            "What columns are available in chiller tables?",
            "List all 357 equipment tables in command_center_data",
            "What's the structure of the alerts table?",
            "Show me the relationships between buildings, zones, and equipment_registry",
            "What indexes exist on transformer tables?",
        ],
        "reasoning_chain": [
            "First, I'll connect to the PostgreSQL database",
            "Then I'll query information_schema for table metadata",
            "Next, I'll examine the schema structure",
            "Finally, I'll summarize the key columns and types",
        ],
        "tool_sequence": ["Bash", "Read", "Bash"],
        "exploration": ExplorationDepth.MINIMAL,
    },

    "maintenance_analysis": {
        "prompts": [
            "When was the last maintenance for chiller_001?",
            "Show maintenance history for all transformers (trf_001 to trf_010)",
            "Find equipment with overdue maintenance",
            "What's the MTBF for motor_001 to motor_015?",
            "Show alert frequency by equipment type",
            "Analyze pump_001 to pump_020 bearing replacement patterns",
        ],
        "reasoning_chain": [
            "First, I'll query the maintenance_records table",
            "Then I'll join with equipment_registry for details",
            "Next, I'll calculate maintenance intervals and frequencies",
            "Finally, I'll identify patterns and predict next maintenance",
        ],
        "tool_sequence": ["Bash", "Bash", "Read", "Bash"],
        "exploration": ExplorationDepth.THOROUGH,
    },

    "energy_optimization": {
        "prompts": [
            "What's the optimal chiller staging to minimize energy cost?",
            "Calculate total facility energy consumption for July 2024",
            "Show me the load curve for all transformers combined",
            "When should we switch from grid to DG to save cost?",
            "Analyze APFC panel effectiveness across all 20 units",
            "What's the ROI of running chillers at different setpoints?",
        ],
        "reasoning_chain": [
            "First, I'll query energy consumption across all equipment",
            "Then I'll calculate costs using energy_configs pricing",
            "Next, I'll simulate different operating scenarios",
            "Finally, I'll recommend the optimal configuration",
        ],
        "tool_sequence": ["Bash", "Bash", "Read", "Bash"],
        "exploration": ExplorationDepth.THOROUGH,
    },

    "real_time_monitoring": {
        "prompts": [
            "Show me current status of all 6 DG sets",
            "What's the live power factor across all LT panels?",
            "Display real-time cooling tower approach temperatures",
            "Monitor UPS battery status for ups_001 to ups_008",
            "Show active alerts for the last 10 minutes",
            "What equipment is currently in fault state?",
        ],
        "reasoning_chain": [
            "First, I'll query the latest timestamp for real-time data",
            "Then I'll fetch current values for all requested parameters",
            "Next, I'll check alerts table for active alarms",
            "Finally, I'll format the data for dashboard display",
        ],
        "tool_sequence": ["Bash", "Read", "Bash"],
        "exploration": ExplorationDepth.MINIMAL,
    },

    "data_aggregation": {
        "prompts": [
            "Calculate hourly averages for chiller_001 for June 15, 2024",
            "Show daily peak demand for all transformers in Q2 2024",
            "Aggregate monthly energy consumption by building",
            "What's the 15-minute interval data for motor_005 yesterday?",
            "Create weekly summary report for all AHUs",
            "Calculate shift-wise production metrics (3 shifts)",
        ],
        "reasoning_chain": [
            "First, I'll use date_trunc to aggregate by time period",
            "Then I'll apply statistical functions (AVG, MAX, SUM)",
            "Next, I'll group by equipment, building, or zone",
            "Finally, I'll order and format the results",
        ],
        "tool_sequence": ["Bash", "Bash", "Read"],
        "exploration": ExplorationDepth.MODERATE,
    },

    "predictive_maintenance": {
        "prompts": [
            "Predict next chiller filter change based on ΔP trend",
            "When will motor_003 bearings need replacement?",
            "Forecast transformer oil testing schedule",
            "Identify pumps showing early wear indicators",
            "Calculate remaining useful life for compressor_001",
            "Show equipment health scores across all 357 tables",
        ],
        "reasoning_chain": [
            "First, I'll fetch historical trend data for degradation parameters",
            "Then I'll calculate rates of change and extrapolate",
            "Next, I'll compare against maintenance thresholds",
            "Finally, I'll generate predictions and confidence intervals",
        ],
        "tool_sequence": ["Bash", "Bash", "Read", "Bash"],
        "exploration": ExplorationDepth.THOROUGH,
    },
}


class FastTrackBootstrap:
    """Generate synthetic training data to fast-track training."""

    def __init__(self):
        self.storage = TraceStorage()
        self.trace_id_counter = 0

    def generate_synthetic_traces(self, num_traces: int = 500) -> List[ClaudeTrace]:
        """Generate synthetic Claude-like traces."""
        print(f"🚀 Generating {num_traces} synthetic traces...")

        traces = []
        workflow_types = list(WORKFLOW_TEMPLATES.keys())

        for i in range(num_traces):
            # Pick random workflow type
            workflow_type = random.choice(workflow_types)
            template = WORKFLOW_TEMPLATES[workflow_type]

            # Generate trace
            trace = self._generate_trace_from_template(workflow_type, template)
            traces.append(trace)

            if (i + 1) % 100 == 0:
                print(f"  Generated {i + 1}/{num_traces} traces...")

        print(f"✅ Generated {len(traces)} synthetic traces")
        return traces

    def _generate_trace_from_template(self, workflow_type: str, template: Dict) -> ClaudeTrace:
        """Generate a single trace from a template."""
        self.trace_id_counter += 1

        # Pick random prompt
        prompt = random.choice(template["prompts"])

        # Build reasoning chain (with variations)
        reasoning_chain = template["reasoning_chain"].copy()
        random.shuffle(reasoning_chain[1:-1])  # Vary middle steps

        # Build tool sequence
        tool_sequence = template["tool_sequence"].copy()

        # Create tool calls
        tool_calls = []
        for i, tool in enumerate(tool_sequence):
            tool_call = ToolCall(
                tool=tool,
                args={"target": f"example_{i}.py"},
                output=f"Mock output for {tool}",
                timestamp=datetime.now(),
                reasoning=reasoning_chain[i] if i < len(reasoning_chain) else "Execute step"
            )
            tool_calls.append(tool_call)

        # Build response
        response = f"{workflow_type.replace('_', ' ').title()} Result:\n\n"
        response += "\n".join([f"{i+1}. {step}" for i, step in enumerate(reasoning_chain)])
        response += f"\n\nCompleted with {len(tool_calls)} tool calls."

        # Create trace
        trace = ClaudeTrace(
            trace_id=f"synthetic_{self.trace_id_counter:04d}",
            session_id=f"bootstrap_session",
            timestamp=datetime.now(),
            user_prompt=prompt,
            claude_response=response,
            tool_calls=tool_calls,
            working_directory="/home/rohith/desktop/CommandCenter",
            response_time_ms=random.randint(1000, 5000),
            task_completed=True,
        )

        # Add reasoning signals
        trace.reasoning_signals = ReasoningSignals(
            tool_sequence=[tc.tool for tc in tool_calls],
            reasoning_steps=len(reasoning_chain),
            exploration_depth=template["exploration"],
            multi_step_reasoning=True,  # All bootstrap traces are multi-step by design
            used_terminal=any(tc.tool == "Bash" for tc in tool_calls),
            used_rag=any(tc.tool in ["Read", "Grep", "Glob"] for tc in tool_calls),
            constraints_detected=[
                ConstraintDetection(
                    constraint=f"Follow {workflow_type} pattern",
                    source="workflow_template",
                    impact="Determined tool sequence and reasoning approach"
                )
            ],
            tools_pruned=[],
            self_corrections=[],
        )

        return trace

    def import_command_center_rl_data(self) -> List[ClaudeTrace]:
        """Import existing RL feedback data from Command Center backend."""
        print("🔍 Importing Command Center RL data...")

        # Path to Command Center backend RL data
        cc_backend = Path("/home/rohith/desktop/CommandCenter/backend")
        rl_data_file = cc_backend / "rl" / "dpo_pairs.jsonl"

        traces = []

        if not rl_data_file.exists():
            print(f"  ⚠️  No RL data found at {rl_data_file}")
            return traces

        # Load DPO pairs and convert to traces
        with open(rl_data_file, 'r') as f:
            for line in f:
                try:
                    dpo_pair = json.loads(line)
                    trace = self._convert_dpo_to_trace(dpo_pair)
                    if trace:
                        traces.append(trace)
                except Exception as e:
                    continue

        print(f"✅ Imported {len(traces)} traces from Command Center RL")
        return traces

    def _convert_dpo_to_trace(self, dpo_pair: Dict) -> ClaudeTrace:
        """Convert a DPO pair to a ClaudeTrace."""
        self.trace_id_counter += 1

        # Extract prompt and chosen response
        prompt = dpo_pair.get("prompt", "")
        chosen = dpo_pair.get("chosen", "")

        # Create minimal trace
        trace = ClaudeTrace(
            trace_id=f"cc_rl_{self.trace_id_counter:04d}",
            session_id="command_center_import",
            timestamp=datetime.now(),
            user_prompt=prompt,
            claude_response=chosen,
            tool_calls=[],  # No tool info in DPO pairs
            working_directory="/home/rohith/desktop/CommandCenter",
            response_time_ms=0,
            task_completed=True,
        )

        # Minimal reasoning signals
        trace.reasoning_signals = ReasoningSignals(
            tool_sequence=[],
            reasoning_steps=1,
            exploration_depth=ExplorationDepth.MINIMAL,
            constraints_detected=[],
            tools_pruned=[],
            self_corrections=[],
        )

        return trace

    def bootstrap_now(self, target_traces: int = 500):
        """Bootstrap training data immediately."""
        print("=" * 70)
        print(" 🚀 FAST-TRACK BOOTSTRAP - 6 Months → NOW")
        print("=" * 70)
        print()

        all_traces = []

        # 1. Generate synthetic traces
        print("Step 1: Generate synthetic Claude-like workflows")
        synthetic = self.generate_synthetic_traces(target_traces)
        all_traces.extend(synthetic)
        print()

        # 2. Import Command Center RL data
        print("Step 2: Import Command Center RL feedback data")
        cc_traces = self.import_command_center_rl_data()
        all_traces.extend(cc_traces)
        print()

        # 3. Save all traces
        print("Step 3: Save training data")
        for trace in all_traces:
            self.storage.save_trace(trace)

        total = self.storage.get_trace_count()
        print(f"✅ Total traces in storage: {total}")
        print()

        # 4. Show statistics
        print("=" * 70)
        print(" 📊 Bootstrap Statistics")
        print("=" * 70)
        print(f"Synthetic traces: {len(synthetic)}")
        print(f"Command Center imports: {len(cc_traces)}")
        print(f"Total: {total}")
        print()

        # 5. Next steps
        print("=" * 70)
        print(" 🎯 Ready for Training!")
        print("=" * 70)
        print()
        print("You can now:")
        print("  1. Build dataset:  ./run.sh build-dataset")
        print("  2. Train SFT:      ./run.sh train --phase sft")
        print("  3. Train PPO:      ./run.sh train --phase ppo")
        print("  4. Export GGUF:    ./run.sh export")
        print()
        print("Or start orchestrator for continuous training:")
        print("  ./run.sh orchestrator start")
        print()

        return total


def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Fast-track bootstrap")
    parser.add_argument("--traces", type=int, default=500, help="Number of synthetic traces")
    args = parser.parse_args()

    bootstrap = FastTrackBootstrap()
    bootstrap.bootstrap_now(target_traces=args.traces)


if __name__ == "__main__":
    main()
