/**
 * RL Agent Configuration for Command Center
 *
 * Extends the CC QA agent config with RL-specific settings
 * for evaluation thresholds, API endpoints, and training parameters.
 */
import type { AgentConfig, RunnerConfig } from './config.js';
export interface RLConfig {
    apiBaseUrl: string;
    feedbackApiKey: string;
    evaluationThreshold: number;
    latencyBudgetMs: number;
    maxEvalRetries: number;
    batchSize: number;
    cooldownMs: number;
}
export declare const rlAgentConfig: AgentConfig;
export declare const rlRunnerConfig: RunnerConfig;
export declare const rlConfig: RLConfig;
export declare const EVAL_WEIGHTS: {
    readonly widgetCountMatch: 0.15;
    readonly scenarioRelevance: 0.35;
    readonly dataAccuracy: 0.25;
    readonly responseQuality: 0.15;
    readonly latencyScore: 0.1;
};
export declare const EXPECTED_SCENARIOS: Record<string, string[]>;
//# sourceMappingURL=rl-config.d.ts.map