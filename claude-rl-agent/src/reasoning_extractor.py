"""
Reasoning Signal Extractor for Claude Code Traces

This module extracts latent reasoning patterns from Claude's responses to capture
HOW Claude designs and executes problem-solving workflows, not just what it says.

Key extraction targets:
1. Constraint detection: What limitations did Claude identify?
2. Pruning decisions: What approaches did Claude consider but reject?
3. Self-correction: How did Claude adapt when things didn't work?
4. Tool workflow: What multi-step pipeline did Claude design?
5. Reasoning depth: How thoroughly did Claude explore before answering?

Goal: Train LLaMA to replicate Claude's workflow design capability.
"""

import re
import logging
from typing import List, Optional, Tuple
from datetime import datetime

try:
    from .claude_trace_schema import (
        ClaudeTrace,
        ToolCall,
        ReasoningSignals,
        ConstraintDetection,
        PruningDecision,
        SelfCorrection,
        ExplorationDepth
    )
except ImportError:
    from claude_trace_schema import (
        ClaudeTrace,
        ToolCall,
        ReasoningSignals,
        ConstraintDetection,
        PruningDecision,
        SelfCorrection,
        ExplorationDepth
    )

logger = logging.getLogger(__name__)


class ReasoningSignalExtractor:
    """
    Extracts behavioral reasoning signals from Claude Code traces.

    This is the core of behavioral replication - we need to understand
    HOW Claude approaches problems, not just the final answers.
    """

    # Regex patterns for detecting constraints
    CONSTRAINT_PATTERNS = [
        r"(?:can't|cannot|must not|shouldn't|avoid|limited to|restricted to)",
        r"(?:need to|must|have to|required to|important to)\s+(?:preserve|maintain|keep|ensure)",
        r"(?:without breaking|while preserving|to avoid)",
        r"(?:this would|this will|that might)\s+(?:break|fail|cause issues)"
    ]

    # Patterns for pruning decisions (considered but rejected)
    PRUNING_PATTERNS = [
        r"(?:could use|could|might|alternatively)\s+(\w+),?\s+but\s+(.+)",
        r"(?:instead of|rather than)\s+(.+?),\s+(?:I'll|I will|let me)\s+(.+)",
        r"(?:considered|thought about)\s+(.+?),?\s+but\s+(.+)"
    ]

    # Patterns for self-correction
    SELF_CORRECTION_PATTERNS = [
        r"(?:actually|wait|hold on|let me),?\s+(.+)",
        r"(?:that (?:didn't|won't) work|that failed),?\s+(?:let me|I'll)\s+(.+)",
        r"(?:I need to|I should)\s+(.+?)\s+(?:first|before|instead)"
    ]

    # Patterns for explicit planning
    PLAN_PATTERNS = [
        r"(?:first|1\.|step 1)",
        r"(?:then|next|after that|2\.|step 2)",
        r"(?:finally|lastly|3\.|step 3)"
    ]

    # Tool keywords
    TOOL_KEYWORDS = {
        "Read": ["read", "reading", "view", "check the file", "look at"],
        "Write": ["write", "create new", "new file"],
        "Edit": ["edit", "modify", "update", "change"],
        "Bash": ["run", "execute", "command", "terminal", "shell"],
        "Grep": ["search for", "find", "grep", "look for"],
        "Glob": ["find files", "search files", "locate"],
        "RAG": ["query", "search database", "RAG", "database"],
        "WebSearch": ["search", "web search", "google"]
    }

    def __init__(self):
        pass

    def extract_signals(self, trace: ClaudeTrace) -> ReasoningSignals:
        """
        Extract all reasoning signals from a Claude trace.

        This is the main entry point. It analyzes the trace and returns
        a ReasoningSignals object with all extracted patterns.
        """
        signals = ReasoningSignals()

        # Extract from text
        signals.constraints_detected = self._extract_constraints(trace)
        signals.tools_pruned = self._extract_pruning_decisions(trace)
        signals.self_corrections = self._extract_self_corrections(trace)
        signals.explicit_plan = self._extract_explicit_plan(trace)

        # Analyze tool usage
        signals.tool_sequence = self._extract_tool_sequence(trace)
        signals.parallel_tools = self._extract_parallel_tools(trace)

        # Workflow characteristics
        signals.used_rag = self._check_used_rag(trace)
        signals.used_terminal = self._check_used_terminal(trace)
        signals.used_web_search = self._check_used_web_search(trace)
        signals.multi_step_reasoning = len(signals.tool_sequence) > 2

        # Reasoning depth
        signals.reasoning_steps = self._count_reasoning_steps(trace)
        signals.exploration_depth = self._determine_exploration_depth(
            signals.reasoning_steps,
            len(signals.tool_sequence)
        )

        return signals

    def _extract_constraints(self, trace: ClaudeTrace) -> List[ConstraintDetection]:
        """
        Extract constraints/limitations that Claude identified.

        Examples from response text:
        - "Can't modify this without breaking backward compatibility"
        - "Need to preserve existing test coverage"
        - "Must avoid changing the public API"
        """
        constraints = []
        response = trace.claude_response.lower()

        for pattern in self.CONSTRAINT_PATTERNS:
            matches = re.finditer(pattern, response, re.IGNORECASE)
            for match in matches:
                # Extract surrounding context
                start = max(0, match.start() - 50)
                end = min(len(response), match.end() + 100)
                context = response[start:end].strip()

                # Try to determine source and impact
                source = "response_text"
                impact = "affected_approach"

                # Check if constraint mentions specific tools or files
                if "file" in context or "code" in context:
                    source = "code_structure"
                if "test" in context:
                    source = "test_coverage"
                if "api" in context or "interface" in context:
                    source = "public_api"

                constraints.append(ConstraintDetection(
                    constraint=context[:150],  # Limit length
                    source=source,
                    impact=impact
                ))

        # Deduplicate similar constraints
        return self._deduplicate_constraints(constraints)

    def _extract_pruning_decisions(self, trace: ClaudeTrace) -> List[PruningDecision]:
        """
        Extract approaches Claude considered but rejected.

        Examples:
        - "Could use Write, but Edit is safer"
        - "Considered rewriting from scratch, but refactoring is better"
        """
        pruning_decisions = []
        response = trace.claude_response

        for pattern in self.PRUNING_PATTERNS:
            matches = re.finditer(pattern, response, re.IGNORECASE)
            for match in matches:
                groups = match.groups()
                if len(groups) >= 2:
                    rejected = groups[0].strip()
                    reason = groups[1].strip()

                    # Try to infer the chosen alternative from tool calls
                    chosen = "unknown"
                    if trace.tool_calls:
                        chosen = trace.tool_calls[-1].tool  # Last tool used

                    pruning_decisions.append(PruningDecision(
                        rejected_approach=rejected[:100],
                        reason=reason[:100],
                        chosen_alternative=chosen
                    ))

        return pruning_decisions

    def _extract_self_corrections(self, trace: ClaudeTrace) -> List[SelfCorrection]:
        """
        Extract moments where Claude adjusted its approach.

        Examples:
        - "Actually, let me read the file first"
        - "That didn't work, let me try a different search pattern"
        """
        corrections = []
        response = trace.claude_response

        for i, pattern in enumerate(self.SELF_CORRECTION_PATTERNS):
            matches = re.finditer(pattern, response, re.IGNORECASE)
            for match in matches:
                correction_text = match.group(1).strip() if len(match.groups()) > 0 else match.group(0)

                # Try to determine what triggered the correction
                trigger = "reconsideration"
                if "error" in response.lower() or "fail" in response.lower():
                    trigger = "error"
                elif "actually" in match.group(0).lower():
                    trigger = "new_information"

                corrections.append(SelfCorrection(
                    step_number=i + 1,
                    original_plan="unknown",  # Hard to extract without full context
                    correction=correction_text[:150],
                    trigger=trigger
                ))

        return corrections

    def _extract_explicit_plan(self, trace: ClaudeTrace) -> Optional[str]:
        """
        Extract explicit planning statements.

        Examples:
        - "First I'll read the file, then search for the function, finally edit it"
        """
        response = trace.claude_response

        # Check if response contains planning keywords
        has_first = any(re.search(p, response, re.IGNORECASE) for p in [r"\bfirst\b", r"\b1\b", r"step 1"])
        has_then = any(re.search(p, response, re.IGNORECASE) for p in [r"\bthen\b", r"\bnext\b", r"\b2\b"])

        if has_first and has_then:
            # Extract the planning section (first 500 chars containing these keywords)
            for i in range(0, len(response) - 200, 50):
                snippet = response[i:i + 500]
                if "first" in snippet.lower() and ("then" in snippet.lower() or "next" in snippet.lower()):
                    return snippet.strip()

        return None

    def _extract_tool_sequence(self, trace: ClaudeTrace) -> List[str]:
        """
        Extract the sequence of tools Claude used.

        This is critical - we want LLaMA to learn the same tool chaining patterns.
        """
        return [tc.tool for tc in trace.tool_calls]

    def _extract_parallel_tools(self, trace: ClaudeTrace) -> List[List[str]]:
        """
        Detect tools called in parallel (within same timestamp second).

        Claude often calls multiple Read tools in parallel for efficiency.
        LLaMA should learn this pattern too.
        """
        if not trace.tool_calls:
            return []

        parallel_groups = []
        current_group = [trace.tool_calls[0].tool]
        current_timestamp = trace.tool_calls[0].timestamp

        for tc in trace.tool_calls[1:]:
            # If within 1 second, consider parallel
            if abs((tc.timestamp - current_timestamp).total_seconds()) < 1:
                current_group.append(tc.tool)
            else:
                if len(current_group) > 1:
                    parallel_groups.append(current_group)
                current_group = [tc.tool]
                current_timestamp = tc.timestamp

        if len(current_group) > 1:
            parallel_groups.append(current_group)

        return parallel_groups

    def _check_used_rag(self, trace: ClaudeTrace) -> bool:
        """Did Claude use RAG or database queries?"""
        response_lower = trace.claude_response.lower()
        return any(keyword in response_lower for keyword in ["database", "query", "rag", "search database"])

    def _check_used_terminal(self, trace: ClaudeTrace) -> bool:
        """Did Claude use terminal/bash commands?"""
        return any(tc.tool == "Bash" for tc in trace.tool_calls)

    def _check_used_web_search(self, trace: ClaudeTrace) -> bool:
        """Did Claude search the web?"""
        return any(tc.tool == "WebSearch" for tc in trace.tool_calls)

    def _count_reasoning_steps(self, trace: ClaudeTrace) -> int:
        """
        Count intermediate reasoning steps in Claude's response.

        Looks for phrases like:
        - "First, I'll..."
        - "Let me check..."
        - "Looking at..."
        """
        response = trace.claude_response
        reasoning_indicators = [
            r"(?:first|initially|to start),?\s+(?:I'll|I will|let me)",
            r"(?:next|then|after that),?\s+(?:I'll|I will|let me)",
            r"(?:let me|I'll|I will)\s+(?:check|look|read|search|analyze)",
            r"(?:looking at|checking|analyzing|examining)"
        ]

        steps = 0
        for pattern in reasoning_indicators:
            steps += len(re.findall(pattern, response, re.IGNORECASE))

        # Also count tool calls as reasoning steps
        steps += len(trace.tool_calls)

        return steps

    def _determine_exploration_depth(self, reasoning_steps: int, tool_count: int) -> ExplorationDepth:
        """
        Determine how thoroughly Claude explored before answering.
        """
        total_steps = reasoning_steps + tool_count

        if total_steps >= 10:
            return ExplorationDepth.EXHAUSTIVE
        elif total_steps >= 6:
            return ExplorationDepth.THOROUGH
        elif total_steps >= 3:
            return ExplorationDepth.MODERATE
        else:
            return ExplorationDepth.MINIMAL

    def _deduplicate_constraints(self, constraints: List[ConstraintDetection]) -> List[ConstraintDetection]:
        """Remove very similar constraints (within edit distance)."""
        if len(constraints) <= 1:
            return constraints

        unique = []
        for constraint in constraints:
            is_duplicate = False
            for existing in unique:
                # Simple similarity check
                if self._similarity(constraint.constraint, existing.constraint) > 0.8:
                    is_duplicate = True
                    break
            if not is_duplicate:
                unique.append(constraint)

        return unique

    def _similarity(self, s1: str, s2: str) -> float:
        """Compute similarity between two strings (0-1)."""
        s1_words = set(s1.lower().split())
        s2_words = set(s2.lower().split())

        if not s1_words or not s2_words:
            return 0.0

        intersection = s1_words & s2_words
        union = s1_words | s2_words

        return len(intersection) / len(union) if union else 0.0


class WorkflowExtractor:
    """
    Extracts the complete workflow/pipeline that Claude designed.

    This goes beyond individual tool calls to understand the STRUCTURE
    of Claude's problem-solving approach.
    """

    def extract_workflow_graph(self, trace: ClaudeTrace) -> dict:
        """
        Build a graph representation of Claude's workflow.

        Returns a dict with:
        - nodes: List of steps (tool calls, reasoning steps)
        - edges: Dependencies between steps
        - branching: If/else logic Claude used
        - error_handling: How Claude recovered from failures
        """
        nodes = []
        edges = []

        # Build nodes from tool calls
        for i, tc in enumerate(trace.tool_calls):
            nodes.append({
                "id": f"tool_{i}",
                "type": "tool_call",
                "tool": tc.tool,
                "args": tc.args,
                "reasoning": tc.reasoning
            })

            # Add edge from previous step
            if i > 0:
                edges.append({
                    "from": f"tool_{i-1}",
                    "to": f"tool_{i}",
                    "type": "sequential"
                })

        # Detect branching logic
        branching = self._detect_branching(trace)

        # Detect error handling
        error_handling = self._detect_error_handling(trace)

        return {
            "nodes": nodes,
            "edges": edges,
            "branching": branching,
            "error_handling": error_handling,
            "workflow_type": self._classify_workflow_type(trace)
        }

    def _detect_branching(self, trace: ClaudeTrace) -> List[dict]:
        """Detect if-else branching in Claude's approach."""
        branching = []
        response = trace.claude_response.lower()

        # Look for conditional logic
        if_patterns = [
            r"if\s+(.+?),?\s+(?:then|I'll)\s+(.+?)(?:\.|else|otherwise)",
            r"depending on\s+(.+?),?\s+(?:I'll|I will)\s+(.+)"
        ]

        for pattern in if_patterns:
            matches = re.finditer(pattern, response)
            for match in matches:
                branching.append({
                    "condition": match.group(1)[:100],
                    "action": match.group(2)[:100]
                })

        return branching

    def _detect_error_handling(self, trace: ClaudeTrace) -> List[dict]:
        """Detect how Claude handled errors or failures."""
        error_handling = []

        # Check if any tool calls failed (would be in errors_encountered)
        if trace.errors_encountered:
            for error in trace.errors_encountered:
                # Try to find recovery action
                recovery = "unknown"
                # This would require more context from the trace
                error_handling.append({
                    "error": error,
                    "recovery": recovery
                })

        return error_handling

    def _classify_workflow_type(self, trace: ClaudeTrace) -> str:
        """
        Classify the type of workflow Claude used.

        Types:
        - linear: Sequential steps (A → B → C)
        - parallel: Multiple independent steps
        - iterative: Repeated steps with refinement
        - exploratory: Many read/search operations before action
        - direct: Minimal exploration, immediate action
        """
        tool_sequence = [tc.tool for tc in trace.tool_calls]

        if not tool_sequence:
            return "direct"

        # Check for parallel operations
        parallel_count = len(self._extract_parallel_tools_static(trace))
        if parallel_count > 0:
            return "parallel"

        # Check for iteration (same tool repeated)
        unique_tools = set(tool_sequence)
        if len(unique_tools) < len(tool_sequence) / 2:
            return "iterative"

        # Check for exploration (many Read/Grep before Edit/Write)
        read_tools = ["Read", "Grep", "Glob"]
        write_tools = ["Edit", "Write", "Bash"]

        read_count = sum(1 for t in tool_sequence if t in read_tools)
        write_count = sum(1 for t in tool_sequence if t in write_tools)

        if read_count > write_count * 2:
            return "exploratory"

        return "linear"

    def _extract_parallel_tools_static(self, trace: ClaudeTrace) -> List[List[str]]:
        """Static version for workflow classification."""
        extractor = ReasoningSignalExtractor()
        return extractor._extract_parallel_tools(trace)
