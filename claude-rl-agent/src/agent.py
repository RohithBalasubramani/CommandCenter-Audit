"""
Claude Behavioral Replication Agent

A complete RL system that trains LLaMA to replicate Claude Code's workflow design capability.

Usage:
    # Automated Engine (recommended)
    python agent.py engine start           # Start automated capture daemon
    python agent.py engine status          # Check status
    python agent.py engine install         # Install CLI hooks

    # Manual Capture (alternative)
    python agent.py capture --interactive
    python agent.py capture --demo

    # Training
    python agent.py build-dataset          # Build training dataset
    python agent.py train --phase sft      # Behavioral cloning
    python agent.py train --phase ppo      # RL alignment

    # Deployment
    python agent.py deploy --test          # Deploy and test
"""

import argparse
import logging
import sys
import os
import subprocess
from pathlib import Path
from typing import Optional
from datetime import datetime

# Add paths
AGENT_DIR = Path(__file__).parent.parent
ENGINE_DIR = AGENT_DIR / "engine"
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(ENGINE_DIR))

from claude_capture_hook import ClaudeCapturer, InteractiveCaptureSession
from behavioral_cloning_builder import BehavioralCloningDatasetBuilder
from claude_trace_schema import TraceStorage

# Training modules imported lazily (require heavy dependencies)
# from sft_trainer import ClaudeSFTTrainer, SFTConfig
# from ppo_trainer import ClaudePPOTrainer, PPOTrainingConfig
# from training_orchestrator import TrainingOrchestrator, OrchestratorConfig

logger = logging.getLogger(__name__)


class ClaudeRLAgent:
    """
    Main agent for training LLaMA to replicate Claude's behavioral patterns.
    
    Architecture:
        Phase 1 (Capture): Collect Claude workflows → traces.jsonl
        Phase 2 (Dataset): Build SFT dataset → bc_dataset.jsonl
        Phase 3 (SFT): Behavioral cloning → llama-claude-bc-v1.gguf
        Phase 4 (PPO): RL alignment → llama-claude-ppo-v{N}.gguf
        Phase 5 (Deploy): Export to Ollama → cc-claude-agent:latest
    """
    
    def __init__(self, data_dir: str = "/home/rohith/desktop/CommandCenter/claude-rl-agent/data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.traces_dir = self.data_dir / "traces"
        self.datasets_dir = self.data_dir / "datasets"
        self.models_dir = self.data_dir / "models"
        
        # Create subdirectories
        self.traces_dir.mkdir(exist_ok=True)
        self.datasets_dir.mkdir(exist_ok=True)
        self.models_dir.mkdir(exist_ok=True)
        
    def capture_interactive(self):
        """Start interactive capture session."""
        print("🎯 Phase 1: Capture Claude's Workflow Design")
        print()
        print("This will help you capture Claude Code interactions.")
        print("For each question you ask Claude, you'll log:")
        print("  - The prompt")
        print("  - Tools Claude used (Read, Bash, Grep, etc.)")
        print("  - Claude's response")
        print()
        print("Goal: 500-1000 diverse traces")
        print()
        
        session = InteractiveCaptureSession()
        session.run()
    
    def capture_demo(self):
        """Run the demonstration workflow."""
        from demo_workflow_capture import demonstrate_workflow_capture, show_training_impact
        
        print("🎯 Running Workflow Capture Demonstration")
        print()
        
        trace = demonstrate_workflow_capture()
        show_training_impact()
        
        return trace
    
    def build_dataset(self, min_traces: int = 1):
        """Build training dataset from captured traces."""
        print("🎯 Phase 2: Build Training Dataset")
        print()
        
        # Load traces
        storage = TraceStorage(str(self.traces_dir))
        trace_count = storage.get_trace_count()
        
        print(f"Found {trace_count} captured traces")
        
        if trace_count < min_traces:
            print(f"❌ Need at least {min_traces} traces to build dataset")
            print()
            print("Capture more traces first:")
            print("  python agent.py capture --interactive")
            return None
        
        # Build dataset
        builder = BehavioralCloningDatasetBuilder(storage)
        samples = builder.build_dataset(
            min_reasoning_steps=2,
            require_multi_step=True
        )
        
        # Save dataset
        dataset_path = builder.save_dataset(
            output_path=self.datasets_dir / "bc_dataset.jsonl",
            format="jsonl"
        )
        
        # Show statistics
        stats = builder.get_statistics()
        print()
        print(f"✅ Built {stats['total_samples']} training samples")
        print()
        print("Statistics:")
        print(f"  - Workflow types: {stats['workflow_types']}")
        print(f"  - Exploration depths: {stats['exploration_depths']}")
        print(f"  - Avg reasoning steps: {stats['avg_reasoning_steps']:.1f}")
        print(f"  - Avg tool calls: {stats['avg_tool_calls']:.1f}")
        print()
        print(f"📂 Dataset saved: {dataset_path}")
        print()
        
        return dataset_path
    
    def train_sft(self, dataset_path: Optional[str] = None, epochs: int = 3):
        """Train LLaMA with behavioral cloning (SFT)."""
        print("🎯 Phase 3: Behavioral Cloning (SFT)")
        print()

        # Lazy import (requires heavy dependencies)
        try:
            from sft_trainer import ClaudeSFTTrainer, SFTConfig
        except ImportError as e:
            print("❌ Missing training dependencies!")
            print()
            print("Install with:")
            print("  pip install unsloth trl transformers datasets torch")
            print()
            print("Or use conda:")
            print("  conda install -c conda-forge unsloth trl transformers datasets pytorch")
            print()
            return None

        # Find latest dataset if not specified
        if dataset_path is None:
            dataset_files = list(self.datasets_dir.glob("*.jsonl"))
            if not dataset_files:
                print("❌ No dataset found!")
                print("   Run: python agent.py build-dataset")
                return None
            dataset_path = max(dataset_files, key=lambda p: p.stat().st_mtime)
            print(f"Using dataset: {dataset_path.name}")
            print()

        # Create config
        config = SFTConfig(
            num_epochs=epochs,
            batch_size=2,
            learning_rate=2e-4,
        )

        # Train
        trainer = ClaudeSFTTrainer(config)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_name = f"claude-bc-{timestamp}"

        try:
            model_path = trainer.train(str(dataset_path), output_name)
            print()
            print("=" * 70)
            print("✅ SFT TRAINING COMPLETE!")
            print("=" * 70)
            print(f"Model saved: {model_path}")
            print()
            print("Next steps:")
            print("  1. Run PPO training: python agent.py train --phase ppo")
            print("  2. Or export to GGUF: python agent.py export")
            print()
            return model_path
        except Exception as e:
            print(f"❌ Training failed: {e}")
            logger.error(f"SFT training failed: {e}", exc_info=True)
            return None
    
    def train_ppo(self, sft_model_path: Optional[str] = None, episodes: int = 100):
        """Train LLaMA with PPO (RL)."""
        print("🎯 Phase 4: PPO Behavioral Alignment")
        print()

        # Lazy import
        try:
            from ppo_trainer import ClaudePPOTrainer, PPOTrainingConfig
        except ImportError:
            print("❌ Missing training dependencies!")
            print("   Install: pip install unsloth trl transformers datasets torch")
            return None

        # Find latest SFT model if not specified
        if sft_model_path is None:
            sft_checkpoints = list(self.models_dir.glob("sft_checkpoints/*/final"))
            if not sft_checkpoints:
                print("❌ No SFT model found!")
                print("   Run: python agent.py train --phase sft")
                return None
            sft_model_path = max(sft_checkpoints, key=lambda p: p.stat().st_mtime)
            print(f"Using SFT model: {sft_model_path}")
            print()

        # Find latest dataset
        dataset_files = list(self.datasets_dir.glob("*.jsonl"))
        if not dataset_files:
            print("❌ No dataset found!")
            print("   Run: python agent.py build-dataset")
            return None
        dataset_path = max(dataset_files, key=lambda p: p.stat().st_mtime)

        # Create config
        config = PPOTrainingConfig(
            sft_model_path=str(sft_model_path),
            num_episodes=episodes,
            learning_rate=1.4e-5,
        )

        # Train
        trainer = ClaudePPOTrainer(config)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_name = f"claude-ppo-{timestamp}"

        try:
            model_path = trainer.train(str(dataset_path), output_name)
            print()
            print("=" * 70)
            print("✅ PPO TRAINING COMPLETE!")
            print("=" * 70)
            print(f"Model saved: {model_path}")
            print()
            print("Next steps:")
            print("  1. Export to GGUF: python agent.py export")
            print("  2. Deploy to Ollama: python agent.py deploy")
            print()
            return model_path
        except Exception as e:
            print(f"❌ Training failed: {e}")
            logger.error(f"PPO training failed: {e}", exc_info=True)
            return None
    
    def deploy(self, test: bool = True):
        """Deploy trained model to Ollama."""
        print("🎯 Phase 5: Deploy to Ollama")
        print()
        print("❌ Not yet implemented - coming after training!")
        print()
    
    def status(self):
        """Show current progress."""
        print("=" * 70)
        print(" Claude Behavioral Replication Agent - Status")
        print("=" * 70)
        print()

        # Check engine daemon
        daemon_running = self._check_daemon_running()
        if daemon_running:
            print("🟢 Automated Engine: RUNNING")
        else:
            print("🔴 Automated Engine: STOPPED")
            print("   (Start: python agent.py engine start)")
        print()

        # Check traces
        storage = TraceStorage(str(self.traces_dir))
        trace_count = storage.get_trace_count()

        print("📊 Phase 1: Data Collection")
        print(f"   Traces captured: {trace_count}/500")
        print(f"   Progress to MVP: {trace_count}/50 ({trace_count*2}%)")
        print(f"   Progress to production: {trace_count}/500 ({trace_count/5:.1f}%)")

        # Auto-training threshold
        traces_until_train = max(0, 50 - trace_count)
        if traces_until_train > 0:
            print(f"   Next auto-train in: {traces_until_train} traces")
        else:
            print(f"   ✅ Ready for training!")
        print()

        # Check dataset
        dataset_files = list(self.datasets_dir.glob("*.jsonl"))
        print("📊 Phase 2: Dataset")
        if dataset_files:
            latest = max(dataset_files, key=lambda p: p.stat().st_mtime)
            print(f"   ✅ Dataset built: {latest.name}")
            print(f"   Created: {datetime.fromtimestamp(latest.stat().st_mtime).strftime('%Y-%m-%d %H:%M')}")
        else:
            print(f"   ❌ No dataset yet")
            if trace_count >= 10:
                print(f"   → Run: python agent.py build-dataset")
        print()

        # Check models
        model_files = list(self.models_dir.glob("*.gguf"))
        print("📊 Phase 3-4: Models")
        if model_files:
            for model in model_files:
                print(f"   ✅ {model.name}")
        else:
            print(f"   ❌ No models yet (training not started)")
        print()

        print("=" * 70)
        print()

        # Show next steps
        if not daemon_running:
            print("🎯 Recommended: Start Automated Engine")
            print("   Run: python agent.py engine install")
            print("        python agent.py engine start")
            print()
        elif trace_count < 50:
            print("🎯 Keep using Claude - auto-capturing!")
            print("   Every Claude CLI interaction is captured automatically")
            print("   Goal: 50 traces for MVP, 500 for production")
        elif not dataset_files:
            print("🎯 Next Step: Build training dataset")
            print("   Run: python agent.py build-dataset")
        else:
            print("🎯 Next Step: Wait for SFT trainer (Week 2)")
        print()

    def _check_daemon_running(self) -> bool:
        """Check if automated engine daemon is running."""
        pid_file = ENGINE_DIR / "daemon.pid"
        if not pid_file.exists():
            return False

        try:
            pid = int(pid_file.read_text())
            os.kill(pid, 0)  # Check if process exists
            return True
        except (ValueError, ProcessLookupError):
            return False

    # Automated Engine Methods

    def engine_start(self):
        """Start the automated capture daemon."""
        print("=" * 70)
        print(" Starting Automated Capture Engine")
        print("=" * 70)
        print()

        if self._check_daemon_running():
            print("❌ Daemon is already running!")
            print()
            print("Check status: python agent.py engine status")
            return

        # Start daemon
        daemon_script = ENGINE_DIR / "auto_capture_daemon.py"
        proc = subprocess.Popen(
            [sys.executable, str(daemon_script), "start"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            start_new_session=True
        )

        # Save PID
        pid_file = ENGINE_DIR / "daemon.pid"
        pid_file.write_text(str(proc.pid))

        print(f"✅ Daemon started (PID: {proc.pid})")
        print()
        print("The engine is now:")
        print("  • Monitoring Claude Code CLI interactions")
        print("  • Auto-capturing all prompts and responses")
        print("  • Extracting reasoning signals")
        print("  • Storing traces for training")
        print("  • Will auto-train when threshold reached (50 traces)")
        print()
        print(f"Logs: {AGENT_DIR}/logs/capture_engine_*.log")
        print()
        print("Check status anytime: python agent.py engine status")
        print()

    def engine_stop(self):
        """Stop the automated daemon."""
        print("Stopping Automated Capture Engine...")
        print()

        pid_file = ENGINE_DIR / "daemon.pid"
        if not pid_file.exists():
            print("❌ Daemon is not running")
            return

        try:
            pid = int(pid_file.read_text())
            os.kill(pid, 15)  # SIGTERM
            pid_file.unlink()
            print(f"✅ Daemon stopped (PID: {pid})")
        except (ValueError, ProcessLookupError):
            print(f"⚠️  Process not found (cleaning up PID file)")
            pid_file.unlink()

    def engine_install(self):
        """Install CLI wrapper and show setup instructions."""
        print("=" * 70)
        print(" Installing Automated Capture Hooks")
        print("=" * 70)
        print()

        cli_wrapper = AGENT_DIR / "hooks" / "claude_cli_wrapper.sh"
        cli_wrapper.chmod(0o755)

        print(f"✅ CLI wrapper ready: {cli_wrapper}")
        print()
        print("📝 To activate auto-capture, add to ~/.bashrc or ~/.zshrc:")
        print()
        print(f'   alias claude="{cli_wrapper}"')
        print()
        print("Then reload your shell:")
        print("   source ~/.bashrc")
        print()
        print("After that, every Claude CLI command is auto-captured!")
        print()
        print("Optional: Run as systemd service (auto-start on boot)")
        print("  1. sudo cp engine/claude-rl-capture.service /etc/systemd/system/")
        print("  2. sudo systemctl daemon-reload")
        print("  3. sudo systemctl enable --now claude-rl-capture")
        print()

    def engine_status(self):
        """Show detailed engine status."""
        # Just call the main status method
        self.status()

    # Orchestrator Methods

    def orchestrator_start(self):
        """Start continuous training orchestrator."""
        print("=" * 70)
        print(" Starting Continuous Training Orchestrator")
        print("=" * 70)
        print()

        # Lazy import
        try:
            from training_orchestrator import TrainingOrchestrator, OrchestratorConfig
        except ImportError:
            print("❌ Missing training dependencies!")
            print("   Install: pip install unsloth trl transformers datasets torch")
            return

        config = OrchestratorConfig(
            min_traces_for_sft=50,
            traces_per_training_cycle=50,
            auto_export_gguf=True,
            auto_deploy_ollama=False,  # User approval required
        )

        orchestrator = TrainingOrchestrator(config)

        print("The orchestrator will:")
        print("  • Monitor trace collection")
        print("  • Auto-build datasets at thresholds")
        print("  • Auto-train SFT models")
        print("  • Auto-train PPO models")
        print("  • Auto-export to GGUF")
        print()
        print("Starting continuous loop...")
        print("(Press Ctrl+C to stop)")
        print()

        orchestrator.run_continuous_loop()

    def orchestrator_once(self):
        """Run one training cycle."""
        try:
            from training_orchestrator import TrainingOrchestrator, OrchestratorConfig
        except ImportError:
            print("❌ Missing training dependencies!")
            return

        config = OrchestratorConfig()
        orchestrator = TrainingOrchestrator(config)

        should_train, reason = orchestrator.check_training_needed()

        if should_train:
            print(f"Running training cycle: {reason}")
            orchestrator.run_training_cycle()
        else:
            print(f"Training not needed: {reason}")

    def orchestrator_status(self):
        """Show orchestrator status."""
        try:
            from training_orchestrator import TrainingOrchestrator
        except ImportError:
            print("❌ Missing training dependencies!")
            return

        orchestrator = TrainingOrchestrator()
        status = orchestrator.get_status()

        print("=" * 70)
        print(" Training Orchestrator Status")
        print("=" * 70)
        print()
        print(f"Training cycles completed: {status['total_cycles_completed']}")
        print(f"Total traces collected: {status['total_traces']}")
        print(f"New traces since last training: {status['new_traces_since_last_training']}")
        print(f"Next training in: {status['next_training_in']} traces")
        print()
        if status['last_sft_model']:
            print(f"Latest SFT model: {Path(status['last_sft_model']).name}")
        if status['last_ppo_model']:
            print(f"Latest PPO model: {Path(status['last_ppo_model']).name}")
        print()

    # Fast-Track Bootstrap

    def bootstrap_now(self, num_traces: int = 500):
        """Fast-track bootstrap - generate synthetic training data immediately."""
        print("=" * 70)
        print(" 🚀 FAST-TRACK BOOTSTRAP")
        print(" 6 Months → NOW")
        print("=" * 70)
        print()

        from fast_track_bootstrap import FastTrackBootstrap

        bootstrap = FastTrackBootstrap()
        total = bootstrap.bootstrap_now(target_traces=num_traces)

        print("=" * 70)
        print(" ✅ BOOTSTRAP COMPLETE!")
        print("=" * 70)
        print()
        print("Next steps:")
        print("  1. Build dataset:  ./run.sh build-dataset")
        print("  2. Train now:      ./run.sh train --phase sft")
        print()
        print("Or use orchestrator:")
        print("  ./run.sh orchestrator once")
        print()

        return total

    def export_gguf(self, model_path: Optional[str] = None):
        """Export model to GGUF format."""
        print("=" * 70)
        print(" Exporting Model to GGUF")
        print("=" * 70)
        print()

        # Lazy import
        try:
            from sft_trainer import ClaudeSFTTrainer
        except ImportError:
            print("❌ Missing training dependencies!")
            print("   Install: pip install unsloth trl transformers datasets torch")
            return None

        # Find latest model if not specified
        if model_path is None:
            # Try PPO first, then SFT
            ppo_models = list(self.models_dir.glob("ppo_checkpoints/*/final"))
            sft_models = list(self.models_dir.glob("sft_checkpoints/*/final"))

            all_models = ppo_models + sft_models
            if not all_models:
                print("❌ No trained models found!")
                print("   Run: python agent.py train --phase sft")
                return None

            model_path = max(all_models, key=lambda p: p.stat().st_mtime)
            print(f"Using model: {model_path}")
            print()

        # Export
        trainer = ClaudeSFTTrainer()
        timestamp = datetime.now().strftime("%Y%m%d")
        output_name = f"claude-bc-{timestamp}"

        try:
            gguf_path = trainer.export_to_gguf(str(model_path), output_name)
            print()
            print("=" * 70)
            print("✅ GGUF EXPORT COMPLETE!")
            print("=" * 70)
            print(f"GGUF file: {gguf_path}")
            print()
            print("Next steps:")
            print("  1. Deploy to Ollama: python agent.py deploy")
            print()
            return gguf_path
        except Exception as e:
            print(f"❌ Export failed: {e}")
            logger.error(f"GGUF export failed: {e}", exc_info=True)
            return None


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Claude Behavioral Replication Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Automated Engine (recommended)
  %(prog)s engine install            Install automated capture hooks
  %(prog)s engine start              Start background daemon
  %(prog)s engine status             Check engine status
  %(prog)s engine stop               Stop daemon

  # Manual Capture
  %(prog)s capture --demo            Run demonstration
  %(prog)s capture --interactive     Manual capture session

  # Fast-Track Bootstrap (6 Months → NOW)
  %(prog)s bootstrap                 Generate 500 synthetic traces instantly
  %(prog)s bootstrap --traces 1000   Generate 1000 synthetic traces

  # Training
  %(prog)s build-dataset             Build training dataset
  %(prog)s train --phase sft         Train with behavioral cloning (SFT)
  %(prog)s train --phase ppo         RL alignment training (PPO)

  # Continuous Training (Fully Automated)
  %(prog)s orchestrator start        Start continuous training loop
  %(prog)s orchestrator once         Run one training cycle
  %(prog)s orchestrator status       Check orchestrator status

  # Export & Deploy
  %(prog)s export                    Export model to GGUF format
  %(prog)s deploy                    Deploy to Ollama

  # Status
  %(prog)s status                    Show overall status
        """
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Engine command (AUTOMATED)
    engine_parser = subparsers.add_parser("engine", help="Automated capture engine (recommended)")
    engine_parser.add_argument(
        "engine_command",
        choices=["start", "stop", "status", "install"],
        help="Engine command"
    )

    # Capture command (MANUAL)
    capture_parser = subparsers.add_parser("capture", help="Manual capture workflows")
    capture_parser.add_argument("--interactive", action="store_true", help="Interactive capture session")
    capture_parser.add_argument("--demo", action="store_true", help="Run demonstration")

    # Bootstrap command (FAST-TRACK)
    bootstrap_parser = subparsers.add_parser("bootstrap", help="Fast-track bootstrap - generate synthetic training data")
    bootstrap_parser.add_argument("--traces", type=int, default=500, help="Number of synthetic traces to generate")

    # Build dataset command
    subparsers.add_parser("build-dataset", help="Build training dataset from traces")

    # Train command
    train_parser = subparsers.add_parser("train", help="Train LLaMA model")
    train_parser.add_argument("--phase", choices=["sft", "ppo"], default="sft", help="Training phase")
    train_parser.add_argument("--epochs", type=int, default=3, help="Number of training epochs (SFT)")
    train_parser.add_argument("--episodes", type=int, default=100, help="Number of training episodes (PPO)")

    # Orchestrator command
    orch_parser = subparsers.add_parser("orchestrator", help="Continuous training orchestrator")
    orch_parser.add_argument(
        "orch_command",
        choices=["start", "once", "status"],
        help="Orchestrator command"
    )

    # Export command
    export_parser = subparsers.add_parser("export", help="Export model to GGUF format")
    export_parser.add_argument("--model-path", help="Path to model checkpoint")

    # Deploy command
    deploy_parser = subparsers.add_parser("deploy", help="Deploy model to Ollama")
    deploy_parser.add_argument("--test", action="store_true", help="Run tests after deployment")

    # Status command
    subparsers.add_parser("status", help="Show current progress")

    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Create agent
    agent = ClaudeRLAgent()

    # Execute command
    if args.command == "engine":
        if args.engine_command == "start":
            agent.engine_start()
        elif args.engine_command == "stop":
            agent.engine_stop()
        elif args.engine_command == "status":
            agent.engine_status()
        elif args.engine_command == "install":
            agent.engine_install()

    elif args.command == "capture":
        if args.demo:
            agent.capture_demo()
        else:
            agent.capture_interactive()

    elif args.command == "bootstrap":
        agent.bootstrap_now(num_traces=args.traces)

    elif args.command == "build-dataset":
        agent.build_dataset()

    elif args.command == "train":
        if args.phase == "sft":
            agent.train_sft(epochs=args.epochs)
        elif args.phase == "ppo":
            agent.train_ppo(episodes=args.episodes)

    elif args.command == "orchestrator":
        if args.orch_command == "start":
            agent.orchestrator_start()
        elif args.orch_command == "once":
            agent.orchestrator_once()
        elif args.orch_command == "status":
            agent.orchestrator_status()

    elif args.command == "export":
        agent.export_gguf(model_path=args.model_path)

    elif args.command == "deploy":
        agent.deploy(test=args.test)

    elif args.command == "status":
        agent.status()

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
