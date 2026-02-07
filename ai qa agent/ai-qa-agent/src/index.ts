/**
 * AI QA Agent — A state-of-the-art, framework-agnostic AI testing agent.
 *
 * This package provides a complete AI-powered testing solution that:
 * - Acts like a real user testing your web application
 * - Uses Claude Code CLI for intelligent decision making
 * - Works with any web framework (React, Vue, Angular, plain HTML)
 * - Adapts to MUI, Tailwind, Bootstrap, Ant Design, and more
 * - Provides detailed evidence and debugging information
 *
 * @example
 * ```typescript
 * import { AITestRunner, createConfig, type TestScenario } from '@neurareport/ai-qa-agent'
 * import { test } from '@playwright/test'
 *
 * const config = createConfig({
 *   appName: 'My App',
 *   baseUrl: 'http://localhost:3000',
 *   uiFramework: 'tailwind',
 *   llm: { model: 'sonnet', useVision: true },
 * })
 *
 * const scenario: TestScenario = {
 *   id: 'login-001',
 *   name: 'User can log in',
 *   goal: 'Log in to the application using valid credentials',
 *   startUrl: '/login',
 *   maxActions: 20,
 *   successCriteria: [
 *     { description: 'Dashboard is visible', check: { check: 'url_contains', expected: '/dashboard' } },
 *   ],
 * }
 *
 * test('AI Agent: Login', async ({ page }) => {
 *   const runner = new AITestRunner(page, {
 *     agent: config,
 *     evidenceBaseDir: './evidence/login',
 *   })
 *   const result = await runner.runScenario(scenario)
 *   expect(result.status).toBe('pass')
 * })
 * ```
 */

// ─── Types ───────────────────────────────────────────────────────────

export type {
  // Action types
  AgentActionType,
  AgentAction,
  ActionTarget,
  VerifyAssertion,

  // Observation types
  PageObservation,
  InteractiveElement,
  ApiCallRecord,

  // Scenario types
  TestScenario,
  QaAgentProfile,
  PersonaModifier,
  SuccessCriterion,
  BackendCheck,
  SetupAction,
  TeardownAction,

  // Result types
  ScenarioResult,
  ActionLogEntry,
  CriterionResult,
  BackendCheckResult,
  FailureCategory,

  // Progress tracking
  GoalLedger,
  PerceptionEntry,

  // Learning
  CachedActionSequence,
  LessonLearned,

  // Reports
  AuditReport,

  // Failure mode mitigations
  ActionVerification,
  PageStability,
  ReplayDetection,
} from './types'

// ─── Configuration ───────────────────────────────────────────────────

export type {
  UIFramework,
  ElementDiscoveryConfig,
  LLMConfig,
  AgentConfig,
  RunnerConfig,
} from './config'

export {
  FRAMEWORK_PRESETS,
  DEFAULT_LLM_CONFIG,
  DEFAULT_AGENT_CONFIG,
  DEFAULT_RUNNER_CONFIG,
  createConfig,
  createRunnerConfig,
  getElementSelectors,
} from './config'

// ─── Browser Agent ───────────────────────────────────────────────────

export { BrowserAgent } from './browser-agent'

// ─── Agent Brain ─────────────────────────────────────────────────────

export { AgentBrain } from './agent-brain'

// ─── Test Runner ─────────────────────────────────────────────────────

export type { AITestRunnerConfig } from './test-runner'

export {
  AITestRunner,
  generateAuditReport,
  runScenarios,
} from './test-runner'
