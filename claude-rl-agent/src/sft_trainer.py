#!/usr/bin/env python3
"""
Supervised Fine-Tuning (SFT) Trainer for Behavioral Cloning

Trains LLaMA 3.1 8B to replicate Claude's workflow design patterns using QLoRA.
"""

import os
import json
import torch
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime
import logging

try:
    from unsloth import FastLanguageModel
    from trl import SFTTrainer
    from transformers import TrainingArguments
    from datasets import Dataset
except ImportError as e:
    print(f"⚠️  Missing dependencies. Install with:")
    print(f"   pip install unsloth trl transformers datasets")
    raise e

from config import AGENT_ROOT, MODELS_DIR, DATASETS_DIR

logger = logging.getLogger(__name__)


@dataclass
class SFTConfig:
    """Configuration for SFT training."""

    # Model settings
    base_model: str = "unsloth/Meta-Llama-3.1-8B-Instruct"
    max_seq_length: int = 4096
    load_in_4bit: bool = True

    # LoRA settings
    lora_r: int = 16
    lora_alpha: int = 16
    lora_dropout: float = 0.05
    target_modules: List[str] = None

    # Training settings
    batch_size: int = 2
    gradient_accumulation_steps: int = 4
    learning_rate: float = 2e-4
    num_epochs: int = 3
    warmup_steps: int = 10
    max_steps: int = -1  # -1 means train for full epochs

    # Output settings
    output_dir: str = str(MODELS_DIR / "sft_checkpoints")
    save_steps: int = 50
    logging_steps: int = 10

    def __post_init__(self):
        if self.target_modules is None:
            # Target all attention and MLP layers for maximum learning
            self.target_modules = [
                "q_proj", "k_proj", "v_proj", "o_proj",
                "gate_proj", "up_proj", "down_proj"
            ]


class ClaudeSFTTrainer:
    """Trains LLaMA to replicate Claude's behavioral patterns."""

    def __init__(self, config: Optional[SFTConfig] = None):
        self.config = config or SFTConfig()
        self.model = None
        self.tokenizer = None
        self.trainer = None

    def load_model(self):
        """Load base model with LoRA adapters."""
        logger.info(f"Loading base model: {self.config.base_model}")

        # Determine device
        import torch
        device_map = {"": 0} if torch.cuda.is_available() else "cpu"

        self.model, self.tokenizer = FastLanguageModel.from_pretrained(
            model_name=self.config.base_model,
            max_seq_length=self.config.max_seq_length,
            dtype=None,  # Auto-detect
            load_in_4bit=self.config.load_in_4bit,
            device_map=device_map,  # Place everything on GPU 0 or CPU
        )

        # Add LoRA adapters
        logger.info(f"Adding LoRA adapters (r={self.config.lora_r})")
        self.model = FastLanguageModel.get_peft_model(
            self.model,
            r=self.config.lora_r,
            target_modules=self.config.target_modules,
            lora_alpha=self.config.lora_alpha,
            lora_dropout=self.config.lora_dropout,
            bias="none",
            use_gradient_checkpointing="unsloth",  # Memory efficient
            random_state=42,
        )

        logger.info("✅ Model loaded with LoRA adapters")

    def load_dataset(self, dataset_path: str) -> Dataset:
        """Load and format behavioral cloning dataset."""
        logger.info(f"Loading dataset: {dataset_path}")

        # Load JSONL dataset
        samples = []
        with open(dataset_path, 'r') as f:
            for line in f:
                samples.append(json.loads(line))

        logger.info(f"Loaded {len(samples)} training samples")

        # Format samples for instruction tuning
        formatted_samples = []
        for sample in samples:
            # Build the training prompt
            prompt = self._format_training_sample(sample)
            formatted_samples.append({"text": prompt})

        # Convert to HuggingFace Dataset
        dataset = Dataset.from_list(formatted_samples)
        logger.info(f"✅ Dataset formatted: {len(dataset)} samples")

        return dataset

    def _format_training_sample(self, sample: Dict) -> str:
        """Format a sample into instruction-tuning format.

        Format:
        <|begin_of_text|><|start_header_id|>system<|end_header_id|>
        You are Claude Code, an AI assistant that designs and executes workflows.
        <|eot_id|><|start_header_id|>user<|end_header_id|>
        {user_prompt}
        <|eot_id|><|start_header_id|>assistant<|end_header_id|>
        {reasoning_chain}
        Tools used: {tool_sequence}
        {response}
        <|eot_id|>
        """

        system_prompt = (
            "You are Claude Code, an AI assistant that designs and executes complex "
            "multi-step workflows. For each task, you:\n"
            "1. Analyze the request and identify constraints\n"
            "2. Design a workflow (sequence of tools and reasoning steps)\n"
            "3. Execute the workflow systematically\n"
            "4. Synthesize results into a coherent response\n\n"
            "Think step-by-step and show your reasoning process."
        )

        # Build reasoning chain text
        reasoning_text = "\n".join(sample.get('reasoning_chain', []))

        # Build tool sequence text
        tool_sequence = sample.get('tool_sequence', [])
        if tool_sequence:
            tools_text = "\n\nWorkflow executed:\n"
            for i, tool in enumerate(tool_sequence, 1):
                tools_text += f"{i}. {tool['tool']}: {tool.get('reasoning', '')}\n"
        else:
            tools_text = ""

        # Format using LLaMA 3.1 chat template
        prompt = (
            f"<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n"
            f"{system_prompt}\n"
            f"<|eot_id|><|start_header_id|>user<|end_header_id|>\n"
            f"{sample['prompt']}\n"
            f"<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n"
            f"{reasoning_text}{tools_text}\n\n"
            f"{sample['response']}\n"
            f"<|eot_id|>"
        )

        return prompt

    def train(self, dataset_path: str, output_name: Optional[str] = None):
        """Train the model on behavioral cloning data."""

        # Load model and dataset
        if self.model is None:
            self.load_model()

        dataset = self.load_dataset(dataset_path)

        # Setup output directory
        if output_name is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_name = f"claude-bc-{timestamp}"

        output_dir = Path(self.config.output_dir) / output_name
        output_dir.mkdir(parents=True, exist_ok=True)

        # Training arguments
        training_args = TrainingArguments(
            output_dir=str(output_dir),
            per_device_train_batch_size=self.config.batch_size,
            gradient_accumulation_steps=self.config.gradient_accumulation_steps,
            warmup_steps=self.config.warmup_steps,
            max_steps=self.config.max_steps,
            num_train_epochs=self.config.num_epochs,
            learning_rate=self.config.learning_rate,
            fp16=not torch.cuda.is_bf16_supported(),
            bf16=torch.cuda.is_bf16_supported(),
            logging_steps=self.config.logging_steps,
            save_steps=self.config.save_steps,
            save_total_limit=3,
            optim="adamw_8bit",  # Memory efficient optimizer
            weight_decay=0.01,
            lr_scheduler_type="cosine",
            seed=42,
            report_to="none",  # Disable wandb
        )

        # Initialize trainer
        logger.info("Initializing SFT Trainer")
        self.trainer = SFTTrainer(
            model=self.model,
            tokenizer=self.tokenizer,
            train_dataset=dataset,
            dataset_text_field="text",
            max_seq_length=self.config.max_seq_length,
            args=training_args,
            packing=False,  # Don't pack sequences
        )

        # Start training
        logger.info("=" * 70)
        logger.info("🚀 Starting Behavioral Cloning Training")
        logger.info("=" * 70)
        logger.info(f"Model: {self.config.base_model}")
        logger.info(f"Dataset: {len(dataset)} samples")
        logger.info(f"Epochs: {self.config.num_epochs}")
        logger.info(f"Batch size: {self.config.batch_size}")
        logger.info(f"Gradient accumulation: {self.config.gradient_accumulation_steps}")
        logger.info(f"Effective batch size: {self.config.batch_size * self.config.gradient_accumulation_steps}")
        logger.info(f"Learning rate: {self.config.learning_rate}")
        logger.info(f"Output: {output_dir}")
        logger.info("=" * 70)

        # Train
        self.trainer.train()

        logger.info("✅ Training complete!")

        # Save final model
        final_dir = output_dir / "final"
        logger.info(f"Saving final model to: {final_dir}")
        self.trainer.save_model(str(final_dir))

        return str(final_dir)

    def export_to_gguf(self, model_path: str, output_name: Optional[str] = None):
        """Export trained model to GGUF format for Ollama."""
        logger.info("=" * 70)
        logger.info("📦 Exporting to GGUF Format")
        logger.info("=" * 70)

        model_path = Path(model_path)
        if not model_path.exists():
            raise FileNotFoundError(f"Model not found: {model_path}")

        # Setup output
        if output_name is None:
            output_name = f"claude-bc-{datetime.now().strftime('%Y%m%d')}"

        export_dir = MODELS_DIR / "gguf"
        export_dir.mkdir(parents=True, exist_ok=True)
        output_file = export_dir / f"{output_name}.gguf"

        # Load model for export
        logger.info("Loading model for export...")
        model, tokenizer = FastLanguageModel.from_pretrained(
            model_name=str(model_path),
            max_seq_length=self.config.max_seq_length,
            dtype=None,
            load_in_4bit=False,  # Export in full precision
        )

        # Export
        logger.info(f"Exporting to: {output_file}")
        model.save_pretrained_gguf(
            str(export_dir),
            tokenizer,
            quantization_method="q4_k_m",  # 4-bit quantization
        )

        # Rename to our desired name
        exported_files = list(export_dir.glob("*.gguf"))
        if exported_files:
            exported_files[0].rename(output_file)
            logger.info(f"✅ Exported to: {output_file}")
            return str(output_file)
        else:
            raise RuntimeError("Export failed - no GGUF file created")


def main():
    """CLI entry point for SFT training."""
    import argparse

    parser = argparse.ArgumentParser(description="Train LLaMA with behavioral cloning")
    parser.add_argument("--dataset", required=True, help="Path to training dataset (JSONL)")
    parser.add_argument("--output-name", help="Name for output model")
    parser.add_argument("--export-gguf", action="store_true", help="Export to GGUF after training")
    parser.add_argument("--epochs", type=int, default=3, help="Number of training epochs")
    parser.add_argument("--batch-size", type=int, default=2, help="Batch size per device")
    parser.add_argument("--learning-rate", type=float, default=2e-4, help="Learning rate")

    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Create config
    config = SFTConfig(
        num_epochs=args.epochs,
        batch_size=args.batch_size,
        learning_rate=args.learning_rate,
    )

    # Train
    trainer = ClaudeSFTTrainer(config)
    model_path = trainer.train(args.dataset, args.output_name)

    # Export to GGUF if requested
    if args.export_gguf:
        trainer.export_to_gguf(model_path, args.output_name)

    print()
    print("=" * 70)
    print("✅ TRAINING COMPLETE!")
    print("=" * 70)
    print(f"Model saved: {model_path}")
    print()


if __name__ == "__main__":
    main()
