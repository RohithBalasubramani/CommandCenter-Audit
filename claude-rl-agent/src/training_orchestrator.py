#!/usr/bin/env python3
"""
Continuous Training Orchestrator

Manages the full training lifecycle:
1. Monitor trace collection
2. Trigger dataset building at thresholds
3. Run SFT training
4. Run PPO training
5. Export to GGUF
6. Deploy to Ollama
7. Run evaluation tests
8. Repeat
"""

import os
import time
import logging
from pathlib import Path
from typing import Optional, Dict
from datetime import datetime
from dataclasses import dataclass
import json

from config import AGENT_ROOT, MODELS_DIR, DATASETS_DIR
from claude_trace_schema import TraceStorage
from behavioral_cloning_builder import BehavioralCloningDatasetBuilder
from sft_trainer import ClaudeSFTTrainer, SFTConfig
from ppo_trainer import ClaudePPOTrainer, PPOTrainingConfig

logger = logging.getLogger(__name__)


@dataclass
class OrchestratorConfig:
    """Configuration for training orchestrator."""

    # Thresholds
    min_traces_for_sft: int = 50
    min_traces_for_ppo: int = 100
    traces_per_training_cycle: int = 50

    # Training cycles
    sft_frequency: int = 1  # Run SFT every N cycles
    ppo_frequency: int = 2  # Run PPO every N cycles (after SFT)

    # Model versioning
    model_name_prefix: str = "claude-bc"
    keep_last_n_models: int = 3

    # Automation
    auto_export_gguf: bool = True
    auto_deploy_ollama: bool = False  # Disabled by default (requires user approval)
    auto_evaluate: bool = True

    # Monitoring
    check_interval_seconds: int = 300  # Check for new traces every 5 minutes


class TrainingOrchestrator:
    """
    Orchestrates continuous training pipeline.

    This is the brain of the automated system:
    - Monitors trace collection
    - Triggers training when thresholds are met
    - Manages model versioning
    - Tracks training history
    """

    def __init__(self, config: Optional[OrchestratorConfig] = None):
        self.config = config or OrchestratorConfig()

        # Storage
        self.trace_storage = TraceStorage()
        self.history_file = AGENT_ROOT / "data" / "training_history.json"
        self.history = self._load_history()

        # Training state
        self.last_trained_trace_count = 0
        self.training_cycle = 0
        self.sft_model_path = None
        self.ppo_model_path = None

    def _load_history(self) -> Dict:
        """Load training history from disk."""
        if self.history_file.exists():
            with open(self.history_file, 'r') as f:
                return json.load(f)
        return {
            "cycles": [],
            "models": [],
            "last_sft": None,
            "last_ppo": None,
            "total_traces_used": 0,
        }

    def _save_history(self):
        """Save training history to disk."""
        self.history_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.history_file, 'w') as f:
            json.dump(self.history, f, indent=2)

    def check_training_needed(self) -> tuple[bool, str]:
        """
        Check if training should be triggered.

        Returns:
            (should_train, reason)
        """
        trace_count = self.trace_storage.get_trace_count()
        new_traces = trace_count - self.last_trained_trace_count

        # First time: need minimum traces for SFT
        if self.training_cycle == 0:
            if trace_count >= self.config.min_traces_for_sft:
                return True, f"Initial training: {trace_count} traces available"
            else:
                return False, f"Need {self.config.min_traces_for_sft - trace_count} more traces"

        # Subsequent cycles: check for threshold
        if new_traces >= self.config.traces_per_training_cycle:
            return True, f"Training cycle {self.training_cycle + 1}: {new_traces} new traces"

        return False, f"Only {new_traces} new traces (need {self.config.traces_per_training_cycle})"

    def run_training_cycle(self):
        """Execute a full training cycle."""
        self.training_cycle += 1

        logger.info("=" * 70)
        logger.info(f"🎯 TRAINING CYCLE {self.training_cycle}")
        logger.info("=" * 70)

        cycle_start = datetime.now()
        cycle_info = {
            "cycle": self.training_cycle,
            "start_time": cycle_start.isoformat(),
            "traces_used": self.trace_storage.get_trace_count(),
        }

        try:
            # Step 1: Build dataset
            logger.info("\n📊 Step 1: Building training dataset")
            dataset_path = self._build_dataset()
            cycle_info["dataset"] = str(dataset_path)

            # Step 2: Run SFT if scheduled
            if self.training_cycle % self.config.sft_frequency == 0:
                logger.info("\n🎓 Step 2: Running SFT (Behavioral Cloning)")
                self.sft_model_path = self._run_sft_training(dataset_path)
                cycle_info["sft_model"] = str(self.sft_model_path)
                self.history["last_sft"] = str(self.sft_model_path)

            # Step 3: Run PPO if scheduled and SFT exists
            if (self.training_cycle % self.config.ppo_frequency == 0 and
                self.sft_model_path is not None):
                logger.info("\n🎮 Step 3: Running PPO (RL Alignment)")
                self.ppo_model_path = self._run_ppo_training(dataset_path)
                cycle_info["ppo_model"] = str(self.ppo_model_path)
                self.history["last_ppo"] = str(self.ppo_model_path)

            # Step 4: Export to GGUF if enabled
            if self.config.auto_export_gguf:
                logger.info("\n📦 Step 4: Exporting to GGUF")
                # Use PPO model if available, otherwise SFT
                export_model = self.ppo_model_path or self.sft_model_path
                if export_model:
                    gguf_path = self._export_to_gguf(export_model)
                    cycle_info["gguf_model"] = str(gguf_path)

            # Step 5: Deploy to Ollama if enabled
            if self.config.auto_deploy_ollama:
                logger.info("\n🚀 Step 5: Deploying to Ollama")
                # This would deploy the GGUF model
                # Disabled by default - requires user approval
                pass

            # Step 6: Run evaluation if enabled
            if self.config.auto_evaluate:
                logger.info("\n✅ Step 6: Running evaluation")
                eval_results = self._run_evaluation()
                cycle_info["evaluation"] = eval_results

            # Update state
            self.last_trained_trace_count = self.trace_storage.get_trace_count()
            cycle_info["end_time"] = datetime.now().isoformat()
            cycle_info["duration_minutes"] = (
                datetime.now() - cycle_start
            ).total_seconds() / 60

            # Save to history
            self.history["cycles"].append(cycle_info)
            self.history["total_traces_used"] = self.last_trained_trace_count
            self._save_history()

            logger.info("\n" + "=" * 70)
            logger.info(f"✅ CYCLE {self.training_cycle} COMPLETE!")
            logger.info(f"   Duration: {cycle_info['duration_minutes']:.1f} minutes")
            logger.info("=" * 70)

        except Exception as e:
            logger.error(f"❌ Training cycle failed: {e}")
            cycle_info["error"] = str(e)
            cycle_info["status"] = "failed"
            self.history["cycles"].append(cycle_info)
            self._save_history()
            raise

    def _build_dataset(self) -> Path:
        """Build training dataset from traces."""
        builder = BehavioralCloningDatasetBuilder(self.trace_storage)
        samples = builder.build_dataset(
            min_reasoning_steps=2,
            require_multi_step=True
        )

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        dataset_path = DATASETS_DIR / f"bc_dataset_{timestamp}.jsonl"

        builder.save_dataset(
            output_path=dataset_path,
            format="jsonl"
        )

        stats = builder.get_statistics()
        logger.info(f"✅ Dataset built: {stats['total_samples']} samples")

        return dataset_path

    def _run_sft_training(self, dataset_path: Path) -> Path:
        """Run SFT training."""
        config = SFTConfig(
            num_epochs=3,
            batch_size=2,
            learning_rate=2e-4,
        )

        trainer = ClaudeSFTTrainer(config)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_name = f"{self.config.model_name_prefix}-sft-{timestamp}"

        model_path = trainer.train(str(dataset_path), output_name)
        logger.info(f"✅ SFT training complete: {model_path}")

        return Path(model_path)

    def _run_ppo_training(self, dataset_path: Path) -> Path:
        """Run PPO training."""
        if self.sft_model_path is None:
            raise ValueError("Cannot run PPO without SFT model")

        config = PPOTrainingConfig(
            sft_model_path=str(self.sft_model_path),
            num_episodes=100,
            learning_rate=1.4e-5,
        )

        trainer = ClaudePPOTrainer(config)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_name = f"{self.config.model_name_prefix}-ppo-{timestamp}"

        model_path = trainer.train(str(dataset_path), output_name)
        logger.info(f"✅ PPO training complete: {model_path}")

        return Path(model_path)

    def _export_to_gguf(self, model_path: Path) -> Path:
        """Export model to GGUF format."""
        # Use the SFT trainer's export method
        trainer = ClaudeSFTTrainer()
        timestamp = datetime.now().strftime("%Y%m%d")
        output_name = f"{self.config.model_name_prefix}-{timestamp}"

        gguf_path = trainer.export_to_gguf(str(model_path), output_name)
        logger.info(f"✅ GGUF export complete: {gguf_path}")

        return Path(gguf_path)

    def _run_evaluation(self) -> Dict:
        """Run evaluation on current model."""
        # TODO: Implement evaluation
        # For now, return dummy results
        return {
            "status": "not_implemented",
            "timestamp": datetime.now().isoformat(),
        }

    def run_continuous_loop(self):
        """Run continuous training loop."""
        logger.info("=" * 70)
        logger.info(" 🤖 CONTINUOUS TRAINING ORCHESTRATOR")
        logger.info("=" * 70)
        logger.info(f"Check interval: {self.config.check_interval_seconds}s")
        logger.info(f"SFT threshold: {self.config.min_traces_for_sft} traces")
        logger.info(f"Training cycle size: {self.config.traces_per_training_cycle} traces")
        logger.info("=" * 70)

        while True:
            try:
                # Check if training is needed
                should_train, reason = self.check_training_needed()

                trace_count = self.trace_storage.get_trace_count()
                logger.info(f"\n📊 Status: {trace_count} traces collected")
                logger.info(f"   {reason}")

                if should_train:
                    logger.info("\n🚀 Triggering training cycle...")
                    self.run_training_cycle()
                else:
                    logger.info(f"\n⏳ Waiting for more traces...")

                # Wait before next check
                time.sleep(self.config.check_interval_seconds)

            except KeyboardInterrupt:
                logger.info("\n\n⚠️  Orchestrator stopped by user")
                break
            except Exception as e:
                logger.error(f"\n\n❌ Error in orchestrator: {e}")
                logger.info("Retrying in 60 seconds...")
                time.sleep(60)

    def get_status(self) -> Dict:
        """Get current orchestrator status."""
        trace_count = self.trace_storage.get_trace_count()
        new_traces = trace_count - self.last_trained_trace_count

        return {
            "training_cycle": self.training_cycle,
            "total_traces": trace_count,
            "new_traces_since_last_training": new_traces,
            "next_training_in": max(
                0,
                self.config.traces_per_training_cycle - new_traces
            ),
            "last_sft_model": self.history.get("last_sft"),
            "last_ppo_model": self.history.get("last_ppo"),
            "total_cycles_completed": len(self.history["cycles"]),
        }


def main():
    """CLI entry point for orchestrator."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Continuous training orchestrator"
    )
    parser.add_argument(
        "--mode",
        choices=["continuous", "once", "status"],
        default="continuous",
        help="Run mode"
    )
    parser.add_argument(
        "--sft-threshold",
        type=int,
        default=50,
        help="Minimum traces for SFT training"
    )
    parser.add_argument(
        "--cycle-size",
        type=int,
        default=50,
        help="Traces per training cycle"
    )

    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    # Create orchestrator
    config = OrchestratorConfig(
        min_traces_for_sft=args.sft_threshold,
        traces_per_training_cycle=args.cycle_size,
    )
    orchestrator = TrainingOrchestrator(config)

    if args.mode == "status":
        # Print status
        status = orchestrator.get_status()
        print(json.dumps(status, indent=2))

    elif args.mode == "once":
        # Run one training cycle
        should_train, reason = orchestrator.check_training_needed()
        if should_train:
            orchestrator.run_training_cycle()
        else:
            print(f"Training not needed: {reason}")

    else:
        # Run continuous loop
        orchestrator.run_continuous_loop()


if __name__ == "__main__":
    main()
