#!/usr/bin/env python3
"""
Automated Parallel Runner

Runs prompts through BOTH Claude CLI and LLaMA simultaneously:
1. Execute prompt in Claude Code CLI (automated)
2. Execute same prompt in LLaMA (via Ollama)
3. Capture both responses
4. Compare and identify differences
5. Train LLaMA to match Claude

This creates a continuous improvement loop.
"""

import subprocess
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple
import logging

from claude_trace_schema import ClaudeTrace, ToolCall, TraceStorage
from reasoning_extractor import ReasoningSignalExtractor

logger = logging.getLogger(__name__)


class AutomatedRunner:
    """
    Automated parallel execution and comparison system.

    Runs prompts through both Claude and LLaMA, captures responses,
    compares them, and uses differences for training.
    """

    def __init__(
        self,
        claude_cli_path: str = "claude",
        llama_model: str = "cc-claude-agent:latest",
        storage_dir: str = "/home/rohith/desktop/CommandCenter/claude-rl-agent/data"
    ):
        self.claude_cli = claude_cli_path
        self.llama_model = llama_model
        self.storage = TraceStorage(storage_dir)
        self.extractor = ReasoningSignalExtractor()

        # Comparison results storage
        self.comparison_log = Path(storage_dir) / "comparison_log.jsonl"
        self.dpo_pairs = Path(storage_dir) / "dpo_pairs.jsonl"

    def run_claude_cli(self, prompt: str) -> Tuple[str, float]:
        """
        Run prompt through Claude Code CLI.

        Returns:
            (response, duration_seconds)
        """
        logger.info(f"Running Claude CLI: {prompt[:50]}...")

        start_time = time.time()

        try:
            result = subprocess.run(
                [self.claude_cli, prompt],
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
            )

            duration = time.time() - start_time
            response = result.stdout

            logger.info(f"Claude completed in {duration:.2f}s")
            return response, duration

        except subprocess.TimeoutExpired:
            logger.error(f"Claude CLI timeout after 300s")
            return "[ERROR: Timeout]", 300.0
        except Exception as e:
            logger.error(f"Claude CLI error: {e}")
            return f"[ERROR: {e}]", 0.0

    def run_llama(self, prompt: str) -> Tuple[str, float]:
        """
        Run prompt through LLaMA via Ollama.

        Returns:
            (response, duration_seconds)
        """
        logger.info(f"Running LLaMA: {prompt[:50]}...")

        start_time = time.time()

        try:
            result = subprocess.run(
                ["ollama", "run", self.llama_model, prompt],
                capture_output=True,
                text=True,
                timeout=300,
            )

            duration = time.time() - start_time
            response = result.stdout

            logger.info(f"LLaMA completed in {duration:.2f}s")
            return response, duration

        except subprocess.TimeoutExpired:
            logger.error(f"LLaMA timeout after 300s")
            return "[ERROR: Timeout]", 300.0
        except Exception as e:
            logger.error(f"LLaMA error: {e}")
            return f"[ERROR: {e}]", 0.0

    def extract_reasoning_signals(self, response: str) -> ReasoningSignals:
        """
        Extract ALL reasoning signals from a response.

        Captures:
        - Tool calls and sequences
        - Reasoning steps
        - Constraint detection
        - Self-corrections
        - Exploration depth
        - Everything Claude thinks through
        """
        # Create a mock trace for the extractor
        mock_trace = ClaudeTrace(
            trace_id="temp",
            session_id="comparison",
            timestamp=datetime.now(),
            user_prompt="",
            claude_response=response,
            tool_calls=[],
            working_directory="/tmp",
            response_time_ms=0,
            task_completed=True
        )

        # Extract signals
        signals = self.extractor.extract_signals(mock_trace)
        return signals

    def compare_behavioral_patterns(
        self,
        claude_signals: ReasoningSignals,
        llama_signals: ReasoningSignals
    ) -> Dict:
        """
        Deep comparison of behavioral patterns - not just text similarity.

        Compares:
        - Tool sequences (Claude: Bash→Read→Bash vs LLaMA: ???)
        - Reasoning depth (step counts)
        - Constraint detection (did both identify constraints?)
        - Self-correction (did both self-correct?)
        - Exploration appropriateness
        - All cognitive patterns
        """
        behavioral_comparison = {}

        # 1. Tool Sequence Comparison
        claude_tools = claude_signals.tool_sequence
        llama_tools = llama_signals.tool_sequence

        tool_match = (claude_tools == llama_tools)
        tool_overlap = len(set(claude_tools) & set(llama_tools)) / max(len(set(claude_tools) | set(llama_tools)), 1)

        behavioral_comparison["tool_sequence"] = {
            "claude": claude_tools,
            "llama": llama_tools,
            "exact_match": tool_match,
            "overlap": tool_overlap,
            "divergence": "DIFFERENT" if not tool_match else "SAME"
        }

        # 2. Reasoning Depth Comparison
        claude_steps = claude_signals.reasoning_steps
        llama_steps = llama_signals.reasoning_steps

        step_ratio = min(claude_steps, llama_steps) / max(claude_steps, llama_steps, 1)

        behavioral_comparison["reasoning_depth"] = {
            "claude_steps": claude_steps,
            "llama_steps": llama_steps,
            "similarity": step_ratio,
            "divergence": "DIFFERENT" if step_ratio < 0.8 else "SIMILAR"
        }

        # 3. Constraint Detection Comparison
        claude_constraints = len(claude_signals.constraints_detected)
        llama_constraints = len(llama_signals.constraints_detected)

        behavioral_comparison["constraint_detection"] = {
            "claude_count": claude_constraints,
            "llama_count": llama_constraints,
            "both_detected": claude_constraints > 0 and llama_constraints > 0,
            "divergence": "MISSING" if claude_constraints > llama_constraints else "SIMILAR"
        }

        # 4. Self-Correction Comparison
        claude_corrections = len(claude_signals.self_corrections)
        llama_corrections = len(llama_signals.self_corrections)

        behavioral_comparison["self_correction"] = {
            "claude_count": claude_corrections,
            "llama_count": llama_corrections,
            "both_corrected": claude_corrections > 0 and llama_corrections > 0,
            "divergence": "MISSING" if claude_corrections > llama_corrections else "SIMILAR"
        }

        # 5. Exploration Depth Comparison
        claude_exploration = claude_signals.exploration_depth.value if hasattr(claude_signals.exploration_depth, 'value') else str(claude_signals.exploration_depth)
        llama_exploration = llama_signals.exploration_depth.value if hasattr(llama_signals.exploration_depth, 'value') else str(llama_signals.exploration_depth)

        behavioral_comparison["exploration_depth"] = {
            "claude": claude_exploration,
            "llama": llama_exploration,
            "match": claude_exploration == llama_exploration,
            "divergence": "DIFFERENT" if claude_exploration != llama_exploration else "SAME"
        }

        # 6. Tool Pruning Comparison (approaches considered but rejected)
        claude_pruned = len(claude_signals.tools_pruned)
        llama_pruned = len(llama_signals.tools_pruned)

        behavioral_comparison["tool_pruning"] = {
            "claude_count": claude_pruned,
            "llama_count": llama_pruned,
            "divergence": "MISSING" if claude_pruned > llama_pruned else "SIMILAR"
        }

        # 7. Overall Behavioral Similarity Score (0-1)
        similarity_scores = [
            1.0 if tool_match else tool_overlap,
            step_ratio,
            1.0 if claude_exploration == llama_exploration else 0.5,
            1.0 if claude_constraints == llama_constraints else 0.7,
            1.0 if claude_corrections == llama_corrections else 0.8,
        ]

        behavioral_similarity = sum(similarity_scores) / len(similarity_scores)
        behavioral_comparison["overall_similarity"] = behavioral_similarity

        # 8. Determine if training is needed
        # Train if behavioral patterns differ significantly
        needs_training = (
            not tool_match or
            step_ratio < 0.8 or
            claude_exploration != llama_exploration or
            (claude_constraints > 0 and llama_constraints == 0) or
            (claude_corrections > 0 and llama_corrections == 0) or
            behavioral_similarity < 0.7
        )

        behavioral_comparison["should_train"] = needs_training
        behavioral_comparison["training_reason"] = []

        if not tool_match:
            behavioral_comparison["training_reason"].append("Tool sequence mismatch")
        if step_ratio < 0.8:
            behavioral_comparison["training_reason"].append("Reasoning depth differs")
        if claude_exploration != llama_exploration:
            behavioral_comparison["training_reason"].append("Exploration depth mismatch")
        if claude_constraints > 0 and llama_constraints == 0:
            behavioral_comparison["training_reason"].append("LLaMA missing constraint detection")
        if claude_corrections > 0 and llama_corrections == 0:
            behavioral_comparison["training_reason"].append("LLaMA missing self-correction")

        return behavioral_comparison

    def compare_responses(
        self,
        prompt: str,
        claude_response: str,
        llama_response: str
    ) -> Dict:
        """
        Deep comparison of Claude vs LLaMA - EVERYTHING, not just text.

        Extracts and compares:
        - All tool calls
        - Complete reasoning chains
        - Constraint detection
        - Self-corrections
        - Exploration patterns
        - Cognitive workflow
        """
        comparison = {
            "timestamp": datetime.now().isoformat(),
            "prompt": prompt,
            "claude_response": claude_response,
            "llama_response": llama_response,
        }

        # Extract reasoning signals from both responses
        logger.info("Extracting Claude's reasoning signals...")
        claude_signals = self.extract_reasoning_signals(claude_response)

        logger.info("Extracting LLaMA's reasoning signals...")
        llama_signals = self.extract_reasoning_signals(llama_response)

        # Deep behavioral comparison
        behavioral_comparison = self.compare_behavioral_patterns(
            claude_signals,
            llama_signals
        )

        comparison["behavioral_comparison"] = behavioral_comparison
        comparison["should_train"] = behavioral_comparison["should_train"]
        comparison["training_reason"] = behavioral_comparison.get("training_reason", [])

        # Also do basic text similarity for reference
        claude_len = len(claude_response)
        llama_len = len(llama_response)
        len_ratio = min(claude_len, llama_len) / max(claude_len, llama_len, 1)

        claude_words = set(claude_response.lower().split())
        llama_words = set(llama_response.lower().split())
        if claude_words or llama_words:
            jaccard = len(claude_words & llama_words) / len(claude_words | llama_words)
        else:
            jaccard = 0

        comparison["text_similarity"] = {
            "length_ratio": len_ratio,
            "word_overlap": jaccard,
            "claude_length": claude_len,
            "llama_length": llama_len,
        }

        if behavioral_comparison["should_train"]:
            logger.info(f"Behavioral divergence detected!")
            logger.info(f"  Reasons: {', '.join(behavioral_comparison['training_reason'])}")
            logger.info(f"  Overall similarity: {behavioral_comparison['overall_similarity']:.2%}")

        return comparison

    def create_dpo_pair(self, comparison: Dict) -> Dict:
        """
        Create DPO training pair from comparison.

        DPO format:
        - prompt: The question
        - chosen: Claude's response (better)
        - rejected: LLaMA's response (worse)
        """
        return {
            "prompt": comparison["prompt"],
            "chosen": comparison["claude_response"],
            "rejected": comparison["llama_response"],
            "timestamp": comparison["timestamp"],
            "metrics": comparison["metrics"],
        }

    def save_comparison(self, comparison: Dict):
        """Save comparison result to log."""
        with open(self.comparison_log, 'a') as f:
            f.write(json.dumps(comparison) + '\n')

    def save_dpo_pair(self, dpo_pair: Dict):
        """Save DPO training pair."""
        with open(self.dpo_pairs, 'a') as f:
            f.write(json.dumps(dpo_pair) + '\n')

    def run_parallel_comparison(self, prompt: str) -> Dict:
        """
        Run prompt through both Claude and LLaMA, compare results.

        Returns comparison dict.
        """
        print(f"\n{'='*70}")
        print(f"Running parallel comparison:")
        print(f"Prompt: {prompt[:60]}...")
        print(f"{'='*70}\n")

        # Run both in parallel (could use threading, but sequential for simplicity)
        claude_response, claude_time = self.run_claude_cli(prompt)
        llama_response, llama_time = self.run_llama(prompt)

        # Compare
        comparison = self.compare_responses(prompt, claude_response, llama_response)
        comparison["claude_time"] = claude_time
        comparison["llama_time"] = llama_time

        # Save
        self.save_comparison(comparison)

        # Create DPO pair if divergent
        if comparison["should_train"]:
            dpo_pair = self.create_dpo_pair(comparison)
            self.save_dpo_pair(dpo_pair)
            print(f"✅ DPO pair saved for training")
        else:
            print(f"✅ Responses similar - no training needed")

        # Print detailed behavioral comparison
        behavioral = comparison["behavioral_comparison"]

        print(f"\n{'─'*70}")
        print(f"BEHAVIORAL COMPARISON RESULTS")
        print(f"{'─'*70}")

        print(f"\n⏱  Execution Time:")
        print(f"  Claude: {claude_time:.2f}s | LLaMA: {llama_time:.2f}s")

        print(f"\n🔧 Tool Sequence:")
        print(f"  Claude: {' → '.join(behavioral['tool_sequence']['claude']) if behavioral['tool_sequence']['claude'] else 'None'}")
        print(f"  LLaMA:  {' → '.join(behavioral['tool_sequence']['llama']) if behavioral['tool_sequence']['llama'] else 'None'}")
        print(f"  Match:  {behavioral['tool_sequence']['divergence']}")

        print(f"\n🧠 Reasoning Depth:")
        print(f"  Claude: {behavioral['reasoning_depth']['claude_steps']} steps")
        print(f"  LLaMA:  {behavioral['reasoning_depth']['llama_steps']} steps")
        print(f"  Status: {behavioral['reasoning_depth']['divergence']}")

        print(f"\n🚧 Constraint Detection:")
        print(f"  Claude: {behavioral['constraint_detection']['claude_count']} constraints")
        print(f"  LLaMA:  {behavioral['constraint_detection']['llama_count']} constraints")
        print(f"  Status: {behavioral['constraint_detection']['divergence']}")

        print(f"\n🔄 Self-Correction:")
        print(f"  Claude: {behavioral['self_correction']['claude_count']} corrections")
        print(f"  LLaMA:  {behavioral['self_correction']['llama_count']} corrections")

        print(f"\n🔍 Exploration Depth:")
        print(f"  Claude: {behavioral['exploration_depth']['claude']}")
        print(f"  LLaMA:  {behavioral['exploration_depth']['llama']}")
        print(f"  Status: {behavioral['exploration_depth']['divergence']}")

        print(f"\n📊 Overall Behavioral Similarity: {behavioral['overall_similarity']:.1%}")
        print(f"📝 Text Overlap: {comparison['text_similarity']['word_overlap']:.1%}")

        print(f"\n{'─'*70}")
        if comparison['should_train']:
            print(f"🎯 TRAINING NEEDED")
            print(f"   Reasons:")
            for reason in comparison['training_reason']:
                print(f"   • {reason}")
        else:
            print(f"✅ PATTERNS MATCH - No training needed")
        print(f"{'─'*70}")

        return comparison

    def run_batch(self, prompts: List[str], max_prompts: int = None):
        """
        Run batch of prompts through parallel comparison.

        Args:
            prompts: List of prompts to run
            max_prompts: Optional limit on number of prompts
        """
        if max_prompts:
            prompts = prompts[:max_prompts]

        print(f"\n{'='*70}")
        print(f" Automated Parallel Runner - Batch Mode")
        print(f"{'='*70}")
        print(f"Running {len(prompts)} prompts through Claude + LLaMA\n")

        results = []
        divergent_count = 0

        for i, prompt in enumerate(prompts, 1):
            print(f"\n[{i}/{len(prompts)}] Processing...")

            try:
                comparison = self.run_parallel_comparison(prompt)
                results.append(comparison)

                if comparison["should_train"]:
                    divergent_count += 1

            except Exception as e:
                logger.error(f"Error processing prompt: {e}")
                continue

        # Print summary
        print(f"\n{'='*70}")
        print(f" Batch Complete")
        print(f"{'='*70}")
        print(f"Total prompts:     {len(results)}")
        print(f"Divergent:         {divergent_count}")
        print(f"DPO pairs created: {divergent_count}")
        print(f"Training ready:    {divergent_count > 0}")
        print()

        if divergent_count > 0:
            print(f"Next step: Train LLaMA on DPO pairs:")
            print(f"  ./run.sh train --phase ppo")

        return results


# Command Center specific prompt generator
def generate_command_center_prompts(count: int = 50) -> List[str]:
    """Generate Command Center database prompts."""

    prompts = [
        # Equipment queries
        "What's the average power consumption of chiller_001 in the last 24 hours?",
        "Show me the current status of all 6 DG sets",
        "Compare efficiency of transformer trf_001 vs trf_002 today",
        "List all equipment in fault state right now",
        "What's the total energy consumption for July 2024?",

        # Anomaly detection
        "Find temperature anomalies in chiller_003 for last week",
        "Detect power spikes in transformer trf_002 yesterday",
        "Show motor_005 vibration trends for the past month",
        "Identify unusual runtime patterns for DG sets",

        # Maintenance
        "When was the last maintenance for chiller_001?",
        "Show maintenance history for all transformers",
        "Which equipment needs maintenance in the next 30 days?",
        "Calculate MTBF for motor_001 to motor_015",

        # Real-time monitoring
        "What's the current power factor across all LT panels?",
        "Display real-time cooling tower temperatures",
        "Show UPS battery status for all 8 units",
        "What alerts have been triggered in the last hour?",

        # Data aggregation
        "Calculate hourly averages for chiller_001 on June 15, 2024",
        "Show daily peak demand for all transformers in Q2 2024",
        "Aggregate monthly energy by building",
        "Create a weekly summary for all AHUs",

        # Optimization
        "What's the optimal chiller staging to minimize cost?",
        "When should we switch from grid to DG?",
        "Show the load curve for all transformers combined",
        "Calculate ROI of different chiller setpoints",

        # Schema queries
        "Show me the schema of lt_mcc_001 table",
        "List all 357 equipment tables",
        "What columns are in the alerts table?",
        "Show relationships between buildings and equipment",

        # Predictive maintenance
        "Predict next chiller filter change based on pressure drop trend",
        "When will motor_003 bearings need replacement?",
        "Forecast transformer oil testing schedule",
        "Show equipment health scores across all tables",
    ]

    # Repeat to reach desired count
    while len(prompts) < count:
        prompts.extend(prompts[:count - len(prompts)])

    return prompts[:count]


def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Automated parallel Claude vs LLaMA runner"
    )
    parser.add_argument(
        "--prompt",
        help="Single prompt to run"
    )
    parser.add_argument(
        "--batch",
        type=int,
        help="Run batch of N prompts"
    )
    parser.add_argument(
        "--llama-model",
        default="cc-claude-agent:latest",
        help="LLaMA model name in Ollama"
    )

    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    # Create runner
    runner = AutomatedRunner(llama_model=args.llama_model)

    if args.prompt:
        # Single prompt
        runner.run_parallel_comparison(args.prompt)

    elif args.batch:
        # Batch mode
        prompts = generate_command_center_prompts(args.batch)
        runner.run_batch(prompts, max_prompts=args.batch)

    else:
        print("Usage:")
        print("  Single: python automated_runner.py --prompt 'your prompt'")
        print("  Batch:  python automated_runner.py --batch 50")


if __name__ == "__main__":
    main()
