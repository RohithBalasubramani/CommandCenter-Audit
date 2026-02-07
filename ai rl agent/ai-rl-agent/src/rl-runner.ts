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

import * as fs from 'fs'
import * as path from 'path'
import { chromium } from '@playwright/test'
import { AITestRunner, generateAuditReport, runScenarios } from './test-runner.js'
import { rlAgentConfig, rlRunnerConfig, rlConfig } from './rl-config.js'
import { rlScenarios, EVAL_QUERIES } from './rl-scenarios.js'
import { RLClient } from './rl-client.js'
import { RLEvaluator, type RLEvaluation, type PageWidget } from './rl-evaluator.js'
import type { TestScenario, ScenarioResult } from './types.js'

// ─── CLI Argument Parsing ───────────────────────────────────────────

type RunMode = 'evaluate' | 'train-cycle' | 'status' | 'weights' | 'api-eval'

interface CLIArgs {
  mode: RunMode
  category?: string
  id?: string
  tag?: string
  priority?: string
  headed?: boolean
  list?: boolean
  dryRun?: boolean
}

function parseArgs(): CLIArgs {
  const args = process.argv.slice(2)
  const parsed: CLIArgs = { mode: 'evaluate' }

  for (let i = 0; i < args.length; i++) {
    switch (args[i]) {
      case '--mode':
        parsed.mode = args[++i] as RunMode
        break
      case '--category':
        parsed.category = args[++i]
        break
      case '--id':
        parsed.id = args[++i]
        break
      case '--tag':
        parsed.tag = args[++i]
        break
      case '--priority':
        parsed.priority = args[++i]
        break
      case '--headed':
        parsed.headed = true
        break
      case '--list':
        parsed.list = true
        break
      case '--dry-run':
        parsed.dryRun = true
        break
      case '--help':
      case '-h':
        printUsage()
        process.exit(0)
    }
  }
  return parsed
}

function printUsage() {
  console.log(`
Command Center — AI RL Agent
══════════════════════════════

Usage: npx tsx src/rl-runner.ts [options]

Modes:
  --mode evaluate       Browser+API evaluation (no feedback submitted) [default]
  --mode api-eval       Pure API evaluation — no browser, sends queries directly (fast)
  --mode train-cycle    Full evaluate → feedback → train → re-evaluate
  --mode status         Print RL system status
  --mode weights        Show current reward weights

Filters:
  --category <name>     Run scenarios in a specific category
  --id <id>             Run a single scenario by ID
  --tag <tag>           Filter by tag (e.g., smoke, safety, feedback)
  --priority <level>    Filter by priority (critical, high, medium)

Options:
  --headed              Show the browser window
  --list                List all scenarios and exit
  --dry-run             Show which scenarios would run, don't execute
  --help, -h            Show this help

Examples:
  npx tsx src/rl-runner.ts                                    # Evaluate all 25 scenarios
  npx tsx src/rl-runner.ts --mode status                      # Check RL system
  npx tsx src/rl-runner.ts --mode train-cycle --tag smoke     # Quick training cycle
  npx tsx src/rl-runner.ts --id rl-eval-003 --headed          # Debug safety scenario
  npx tsx src/rl-runner.ts --category "Feedback" --dry-run    # Preview feedback scenarios
`)
}

// ─── Server Health Checks ───────────────────────────────────────────

async function ensureServersRunning(client: RLClient): Promise<boolean> {
  console.log('Checking server health...')

  const health = await client.checkServers(rlAgentConfig.baseUrl)

  if (health.frontend) {
    console.log(`  Frontend (${rlAgentConfig.baseUrl}): UP`)
  } else {
    console.error(`  Frontend (${rlAgentConfig.baseUrl}): DOWN`)
  }

  if (health.backend) {
    console.log(`  Backend  (${rlConfig.apiBaseUrl}): UP`)
  } else {
    console.error(`  Backend  (${rlConfig.apiBaseUrl}): DOWN`)
  }

  if (!health.frontend || !health.backend) {
    console.error(`
One or more servers are not running. Start them with:

  cd /home/rohith/desktop/CommandCenter && bash scripts/dev.sh

Then re-run:
  npx tsx src/rl-runner.ts
`)
    return false
  }

  console.log('  All servers healthy.\n')
  return true
}

// ─── Scenario Filtering ─────────────────────────────────────────────

function filterScenarios(scenarios: TestScenario[], args: CLIArgs): TestScenario[] {
  let filtered = [...scenarios]

  if (args.id) {
    filtered = filtered.filter(s => s.id === args.id)
    if (filtered.length === 0) {
      console.error(`No scenario found with id: ${args.id}`)
      console.log('Available IDs:')
      scenarios.forEach(s => console.log(`  ${s.id} — ${s.name}`))
      process.exit(1)
    }
  }

  if (args.category) {
    const cat = args.category.toLowerCase()
    filtered = filtered.filter(s => s.category?.toLowerCase().includes(cat))
  }

  if (args.tag) {
    filtered = filtered.filter(s => s.tags?.includes(args.tag!))
  }

  if (args.priority) {
    filtered = filtered.filter(s => s.priority === args.priority)
  }

  return filtered
}

function listScenarios(scenarios: TestScenario[]) {
  const categories = new Map<string, TestScenario[]>()
  for (const s of scenarios) {
    const cat = s.category || 'Uncategorized'
    if (!categories.has(cat)) categories.set(cat, [])
    categories.get(cat)!.push(s)
  }

  console.log(`\nCommand Center AI RL Agent — ${scenarios.length} Scenarios\n`)
  for (const [cat, items] of categories) {
    console.log(`${cat} (${items.length})`)
    for (const s of items) {
      const tags = s.tags?.length ? ` [${s.tags.join(', ')}]` : ''
      const pri = s.priority ? ` (${s.priority})` : ''
      console.log(`  ${s.id.padEnd(24)} ${s.name}${pri}${tags}`)
    }
    console.log()
  }
}

// ─── Mode: Status ───────────────────────────────────────────────────

async function runStatusMode(client: RLClient) {
  console.log('\nRL System Status')
  console.log('═'.repeat(50))

  try {
    const status = await client.getStatus()

    console.log(`\n  Running: ${status.running ? 'YES' : 'NO'}`)

    console.log('\n  Buffer:')
    if (status.buffer) {
      for (const [key, value] of Object.entries(status.buffer)) {
        console.log(`    ${key}: ${value}`)
      }
    }

    console.log('\n  Trainer:')
    if (status.trainer) {
      for (const [key, value] of Object.entries(status.trainer)) {
        console.log(`    ${key}: ${value}`)
      }
    }

    console.log('\n  Config:')
    if (status.config) {
      for (const [key, value] of Object.entries(status.config)) {
        console.log(`    ${key}: ${value}`)
      }
    }

    console.log()
  } catch (err: any) {
    console.error(`  Failed to get status: ${err.message}`)
    process.exit(1)
  }
}

// ─── Mode: Weights ──────────────────────────────────────────────────

async function runWeightsMode(client: RLClient) {
  console.log('\nRL Reward Weights')
  console.log('═'.repeat(50))

  try {
    const status = await client.getStatus()

    console.log('\n  Current Configuration:')
    if (status.config) {
      for (const [key, value] of Object.entries(status.config)) {
        console.log(`    ${key}: ${value}`)
      }
    }

    console.log('\n  Trainer State:')
    if (status.trainer) {
      const t = status.trainer as Record<string, any>
      if (t.tier1_steps !== undefined) console.log(`    Scorer training steps: ${t.tier1_steps}`)
      if (t.tier2_runs !== undefined) console.log(`    LoRA training runs: ${t.tier2_runs}`)
      if (t.dpo_pairs_ready !== undefined) console.log(`    DPO pairs ready: ${t.dpo_pairs_ready}`)
      if (t.scorer_loss !== undefined) console.log(`    Scorer loss: ${t.scorer_loss}`)
    }

    console.log('\n  Note: Reward weights are configured in backend/rl/config.py:')
    console.log('    explicit_rating: 1.0')
    console.log('    follow_up_type:  0.5')
    console.log('    widget_engagement: 0.3')
    console.log('    response_latency: 0.1')
    console.log('    intent_confidence: 0.1')
    console.log()
  } catch (err: any) {
    console.error(`  Failed to get weights: ${err.message}`)
    process.exit(1)
  }
}

// ─── Mode: API Eval (no browser) ────────────────────────────────────

async function runApiEvalMode(
  client: RLClient,
  evaluator: RLEvaluator,
  evidenceDir: string,
  submitFeedback: boolean = false,
): Promise<RLEvaluation[]> {
  const queries = EVAL_QUERIES
  console.log(`\nAPI Evaluation: ${queries.length} queries (no browser)\n`)

  const evaluations: RLEvaluation[] = []
  let passCount = 0
  let failCount = 0

  for (let i = 0; i < queries.length; i++) {
    const query = queries[i]
    const num = `[${i + 1}/${queries.length}]`

    try {
      const result = await client.orchestrate(query)
      const widgetCount = result.layout_json?.widgets?.length || 0

      // Build page widgets from API response (since no browser)
      const pageWidgets: PageWidget[] = (result.layout_json?.widgets || []).map(w => ({
        scenario: w.scenario,
        fixture: w.fixture,
        size: w.size,
      }))

      const evaluation = await evaluator.evaluateResponse(query, result, pageWidgets)
      evaluations.push(evaluation)

      const scoreStr = (evaluation.overallScore * 100).toFixed(1)
      const latencyStr = `${result.processing_time_ms}ms`
      const icon = evaluation.rating === 'up' ? 'PASS' : 'FAIL'

      if (evaluation.rating === 'up') passCount++
      else failCount++

      console.log(`  ${num} ${icon} ${scoreStr}% ${latencyStr} [${widgetCount}w] ${query.slice(0, 60)}`)

      // Submit feedback if requested
      if (submitFeedback) {
        try {
          const feedback = evaluator.generateFeedback(evaluation)
          await client.submitFeedback(feedback)
          console.log(`       -> feedback: ${evaluation.rating}`)
        } catch (err: any) {
          console.warn(`       -> feedback failed: ${err.message?.slice(0, 60)}`)
        }
      }

      // Cooldown between queries (4s to stay within 20/min feedback throttle)
      await new Promise(resolve => setTimeout(resolve, 4000))

    } catch (err: any) {
      failCount++
      console.error(`  ${num} ERROR ${query.slice(0, 60)}: ${err.message?.slice(0, 80)}`)
    }
  }

  // Save results
  if (evaluations.length > 0) {
    const batch = evaluator.summarizeBatch(evaluations)
    fs.writeFileSync(
      path.join(evidenceDir, 'api-evaluation-report.json'),
      JSON.stringify(batch, null, 2),
    )

    console.log(`\n${'═'.repeat(60)}`)
    console.log('  API Evaluation Summary')
    console.log(`  Total: ${batch.summary.total} | Passed: ${passCount} | Failed: ${failCount}`)
    console.log(`  Average Score: ${(batch.summary.averageScore * 100).toFixed(1)}%`)
    console.log(`  Average Latency: ${batch.summary.averageLatencyMs.toFixed(0)}ms`)
    console.log(`${'═'.repeat(60)}`)
  }

  return evaluations
}

// ─── Mode: Evaluate ─────────────────────────────────────────────────

async function runEvaluateMode(
  client: RLClient,
  evaluator: RLEvaluator,
  scenarios: TestScenario[],
  args: CLIArgs,
  evidenceDir: string,
): Promise<RLEvaluation[]> {
  console.log(`\nEvaluating ${scenarios.length} scenario(s)...\n`)

  // Launch browser
  const browser = await chromium.launch({
    headless: !args.headed && !rlRunnerConfig.headed,
  })

  const context = await browser.newContext({
    viewport: rlRunnerConfig.viewport || { width: 1440, height: 900 },
    permissions: rlRunnerConfig.permissions as any,
  })

  if (rlRunnerConfig.recordTrace) {
    await context.tracing.start({ screenshots: true, snapshots: true })
  }

  const page = await context.newPage()
  const evaluations: RLEvaluation[] = []

  try {
    // Run each scenario through the AI test runner
    const results = await runScenarios(
      page,
      scenarios,
      {
        agent: rlAgentConfig,
        evidenceBaseDir: evidenceDir,
        screenshotEveryStep: rlAgentConfig.screenshotEveryStep,
        actionDelay: rlAgentConfig.actionDelay,
      },
      {
        maxRetries: rlRunnerConfig.maxRetries || 1,
        onScenarioComplete: async (result: ScenarioResult) => {
          console.log(`  ${result.status === 'pass' ? 'PASS' : 'FAIL'} ${result.scenarioId} — ${result.scenarioName}`)

          // Also run API-level evaluation for scenarios with queries
          const queryHint = scenarios.find(s => s.id === result.scenarioId)?.hints?.find(h => h.startsWith('Query:'))
          if (queryHint) {
            const query = queryHint.replace(/^Query:\s*"/, '').replace(/"$/, '')
            try {
              const orchestrateResult = await client.orchestrate(query)
              const pageWidgets = await extractPageWidgets(page)
              const evaluation = await evaluator.evaluateResponse(query, orchestrateResult, pageWidgets)
              evaluations.push(evaluation)
              console.log(`    Score: ${(evaluation.overallScore * 100).toFixed(1)}% (${evaluation.rating})`)
            } catch (err: any) {
              console.warn(`    Evaluation failed: ${err.message?.slice(0, 80)}`)
            }
          }
        },
      },
    )

    // Generate scenario test report
    const report = generateAuditReport(results, 'Command Center RL Agent', '1.0.0')
    fs.writeFileSync(path.join(evidenceDir, 'scenario-report.json'), JSON.stringify(report, null, 2))
    fs.writeFileSync(path.join(evidenceDir, 'scenario-summary.txt'), report.summary)

  } finally {
    if (rlRunnerConfig.recordTrace) {
      const tracePath = path.join(evidenceDir, 'trace.zip')
      await context.tracing.stop({ path: tracePath }).catch(() => {})
    }
    await page.close().catch(() => {})
    await context.close().catch(() => {})
    await browser.close().catch(() => {})
  }

  // Save evaluation results
  if (evaluations.length > 0) {
    const batch = evaluator.summarizeBatch(evaluations)
    fs.writeFileSync(
      path.join(evidenceDir, 'evaluation-report.json'),
      JSON.stringify(batch, null, 2),
    )

    console.log(`\n${'═'.repeat(60)}`)
    console.log(`  RL Evaluation Summary`)
    console.log(`  Total: ${batch.summary.total} | Passed: ${batch.summary.passed} | Failed: ${batch.summary.failed}`)
    console.log(`  Average Score: ${(batch.summary.averageScore * 100).toFixed(1)}%`)
    console.log(`  Average Latency: ${batch.summary.averageLatencyMs.toFixed(0)}ms`)
    console.log(`${'═'.repeat(60)}`)
  }

  return evaluations
}

// ─── Mode: Train Cycle ──────────────────────────────────────────────

async function runTrainCycleMode(
  client: RLClient,
  evaluator: RLEvaluator,
  scenarios: TestScenario[],
  args: CLIArgs,
  evidenceDir: string,
) {
  console.log('\n╔══════════════════════════════════════════════════╗')
  console.log('║   RL Training Cycle                               ║')
  console.log('║   evaluate → feedback → train → re-evaluate       ║')
  console.log('╚══════════════════════════════════════════════════╝\n')

  // Step 1: Record baseline status
  console.log('Step 1: Recording baseline RL status...')
  let baselineStatus
  try {
    baselineStatus = await client.getStatus()
    console.log(`  Buffer: ${JSON.stringify(baselineStatus.buffer)}`)
    console.log(`  Trainer: ${JSON.stringify(baselineStatus.trainer)}`)
  } catch (err: any) {
    console.error(`  Failed to get baseline status: ${err.message}`)
  }

  // Step 2: Evaluate scenarios
  console.log('\nStep 2: Evaluating scenarios (baseline)...')
  const baselineDir = path.join(evidenceDir, 'baseline')
  fs.mkdirSync(baselineDir, { recursive: true })
  const baselineEvals = await runEvaluateMode(client, evaluator, scenarios, args, baselineDir)

  // Step 3: Submit feedback
  console.log('\nStep 3: Submitting feedback...')
  let feedbackCount = 0
  for (const evaluation of baselineEvals) {
    try {
      const feedback = evaluator.generateFeedback(evaluation)
      await client.submitFeedback(feedback)
      feedbackCount++
      console.log(`  Submitted feedback for ${evaluation.queryId}: ${evaluation.rating}`)
    } catch (err: any) {
      console.warn(`  Failed to submit feedback: ${err.message?.slice(0, 80)}`)
    }

    // Cooldown between feedback submissions
    await new Promise(resolve => setTimeout(resolve, rlConfig.cooldownMs))
  }
  console.log(`  Total feedback submitted: ${feedbackCount}`)

  // Step 4: Check if training should be triggered
  console.log('\nStep 4: Checking training readiness...')
  try {
    const status = await client.getStatus()
    const dpoReady = (status.trainer as any)?.dpo_pairs_ready || 0
    console.log(`  DPO pairs ready: ${dpoReady} (need ≥50 for LoRA)`)

    if (dpoReady >= 50) {
      console.log('  Approving LoRA training...')
      const approval = await client.approveTraining()
      console.log(`  Training approved: ${approval.status}`)

      // Poll until training completes (max 10 min)
      console.log('  Waiting for training to complete...')
      const deadline = Date.now() + 600_000
      while (Date.now() < deadline) {
        await new Promise(resolve => setTimeout(resolve, 15_000))
        const s = await client.getStatus()
        const tier2 = (s.trainer as any)?.tier2_runs || 0
        const baseTier2 = (baselineStatus?.trainer as any)?.tier2_runs || 0
        if (tier2 > baseTier2) {
          console.log(`  Training complete! Tier 2 runs: ${baseTier2} → ${tier2}`)
          break
        }
        console.log('  Still training...')
      }
    } else {
      console.log(`  Not enough DPO pairs for LoRA training (${dpoReady}/50). Scorer will still update.`)
    }
  } catch (err: any) {
    console.warn(`  Training check failed: ${err.message}`)
  }

  // Step 5: Re-evaluate
  console.log('\nStep 5: Re-evaluating (after training)...')
  const afterDir = path.join(evidenceDir, 'after-training')
  fs.mkdirSync(afterDir, { recursive: true })
  const afterEvals = await runEvaluateMode(client, evaluator, scenarios, args, afterDir)

  // Step 6: Compare
  console.log('\nStep 6: Comparing before vs after...')
  const baselineAvg = baselineEvals.length > 0
    ? baselineEvals.reduce((s, e) => s + e.overallScore, 0) / baselineEvals.length
    : 0
  const afterAvg = afterEvals.length > 0
    ? afterEvals.reduce((s, e) => s + e.overallScore, 0) / afterEvals.length
    : 0

  const delta = afterAvg - baselineAvg
  const deltaPercent = baselineAvg > 0 ? (delta / baselineAvg * 100).toFixed(1) : 'N/A'

  const comparison = {
    baseline: { count: baselineEvals.length, averageScore: baselineAvg },
    after: { count: afterEvals.length, averageScore: afterAvg },
    delta,
    deltaPercent,
    timestamp: new Date().toISOString(),
  }

  fs.writeFileSync(
    path.join(evidenceDir, 'training-comparison.json'),
    JSON.stringify(comparison, null, 2),
  )

  console.log(`\n${'═'.repeat(60)}`)
  console.log('  Training Cycle Results')
  console.log(`  Baseline avg score: ${(baselineAvg * 100).toFixed(1)}% (${baselineEvals.length} evals)`)
  console.log(`  After avg score:    ${(afterAvg * 100).toFixed(1)}% (${afterEvals.length} evals)`)
  console.log(`  Delta:              ${delta >= 0 ? '+' : ''}${(delta * 100).toFixed(1)}% (${deltaPercent}% relative)`)
  console.log(`${'═'.repeat(60)}`)
}

// ─── Helpers ────────────────────────────────────────────────────────

async function extractPageWidgets(page: import('@playwright/test').Page): Promise<PageWidget[]> {
  return page.evaluate(() => {
    const elements = document.querySelectorAll('[data-scenario]')
    const widgets: Array<{
      scenario: string
      fixture?: string
      size?: string
      textContent?: string
    }> = []

    const seen = new Set<string>()
    elements.forEach(el => {
      const scenario = el.getAttribute('data-scenario') || ''
      const key = `${scenario}-${el.getAttribute('data-size') || ''}`
      if (!seen.has(key)) {
        seen.add(key)
        widgets.push({
          scenario,
          fixture: el.getAttribute('data-fixture') || undefined,
          size: el.getAttribute('data-size') || undefined,
          textContent: (el.textContent || '').slice(0, 200),
        })
      }
    })

    return widgets
  })
}

// ─── Main ───────────────────────────────────────────────────────────

async function main() {
  const args = parseArgs()

  console.log(`
╔══════════════════════════════════════════════════╗
║   Command Center — AI RL Agent                    ║
║   Autonomous reinforcement learning               ║
╚══════════════════════════════════════════════════╝
`)

  // Initialize client
  const client = new RLClient({
    apiBaseUrl: rlConfig.apiBaseUrl,
    feedbackApiKey: rlConfig.feedbackApiKey,
  })

  // Status and weights modes don't need a browser
  if (args.mode === 'status') {
    await runStatusMode(client)
    process.exit(0)
  }

  if (args.mode === 'weights') {
    await runWeightsMode(client)
    process.exit(0)
  }

  // api-eval mode only needs backend, not frontend
  if (args.mode === 'api-eval') {
    const health = await client.checkServers(rlAgentConfig.baseUrl)
    if (!health.backend) {
      console.error(`Backend (${rlConfig.apiBaseUrl}) is DOWN. Start it first.`)
      process.exit(1)
    }
    console.log(`Backend (${rlConfig.apiBaseUrl}): UP\n`)

    const evidenceDir = path.resolve(rlAgentConfig.evidenceDir || './evidence/rl')
    fs.mkdirSync(evidenceDir, { recursive: true })
    const evaluator = new RLEvaluator(rlConfig, rlAgentConfig)

    const evaluations = await runApiEvalMode(client, evaluator, evidenceDir, true)
    const passed = evaluations.filter(e => e.rating === 'up').length
    console.log(`\nFeedback submitted for all ${evaluations.length} evaluations.`)
    console.log(`Exit code: ${passed === evaluations.length ? 0 : 1}`)
    process.exit(passed === evaluations.length ? 0 : 1)
  }

  // List mode
  if (args.list) {
    listScenarios(rlScenarios)
    process.exit(0)
  }

  // Filter scenarios
  const scenarios = filterScenarios(rlScenarios, args)

  if (scenarios.length === 0) {
    console.error('No scenarios match the given filters.')
    process.exit(1)
  }

  // Dry run
  if (args.dryRun) {
    console.log(`Would run ${scenarios.length} scenarios:\n`)
    scenarios.forEach(s => {
      console.log(`  ${s.id.padEnd(24)} ${s.name}`)
    })
    process.exit(0)
  }

  // Health check
  const serversOk = await ensureServersRunning(client)
  if (!serversOk) {
    process.exit(1)
  }

  // Create evidence directory
  const evidenceDir = path.resolve(rlAgentConfig.evidenceDir || './evidence/rl')
  fs.mkdirSync(evidenceDir, { recursive: true })

  // Initialize evaluator
  const evaluator = new RLEvaluator(rlConfig, rlAgentConfig)

  // Run mode
  if (args.mode === 'evaluate') {
    const evaluations = await runEvaluateMode(client, evaluator, scenarios, args, evidenceDir)
    const passed = evaluations.filter(e => e.rating === 'up').length
    console.log(`\nExit code: ${passed === evaluations.length ? 0 : 1}`)
    process.exit(passed === evaluations.length ? 0 : 1)
  }

  if (args.mode === 'train-cycle') {
    await runTrainCycleMode(client, evaluator, scenarios, args, evidenceDir)
    process.exit(0)
  }

  // Default: api-eval (fastest, generates most training data)
  await runApiEvalMode(client, evaluator, evidenceDir, true)
}

// Run
main().catch(err => {
  console.error('Unhandled error:', err)
  process.exit(2)
})
