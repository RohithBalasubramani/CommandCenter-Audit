"""
Claude Code Interaction Capture System

This module provides tools to capture Claude Code interactions for training data.

Since we don't have direct access to Claude Code's internals, this implements
a MANUAL capture system where you can log interactions by:
1. Copy-pasting Claude's responses
2. Recording tool calls used
3. Noting your prompts

Future automation options:
- Proxy wrapper around Claude API
- VSCode extension hooks
- Claude CLI modification (if open-source)

Usage:
    # Start a new capture session
    capturer = ClaudeCapturer()

    # Before asking Claude
    capturer.start_trace("What's the difference between transformer 1 and 2?")

    # After Claude responds
    capturer.add_tool_call("Read", {"file_path": "config.py"}, "file contents...")
    capturer.add_tool_call("Bash", {"command": "psql ..."}, "query results...")
    capturer.finish_trace("Claude's final response here")

    # Save to disk
    capturer.save()
"""

import uuid
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List

try:
    from .claude_trace_schema import ClaudeTrace, ToolCall, TraceStorage
    from .reasoning_extractor import ReasoningSignalExtractor
except ImportError:
    from claude_trace_schema import ClaudeTrace, ToolCall, TraceStorage
    from reasoning_extractor import ReasoningSignalExtractor

logger = logging.getLogger(__name__)


class ClaudeCapturer:
    """
    Manual capture system for Claude Code interactions.

    This allows you to log Claude's problem-solving workflow as you use it,
    building a training dataset for LLaMA.
    """

    def __init__(self, storage_dir: str = "/home/rohith/desktop/CommandCenter/rl_training_data/claude_traces"):
        self.storage = TraceStorage(storage_dir)
        self.extractor = ReasoningSignalExtractor()
        self.current_trace: Optional[ClaudeTrace] = None
        self.session_id = str(uuid.uuid4())

    def start_trace(
        self,
        user_prompt: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        working_directory: str = "/home/rohith"
    ):
        """
        Start capturing a new Claude interaction.

        Args:
            user_prompt: The question you're asking Claude
            conversation_history: Previous turns in the conversation
            working_directory: Current working directory
        """
        self.current_trace = ClaudeTrace(
            trace_id=str(uuid.uuid4()),
            session_id=self.session_id,
            timestamp=datetime.now(),
            user_prompt=user_prompt,
            conversation_history=conversation_history or [],
            working_directory=working_directory,
            claude_response="",  # Will be filled in later
        )

        logger.info(f"Started trace {self.current_trace.trace_id} for prompt: {user_prompt[:100]}")

    def add_tool_call(
        self,
        tool: str,
        args: Dict[str, Any],
        output: str,
        reasoning: Optional[str] = None
    ):
        """
        Add a tool call that Claude made.

        Args:
            tool: Tool name (e.g., "Read", "Bash", "Grep")
            args: Tool arguments
            output: Tool result
            reasoning: Optional explanation of why Claude used this tool
        """
        if not self.current_trace:
            raise RuntimeError("No active trace. Call start_trace() first.")

        tool_call = ToolCall(
            tool=tool,
            args=args,
            output=output,
            timestamp=datetime.now(),
            reasoning=reasoning
        )

        self.current_trace.tool_calls.append(tool_call)
        logger.debug(f"Added tool call: {tool}")

    def add_error(self, error_message: str):
        """Record an error that Claude encountered."""
        if not self.current_trace:
            raise RuntimeError("No active trace. Call start_trace() first.")

        self.current_trace.errors_encountered.append(error_message)

    def finish_trace(
        self,
        claude_response: str,
        user_feedback: Optional[str] = None,
        response_time_ms: Optional[int] = None
    ) -> ClaudeTrace:
        """
        Complete the current trace with Claude's final response.

        Args:
            claude_response: Claude's full response text
            user_feedback: Optional user rating ("up", "down", or None)
            response_time_ms: How long Claude took to respond

        Returns:
            The completed ClaudeTrace
        """
        if not self.current_trace:
            raise RuntimeError("No active trace. Call start_trace() first.")

        self.current_trace.claude_response = claude_response
        self.current_trace.user_feedback = user_feedback

        if response_time_ms:
            self.current_trace.response_time_ms = response_time_ms

        # Extract reasoning signals automatically
        logger.info("Extracting reasoning signals...")
        self.current_trace.reasoning_signals = self.extractor.extract_signals(self.current_trace)

        logger.info(f"Finished trace {self.current_trace.trace_id}")
        logger.info(f"  - Tool calls: {len(self.current_trace.tool_calls)}")
        logger.info(f"  - Reasoning steps: {self.current_trace.reasoning_signals.reasoning_steps}")
        logger.info(f"  - Exploration depth: {self.current_trace.reasoning_signals.exploration_depth.value}")
        logger.info(f"  - Constraints detected: {len(self.current_trace.reasoning_signals.constraints_detected)}")

        completed_trace = self.current_trace
        self.current_trace = None
        return completed_trace

    def save(self, trace: Optional[ClaudeTrace] = None):
        """
        Save a trace to disk.

        Args:
            trace: Trace to save (defaults to current trace)
        """
        if trace is None:
            if self.current_trace:
                trace = self.current_trace
            else:
                raise ValueError("No trace to save")

        self.storage.save_trace(trace)
        logger.info(f"Saved trace {trace.trace_id} to disk")

    def get_trace_count(self) -> int:
        """Get the total number of captured traces."""
        return self.storage.get_trace_count()


class AutomaticCaptureHook:
    """
    Placeholder for future automatic capture system.

    This would hook into Claude Code's CLI or API to automatically
    capture all interactions without manual intervention.

    Implementation approaches:
    1. Proxy wrapper around Claude API
    2. Modify Claude CLI logging
    3. VSCode extension hooks
    """

    def __init__(self):
        self.capturer = ClaudeCapturer()

    def install_hook(self):
        """Install the capture hook (not yet implemented)."""
        raise NotImplementedError(
            "Automatic capture not yet implemented. "
            "Use ClaudeCapturer for manual capture."
        )

    def capture_request(self, prompt: str) -> str:
        """Intercept a request to Claude."""
        self.capturer.start_trace(prompt)
        return prompt

    def capture_response(self, response: str):
        """Intercept Claude's response."""
        # Extract tool calls from response (would need parsing logic)
        self.capturer.finish_trace(response)
        self.capturer.save()


class InteractiveCaptureSession:
    """
    Interactive CLI for capturing Claude traces manually.

    Usage:
        session = InteractiveCaptureSession()
        session.run()

    This provides a guided workflow for logging Claude interactions.
    """

    def __init__(self):
        self.capturer = ClaudeCapturer()

    def run(self):
        """Start an interactive capture session."""
        print("=" * 60)
        print("Claude Code Trace Capture Session")
        print("=" * 60)
        print(f"Total traces captured so far: {self.capturer.get_trace_count()}")
        print()

        while True:
            print("\n" + "=" * 60)
            user_prompt = input("Enter your prompt to Claude (or 'quit' to exit): ").strip()

            if user_prompt.lower() in ['quit', 'exit', 'q']:
                break

            if not user_prompt:
                continue

            self.capturer.start_trace(user_prompt)

            print("\nNow, ask this question to Claude Code and observe its response.")
            print("We'll capture the tool calls Claude makes...")
            print()

            # Capture tool calls
            while True:
                print("\nDid Claude use a tool? (Read/Write/Edit/Bash/Grep/Glob/etc.)")
                tool = input("Tool name (or 'done' if no more tools): ").strip()

                if tool.lower() == 'done':
                    break

                if not tool:
                    continue

                # Get tool arguments
                print(f"What were the arguments to {tool}?")
                args_str = input("Args (as key=value, comma separated): ").strip()
                args = self._parse_args(args_str)

                # Get tool output
                print(f"What was the output of {tool}?")
                output = input("Output (press Enter twice when done):\n")
                # Allow multi-line input
                lines = [output]
                while True:
                    line = input()
                    if not line:
                        break
                    lines.append(line)
                output = "\n".join(lines)

                # Optional reasoning
                reasoning = input("Why did Claude use this tool? (optional): ").strip()

                self.capturer.add_tool_call(
                    tool=tool,
                    args=args,
                    output=output,
                    reasoning=reasoning if reasoning else None
                )

            # Capture final response
            print("\nWhat was Claude's final response?")
            print("(Enter the full text, then press Enter twice when done)")
            response_lines = []
            while True:
                line = input()
                if not line:
                    if response_lines:  # Need two empty lines to finish
                        break
                response_lines.append(line)
            claude_response = "\n".join(response_lines)

            # Optional feedback
            feedback = input("\nWas Claude's response helpful? (up/down/skip): ").strip().lower()
            if feedback not in ['up', 'down']:
                feedback = None

            # Finish and save
            trace = self.capturer.finish_trace(claude_response, user_feedback=feedback)
            self.capturer.save(trace)

            print(f"\n✓ Trace saved! (ID: {trace.trace_id})")
            print(f"  - Tool calls: {len(trace.tool_calls)}")
            print(f"  - Reasoning steps: {trace.reasoning_signals.reasoning_steps}")
            print(f"  - Exploration: {trace.reasoning_signals.exploration_depth.value}")

            # Ask if user wants to continue
            continue_capture = input("\nCapture another interaction? (y/n): ").strip().lower()
            if continue_capture != 'y':
                break

        print(f"\nSession complete. Total traces captured: {self.capturer.get_trace_count()}")

    def _parse_args(self, args_str: str) -> Dict[str, Any]:
        """Parse 'key=value, key2=value2' into dict."""
        if not args_str:
            return {}

        args = {}
        for pair in args_str.split(','):
            pair = pair.strip()
            if '=' in pair:
                key, value = pair.split('=', 1)
                args[key.strip()] = value.strip()

        return args


# Convenience functions

def start_capture_session():
    """Start an interactive capture session."""
    session = InteractiveCaptureSession()
    session.run()


def quick_capture(prompt: str, claude_response: str, tool_calls: List[tuple] = None):
    """
    Quick one-line capture for simple interactions.

    Args:
        prompt: User's question
        claude_response: Claude's response
        tool_calls: List of (tool, args, output) tuples

    Example:
        quick_capture(
            prompt="What's in config.py?",
            claude_response="Looking at config.py, I see...",
            tool_calls=[
                ("Read", {"file_path": "config.py"}, "file contents...")
            ]
        )
    """
    capturer = ClaudeCapturer()
    capturer.start_trace(prompt)

    if tool_calls:
        for tool, args, output in tool_calls:
            capturer.add_tool_call(tool, args, output)

    trace = capturer.finish_trace(claude_response)
    capturer.save(trace)

    print(f"✓ Trace saved! (ID: {trace.trace_id})")
    return trace


if __name__ == "__main__":
    # Run interactive capture session
    start_capture_session()
