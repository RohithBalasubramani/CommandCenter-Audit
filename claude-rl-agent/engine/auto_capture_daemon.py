#!/usr/bin/env python3
"""
Automated Claude Code Capture Daemon

Runs in the background and automatically captures ALL Claude Code CLI interactions.

This daemon:
1. Monitors ~/.claude/ directory for new conversation logs
2. Automatically parses Claude interactions
3. Extracts reasoning signals
4. Stores traces continuously
5. Triggers training when thresholds met

Usage:
    python auto_capture_daemon.py start
    python auto_capture_daemon.py stop
    python auto_capture_daemon.py status
"""

import os
import sys
import json
import time
import logging
import signal
import re
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any
import threading
import queue
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from claude_trace_schema import ClaudeTrace, ToolCall, TraceStorage
from reasoning_extractor import ReasoningSignalExtractor
from behavioral_cloning_builder import BehavioralCloningDatasetBuilder

logger = logging.getLogger(__name__)


class ClaudeLogMonitor(FileSystemEventHandler):
    """
    Monitors Claude Code's log/conversation files for new interactions.

    Claude Code stores conversations in ~/.claude/projects/*/
    We watch these directories and parse new interactions automatically.
    """

    def __init__(self, capture_engine):
        self.engine = capture_engine
        self.processed_files = set()

    def on_modified(self, event):
        """Called when a file is modified."""
        if event.is_directory:
            return

        # Check if it's a conversation file
        if not self._is_conversation_file(event.src_path):
            return

        # Avoid processing same file multiple times
        if event.src_path in self.processed_files:
            return

        logger.info(f"Detected new Claude interaction: {event.src_path}")
        self.engine.process_conversation_file(event.src_path)
        self.processed_files.add(event.src_path)

    def _is_conversation_file(self, filepath: str) -> bool:
        """Check if file is a Claude conversation file."""
        # Claude stores conversations as JSON or log files
        return filepath.endswith(('.json', '.log', '.jsonl'))


class AutomatedCaptureEngine:
    """
    Automated engine that continuously captures Claude Code interactions.

    Architecture:
        1. File Monitor: Watches ~/.claude/ for new conversations
        2. Parser: Extracts prompts, responses, tool calls
        3. Reasoning Extractor: Analyzes workflow patterns
        4. Storage: Saves traces automatically
        5. Training Trigger: Starts training when threshold met
    """

    def __init__(
        self,
        data_dir: str = "/home/rohith/desktop/CommandCenter/claude-rl-agent/data",
        log_dir: str = "/home/rohith/desktop/CommandCenter/claude-rl-agent/logs"
    ):
        self.data_dir = Path(data_dir)
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Setup logging
        self._setup_logging()

        # Initialize components
        self.storage = TraceStorage(str(self.data_dir / "traces"))
        self.extractor = ReasoningSignalExtractor()
        self.dataset_builder = BehavioralCloningDatasetBuilder(self.storage)

        # File monitor
        self.observer = Observer()
        self.monitor = ClaudeLogMonitor(self)

        # State
        self.running = False
        self.last_train_time = None
        self.traces_since_last_train = 0

        # Config
        self.TRAIN_THRESHOLD = 50  # Train after 50 new traces
        self.TRAIN_INTERVAL_HOURS = 24  # Or every 24 hours

        logger.info("Automated Capture Engine initialized")

    def _setup_logging(self):
        """Setup logging to file and console."""
        log_file = self.log_dir / f"capture_engine_{datetime.now().strftime('%Y%m%d')}.log"

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )

    def start(self):
        """Start the automated capture engine."""
        logger.info("=" * 70)
        logger.info("Starting Automated Claude Code Capture Engine")
        logger.info("=" * 70)

        self.running = True

        # Watch Claude's directories
        claude_dirs = self._find_claude_directories()
        for directory in claude_dirs:
            logger.info(f"Monitoring: {directory}")
            self.observer.schedule(self.monitor, directory, recursive=True)

        self.observer.start()

        # Start background threads
        self._start_training_monitor()

        logger.info("Engine started successfully")
        logger.info(f"Watching {len(claude_dirs)} Claude directories")
        logger.info(f"Auto-training threshold: {self.TRAIN_THRESHOLD} traces")
        logger.info("")

        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()

    def stop(self):
        """Stop the engine gracefully."""
        logger.info("Stopping Automated Capture Engine...")
        self.running = False
        self.observer.stop()
        self.observer.join()
        logger.info("Engine stopped")

    def _find_claude_directories(self) -> List[str]:
        """Find Claude Code's conversation storage directories."""
        directories = []

        # Claude stores conversations in ~/.claude/projects/
        claude_home = Path.home() / ".claude"
        if claude_home.exists():
            # Watch projects directory
            projects_dir = claude_home / "projects"
            if projects_dir.exists():
                directories.append(str(projects_dir))

            # Watch conversation history
            if (claude_home / "conversations").exists():
                directories.append(str(claude_home / "conversations"))

        # Also watch our own data directory for manual additions
        directories.append(str(self.data_dir / "traces"))

        return directories

    def process_conversation_file(self, filepath: str):
        """
        Process a conversation file and extract traces.

        This parses Claude's conversation format and builds ClaudeTrace objects.
        """
        try:
            with open(filepath, 'r') as f:
                # Try to parse as JSON
                try:
                    data = json.load(f)
                except json.JSONDecodeError:
                    # Not JSON, try line-by-line
                    f.seek(0)
                    data = f.read()

            # Parse the conversation
            traces = self._parse_conversation(data, filepath)

            # Save each trace
            for trace in traces:
                # Extract reasoning signals
                trace.reasoning_signals = self.extractor.extract_signals(trace)

                # Save
                self.storage.save_trace(trace)
                logger.info(f"✅ Captured trace: {trace.trace_id}")
                logger.info(f"   Tools: {' → '.join(trace.reasoning_signals.tool_sequence)}")
                logger.info(f"   Depth: {trace.reasoning_signals.exploration_depth.value}")

                self.traces_since_last_train += 1

            # Check if we should trigger training
            self._check_training_threshold()

        except Exception as e:
            logger.error(f"Failed to process {filepath}: {e}")

    def _parse_conversation(self, data: Any, source_file: str) -> List[ClaudeTrace]:
        """
        Parse conversation data into ClaudeTrace objects.

        Handles different conversation formats:
        - Claude CLI JSON format
        - VSCode extension format
        - Plain text logs
        """
        traces = []

        if isinstance(data, dict):
            # JSON format
            traces = self._parse_json_conversation(data, source_file)
        elif isinstance(data, str):
            # Plain text format
            traces = self._parse_text_conversation(data, source_file)

        return traces

    def _parse_json_conversation(self, data: dict, source_file: str) -> List[ClaudeTrace]:
        """Parse JSON-formatted conversation."""
        traces = []

        # Look for conversation turns
        messages = data.get('messages', [])
        conversation_history = []

        for i, msg in enumerate(messages):
            role = msg.get('role', '')
            content = msg.get('content', '')

            if role == 'user':
                # Start new trace
                user_prompt = content
            elif role == 'assistant' and user_prompt:
                # Extract tool calls from assistant message
                tool_calls = self._extract_tool_calls(content)

                # Create trace
                trace = ClaudeTrace(
                    trace_id=f"{Path(source_file).stem}_{i}",
                    session_id=Path(source_file).stem,
                    timestamp=datetime.now(),
                    user_prompt=user_prompt,
                    claude_response=content,
                    conversation_history=conversation_history.copy(),
                    tool_calls=tool_calls,
                    working_directory=str(Path(source_file).parent)
                )

                traces.append(trace)

                # Update history
                conversation_history.append({'role': 'user', 'content': user_prompt})
                conversation_history.append({'role': 'assistant', 'content': content})

                user_prompt = None

        return traces

    def _parse_text_conversation(self, text: str, source_file: str) -> List[ClaudeTrace]:
        """Parse plain text conversation."""
        traces = []

        # Split by user/assistant markers
        parts = re.split(r'(?:User:|Human:|Assistant:|Claude:)', text)

        user_prompt = None
        for i, part in enumerate(parts):
            part = part.strip()
            if not part:
                continue

            if i % 2 == 1:  # User message
                user_prompt = part
            elif i % 2 == 0 and user_prompt:  # Assistant message
                tool_calls = self._extract_tool_calls(part)

                trace = ClaudeTrace(
                    trace_id=f"{Path(source_file).stem}_{i}",
                    session_id=Path(source_file).stem,
                    timestamp=datetime.now(),
                    user_prompt=user_prompt,
                    claude_response=part,
                    tool_calls=tool_calls,
                    working_directory=str(Path(source_file).parent)
                )

                traces.append(trace)
                user_prompt = None

        return traces

    def _extract_tool_calls(self, text: str) -> List[ToolCall]:
        """
        Extract tool calls from Claude's response text.

        Looks for patterns like:
        - "Let me read the file..." → Read tool
        - "I'll run a command..." → Bash tool
        - "Searching for..." → Grep tool
        """
        tool_calls = []

        # Pattern 1: Explicit tool mentions
        tool_patterns = {
            'Read': r'(?:read|reading|view|check)\s+(?:the\s+)?file\s+([^\s]+)',
            'Bash': r'(?:run|execute|running)\s+(?:command|the command)[\s:]+([^\n]+)',
            'Grep': r'(?:search|searching|grep)\s+for\s+([^\n]+)',
            'Edit': r'(?:edit|modify|update)\s+(?:the\s+)?file\s+([^\s]+)',
            'Write': r'(?:create|write)\s+(?:new\s+)?file\s+([^\s]+)',
        }

        for tool, pattern in tool_patterns.items():
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                tool_call = ToolCall(
                    tool=tool,
                    args={'inferred': match.group(1).strip()},
                    output="",  # Output not captured in text
                    timestamp=datetime.now(),
                    reasoning=f"Inferred from text: {match.group(0)}"
                )
                tool_calls.append(tool_call)

        return tool_calls

    def _start_training_monitor(self):
        """Start background thread that monitors for training triggers."""
        def training_monitor():
            while self.running:
                time.sleep(60)  # Check every minute
                self._check_training_threshold()

        thread = threading.Thread(target=training_monitor, daemon=True)
        thread.start()
        logger.info("Training monitor thread started")

    def _check_training_threshold(self):
        """Check if we should trigger training."""
        total_traces = self.storage.get_trace_count()

        # Check trace threshold
        if self.traces_since_last_train >= self.TRAIN_THRESHOLD:
            logger.info(f"🎯 Training threshold reached: {self.traces_since_last_train} new traces")
            self._trigger_training()
            return

        # Check time threshold
        if self.last_train_time:
            hours_since_train = (datetime.now() - self.last_train_time).total_seconds() / 3600
            if hours_since_train >= self.TRAIN_INTERVAL_HOURS and total_traces >= 50:
                logger.info(f"🎯 Time threshold reached: {hours_since_train:.1f} hours since last training")
                self._trigger_training()
                return

    def _trigger_training(self):
        """Trigger the training pipeline."""
        logger.info("=" * 70)
        logger.info("🚀 Triggering Automated Training Pipeline")
        logger.info("=" * 70)

        try:
            # Build dataset
            logger.info("Building dataset from traces...")
            samples = self.dataset_builder.build_dataset()

            if len(samples) < 10:
                logger.warning(f"Not enough samples for training: {len(samples)}")
                return

            dataset_path = self.dataset_builder.save_dataset()
            logger.info(f"✅ Dataset saved: {dataset_path}")

            # TODO: Trigger SFT training (Week 2)
            logger.info("⏳ SFT training not yet implemented (coming in Week 2)")

            # Update state
            self.last_train_time = datetime.now()
            self.traces_since_last_train = 0

            logger.info("Training pipeline completed")
            logger.info("=" * 70)

        except Exception as e:
            logger.error(f"Training failed: {e}")

    def get_status(self) -> dict:
        """Get current engine status."""
        return {
            "running": self.running,
            "total_traces": self.storage.get_trace_count(),
            "traces_since_last_train": self.traces_since_last_train,
            "last_train_time": self.last_train_time.isoformat() if self.last_train_time else None,
            "train_threshold": self.TRAIN_THRESHOLD,
        }


def main():
    """Main CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Automated Claude Code Capture Engine")
    parser.add_argument("command", choices=["start", "stop", "status"], help="Command to run")

    args = parser.parse_args()

    engine = AutomatedCaptureEngine()

    if args.command == "start":
        engine.start()
    elif args.command == "stop":
        # TODO: Implement proper daemon stop
        print("Stop via kill PID for now")
    elif args.command == "status":
        status = engine.get_status()
        print(json.dumps(status, indent=2))


if __name__ == "__main__":
    main()
