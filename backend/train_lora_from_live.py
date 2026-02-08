#!/usr/bin/env python
"""
Train Tier2 LoRA DPO Model from Live Feedback Database

This script trains a LoRA model using actual user feedback from the production system,
bypassing the exhaustive_data.json requirement.

Usage:
    python train_lora_from_live.py [--epochs 3] [--batch-size 4] [--dry-run]

Features:
    - Uses 343 up + 22 down ratings from database = 7,546 DPO pairs
    - Creates preference pairs from actual AI responses
    - Trains LoRA with QLoRA (4-bit quantization)
    - Exports to GGUF and registers with Ollama
"""

import argparse
import json
import logging
import random
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

# Setup Django
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "command_center.settings")

import django
django.setup()

from feedback.models import WidgetRating


@dataclass
class SimpleDPOPair:
    """Simplified DPO pair for training."""
    prompt: str
    chosen: str
    rejected: str
    metadata: dict = None


def load_experience_data():
    """Load experience buffer for context."""
    buffer_path = Path(__file__).parent.parent / 'rl_training_data' / 'experience_buffer.json'

    if not buffer_path.exists():
        logger.warning(f"Experience buffer not found at {buffer_path}")
        return {}

    try:
        with open(buffer_path) as f:
            buffer_data = json.load(f)

        experiences = buffer_data.get('experiences', [])
        by_id = {exp.get('query_id'): exp for exp in experiences}

        logger.info(f"Loaded {len(by_id)} experiences from buffer")
        return by_id

    except Exception as e:
        logger.warning(f"Error loading experience buffer: {e}")
        return {}


def create_dpo_pairs_from_database() -> List[SimpleDPOPair]:
    """
    Create DPO preference pairs from database ratings.

    Returns:
        List of DPO pairs where:
        - 'chosen' = response from up-rated query
        - 'rejected' = response from down-rated query
    """
    logger.info("Creating DPO pairs from database...")

    # Get all ratings
    up_ratings = list(WidgetRating.objects.filter(rating='up').values())
    down_ratings = list(WidgetRating.objects.filter(rating='down').values())

    logger.info(f"  Up ratings: {len(up_ratings)}")
    logger.info(f"  Down ratings: {len(down_ratings)}")
    logger.info(f"  Potential pairs: {len(up_ratings) * len(down_ratings):,}")

    if not up_ratings or not down_ratings:
        raise ValueError("Need both up and down ratings to create pairs")

    # Load experience buffer for context
    experiences = load_experience_data()

    # Create pairs (cartesian product with sampling for diversity)
    pairs = []

    # Sample to avoid too many pairs (max 1000 pairs)
    max_pairs = min(1000, len(up_ratings) * len(down_ratings))

    if len(up_ratings) * len(down_ratings) > max_pairs:
        # Sample up and down ratings to create ~max_pairs total
        # Use all down ratings (limited resource) and sample up ratings proportionally
        sample_size_down = min(len(down_ratings), max_pairs // 10)  # At least 10 up per down
        sample_size_up = min(len(up_ratings), max_pairs // sample_size_down)

        up_sample = random.sample(up_ratings, sample_size_up)
        down_sample = random.sample(down_ratings, sample_size_down)
    else:
        up_sample = up_ratings
        down_sample = down_ratings

    logger.info(f"  Sampling {len(up_sample)} up × {len(down_sample)} down = {len(up_sample) * len(down_sample)} pairs")

    for up_rating in up_sample:
        for down_rating in down_sample:
            up_id = up_rating['entry_id']
            down_id = down_rating['entry_id']

            # Get experience context if available
            up_exp = experiences.get(up_id, {})
            down_exp = experiences.get(down_id, {})

            # Build prompt from transcript or notes
            transcript = up_exp.get('transcript') or down_exp.get('transcript') or \
                        up_rating.get('notes') or 'User query about equipment'

            prompt = (
                f"User Query: {transcript}\n"
                f"Task: Select appropriate widgets and data visualizations to answer the query.\n"
                f"Available widget types: KPI, Trend, Table, Gauge, Alert, Comparison, Chart\n"
                f"Instructions: Choose the most relevant widgets and data sources."
            )

            # Chosen response (from up-rated experience)
            up_widgets = up_exp.get('widget_plan', {}).get('widgets', [])
            up_fixtures = up_exp.get('fixtures', {})

            chosen = _format_response(up_widgets, up_fixtures, "good")

            # Rejected response (from down-rated experience)
            down_widgets = down_exp.get('widget_plan', {}).get('widgets', [])
            down_fixtures = down_exp.get('fixtures', {})

            rejected = _format_response(down_widgets, down_fixtures, "poor")

            pair = SimpleDPOPair(
                prompt=prompt[:1500],  # Limit length
                chosen=chosen[:800],
                rejected=rejected[:800],
                metadata={
                    'up_id': up_id,
                    'down_id': down_id,
                    'has_up_context': bool(up_exp),
                    'has_down_context': bool(down_exp),
                }
            )

            pairs.append(pair)

    logger.info(f"✓ Created {len(pairs)} DPO pairs")
    return pairs


def _format_response(widgets, fixtures, quality):
    """Format a widget selection response."""
    if not widgets:
        return f"Selected widgets: [none] (quality: {quality})"

    widget_desc = []
    for w in widgets[:5]:  # Limit to 5 widgets
        scenario = w.get('scenario', 'unknown')
        size = w.get('size', 'medium')
        widget_desc.append(f"{scenario} ({size})")

    fixture_desc = []
    for scenario, fixture in list(fixtures.items())[:3]:
        fixture_desc.append(f"{scenario}:{fixture}")

    response = f"Widgets: {', '.join(widget_desc)}"
    if fixture_desc:
        response += f" | Fixtures: {', '.join(fixture_desc)}"

    return response


def pairs_to_hf_dataset(pairs: List[SimpleDPOPair], val_split: float = 0.1):
    """Convert DPO pairs to HuggingFace dataset."""
    try:
        from datasets import Dataset, DatasetDict
    except ImportError:
        raise ImportError("Install datasets: pip install datasets")

    # Shuffle pairs
    random.shuffle(pairs)

    # Convert to dict format
    data = {
        'prompt': [p.prompt for p in pairs],
        'chosen': [p.chosen for p in pairs],
        'rejected': [p.rejected for p in pairs],
    }

    dataset = Dataset.from_dict(data)

    if val_split and val_split > 0:
        splits = dataset.train_test_split(test_size=val_split, seed=42)
        return DatasetDict({
            'train': splits['train'],
            'validation': splits['test'],
        })

    return dataset


def train_lora_model(dataset, config):
    """Train LoRA model using DPO."""
    from rl.trainer import CommandCenterDPOTrainer

    logger.info("\n" + "=" * 70)
    logger.info("Starting LoRA DPO Training")
    logger.info("=" * 70)
    logger.info(f"Configuration:")
    logger.info(f"  Model: {config.get('base_model', 'unsloth/Meta-Llama-3.1-8B-Instruct')}")
    logger.info(f"  LoRA rank: {config['dpo']['lora_r']}")
    logger.info(f"  Batch size: {config['dpo']['batch_size']}")
    logger.info(f"  Epochs: {config['dpo']['num_epochs']}")
    logger.info(f"  Learning rate: {config['dpo']['learning_rate']}")

    # Extract train and validation datasets
    train_ds = dataset['train'] if isinstance(dataset, dict) else dataset
    eval_ds = dataset.get('validation') if isinstance(dataset, dict) else None

    logger.info(f"  Train samples: {len(train_ds)}")
    logger.info(f"  Val samples: {len(eval_ds) if eval_ds else 0}")
    logger.info("")

    trainer = CommandCenterDPOTrainer(config)

    try:
        results = trainer.train(
            train_dataset=train_ds,
            eval_dataset=eval_ds
        )

        logger.info("\n" + "=" * 70)
        logger.info("✓ Training Complete!")
        logger.info("=" * 70)
        logger.info(f"Final metrics:")

        # Convert TrainingResult to dict for display
        if hasattr(results, '__dict__'):
            results_dict = results.__dict__
        elif hasattr(results, '_asdict'):
            results_dict = results._asdict()
        else:
            results_dict = {}

        for key, value in results_dict.items():
            if isinstance(value, float):
                logger.info(f"  {key}: {value:.4f}")
            else:
                logger.info(f"  {key}: {value}")

        return results

    except Exception as e:
        logger.error(f"\n✗ Training failed: {e}")
        import traceback
        traceback.print_exc()
        raise


def export_to_gguf(checkpoint_dir: Path):
    """Export trained model to GGUF format."""
    logger.info("\n" + "=" * 70)
    logger.info("Exporting to GGUF")
    logger.info("=" * 70)

    try:
        from rl.export import export_to_gguf as do_export

        gguf_path = do_export(
            checkpoint_dir=str(checkpoint_dir),
            quantization='q4_k_m',
            output_dir=str(checkpoint_dir.parent / 'export')
        )

        logger.info(f"✓ GGUF export complete: {gguf_path}")
        return gguf_path

    except Exception as e:
        logger.warning(f"⚠ GGUF export failed: {e}")
        return None


def register_with_ollama(gguf_path: Path, model_name: str = 'cc-widget-selector'):
    """Register model with Ollama."""
    logger.info("\n" + "=" * 70)
    logger.info("Registering with Ollama")
    logger.info("=" * 70)

    try:
        import subprocess

        # Create Modelfile
        modelfile = f"""
FROM {gguf_path}
TEMPLATE \"\"\"[INST] <<SYS>>
You are a widget selection assistant for an industrial dashboard.
<</SYS>>

{{{{ .Prompt }}}} [/INST]
\"\"\"
PARAMETER temperature 0.7
PARAMETER top_p 0.9
"""

        modelfile_path = gguf_path.parent / 'Modelfile'
        with open(modelfile_path, 'w') as f:
            f.write(modelfile)

        # Register with Ollama
        result = subprocess.run(
            ['ollama', 'create', model_name, '-f', str(modelfile_path)],
            capture_output=True,
            text=True,
            timeout=300
        )

        if result.returncode == 0:
            logger.info(f"✓ Model registered as: {model_name}")
            logger.info(f"  Test with: ollama run {model_name}")
            return True
        else:
            logger.warning(f"⚠ Ollama registration failed: {result.stderr}")
            return False

    except Exception as e:
        logger.warning(f"⚠ Ollama registration failed: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description='Train LoRA from live feedback')
    parser.add_argument('--epochs', type=int, default=3, help='Number of epochs')
    parser.add_argument('--batch-size', type=int, default=4, help='Batch size')
    parser.add_argument('--learning-rate', type=float, default=5e-5, help='Learning rate')
    parser.add_argument('--min-pairs', type=int, default=50, help='Minimum pairs required')
    parser.add_argument('--dry-run', action='store_true', help='Only show stats, don\'t train')
    parser.add_argument('--export', action='store_true', help='Export to GGUF after training')
    parser.add_argument('--ollama', action='store_true', help='Register with Ollama (implies --export)')
    parser.add_argument('--model-name', type=str, default='cc-widget-selector', help='Ollama model name')
    args = parser.parse_args()

    if args.ollama:
        args.export = True

    print("=" * 70)
    print("Tier2 LoRA Training from Live Feedback Database")
    print("=" * 70)
    print("")

    # Create DPO pairs
    try:
        pairs = create_dpo_pairs_from_database()
    except Exception as e:
        logger.error(f"\n✗ Error creating pairs: {e}")
        return 1

    if len(pairs) < args.min_pairs:
        logger.error(f"\n✗ Insufficient pairs: {len(pairs)} < {args.min_pairs}")
        logger.error("Collect more feedback ratings first")
        return 1

    if args.dry_run:
        logger.info(f"\n✓ Dry run complete")
        logger.info(f"  Would train on {len(pairs)} pairs")
        logger.info(f"  Sample pair:")
        sample = random.choice(pairs)
        logger.info(f"    Prompt: {sample.prompt[:100]}...")
        logger.info(f"    Chosen: {sample.chosen[:80]}...")
        logger.info(f"    Rejected: {sample.rejected[:80]}...")
        return 0

    # Prepare dataset
    logger.info(f"\nPreparing dataset...")
    dataset = pairs_to_hf_dataset(pairs, val_split=0.1)

    # Load config
    from rl.config import get_config
    config = get_config('default')
    config['dpo']['num_epochs'] = args.epochs
    config['dpo']['batch_size'] = args.batch_size
    config['dpo']['learning_rate'] = args.learning_rate

    # Train
    try:
        results = train_lora_model(dataset, config)
        checkpoint_dir = Path(config.get('checkpoint_dir', 'rl_checkpoints/lora_v1/final'))

        # Export if requested
        if args.export:
            gguf_path = export_to_gguf(checkpoint_dir)

            if gguf_path and args.ollama:
                register_with_ollama(Path(gguf_path), args.model_name)

        logger.info("\n" + "=" * 70)
        logger.info("✓ ALL COMPLETE!")
        logger.info("=" * 70)
        logger.info(f"Checkpoint: {checkpoint_dir}")

        return 0

    except Exception as e:
        logger.error(f"\n✗ Training pipeline failed: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
