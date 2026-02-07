/**
 * AI RL Agent — Autonomous reinforcement learning agent for Command Center.
 *
 * Built on the AI QA Agent framework, this package adds:
 * - Response evaluation (widget quality, data accuracy, latency)
 * - Structured feedback submission to the RL training system
 * - RL training lifecycle management (approve, monitor, compare)
 * - A/B model comparison and weight sensitivity analysis
 *
 * @example
 * ```typescript
 * import { RLClient, RLEvaluator } from '@neurareport/ai-rl-agent'
 *
 * const client = new RLClient({ apiBaseUrl: 'http://localhost:8100' })
 * const status = await client.getStatus()
 * console.log(status.buffer, status.trainer)
 * ```
 */
export type { AgentActionType, AgentAction, ActionTarget, VerifyAssertion, PageObservation, InteractiveElement, ApiCallRecord, TestScenario, QaAgentProfile, PersonaModifier, SuccessCriterion, BackendCheck, SetupAction, TeardownAction, ScenarioResult, ActionLogEntry, CriterionResult, BackendCheckResult, FailureCategory, GoalLedger, PerceptionEntry, CachedActionSequence, LessonLearned, AuditReport, ActionVerification, PageStability, ReplayDetection, } from './types';
export type { UIFramework, ElementDiscoveryConfig, LLMConfig, AgentConfig, RunnerConfig, } from './config';
export { FRAMEWORK_PRESETS, DEFAULT_LLM_CONFIG, DEFAULT_AGENT_CONFIG, DEFAULT_RUNNER_CONFIG, createConfig, createRunnerConfig, getElementSelectors, } from './config';
export { BrowserAgent } from './browser-agent';
export { AgentBrain } from './agent-brain';
export type { AITestRunnerConfig } from './test-runner';
export { AITestRunner, generateAuditReport, runScenarios, } from './test-runner';
export { RLClient } from './rl-client';
export type { OrchestrateRequest, OrchestrateResponse, WidgetData, FeedbackRequest, FeedbackResponse, RLStatus, ApproveTrainingResponse, HealthResponse, RLClientConfig, } from './rl-client';
export { RLEvaluator } from './rl-evaluator';
export type { RLEvaluation, ABComparison, FeedbackPayload, EvaluationBatch, InteractionRecord, PageWidget, } from './rl-evaluator';
export { rlAgentConfig, rlRunnerConfig, rlConfig, EVAL_WEIGHTS, EXPECTED_SCENARIOS, } from './rl-config';
export type { RLConfig } from './rl-config';
export { rlScenarios, EVAL_QUERIES } from './rl-scenarios';
//# sourceMappingURL=index.d.ts.map