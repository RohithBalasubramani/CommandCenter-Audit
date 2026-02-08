#!/usr/bin/env python3
"""
Claude RL Engine Control

Master control interface for the automated Claude→LLaMA training engine.

Commands:
    start       Start the automated capture daemon
    stop        Stop the daemon
    status      Show engine status
    train       Manually trigger training
    install     Install CLI wrapper and systemd service
    uninstall   Remove all hooks
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime

ENGINE_DIR = Path(__file__).parent
AGENT_DIR = ENGINE_DIR.parent
LOG_DIR = AGENT_DIR / "logs"


class EngineControl:
    """Master control for the automated RL engine."""

    def __init__(self):
        self.daemon_pid_file = ENGINE_DIR / "daemon.pid"
        self.service_file = ENGINE_DIR / "claude-rl-capture.service"
        self.cli_wrapper = AGENT_DIR / "hooks" / "claude_cli_wrapper.sh"

    def start(self):
        """Start the automated capture daemon."""
        print("=" * 70)
        print(" Starting Claude RL Automated Engine")
        print("=" * 70)
        print()

        # Check if already running
        if self._is_running():
            print("❌ Daemon is already running!")
            print(f"   PID: {self._get_pid()}")
            return

        # Start daemon
        print("Starting capture daemon...")
        daemon_script = ENGINE_DIR / "auto_capture_daemon.py"

        proc = subprocess.Popen(
            [sys.executable, str(daemon_script), "start"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            start_new_session=True
        )

        # Save PID
        self.daemon_pid_file.write_text(str(proc.pid))

        print(f"✅ Daemon started (PID: {proc.pid})")
        print()
        print("The engine is now:")
        print("  • Monitoring Claude Code CLI interactions")
        print("  • Auto-capturing all prompts and responses")
        print("  • Extracting reasoning signals")
        print("  • Storing traces for training")
        print("  • Will auto-train when threshold reached (50 traces)")
        print()
        print(f"Logs: {LOG_DIR}/capture_engine_*.log")
        print()

    def stop(self):
        """Stop the daemon."""
        print("Stopping Claude RL Engine...")

        if not self._is_running():
            print("❌ Daemon is not running")
            return

        pid = self._get_pid()
        try:
            os.kill(pid, 15)  # SIGTERM
            self.daemon_pid_file.unlink()
            print(f"✅ Daemon stopped (PID: {pid})")
        except ProcessLookupError:
            print(f"⚠️  Process {pid} not found (cleaning up PID file)")
            self.daemon_pid_file.unlink()

    def status(self):
        """Show engine status."""
        print("=" * 70)
        print(" Claude RL Engine Status")
        print("=" * 70)
        print()

        # Daemon status
        if self._is_running():
            pid = self._get_pid()
            print(f"🟢 Daemon: RUNNING (PID: {pid})")
        else:
            print(f"🔴 Daemon: STOPPED")
        print()

        # Trace statistics
        sys.path.insert(0, str(AGENT_DIR / "src"))
        from claude_trace_schema import TraceStorage

        storage = TraceStorage()
        trace_count = storage.get_trace_count()

        print(f"📊 Data Collection:")
        print(f"   Total traces captured: {trace_count}")
        print(f"   Progress to MVP: {trace_count}/50 ({trace_count*2}%)")
        print(f"   Progress to production: {trace_count}/500 ({trace_count/5:.1f}%)")
        print()

        # Training status
        print(f"🎯 Training Status:")
        dataset_files = list((AGENT_DIR / "data" / "datasets").glob("*.jsonl"))
        if dataset_files:
            latest = max(dataset_files, key=lambda p: p.stat().st_mtime)
            print(f"   Latest dataset: {latest.name}")
            print(f"   Created: {datetime.fromtimestamp(latest.stat().st_mtime)}")
        else:
            print(f"   No datasets built yet")
        print()

        # Auto-training threshold
        traces_until_train = max(0, 50 - trace_count)
        if traces_until_train > 0:
            print(f"🔔 Next auto-train in: {traces_until_train} traces")
        else:
            print(f"✅ Ready for training! (threshold met)")
        print()

        # CLI wrapper status
        print(f"🔧 CLI Wrapper:")
        if self.cli_wrapper.exists():
            print(f"   Installed: ✅ {self.cli_wrapper}")
        else:
            print(f"   Not installed (run: engine_control.py install)")
        print()

        print("=" * 70)

    def train(self):
        """Manually trigger training."""
        print("=" * 70)
        print(" Manual Training Trigger")
        print("=" * 70)
        print()

        sys.path.insert(0, str(AGENT_DIR / "src"))
        from claude_trace_schema import TraceStorage
        from behavioral_cloning_builder import BehavioralCloningDatasetBuilder

        storage = TraceStorage()
        trace_count = storage.get_trace_count()

        if trace_count < 10:
            print(f"❌ Not enough traces for training: {trace_count}/10 minimum")
            print()
            print("Capture more traces first:")
            print("  - Use Claude Code CLI normally (with wrapper installed)")
            print("  - Or run: ./run.sh capture --interactive")
            return

        print(f"Building dataset from {trace_count} traces...")
        builder = BehavioralCloningDatasetBuilder(storage)
        samples = builder.build_dataset()

        if not samples:
            print("❌ No valid training samples generated")
            return

        dataset_path = builder.save_dataset()
        stats = builder.get_statistics()

        print()
        print(f"✅ Dataset built: {dataset_path}")
        print()
        print("Dataset Statistics:")
        print(f"  Total samples: {stats['total_samples']}")
        print(f"  Workflow types: {stats['workflow_types']}")
        print(f"  Avg reasoning steps: {stats['avg_reasoning_steps']:.1f}")
        print(f"  Avg tool calls: {stats['avg_tool_calls']:.1f}")
        print()

        print("🎯 Next step: SFT Training (coming in Week 2)")
        print("   Command: ./run.sh train --phase sft")
        print()

    def install(self):
        """Install CLI wrapper and systemd service."""
        print("=" * 70)
        print(" Installing Claude RL Engine Hooks")
        print("=" * 70)
        print()

        # Make CLI wrapper executable
        self.cli_wrapper.chmod(0o755)
        print(f"✅ CLI wrapper ready: {self.cli_wrapper}")
        print()

        print("📝 To activate auto-capture, add to ~/.bashrc or ~/.zshrc:")
        print()
        print(f'   alias claude="{self.cli_wrapper}"')
        print()
        print("Then reload your shell:")
        print("   source ~/.bashrc")
        print()

        # Install systemd service (optional)
        print("🔧 To run as systemd service:")
        print()
        print(f"1. Copy service file:")
        print(f"   sudo cp {self.service_file} /etc/systemd/system/")
        print()
        print(f"2. Enable and start:")
        print(f"   sudo systemctl daemon-reload")
        print(f"   sudo systemctl enable claude-rl-capture")
        print(f"   sudo systemctl start claude-rl-capture")
        print()

    def uninstall(self):
        """Remove all hooks."""
        print("Removing Claude RL Engine hooks...")
        print()
        print("Manual steps:")
        print("1. Remove alias from ~/.bashrc or ~/.zshrc")
        print("2. If using systemd:")
        print("   sudo systemctl stop claude-rl-capture")
        print("   sudo systemctl disable claude-rl-capture")
        print("   sudo rm /etc/systemd/system/claude-rl-capture.service")
        print()

    def _is_running(self) -> bool:
        """Check if daemon is running."""
        if not self.daemon_pid_file.exists():
            return False

        try:
            pid = int(self.daemon_pid_file.read_text())
            os.kill(pid, 0)  # Check if process exists
            return True
        except (ValueError, ProcessLookupError):
            return False

    def _get_pid(self) -> int:
        """Get daemon PID."""
        if self.daemon_pid_file.exists():
            return int(self.daemon_pid_file.read_text())
        return None


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Claude RL Engine Control")
    parser.add_argument(
        "command",
        choices=["start", "stop", "status", "train", "install", "uninstall"],
        help="Command to execute"
    )

    args = parser.parse_args()

    control = EngineControl()

    if args.command == "start":
        control.start()
    elif args.command == "stop":
        control.stop()
    elif args.command == "status":
        control.status()
    elif args.command == "train":
        control.train()
    elif args.command == "install":
        control.install()
    elif args.command == "uninstall":
        control.uninstall()


if __name__ == "__main__":
    main()
