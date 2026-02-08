#!/usr/bin/env python
"""
Automated Response Evaluation using Claude Code CLI

This script uses Claude Code to evaluate AI widget selections and provide
thumbs up/down feedback automatically. Claude acts as the "human" supervisor,
creating a self-improving feedback loop.

Usage:
    python auto_evaluate_responses.py [--batch-size 10] [--continuous]

Features:
    - Claude evaluates widget selections for appropriateness
    - Automatic thumbs up/down ratings based on Claude's judgment
    - Stores ratings in database for RL training
    - Can run continuously or one-shot
"""

import argparse
import json
import logging
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
from django.utils import timezone

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "command_center.settings")
import django
django.setup()

from feedback.models import WidgetRating


def load_experience_buffer() -> Dict:
    """Load the experience buffer from disk."""
    buffer_path = Path(__file__).parent.parent / 'rl_training_data' / 'experience_buffer.json'

    if not buffer_path.exists():
        logger.error(f"Experience buffer not found at {buffer_path}")
        return {"experiences": []}

    try:
        with open(buffer_path) as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading experience buffer: {e}")
        return {"experiences": []}


def get_unrated_experiences(experiences: List[Dict], limit: int = 10) -> List[Dict]:
    """Get experiences that haven't been rated yet."""
    unrated = []

    for exp in experiences:
        query_id = exp.get('query_id')
        if not query_id:
            continue

        # Check if already rated
        existing = WidgetRating.objects.filter(entry_id=query_id).first()
        if existing:
            continue

        # Must have widget plan to evaluate
        if not exp.get('widget_plan') or not exp.get('widget_plan', {}).get('widgets'):
            continue

        unrated.append(exp)
        if len(unrated) >= limit:
            break

    return unrated


def evaluate_with_claude(experience: Dict) -> Optional[str]:
    """
    Use Claude Code CLI to evaluate if widget selections are appropriate.

    Returns:
        'up' if appropriate, 'down' if inappropriate, None if uncertain
    """
    query_id = experience.get('query_id')
    transcript = experience.get('transcript', 'Unknown query')
    intent = experience.get('intent', {})
    widget_plan = experience.get('widget_plan', {})
    widgets = widget_plan.get('widgets', [])

    # Build context for Claude
    evaluation_prompt = f"""Evaluate this AI widget selection for an industrial dashboard:

**User Query**: {transcript}

**Intent Detected**:
- Primary intent: {intent.get('primary_intent', 'unknown')}
- Confidence: {intent.get('confidence', 0):.2f}

**Widgets Selected by AI**:
"""

    for i, widget in enumerate(widgets, 1):
        scenario = widget.get('scenario', 'unknown')
        size = widget.get('size', 'medium')
        evaluation_prompt += f"{i}. {scenario} ({size})\n"

    evaluation_prompt += """
**Available Widget Types**: KPI, Trend, Table, Gauge, Alert, Comparison, Chart, Distribution

**Evaluation Criteria**:
1. Are the selected widgets appropriate for answering the user's query?
2. Does the widget selection match the intent (monitoring, comparison, troubleshooting, etc.)?
3. Are the widget types suitable for the data being requested?
4. Is the widget size/prominence appropriate?

**Your Task**:
Evaluate if this widget selection is GOOD or POOR.

Reply with EXACTLY ONE WORD:
- "GOOD" if the selection is appropriate and helpful
- "POOR" if the selection is inappropriate, missing key widgets, or includes irrelevant widgets

Your evaluation (GOOD or POOR):"""

    try:
        # Call Claude Code CLI
        logger.info(f"  Evaluating query_id={query_id}: {transcript[:50]}...")

        result = subprocess.run(
            ['claude'],
            input=evaluation_prompt,
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode != 0:
            logger.warning(f"  Claude CLI failed: {result.stderr}")
            return None

        # Parse response
        response = result.stdout.strip().upper()

        if 'GOOD' in response:
            logger.info(f"  ✓ GOOD - Thumbs up!")
            return 'up'
        elif 'POOR' in response:
            logger.info(f"  ✗ POOR - Thumbs down")
            return 'down'
        else:
            logger.warning(f"  ? Uncertain response: {response[:100]}")
            return None

    except subprocess.TimeoutExpired:
        logger.warning(f"  Timeout evaluating {query_id}")
        return None
    except Exception as e:
        logger.error(f"  Error evaluating {query_id}: {e}")
        return None


def create_rating(experience: Dict, rating: str):
    """Create a WidgetRating entry in the database."""
    query_id = experience.get('query_id')

    # Create rating
    now = timezone.now()
    WidgetRating.objects.create(
        entry_id=query_id,
        rating=rating,
        rated_at=now,
        device_id='claude-auto-evaluator',
        notes=f"Auto-evaluated by Claude Code CLI at {now.isoformat()}"
    )

    logger.info(f"  ✓ Rating saved to database: {rating}")


def evaluate_batch(batch_size: int = 10) -> Dict[str, int]:
    """Evaluate a batch of unrated experiences."""
    logger.info("=" * 70)
    logger.info("Automated Response Evaluation with Claude Code")
    logger.info("=" * 70)

    # Load experiences
    buffer_data = load_experience_buffer()
    experiences = buffer_data.get('experiences', [])

    logger.info(f"Total experiences in buffer: {len(experiences)}")

    # Get unrated
    unrated = get_unrated_experiences(experiences, limit=batch_size)

    if not unrated:
        logger.info("No unrated experiences found!")
        return {"evaluated": 0, "up": 0, "down": 0, "uncertain": 0}

    logger.info(f"Found {len(unrated)} unrated experiences")
    logger.info("")

    stats = {"evaluated": 0, "up": 0, "down": 0, "uncertain": 0}

    for i, exp in enumerate(unrated, 1):
        logger.info(f"[{i}/{len(unrated)}] Evaluating...")

        # Evaluate with Claude
        rating = evaluate_with_claude(exp)

        if rating:
            # Save to database
            create_rating(exp, rating)
            stats["evaluated"] += 1
            stats[rating] += 1
        else:
            stats["uncertain"] += 1

        logger.info("")

        # Small delay to avoid rate limits
        if i < len(unrated):
            time.sleep(2)

    return stats


def run_continuous(batch_size: int = 10, interval: int = 300):
    """Run continuous evaluation loop."""
    logger.info("Starting continuous evaluation mode")
    logger.info(f"Batch size: {batch_size}, Interval: {interval}s")
    logger.info("")

    iteration = 0

    while True:
        iteration += 1
        logger.info(f"\n{'='*70}")
        logger.info(f"Iteration {iteration}")
        logger.info(f"{'='*70}\n")

        try:
            stats = evaluate_batch(batch_size)

            logger.info("\n" + "=" * 70)
            logger.info(f"Batch Complete - Iteration {iteration}")
            logger.info("=" * 70)
            logger.info(f"  Evaluated: {stats['evaluated']}")
            logger.info(f"  Thumbs up: {stats['up']}")
            logger.info(f"  Thumbs down: {stats['down']}")
            logger.info(f"  Uncertain: {stats['uncertain']}")
            logger.info(f"\nNext evaluation in {interval}s...")

            time.sleep(interval)

        except KeyboardInterrupt:
            logger.info("\n\nStopping continuous evaluation...")
            break
        except Exception as e:
            logger.error(f"Error in iteration {iteration}: {e}")
            time.sleep(60)


def main():
    parser = argparse.ArgumentParser(description='Automated response evaluation with Claude Code')
    parser.add_argument('--batch-size', type=int, default=10, help='Number of experiences to evaluate per batch')
    parser.add_argument('--continuous', action='store_true', help='Run continuously')
    parser.add_argument('--interval', type=int, default=300, help='Seconds between evaluations (continuous mode)')
    args = parser.parse_args()

    if args.continuous:
        run_continuous(args.batch_size, args.interval)
    else:
        stats = evaluate_batch(args.batch_size)

        print("\n" + "=" * 70)
        print("Evaluation Complete!")
        print("=" * 70)
        print(f"  Evaluated: {stats['evaluated']}")
        print(f"  Thumbs up: {stats['up']}")
        print(f"  Thumbs down: {stats['down']}")
        print(f"  Uncertain: {stats['uncertain']}")
        print("")

        # Show current database stats
        total_ratings = WidgetRating.objects.count()
        up_count = WidgetRating.objects.filter(rating='up').count()
        down_count = WidgetRating.objects.filter(rating='down').count()

        print(f"Database Stats:")
        print(f"  Total ratings: {total_ratings}")
        print(f"  Up votes: {up_count}")
        print(f"  Down votes: {down_count}")
        print(f"  DPO pairs available: {up_count * down_count:,}")
        print("")

        return 0


if __name__ == '__main__':
    sys.exit(main())
