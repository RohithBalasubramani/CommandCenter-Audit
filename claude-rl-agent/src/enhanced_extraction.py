"""
Enhanced Extraction - Maximum Claude Capability Capture

This module implements ALL extractable signals from MAXIMUM_EXTRACTION.md
that were not yet in the base claude_trace_schema.py.

New capabilities:
1. Assumption statements (explicit assumptions Claude makes)
2. Error validation checks (self-checks Claude performs)
3. Counterfactual paths (alternatives Claude considered)
4. Edit history (changes across conversation turns)
5. Provenance tracking (sources/documents referenced)
6. Safety/refusal signals (safety boundaries)
7. Preference rankings (comparing alternatives)
8. Critique generation (self-evaluation)
9. Numeric reasoning vectors (vectorized behavioral patterns)
10. Token-level confidence (per-token uncertainty)
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
import numpy as np
from enum import Enum


class AssumptionType(Enum):
    """Types of assumptions Claude might make."""
    SYSTEM_STATE = "system_state"  # "Assuming the database is running"
    DATA_PROPERTY = "data_property"  # "Assuming the data is in UTC"
    USER_INTENT = "user_intent"  # "Assuming you want real-time data"
    ENVIRONMENT = "environment"  # "Assuming Python 3.8+"
    CONSTRAINT = "constraint"  # "Assuming memory is limited"


@dataclass
class AssumptionStatement:
    """
    Explicit assumption Claude makes during problem-solving.

    Example: "I'm assuming the database connection uses default port 5432"
    """
    assumption: str  # What is assumed
    assumption_type: AssumptionType
    reasoning: str  # Why this assumption was made
    confidence: float  # 0.0-1.0, how certain Claude is
    consequences: str  # What happens if assumption is wrong
    step_number: int  # When in workflow this was assumed

    def to_dict(self) -> dict:
        return {
            "assumption": self.assumption,
            "assumption_type": self.assumption_type.value,
            "reasoning": self.reasoning,
            "confidence": self.confidence,
            "consequences": self.consequences,
            "step_number": self.step_number
        }


class ValidationCheckType(Enum):
    """Types of self-validation checks."""
    SYNTAX = "syntax"  # Code syntax validation
    TYPE = "type"  # Type checking
    LOGIC = "logic"  # Logical consistency
    DATA = "data"  # Data integrity
    SECURITY = "security"  # Security checks
    PERFORMANCE = "performance"  # Performance checks


@dataclass
class ErrorValidationCheck:
    """
    Self-check that Claude performs to validate correctness.

    Example: "Let me verify this SQL query syntax..."
    """
    check_type: ValidationCheckType
    check_description: str  # What is being checked
    passed: bool  # Did check pass?
    details: str  # Check results or error details
    remediation: Optional[str] = None  # How Claude fixed it if failed
    step_number: int = 0

    def to_dict(self) -> dict:
        return {
            "check_type": self.check_type.value,
            "check_description": self.check_description,
            "passed": self.passed,
            "details": self.details,
            "remediation": self.remediation,
            "step_number": self.step_number
        }


@dataclass
class CounterfactualPath:
    """
    Alternative approach Claude considered but rejected.

    Example: "I could use grep, but a Python script would be more flexible..."
    """
    alternative_approach: str  # What was considered
    pros: List[str]  # Benefits of this approach
    cons: List[str]  # Drawbacks
    rejection_reason: str  # Why Claude chose not to use it
    estimated_effort: str  # "low", "medium", "high"
    chosen_instead: str  # What was chosen instead

    def to_dict(self) -> dict:
        return {
            "alternative_approach": self.alternative_approach,
            "pros": self.pros,
            "cons": self.cons,
            "rejection_reason": self.rejection_reason,
            "estimated_effort": self.estimated_effort,
            "chosen_instead": self.chosen_instead
        }


@dataclass
class EditHistoryEntry:
    """
    A change made during conversation (across multiple turns).

    Tracks how Claude iterates and refines approaches.
    """
    turn_number: int  # Which conversation turn
    what_changed: str  # What was modified
    previous_value: str  # Before
    new_value: str  # After
    change_reason: str  # Why the change
    timestamp: datetime

    def to_dict(self) -> dict:
        return {
            "turn_number": self.turn_number,
            "what_changed": self.what_changed,
            "previous_value": self.previous_value,
            "new_value": self.new_value,
            "change_reason": self.change_reason,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class ProvenanceRecord:
    """
    Source or document that Claude referenced.

    Enables grounding and citation tracking.
    """
    source_type: str  # "file", "url", "database", "memory"
    source_id: str  # File path, URL, table name, etc.
    snippet: Optional[str] = None  # Relevant excerpt (max 200 chars)
    relevance_score: float = 1.0  # How relevant (0.0-1.0)
    timestamp: Optional[datetime] = None
    retrieval_method: str = "unknown"  # "Read", "Grep", "WebSearch", etc.

    def to_dict(self) -> dict:
        return {
            "source_type": self.source_type,
            "source_id": self.source_id,
            "snippet": self.snippet,
            "relevance_score": self.relevance_score,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "retrieval_method": self.retrieval_method
        }


class SafetyLevel(Enum):
    """Safety classification levels."""
    SAFE = "safe"  # No safety concerns
    CAUTION = "caution"  # Proceed with caution
    REVIEW = "review"  # Requires human review
    REFUSE = "refuse"  # Should refuse request


@dataclass
class SafetySignal:
    """
    Safety or refusal signal from Claude.

    Tracks when Claude identifies safety boundaries.
    """
    safety_level: SafetyLevel
    category: str  # "code_execution", "data_access", "system_modification"
    concern: str  # What the safety concern is
    boundary_reason: str  # Why this is a boundary
    suggested_alternative: Optional[str] = None  # Safer alternative
    refused: bool = False  # Did Claude refuse the request?

    def to_dict(self) -> dict:
        return {
            "safety_level": self.safety_level.value,
            "category": self.category,
            "concern": self.concern,
            "boundary_reason": self.boundary_reason,
            "suggested_alternative": self.suggested_alternative,
            "refused": self.refused
        }


@dataclass
class PreferenceRanking:
    """
    Claude's ranking of multiple candidate approaches.

    Example: Ranking different algorithms by suitability.
    """
    candidates: List[str]  # Approaches being ranked
    ranking: List[int]  # Rank order (0 = best)
    criteria: Dict[str, float]  # Scoring criteria {"speed": 0.8, "accuracy": 0.6}
    justification: str  # Why this ranking
    confidence: float = 0.5  # How confident in ranking (0.0-1.0)

    def to_dict(self) -> dict:
        return {
            "candidates": self.candidates,
            "ranking": self.ranking,
            "criteria": self.criteria,
            "justification": self.justification,
            "confidence": self.confidence
        }


@dataclass
class SelfCritique:
    """
    Claude's self-evaluation of its own output.

    Meta-cognition for quality assessment.
    """
    overall_quality: float  # 0.0-1.0
    strengths: List[str]  # What was done well
    weaknesses: List[str]  # What could be improved
    confidence_level: float  # How confident in answer (0.0-1.0)
    uncertainty_sources: List[str]  # What causes uncertainty
    improvement_suggestions: List[str]  # How to improve

    def to_dict(self) -> dict:
        return {
            "overall_quality": self.overall_quality,
            "strengths": self.strengths,
            "weaknesses": self.weaknesses,
            "confidence_level": self.confidence_level,
            "uncertainty_sources": self.uncertainty_sources,
            "improvement_suggestions": self.improvement_suggestions
        }


@dataclass
class TokenConfidence:
    """
    Per-token confidence scores (if available from API).

    Maps token positions to confidence/logprob.
    """
    token_positions: List[int]  # Token indices
    logprobs: List[float]  # Log probabilities
    entropies: List[float]  # Uncertainty per token
    low_confidence_spans: List[tuple]  # (start, end) of uncertain regions

    def to_dict(self) -> dict:
        return {
            "token_positions": self.token_positions,
            "logprobs": self.logprobs,
            "entropies": self.entropies,
            "low_confidence_spans": self.low_confidence_spans
        }


@dataclass
class ReasoningVector:
    """
    Numeric vectorization of Claude's reasoning patterns.

    Fixed-length vector for ML reward model input.
    Components (35 dimensions total):
    """
    # Behavioral patterns (15 dims)
    num_reasoning_steps: int
    exploration_depth_score: float  # 0.0-1.0 (minimal=0.25, moderate=0.5, thorough=0.75, exhaustive=1.0)
    num_tool_calls: int
    num_constraints_detected: int
    num_self_corrections: int
    num_tools_pruned: int
    num_assumptions_made: int
    num_validation_checks: int
    num_counterfactual_paths: int
    multi_step_reasoning: float  # 0.0 or 1.0
    used_rag: float  # 0.0 or 1.0
    used_terminal: float  # 0.0 or 1.0
    used_web_search: float  # 0.0 or 1.0
    parallel_tool_execution: float  # 0.0 or 1.0
    explicit_planning: float  # 0.0 or 1.0

    # Quality indicators (10 dims)
    constraint_adherence_score: float  # 0.0-1.0
    reasoning_depth_score: float  # 0.0-1.0
    tool_efficiency_score: float  # 0.0-1.0
    self_correction_score: float  # 0.0-1.0
    exploration_fit_score: float  # 0.0-1.0
    assumption_clarity_score: float  # 0.0-1.0
    validation_completeness_score: float  # 0.0-1.0
    counterfactual_consideration_score: float  # 0.0-1.0
    overall_confidence: float  # 0.0-1.0
    task_success: float  # 0.0 or 1.0

    # Metadata (10 dims)
    response_time_normalized: float  # Normalized to 0.0-1.0
    response_length_normalized: float  # Normalized to 0.0-1.0
    code_blocks_count: int
    markdown_formatting: float  # 0.0 or 1.0
    json_structured_output: float  # 0.0 or 1.0
    error_encountered: float  # 0.0 or 1.0
    user_feedback_positive: float  # 0.0, 0.5, or 1.0 (down/none/up)
    safety_concerns_raised: int
    provenance_citations: int
    edit_history_length: int

    def to_numpy(self) -> np.ndarray:
        """Convert to numpy array for ML models."""
        return np.array([
            # Behavioral (15)
            float(self.num_reasoning_steps),
            self.exploration_depth_score,
            float(self.num_tool_calls),
            float(self.num_constraints_detected),
            float(self.num_self_corrections),
            float(self.num_tools_pruned),
            float(self.num_assumptions_made),
            float(self.num_validation_checks),
            float(self.num_counterfactual_paths),
            self.multi_step_reasoning,
            self.used_rag,
            self.used_terminal,
            self.used_web_search,
            self.parallel_tool_execution,
            self.explicit_planning,
            # Quality (10)
            self.constraint_adherence_score,
            self.reasoning_depth_score,
            self.tool_efficiency_score,
            self.self_correction_score,
            self.exploration_fit_score,
            self.assumption_clarity_score,
            self.validation_completeness_score,
            self.counterfactual_consideration_score,
            self.overall_confidence,
            self.task_success,
            # Metadata (10)
            self.response_time_normalized,
            self.response_length_normalized,
            float(self.code_blocks_count),
            self.markdown_formatting,
            self.json_structured_output,
            self.error_encountered,
            self.user_feedback_positive,
            float(self.safety_concerns_raised),
            float(self.provenance_citations),
            float(self.edit_history_length)
        ], dtype=np.float32)

    def to_dict(self) -> dict:
        """Serialize to dict."""
        return {
            "num_reasoning_steps": self.num_reasoning_steps,
            "exploration_depth_score": self.exploration_depth_score,
            "num_tool_calls": self.num_tool_calls,
            "num_constraints_detected": self.num_constraints_detected,
            "num_self_corrections": self.num_self_corrections,
            "num_tools_pruned": self.num_tools_pruned,
            "num_assumptions_made": self.num_assumptions_made,
            "num_validation_checks": self.num_validation_checks,
            "num_counterfactual_paths": self.num_counterfactual_paths,
            "multi_step_reasoning": self.multi_step_reasoning,
            "used_rag": self.used_rag,
            "used_terminal": self.used_terminal,
            "used_web_search": self.used_web_search,
            "parallel_tool_execution": self.parallel_tool_execution,
            "explicit_planning": self.explicit_planning,
            "constraint_adherence_score": self.constraint_adherence_score,
            "reasoning_depth_score": self.reasoning_depth_score,
            "tool_efficiency_score": self.tool_efficiency_score,
            "self_correction_score": self.self_correction_score,
            "exploration_fit_score": self.exploration_fit_score,
            "assumption_clarity_score": self.assumption_clarity_score,
            "validation_completeness_score": self.validation_completeness_score,
            "counterfactual_consideration_score": self.counterfactual_consideration_score,
            "overall_confidence": self.overall_confidence,
            "task_success": self.task_success,
            "response_time_normalized": self.response_time_normalized,
            "response_length_normalized": self.response_length_normalized,
            "code_blocks_count": self.code_blocks_count,
            "markdown_formatting": self.markdown_formatting,
            "json_structured_output": self.json_structured_output,
            "error_encountered": self.error_encountered,
            "user_feedback_positive": self.user_feedback_positive,
            "safety_concerns_raised": self.safety_concerns_raised,
            "provenance_citations": self.provenance_citations,
            "edit_history_length": self.edit_history_length
        }


@dataclass
class EnhancedReasoningSignals:
    """
    Extended reasoning signals including all new extraction capabilities.

    This extends the base ReasoningSignals with maximum extraction.
    """
    # New extractions
    assumptions: List[AssumptionStatement] = field(default_factory=list)
    validation_checks: List[ErrorValidationCheck] = field(default_factory=list)
    counterfactual_paths: List[CounterfactualPath] = field(default_factory=list)
    edit_history: List[EditHistoryEntry] = field(default_factory=list)
    provenance: List[ProvenanceRecord] = field(default_factory=list)
    safety_signals: List[SafetySignal] = field(default_factory=list)
    preference_rankings: List[PreferenceRanking] = field(default_factory=list)
    self_critique: Optional[SelfCritique] = None
    token_confidence: Optional[TokenConfidence] = None
    reasoning_vector: Optional[ReasoningVector] = None

    def to_dict(self) -> dict:
        return {
            "assumptions": [a.to_dict() for a in self.assumptions],
            "validation_checks": [v.to_dict() for v in self.validation_checks],
            "counterfactual_paths": [c.to_dict() for c in self.counterfactual_paths],
            "edit_history": [e.to_dict() for e in self.edit_history],
            "provenance": [p.to_dict() for p in self.provenance],
            "safety_signals": [s.to_dict() for s in self.safety_signals],
            "preference_rankings": [r.to_dict() for r in self.preference_rankings],
            "self_critique": self.self_critique.to_dict() if self.self_critique else None,
            "token_confidence": self.token_confidence.to_dict() if self.token_confidence else None,
            "reasoning_vector": self.reasoning_vector.to_dict() if self.reasoning_vector else None
        }


# Export all new types
__all__ = [
    "AssumptionType",
    "AssumptionStatement",
    "ValidationCheckType",
    "ErrorValidationCheck",
    "CounterfactualPath",
    "EditHistoryEntry",
    "ProvenanceRecord",
    "SafetyLevel",
    "SafetySignal",
    "PreferenceRanking",
    "SelfCritique",
    "TokenConfidence",
    "ReasoningVector",
    "EnhancedReasoningSignals"
]
