#!/usr/bin/env python3
"""
Behavioral Reward Model

Scores LLaMA-generated workflows based on behavioral quality metrics:
- Constraint adherence
- Reasoning depth
- Tool efficiency
- Self-correction presence
- Exploration appropriateness
"""

import torch
import torch.nn as nn
from typing import List, Dict, Tuple
from dataclasses import dataclass
import logging

from claude_trace_schema import ClaudeTrace, ReasoningSignals

logger = logging.getLogger(__name__)


@dataclass
class RewardComponents:
    """Individual reward components for workflow quality."""
    constraint_adherence: float  # 0-1: Did it respect constraints?
    reasoning_depth: float  # 0-1: How thorough was the reasoning?
    tool_efficiency: float  # 0-1: Were tools used appropriately?
    self_correction: float  # 0-1: Did it self-correct when needed?
    exploration_fit: float  # 0-1: Was exploration depth appropriate?

    total_reward: float  # Weighted sum

    def to_dict(self) -> Dict[str, float]:
        return {
            "constraint_adherence": self.constraint_adherence,
            "reasoning_depth": self.reasoning_depth,
            "tool_efficiency": self.tool_efficiency,
            "self_correction": self.self_correction,
            "exploration_fit": self.exploration_fit,
            "total_reward": self.total_reward,
        }


class BehavioralRewardModel:
    """
    Lightweight reward model for scoring workflow quality.

    Unlike typical RM that needs a neural network, this uses rule-based
    heuristics combined with learned weights to score behavioral patterns.
    """

    def __init__(self, weights: Dict[str, float] = None):
        # Default weights for reward components
        self.weights = weights or {
            "constraint_adherence": 0.25,
            "reasoning_depth": 0.20,
            "tool_efficiency": 0.20,
            "self_correction": 0.15,
            "exploration_fit": 0.20,
        }

        # Normalize weights to sum to 1.0
        total = sum(self.weights.values())
        self.weights = {k: v/total for k, v in self.weights.items()}

    def compute_reward(
        self,
        reasoning_signals: ReasoningSignals,
        task_complexity: str = "medium"
    ) -> RewardComponents:
        """Compute reward for a generated workflow."""

        # 1. Constraint adherence
        constraint_score = self._score_constraints(reasoning_signals)

        # 2. Reasoning depth
        reasoning_score = self._score_reasoning_depth(
            reasoning_signals,
            task_complexity
        )

        # 3. Tool efficiency
        tool_score = self._score_tool_efficiency(reasoning_signals)

        # 4. Self-correction
        correction_score = self._score_self_correction(reasoning_signals)

        # 5. Exploration fit
        exploration_score = self._score_exploration_fit(
            reasoning_signals,
            task_complexity
        )

        # Compute weighted total
        total_reward = (
            self.weights["constraint_adherence"] * constraint_score +
            self.weights["reasoning_depth"] * reasoning_score +
            self.weights["tool_efficiency"] * tool_score +
            self.weights["self_correction"] * correction_score +
            self.weights["exploration_fit"] * exploration_score
        )

        return RewardComponents(
            constraint_adherence=constraint_score,
            reasoning_depth=reasoning_score,
            tool_efficiency=tool_score,
            self_correction=correction_score,
            exploration_fit=exploration_score,
            total_reward=total_reward,
        )

    def _score_constraints(self, signals: ReasoningSignals) -> float:
        """Score constraint detection and adherence."""
        if not signals.constraints_detected:
            return 0.5  # Neutral - no constraints detected

        # More constraints detected = better awareness
        num_constraints = len(signals.constraints_detected)

        # Check for explicit constraint handling
        has_explicit_handling = any(
            c.handling_strategy is not None
            for c in signals.constraints_detected
        )

        # Score: 0.6 base + 0.2 for multiple constraints + 0.2 for explicit handling
        score = 0.6
        if num_constraints > 1:
            score += 0.2
        if has_explicit_handling:
            score += 0.2

        return min(score, 1.0)

    def _score_reasoning_depth(
        self,
        signals: ReasoningSignals,
        task_complexity: str
    ) -> float:
        """Score reasoning depth appropriateness."""
        steps = signals.reasoning_steps

        # Expected steps by complexity
        complexity_thresholds = {
            "simple": (1, 3),    # 1-3 steps
            "medium": (3, 6),    # 3-6 steps
            "complex": (6, 12),  # 6-12 steps
        }

        min_steps, max_steps = complexity_thresholds.get(
            task_complexity,
            (3, 6)
        )

        # Score based on step count fit
        if steps < min_steps:
            return 0.3  # Too shallow
        elif steps > max_steps * 1.5:
            return 0.6  # Too verbose
        elif min_steps <= steps <= max_steps:
            return 1.0  # Perfect fit
        else:
            return 0.8  # Slightly over but acceptable

    def _score_tool_efficiency(self, signals: ReasoningSignals) -> float:
        """Score tool usage efficiency."""
        tool_sequence = signals.tool_sequence

        if not tool_sequence:
            return 0.4  # No tools used (might be appropriate)

        # Check for tool variety (not just repeating same tool)
        unique_tools = len(set(tool_sequence))
        tool_diversity = unique_tools / len(tool_sequence)

        # Check for logical tool ordering
        # Good patterns: Read → Grep → Bash → Edit
        # Bad patterns: Edit → Read → Edit (redundant)
        has_logical_flow = self._check_tool_flow(tool_sequence)

        # Score: 0.5 base + 0.25 for diversity + 0.25 for logical flow
        score = 0.5 + (tool_diversity * 0.25)
        if has_logical_flow:
            score += 0.25

        return min(score, 1.0)

    def _check_tool_flow(self, tools: List[str]) -> bool:
        """Check if tool sequence follows logical patterns."""
        # Good patterns
        good_patterns = [
            ["Read", "Grep"],      # Read then search
            ["Grep", "Read"],      # Search then read matches
            ["Read", "Edit"],      # Read then modify
            ["Bash", "Read"],      # Run command then check result
        ]

        # Check for any good pattern
        for i in range(len(tools) - 1):
            pair = [tools[i], tools[i+1]]
            if pair in good_patterns:
                return True

        # Check for bad patterns (immediate repetition)
        for i in range(len(tools) - 1):
            if tools[i] == tools[i+1]:
                return False  # Redundant tool calls

        return True  # Neutral

    def _score_self_correction(self, signals: ReasoningSignals) -> float:
        """Score self-correction behavior."""
        corrections = signals.self_corrections

        if not corrections:
            return 0.7  # No corrections needed (good or bad?)

        # Check correction types
        has_approach_correction = any(
            c.correction_type == "approach_revision"
            for c in corrections
        )
        has_error_correction = any(
            c.correction_type == "error_recovery"
            for c in corrections
        )

        # Score: 0.7 base + 0.15 for approach + 0.15 for error
        score = 0.7
        if has_approach_correction:
            score += 0.15
        if has_error_correction:
            score += 0.15

        return min(score, 1.0)

    def _score_exploration_fit(
        self,
        signals: ReasoningSignals,
        task_complexity: str
    ) -> float:
        """Score exploration depth appropriateness."""
        exploration = signals.exploration_depth

        # Expected exploration by complexity
        expected = {
            "simple": "minimal",
            "medium": "moderate",
            "complex": "thorough",
        }

        expected_depth = expected.get(task_complexity, "moderate")

        # Score based on match
        if exploration == expected_depth:
            return 1.0  # Perfect match

        # Exploration levels: minimal < moderate < thorough < exhaustive
        levels = ["minimal", "moderate", "thorough", "exhaustive"]

        try:
            actual_idx = levels.index(exploration)
            expected_idx = levels.index(expected_depth)
            diff = abs(actual_idx - expected_idx)

            if diff == 1:
                return 0.7  # One level off
            elif diff == 2:
                return 0.4  # Two levels off
            else:
                return 0.2  # Far off
        except ValueError:
            return 0.5  # Unknown level

    def compare_traces(
        self,
        claude_trace: ClaudeTrace,
        llama_trace: ClaudeTrace,
    ) -> Tuple[RewardComponents, RewardComponents, float]:
        """
        Compare Claude vs LLaMA traces.

        Returns:
            (claude_reward, llama_reward, similarity_score)
        """
        # Compute rewards for both
        claude_reward = self.compute_reward(claude_trace.reasoning_signals)
        llama_reward = self.compute_reward(llama_trace.reasoning_signals)

        # Compute similarity (0-1, higher = more similar)
        similarity = self._compute_similarity(claude_reward, llama_reward)

        return claude_reward, llama_reward, similarity

    def _compute_similarity(
        self,
        reward1: RewardComponents,
        reward2: RewardComponents
    ) -> float:
        """Compute similarity between two reward profiles."""
        # Compare each component
        components = [
            "constraint_adherence",
            "reasoning_depth",
            "tool_efficiency",
            "self_correction",
            "exploration_fit",
        ]

        similarities = []
        for comp in components:
            val1 = getattr(reward1, comp)
            val2 = getattr(reward2, comp)
            # Similarity = 1 - absolute difference
            sim = 1.0 - abs(val1 - val2)
            similarities.append(sim)

        # Average similarity across components
        return sum(similarities) / len(similarities)


class LearnableRewardModel(nn.Module):
    """
    Neural network-based reward model (optional, for future use).

    Can be trained on human preferences if we collect pairwise comparisons.
    For now, we use the rule-based BehavioralRewardModel.
    """

    def __init__(self, hidden_dim: int = 256):
        super().__init__()

        # Input: encoded reasoning signals (fixed-size vector)
        # Output: scalar reward

        self.encoder = nn.Sequential(
            nn.Linear(128, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(hidden_dim, 1),  # Scalar reward
        )

    def forward(self, reasoning_features: torch.Tensor) -> torch.Tensor:
        """
        Args:
            reasoning_features: (batch_size, 128) encoded reasoning signals

        Returns:
            rewards: (batch_size, 1) scalar rewards
        """
        return self.encoder(reasoning_features)


def main():
    """Demo reward model scoring."""
    from claude_trace_schema import (
        ReasoningSignals,
        ConstraintDetection,
        SelfCorrection,
    )

    # Example signals
    signals = ReasoningSignals(
        tool_sequence=["Read", "Grep", "Bash", "Edit"],
        reasoning_steps=5,
        exploration_depth="moderate",
        constraints_detected=[
            ConstraintDetection(
                constraint_type="file_exists",
                description="Must check if file exists before editing",
                handling_strategy="Read first, then Edit"
            )
        ],
        pruning_decisions=[],
        self_corrections=[
            SelfCorrection(
                original_approach="Direct edit",
                corrected_approach="Read first to verify content",
                correction_type="approach_revision",
                trigger="Realized need to check current state"
            )
        ],
    )

    # Score it
    rm = BehavioralRewardModel()
    reward = rm.compute_reward(signals, task_complexity="medium")

    print("=" * 70)
    print(" Behavioral Reward Model Demo")
    print("=" * 70)
    print()
    print("Workflow Analysis:")
    print(f"  Tools: {' → '.join(signals.tool_sequence)}")
    print(f"  Reasoning steps: {signals.reasoning_steps}")
    print(f"  Exploration: {signals.exploration_depth}")
    print(f"  Constraints detected: {len(signals.constraints_detected)}")
    print(f"  Self-corrections: {len(signals.self_corrections)}")
    print()
    print("Reward Breakdown:")
    print(f"  Constraint adherence: {reward.constraint_adherence:.3f}")
    print(f"  Reasoning depth: {reward.reasoning_depth:.3f}")
    print(f"  Tool efficiency: {reward.tool_efficiency:.3f}")
    print(f"  Self-correction: {reward.self_correction:.3f}")
    print(f"  Exploration fit: {reward.exploration_fit:.3f}")
    print()
    print(f"  TOTAL REWARD: {reward.total_reward:.3f}")
    print()


if __name__ == "__main__":
    main()
