#!/usr/bin/env npx tsx
/**
 * Command Center — AI RL Agent Runner
 *
 * Main entry point for the reinforcement learning agent.
 * Evaluates AI responses, submits training feedback, and manages RL lifecycle.
 *
 * Modes:
 *   evaluate      — Evaluate responses without submitting feedback (default)
 *   train-cycle   — Full evaluate → feedback → train → re-evaluate cycle
 *   status        — Print RL system status
 *   weights       — Show current reward weights
 *
 * Usage:
 *   npx tsx src/rl-runner.ts                              # Evaluate all
 *   npx tsx src/rl-runner.ts --mode evaluate               # Evaluate only
 *   npx tsx src/rl-runner.ts --mode train-cycle            # Full training cycle
 *   npx tsx src/rl-runner.ts --mode status                 # Show RL status
 *   npx tsx src/rl-runner.ts --mode weights                # Show reward weights
 *   npx tsx src/rl-runner.ts --id rl-eval-001              # Single scenario
 *   npx tsx src/rl-runner.ts --category "Widget Quality"   # Filter by category
 *   npx tsx src/rl-runner.ts --headed                      # Show browser
 *   npx tsx src/rl-runner.ts --list                        # List scenarios
 */
export {};
//# sourceMappingURL=rl-runner.d.ts.map