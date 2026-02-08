"""
Enhanced Extractor - Maximum Signal Extraction from Claude Responses

Implements extraction logic for all signals defined in enhanced_extraction.py.

Extraction strategies:
1. Regex pattern matching for explicit statements
2. Heuristic analysis of response structure
3. Tool usage pattern detection
4. Response formatting analysis
5. Behavioral pattern inference
"""

import re
from typing import List, Optional, Tuple
from datetime import datetime
import numpy as np

from enhanced_extraction import (
    AssumptionType, AssumptionStatement,
    ValidationCheckType, ErrorValidationCheck,
    CounterfactualPath, EditHistoryEntry,
    ProvenanceRecord, SafetyLevel, SafetySignal,
    PreferenceRanking, SelfCritique,
    TokenConfidence, ReasoningVector,
    EnhancedReasoningSignals
)
from claude_trace_schema import ClaudeTrace, ExplorationDepth


class EnhancedSignalExtractor:
    """
    Extracts all possible signals from Claude responses.

    Implements maximum extraction as defined in MAXIMUM_EXTRACTION.md.
    """

    def __init__(self):
        # Assumption patterns
        self.assumption_patterns = [
            (r"(?:i'?m |i )assum(?:e|ing)\s+(.+?)(?:\.|$)", AssumptionType.USER_INTENT),
            (r"(?:presuming|supposing)\s+(?:that )?(.+?)(?:\.|$)", AssumptionType.SYSTEM_STATE),
            (r"if (?:we |i )?assume\s+(.+?)(?:\.|$)", AssumptionType.CONSTRAINT),
            (r"taking for granted\s+(?:that )?(.+?)(?:\.|$)", AssumptionType.DATA_PROPERTY),
        ]

        # Validation patterns
        self.validation_patterns = [
            (r"let me (?:verify|check|validate)\s+(.+?)(?:\.|$)", ValidationCheckType.LOGIC),
            (r"(?:checking|verifying)\s+(?:the )?(.+?)(?:\.|$)", ValidationCheckType.DATA),
            (r"to ensure\s+(.+?)(?:\.|$)", ValidationCheckType.LOGIC),
            (r"validat(?:e|ing)\s+(.+?)(?:\.|$)", ValidationCheckType.SYNTAX),
        ]

        # Counterfactual patterns
        self.counterfactual_patterns = [
            r"i could (?:use |do |try )?(.+?)[,\.]?\s+but\s+(.+?)(?:\.|$)",
            r"(?:another|alternative) (?:approach|option|way)\s+(?:would be|is)\s+(.+?)[,\.]?\s+(?:but|however)\s+(.+?)(?:\.|$)",
            r"instead of\s+(.+?)[,\s]+(?:i'?ll|we'?ll)\s+(.+?)(?:\.|$)",
        ]

        # Safety patterns
        self.safety_patterns = [
            (r"(?:cannot|can't|won't)\s+(.+?)\s+(?:as|because|since)\s+(.+?)(?:\.|$)", SafetyLevel.REFUSE),
            (r"(?:caution|careful|warning)[:]\s*(.+?)(?:\.|$)", SafetyLevel.CAUTION),
            (r"(?:should|need to) (?:review|check)\s+(.+?)(?:\.|$)", SafetyLevel.REVIEW),
        ]

        # Confidence indicators
        self.high_confidence_words = ["definitely", "certainly", "clearly", "obviously", "confirmed"]
        self.low_confidence_words = ["might", "maybe", "possibly", "perhaps", "unclear", "uncertain"]
        self.medium_confidence_words = ["probably", "likely", "seems", "appears"]

    def extract_assumptions(self, claude_response: str) -> List[AssumptionStatement]:
        """Extract explicit assumption statements from response."""
        assumptions = []
        step_number = 0

        for pattern, assumption_type in self.assumption_patterns:
            matches = re.finditer(pattern, claude_response, re.IGNORECASE)
            for match in matches:
                assumption_text = match.group(1).strip()

                # Estimate confidence based on language
                confidence = 0.7  # Default
                if any(word in claude_response.lower() for word in self.high_confidence_words):
                    confidence = 0.9
                elif any(word in claude_response.lower() for word in self.low_confidence_words):
                    confidence = 0.4

                assumptions.append(AssumptionStatement(
                    assumption=assumption_text,
                    assumption_type=assumption_type,
                    reasoning="Inferred from explicit statement",
                    confidence=confidence,
                    consequences="Unknown - not explicitly stated",
                    step_number=step_number
                ))
                step_number += 1

        return assumptions

    def extract_validation_checks(self, claude_response: str) -> List[ErrorValidationCheck]:
        """Extract self-validation checks from response."""
        checks = []
        step_number = 0

        for pattern, check_type in self.validation_patterns:
            matches = re.finditer(pattern, claude_response, re.IGNORECASE)
            for match in matches:
                check_desc = match.group(1).strip()

                # Infer if check passed based on context
                # Look for success/failure indicators nearby
                context = claude_response[max(0, match.start()-100):min(len(claude_response), match.end()+100)]
                passed = not any(word in context.lower() for word in ["error", "failed", "incorrect", "wrong"])

                checks.append(ErrorValidationCheck(
                    check_type=check_type,
                    check_description=check_desc,
                    passed=passed,
                    details="Inferred from validation statement",
                    remediation=None,
                    step_number=step_number
                ))
                step_number += 1

        return checks

    def extract_counterfactuals(self, claude_response: str) -> List[CounterfactualPath]:
        """Extract alternative approaches considered but rejected."""
        counterfactuals = []

        for pattern in self.counterfactual_patterns:
            matches = re.finditer(pattern, claude_response, re.IGNORECASE)
            for match in matches:
                if len(match.groups()) >= 2:
                    alternative = match.group(1).strip()
                    rejection_reason = match.group(2).strip()

                    counterfactuals.append(CounterfactualPath(
                        alternative_approach=alternative,
                        pros=["Considered as viable option"],
                        cons=[rejection_reason],
                        rejection_reason=rejection_reason,
                        estimated_effort="medium",
                        chosen_instead="Current approach"
                    ))

        return counterfactuals

    def extract_provenance(self, trace: ClaudeTrace) -> List[ProvenanceRecord]:
        """Extract sources/documents referenced during problem-solving."""
        provenance = []

        for tool_call in trace.tool_calls:
            if tool_call.tool == "Read":
                file_path = tool_call.args.get("file_path", "")
                snippet = tool_call.output[:200] if tool_call.output else None

                provenance.append(ProvenanceRecord(
                    source_type="file",
                    source_id=file_path,
                    snippet=snippet,
                    relevance_score=1.0,
                    timestamp=tool_call.timestamp,
                    retrieval_method="Read"
                ))

            elif tool_call.tool == "Grep":
                path = tool_call.args.get("path", "")
                pattern = tool_call.args.get("pattern", "")

                provenance.append(ProvenanceRecord(
                    source_type="search",
                    source_id=f"{path}:{pattern}",
                    snippet=tool_call.output[:200] if tool_call.output else None,
                    relevance_score=0.8,
                    timestamp=tool_call.timestamp,
                    retrieval_method="Grep"
                ))

            elif tool_call.tool == "WebSearch":
                query = tool_call.args.get("query", "")

                provenance.append(ProvenanceRecord(
                    source_type="web",
                    source_id=query,
                    snippet=tool_call.output[:200] if tool_call.output else None,
                    relevance_score=0.7,
                    timestamp=tool_call.timestamp,
                    retrieval_method="WebSearch"
                ))

        return provenance

    def extract_safety_signals(self, claude_response: str) -> List[SafetySignal]:
        """Extract safety concerns or refusal signals."""
        safety_signals = []

        for pattern, safety_level in self.safety_patterns:
            matches = re.finditer(pattern, claude_response, re.IGNORECASE)
            for match in matches:
                action = match.group(1).strip() if len(match.groups()) >= 1 else "unknown action"
                reason = match.group(2).strip() if len(match.groups()) >= 2 else "safety concern"

                safety_signals.append(SafetySignal(
                    safety_level=safety_level,
                    category="inferred",
                    concern=f"Identified potential issue with: {action}",
                    boundary_reason=reason,
                    suggested_alternative=None,
                    refused=(safety_level == SafetyLevel.REFUSE)
                ))

        return safety_signals

    def extract_self_critique(self, claude_response: str, trace: ClaudeTrace) -> Optional[SelfCritique]:
        """
        Extract self-evaluation signals from response.

        Analyzes confidence indicators and quality signals.
        """
        # Confidence estimation
        high_conf_count = sum(1 for word in self.high_confidence_words if word in claude_response.lower())
        low_conf_count = sum(1 for word in self.low_confidence_words if word in claude_response.lower())

        confidence_level = 0.7  # Default
        if high_conf_count > low_conf_count:
            confidence_level = 0.85
        elif low_conf_count > high_conf_count:
            confidence_level = 0.4

        # Quality indicators
        has_code_blocks = "```" in claude_response
        has_examples = "example:" in claude_response.lower() or "for instance" in claude_response.lower()
        has_explanation = len(claude_response) > 200  # Detailed response

        overall_quality = 0.7  # Base quality
        if has_code_blocks:
            overall_quality += 0.1
        if has_examples:
            overall_quality += 0.1
        if has_explanation:
            overall_quality += 0.1
        overall_quality = min(1.0, overall_quality)

        # Strengths and weaknesses (heuristic)
        strengths = []
        if trace.reasoning_signals and trace.reasoning_signals.multi_step_reasoning:
            strengths.append("Multi-step problem decomposition")
        if len(trace.tool_calls) > 0:
            strengths.append("Appropriate tool usage")
        if has_examples:
            strengths.append("Provided examples")

        weaknesses = []
        uncertainty_sources = []
        if low_conf_count > 0:
            weaknesses.append("Some uncertainty in conclusions")
            uncertainty_sources.append("Incomplete information or ambiguous requirements")

        return SelfCritique(
            overall_quality=overall_quality,
            strengths=strengths,
            weaknesses=weaknesses,
            confidence_level=confidence_level,
            uncertainty_sources=uncertainty_sources,
            improvement_suggestions=[]
        )

    def build_reasoning_vector(self, trace: ClaudeTrace, enhanced_signals: EnhancedReasoningSignals) -> ReasoningVector:
        """
        Build numeric reasoning vector from trace.

        35-dimensional vector capturing all behavioral patterns.
        """
        rs = trace.reasoning_signals
        if not rs:
            # Return minimal vector if no reasoning signals
            return self._minimal_vector()

        # Exploration depth to score
        depth_map = {
            ExplorationDepth.MINIMAL: 0.25,
            ExplorationDepth.MODERATE: 0.5,
            ExplorationDepth.THOROUGH: 0.75,
            ExplorationDepth.EXHAUSTIVE: 1.0
        }
        exploration_score = depth_map.get(rs.exploration_depth, 0.5)

        # User feedback to score
        feedback_map = {"up": 1.0, "down": 0.0, None: 0.5}
        feedback_score = feedback_map.get(trace.user_feedback, 0.5)

        # Response time normalization (assume max 10000ms)
        time_normalized = min(1.0, trace.response_time_ms / 10000.0)

        # Response length normalization (assume max 5000 chars)
        length_normalized = min(1.0, len(trace.claude_response) / 5000.0)

        # Code blocks count
        code_blocks = trace.claude_response.count("```") // 2

        # Quality scores (computed from behavioral patterns)
        constraint_adherence = min(1.0, len(rs.constraints_detected) / 5.0)
        reasoning_depth_score = min(1.0, rs.reasoning_steps / 10.0)
        tool_efficiency = min(1.0, len(trace.tool_calls) / 8.0)
        self_correction_score = min(1.0, len(rs.self_corrections) / 3.0)
        exploration_fit = exploration_score  # Already normalized

        # New extraction scores
        assumption_clarity = min(1.0, len(enhanced_signals.assumptions) / 5.0)
        validation_completeness = min(1.0, len(enhanced_signals.validation_checks) / 5.0)
        counterfactual_consideration = min(1.0, len(enhanced_signals.counterfactual_paths) / 3.0)

        # Overall confidence (from critique or default)
        overall_confidence = enhanced_signals.self_critique.confidence_level if enhanced_signals.self_critique else 0.7

        return ReasoningVector(
            # Behavioral (15 dims)
            num_reasoning_steps=rs.reasoning_steps,
            exploration_depth_score=exploration_score,
            num_tool_calls=len(trace.tool_calls),
            num_constraints_detected=len(rs.constraints_detected),
            num_self_corrections=len(rs.self_corrections),
            num_tools_pruned=len(rs.tools_pruned),
            num_assumptions_made=len(enhanced_signals.assumptions),
            num_validation_checks=len(enhanced_signals.validation_checks),
            num_counterfactual_paths=len(enhanced_signals.counterfactual_paths),
            multi_step_reasoning=1.0 if rs.multi_step_reasoning else 0.0,
            used_rag=1.0 if rs.used_rag else 0.0,
            used_terminal=1.0 if rs.used_terminal else 0.0,
            used_web_search=1.0 if rs.used_web_search else 0.0,
            parallel_tool_execution=1.0 if len(rs.parallel_tools) > 0 else 0.0,
            explicit_planning=1.0 if rs.explicit_plan else 0.0,

            # Quality (10 dims)
            constraint_adherence_score=constraint_adherence,
            reasoning_depth_score=reasoning_depth_score,
            tool_efficiency_score=tool_efficiency,
            self_correction_score=self_correction_score,
            exploration_fit_score=exploration_fit,
            assumption_clarity_score=assumption_clarity,
            validation_completeness_score=validation_completeness,
            counterfactual_consideration_score=counterfactual_consideration,
            overall_confidence=overall_confidence,
            task_success=1.0 if trace.task_completed else 0.0,

            # Metadata (10 dims)
            response_time_normalized=time_normalized,
            response_length_normalized=length_normalized,
            code_blocks_count=code_blocks,
            markdown_formatting=1.0 if ("**" in trace.claude_response or "##" in trace.claude_response) else 0.0,
            json_structured_output=1.0 if trace.response_format == "json" else 0.0,
            error_encountered=1.0 if len(trace.errors_encountered) > 0 else 0.0,
            user_feedback_positive=feedback_score,
            safety_concerns_raised=len(enhanced_signals.safety_signals),
            provenance_citations=len(enhanced_signals.provenance),
            edit_history_length=len(enhanced_signals.edit_history)
        )

    def _minimal_vector(self) -> ReasoningVector:
        """Return minimal vector when no reasoning signals available."""
        return ReasoningVector(
            num_reasoning_steps=0, exploration_depth_score=0.0, num_tool_calls=0,
            num_constraints_detected=0, num_self_corrections=0, num_tools_pruned=0,
            num_assumptions_made=0, num_validation_checks=0, num_counterfactual_paths=0,
            multi_step_reasoning=0.0, used_rag=0.0, used_terminal=0.0, used_web_search=0.0,
            parallel_tool_execution=0.0, explicit_planning=0.0,
            constraint_adherence_score=0.0, reasoning_depth_score=0.0, tool_efficiency_score=0.0,
            self_correction_score=0.0, exploration_fit_score=0.0, assumption_clarity_score=0.0,
            validation_completeness_score=0.0, counterfactual_consideration_score=0.0,
            overall_confidence=0.5, task_success=0.0,
            response_time_normalized=0.5, response_length_normalized=0.5, code_blocks_count=0,
            markdown_formatting=0.0, json_structured_output=0.0, error_encountered=0.0,
            user_feedback_positive=0.5, safety_concerns_raised=0, provenance_citations=0,
            edit_history_length=0
        )

    def extract_all(self, trace: ClaudeTrace) -> EnhancedReasoningSignals:
        """
        Extract ALL enhanced signals from a trace.

        This is the main entry point for maximum extraction.
        """
        response = trace.claude_response

        # Extract all signals
        assumptions = self.extract_assumptions(response)
        validation_checks = self.extract_validation_checks(response)
        counterfactuals = self.extract_counterfactuals(response)
        provenance = self.extract_provenance(trace)
        safety_signals = self.extract_safety_signals(response)
        self_critique = self.extract_self_critique(response, trace)

        # Build enhanced signals object
        enhanced = EnhancedReasoningSignals(
            assumptions=assumptions,
            validation_checks=validation_checks,
            counterfactual_paths=counterfactuals,
            edit_history=[],  # Requires multi-turn tracking
            provenance=provenance,
            safety_signals=safety_signals,
            preference_rankings=[],  # Requires specific prompting
            self_critique=self_critique,
            token_confidence=None,  # Requires API access to logprobs
            reasoning_vector=None  # Will be computed below
        )

        # Build reasoning vector
        enhanced.reasoning_vector = self.build_reasoning_vector(trace, enhanced)

        return enhanced


# Usage example
def enhance_trace_with_maximum_extraction(trace: ClaudeTrace) -> EnhancedReasoningSignals:
    """
    Apply maximum extraction to a trace.

    Args:
        trace: Base ClaudeTrace with basic signals

    Returns:
        EnhancedReasoningSignals with all possible extractions
    """
    extractor = EnhancedSignalExtractor()
    return extractor.extract_all(trace)


__all__ = ["EnhancedSignalExtractor", "enhance_trace_with_maximum_extraction"]
