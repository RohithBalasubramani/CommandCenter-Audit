/**
 * AI Agent Test Runner — Orchestrates the browser agent + LLM brain.
 *
 * This is the main execution loop:
 * 1. Initialize scenario
 * 2. Run setup actions (if any)
 * 3. Observe page state (screenshot + DOM)
 * 4. Send observation to LLM brain → get next action
 * 5. Execute action via browser agent
 * 6. Record result, repeat until done or max actions
 * 7. Run backend brain checks
 * 8. Evaluate success criteria
 * 9. Run teardown actions (if any)
 * 10. Generate evidence report
 *
 * Framework-agnostic: Works with any web application.
 */
import * as fs from 'fs'
import * as path from 'path'
import type { Page } from '@playwright/test'
import { BrowserAgent } from './browser-agent'
import { AgentBrain } from './agent-brain'
import type {
  TestScenario,
  ScenarioResult,
  ActionLogEntry,
  CriterionResult,
  BackendCheckResult,
  AuditReport,
  FailureCategory,
} from './types'
import type { AgentConfig, RunnerConfig } from './config'

export interface AITestRunnerConfig {
  /** Base agent configuration */
  agent: AgentConfig
  /** Directory for all evidence output */
  evidenceBaseDir: string
  /** Whether to take screenshots at every step (default: true) */
  screenshotEveryStep?: boolean
  /** Delay between actions in ms (default: 500) */
  actionDelay?: number
}

export class AITestRunner {
  private browser: BrowserAgent
  private brain: AgentBrain
  private config: AITestRunnerConfig
  private page: Page

  constructor(page: Page, config: AITestRunnerConfig) {
    this.page = page
    this.config = {
      screenshotEveryStep: config.agent.screenshotEveryStep ?? true,
      actionDelay: config.agent.actionDelay ?? 500,
      ...config,
    }

    // Create evidence directory
    fs.mkdirSync(config.evidenceBaseDir, { recursive: true })

    this.browser = new BrowserAgent(page, config.agent, config.evidenceBaseDir)
    this.brain = new AgentBrain(config.agent)
  }

  /** Run a single scenario and return the result */
  async runScenario(scenario: TestScenario): Promise<ScenarioResult> {
    const startTime = Date.now()
    const actionLog: ActionLogEntry[] = []
    let error: string | undefined

    console.log(`\n${'═'.repeat(60)}`)
    console.log(`🤖 AI Agent: ${scenario.name}`)
    console.log(`   Goal: ${scenario.goal.slice(0, 100)}...`)
    console.log(`${'═'.repeat(60)}`)

    // Initialize the brain with this scenario
    this.brain.initScenario(scenario)

    // Run setup actions if any
    if (scenario.setup?.length) {
      console.log('  Running setup actions...')
      for (const setup of scenario.setup) {
        try {
          await this.runSetupAction(setup)
        } catch (err: any) {
          console.warn(`  Setup failed: ${err.message}`)
        }
      }
    }

    // Navigate to start URL
    try {
      const fullUrl = scenario.startUrl.startsWith('http')
        ? scenario.startUrl
        : `${this.config.agent.baseUrl}${scenario.startUrl}`
      await this.page.goto(fullUrl, { waitUntil: 'domcontentloaded', timeout: this.config.agent.pageLoadTimeout || 30_000 })
      await this.page.waitForTimeout(2000)
    } catch (err: any) {
      return this.buildResult(scenario, startTime, actionLog, 'error', `Failed to navigate to start URL: ${err.message}`)
    }

    // Take initial screenshot
    await this.browser.takeScreenshot('initial')

    // Main action loop
    let actionCount = 0
    let isDone = false
    let consecutiveErrors = 0
    const MAX_CONSECUTIVE_ERRORS = 5
    const STEP_TIMEOUT = this.config.agent.llm.timeout || 900_000 // 15 min default

    while (actionCount < scenario.maxActions && !isDone) {
      actionCount++
      const stepStart = Date.now()

      // Bail if page/browser was closed
      if (this.page.isClosed()) {
        console.log(`    ✗ Page closed — stopping agent loop`)
        error = 'Page or browser was closed unexpectedly'
        break
      }

      try {
        const stepResult = await Promise.race([
          this.runSingleStep(actionCount, scenario.maxActions),
          new Promise<{ timedOut: true }>((resolve) =>
            setTimeout(() => resolve({ timedOut: true }), STEP_TIMEOUT)
          ),
        ])

        if ('timedOut' in stepResult) {
          console.warn(`    ⚠ Step ${actionCount} timed out after ${STEP_TIMEOUT / 1000}s — skipping`)
          actionLog.push({
            step: actionCount,
            timestamp: new Date().toISOString(),
            action: { type: 'done', reasoning: `Step timed out after ${STEP_TIMEOUT / 1000}s` },
            result: 'failed',
            error: `Step timeout (${STEP_TIMEOUT / 1000}s)`,
            duration: STEP_TIMEOUT,
          })
          consecutiveErrors++
        } else if (stepResult.isDone) {
          isDone = true
          actionLog.push(stepResult.logEntry)
          break
        } else {
          actionLog.push(stepResult.logEntry)
          if (stepResult.logEntry.result === 'failed') {
            console.log(`    ⚠ Action failed: ${stepResult.logEntry.error?.slice(0, 100)}`)
            consecutiveErrors++
          } else {
            consecutiveErrors = 0
          }
        }

        if (consecutiveErrors >= MAX_CONSECUTIVE_ERRORS) {
          console.log(`    ✗ ${MAX_CONSECUTIVE_ERRORS} consecutive failures — stopping`)
          error = `Stopped after ${MAX_CONSECUTIVE_ERRORS} consecutive action failures`
          break
        }

        // Delay between actions
        if (this.config.actionDelay && !this.page.isClosed()) {
          await this.page.waitForTimeout(this.config.actionDelay).catch(() => {})
        }

      } catch (err: any) {
        const msg = err.message || ''
        console.error(`    ✗ Step ${actionCount} crashed: ${msg.slice(0, 100)}`)
        actionLog.push({
          step: actionCount,
          timestamp: new Date().toISOString(),
          action: { type: 'done', reasoning: `Error: ${msg}` },
          result: 'failed',
          error: msg,
          duration: Date.now() - stepStart,
        })

        // Fatal: page/context destroyed
        if (msg.includes('has been closed') || msg.includes('Target closed') || msg.includes('browser has been closed')) {
          console.log(`    ✗ Browser/page closed — stopping agent loop`)
          error = 'Page or browser was closed unexpectedly'
          break
        }
        consecutiveErrors++
        if (consecutiveErrors >= MAX_CONSECUTIVE_ERRORS) {
          error = `Stopped after ${MAX_CONSECUTIVE_ERRORS} consecutive crashes`
          break
        }
      }
    }

    if (!isDone && actionCount >= scenario.maxActions) {
      error = `Reached maximum actions (${scenario.maxActions}) without completing`
    }

    // Take final screenshot
    await this.browser.takeScreenshot('final')

    // Run backend checks
    const backendResults = await this.runBackendChecks(scenario)

    // Evaluate success criteria
    const criteriaResults = await this.evaluateCriteria(scenario)

    // Run teardown actions
    if (scenario.teardown?.length) {
      const shouldRun = !error || scenario.teardown.some(t => t.runOnFailure)
      if (shouldRun) {
        console.log('  Running teardown actions...')
        for (const teardown of scenario.teardown) {
          if (!error || teardown.runOnFailure) {
            try {
              await this.runTeardownAction(teardown)
            } catch (err: any) {
              console.warn(`  Teardown failed: ${err.message}`)
            }
          }
        }
      }
    }

    // Determine overall status
    const allCriteriaPassed = criteriaResults.every(r => r.passed)
    const allBackendPassed = backendResults.every(r => r.passed)
    const status = error
      ? (actionCount >= scenario.maxActions ? 'timeout' : 'error')
      : (allCriteriaPassed && allBackendPassed ? 'pass' : 'fail')

    // Finalize scenario
    this.brain.finalizeScenario(status === 'pass')

    return this.buildResult(scenario, startTime, actionLog, status, error, criteriaResults, backendResults)
  }

  /** Execute a single step (observe → decide → execute → screenshot) */
  private async runSingleStep(actionCount: number, maxActions: number): Promise<{
    isDone: boolean
    logEntry: ActionLogEntry
  }> {
    const stepStart = Date.now()

    // 1. Observe the current page state
    const observation = await this.browser.observe()

    // 2. Ask the brain what to do
    const action = await this.brain.decideAction(observation)

    console.log(`  [${actionCount}/${maxActions}] ${action.type}: ${action.reasoning?.slice(0, 80)}`)

    // 3. Check if done
    if (action.type === 'done') {
      return {
        isDone: true,
        logEntry: {
          step: actionCount,
          timestamp: new Date().toISOString(),
          action,
          result: 'success',
          duration: Date.now() - stepStart,
        },
      }
    }

    // 4. Execute the action
    const result = await this.browser.execute(action)

    // 5. Take screenshot if configured
    let screenshotPath: string | undefined
    if (this.config.screenshotEveryStep) {
      screenshotPath = await this.browser.takeScreenshot(
        `step-${String(actionCount).padStart(3, '0')}-${action.type}`
      )
    }

    // 6. Record the result
    const duration = Date.now() - stepStart
    this.brain.recordResult(action, result, duration)

    return {
      isDone: false,
      logEntry: {
        step: actionCount,
        timestamp: new Date().toISOString(),
        action,
        result: result.success ? 'success' : 'failed',
        error: result.error,
        duration,
        screenshotAfter: screenshotPath,
      },
    }
  }

  /** Run setup action */
  private async runSetupAction(setup: NonNullable<TestScenario['setup']>[number]) {
    switch (setup.type) {
      case 'api_call':
        if (setup.endpoint) {
          await this.browser.apiCall(setup.method || 'POST', setup.endpoint, setup.body)
        }
        break
      case 'navigate':
        if (setup.url) {
          const fullUrl = setup.url.startsWith('http')
            ? setup.url
            : `${this.config.agent.baseUrl}${setup.url}`
          await this.page.goto(fullUrl)
        }
        break
      case 'wait':
        await this.page.waitForTimeout(setup.waitMs || 1000)
        break
      case 'script':
        if (setup.script) {
          await this.page.evaluate(setup.script)
        }
        break
    }
  }

  /** Run teardown action */
  private async runTeardownAction(teardown: NonNullable<TestScenario['teardown']>[number]) {
    switch (teardown.type) {
      case 'api_call':
        if (teardown.endpoint) {
          await this.browser.apiCall(teardown.method || 'DELETE', teardown.endpoint, teardown.body)
        }
        break
      case 'script':
        if (teardown.script) {
          await this.page.evaluate(teardown.script)
        }
        break
    }
  }

  /** Run backend API checks defined in the scenario */
  private async runBackendChecks(scenario: TestScenario): Promise<BackendCheckResult[]> {
    if (!scenario.backendChecks?.length) return []

    const results: BackendCheckResult[] = []
    for (const check of scenario.backendChecks) {
      try {
        const { status, data } = await this.browser.apiCall(
          check.method,
          check.endpoint,
          check.body,
          check.headers,
        )

        const passed = check.expectedStatus
          ? status === check.expectedStatus
          : status < 400

        results.push({
          description: check.description,
          passed,
          endpoint: check.endpoint,
          status,
          responsePreview: JSON.stringify(data).slice(0, 300),
        })
      } catch (err: any) {
        results.push({
          description: check.description,
          passed: false,
          endpoint: check.endpoint,
          error: err.message,
        })
      }
    }
    return results
  }

  /** Evaluate success criteria against current page state */
  private async evaluateCriteria(scenario: TestScenario): Promise<CriterionResult[]> {
    const results: CriterionResult[] = []
    for (const criterion of scenario.successCriteria) {
      const result = await this.browser.verify(criterion.check)
      results.push({
        description: criterion.description,
        passed: result.passed,
        actual: result.actual,
        expected: criterion.check.expected as string,
        weight: criterion.weight,
      })
    }
    return results
  }

  /** Build the scenario result object */
  private buildResult(
    scenario: TestScenario,
    startTime: number,
    actionLog: ActionLogEntry[],
    status: ScenarioResult['status'],
    error?: string,
    criteriaResults?: CriterionResult[],
    backendResults?: BackendCheckResult[],
  ): ScenarioResult {
    // Failure categorization
    const failureCategory = status !== 'pass'
      ? this.brain.categorizeFailure(error, actionLog)
      : undefined

    const result: ScenarioResult = {
      scenarioId: scenario.id,
      scenarioName: scenario.name,
      status,
      duration: Date.now() - startTime,
      actionCount: actionLog.length,
      actionLog,
      criteriaResults: criteriaResults || [],
      backendResults,
      error,
      failureCategory,
      evidence: {
        screenshots: [],
        networkCaptures: [],
        llmDecisions: '',
      },
    }

    // Save evidence
    const evidenceDir = this.config.evidenceBaseDir

    // Save action log
    const actionLogPath = path.join(evidenceDir, `${scenario.id}-action-log.json`)
    fs.writeFileSync(actionLogPath, JSON.stringify(actionLog, null, 2))

    // Save LLM conversation
    const convoPath = path.join(evidenceDir, `${scenario.id}-llm-conversation.json`)
    fs.writeFileSync(convoPath, JSON.stringify(this.brain.getConversation(), null, 2))
    result.evidence.llmDecisions = convoPath

    // Save perception log
    const perceptionPath = path.join(evidenceDir, `${scenario.id}-perception.json`)
    fs.writeFileSync(perceptionPath, JSON.stringify(this.brain.getPerceptionLog(), null, 2))

    // Save goal ledger
    const ledgerPath = path.join(evidenceDir, `${scenario.id}-goal-ledger.json`)
    fs.writeFileSync(ledgerPath, JSON.stringify(this.brain.getLedger(), null, 2))

    // Save network log
    this.browser.saveNetworkLog(scenario.id)

    // Save full result
    const resultPath = path.join(evidenceDir, `${scenario.id}-result.json`)
    fs.writeFileSync(resultPath, JSON.stringify(result, null, 2))

    // Print summary
    const icon = status === 'pass' ? '✓' : status === 'fail' ? '✗' : status === 'timeout' ? '⏱' : '⚠'
    const ledger = this.brain.getLedger()
    console.log(`\n${icon} ${scenario.name}: ${status.toUpperCase()} (${actionLog.length} actions, ${Math.round(result.duration / 1000)}s)`)
    console.log(`  Goal progress: ${ledger.completedOutcomes.length}/${ledger.requiredOutcomes.length} outcomes | stuck score: ${ledger.stuckScore}`)
    if (criteriaResults?.length) {
      criteriaResults.forEach(c => {
        console.log(`  ${c.passed ? '✓' : '✗'} ${c.description}`)
      })
    }
    const perceptions = this.brain.getPerceptionLog()
    const avgConfidence = perceptions.length
      ? (perceptions.reduce((sum, p) => sum + p.confidence, 0) / perceptions.length).toFixed(2)
      : 'N/A'
    const confusionCount = perceptions.filter(p => p.confusionSignals.length > 0).length
    console.log(`  Confidence: ${avgConfidence} avg | ${confusionCount} confused steps`)
    if (failureCategory) {
      console.log(`  Failure category: ${failureCategory}`)
    }

    return result
  }

  /** Get the browser agent for direct access */
  getBrowserAgent(): BrowserAgent {
    return this.browser
  }

  /** Get the brain for direct access */
  getBrain(): AgentBrain {
    return this.brain
  }
}

// ─── Aggregate report generation ─────────────────────────────────────

export function generateAuditReport(
  results: ScenarioResult[],
  appName: string,
  appVersion?: string
): AuditReport {
  const passed = results.filter(r => r.status === 'pass').length
  const failed = results.filter(r => r.status === 'fail').length
  const errors = results.filter(r => r.status === 'error').length
  const timeouts = results.filter(r => r.status === 'timeout').length
  const skipped = results.filter(r => r.status === 'skipped').length

  // Failure breakdown
  const failureBreakdown: Record<FailureCategory, number> = {
    element_not_found: 0,
    element_not_interactable: 0,
    navigation_error: 0,
    form_error: 0,
    timeout: 0,
    stuck_loop: 0,
    assertion_failed: 0,
    browser_crash: 0,
    llm_error: 0,
    network_error: 0,
    auth_error: 0,
    unknown: 0,
  }
  results.forEach(r => {
    if (r.failureCategory) {
      failureBreakdown[r.failureCategory]++
    }
  })

  const passRate = results.length ? Math.round(passed / results.length * 100) : 0

  const report: AuditReport = {
    timestamp: new Date().toISOString(),
    appName,
    appVersion,
    totalScenarios: results.length,
    passed,
    failed,
    errors,
    timeouts,
    skipped,
    totalDuration: results.reduce((sum, r) => sum + r.duration, 0),
    totalActions: results.reduce((sum, r) => sum + r.actionCount, 0),
    passRate,
    scenarios: results,
    failureBreakdown,
    summary: [
      `AI Agent Audit Report: ${appName}`,
      `═════════════════════`,
      `Total Scenarios: ${results.length}`,
      `Passed: ${passed} | Failed: ${failed} | Errors: ${errors} | Timeouts: ${timeouts} | Skipped: ${skipped}`,
      `Pass Rate: ${passRate}%`,
      `Total Actions: ${results.reduce((sum, r) => sum + r.actionCount, 0)}`,
      `Total Duration: ${Math.round(results.reduce((sum, r) => sum + r.duration, 0) / 1000)}s`,
      '',
      ...results.map(r => {
        const icon = r.status === 'pass' ? '✓' : r.status === 'fail' ? '✗' : '⚠'
        const category = r.failureCategory ? ` [${r.failureCategory}]` : ''
        return `${icon} [${r.status.toUpperCase()}]${category} ${r.scenarioName} (${r.actionCount} actions, ${Math.round(r.duration / 1000)}s)`
      }),
    ].join('\n'),
  }

  return report
}

/** Run multiple scenarios with retry support */
export async function runScenarios(
  page: Page,
  scenarios: TestScenario[],
  config: AITestRunnerConfig,
  options?: {
    maxRetries?: number
    onScenarioComplete?: (result: ScenarioResult) => void
  }
): Promise<ScenarioResult[]> {
  const results: ScenarioResult[] = []
  const maxRetries = options?.maxRetries ?? 0

  for (const scenario of scenarios) {
    let lastResult: ScenarioResult | null = null
    let attempt = 0

    while (attempt <= maxRetries) {
      attempt++
      const runner = new AITestRunner(page, config)
      const result = await runner.runScenario(scenario)
      result.attempt = attempt

      lastResult = result

      if (result.status === 'pass') {
        break
      }

      if (attempt <= maxRetries) {
        console.log(`  Retrying (attempt ${attempt + 1}/${maxRetries + 1})...`)
        result.wasFlaky = true
      }
    }

    if (lastResult) {
      if (lastResult.attempt && lastResult.attempt > 1 && lastResult.status === 'pass') {
        lastResult.wasFlaky = true
      }
      results.push(lastResult)
      options?.onScenarioComplete?.(lastResult)
    }
  }

  return results
}
