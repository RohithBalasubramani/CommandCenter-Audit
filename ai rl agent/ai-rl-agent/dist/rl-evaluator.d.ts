/**
 * RL Evaluator — Core evaluation logic for Command Center responses.
 *
 * Evaluates AI responses by comparing:
 * - What the UI shows (Playwright page observation)
 * - What the backend returned (orchestrate API response)
 * - What the query should have produced (expected scenarios)
 *
 * Generates structured feedback for the RL system.
 */
import type { OrchestrateResponse } from './rl-client.js';
import { type RLConfig } from './rl-config.js';
import type { AgentConfig } from './config.js';
export interface InteractionRecord {
    widget_index: number;
    action: string;
    duration_ms: number;
}
export interface RLEvaluation {
    queryId: string;
    query: string;
    overallScore: number;
    rating: 'up' | 'down';
    widgetCountMatch: boolean;
    scenarioRelevance: number;
    dataAccuracy: number;
    responseQuality: number;
    latencyScore: number;
    interactions: InteractionRecord[];
    correction?: string;
    reasoning: string;
    timestamp: string;
    processingTimeMs: number;
}
export interface ABComparison {
    query: string;
    resultA: RLEvaluation;
    resultB: RLEvaluation;
    winner: 'A' | 'B' | 'tie';
    scoreDelta: number;
    reasoning: string;
}
export interface FeedbackPayload {
    query_id: string;
    rating: 'up' | 'down';
    interactions: Array<{
        widget_index: number;
        action: string;
        duration_ms: number;
    }>;
    correction?: string;
}
export interface EvaluationBatch {
    evaluations: RLEvaluation[];
    summary: {
        total: number;
        passed: number;
        failed: number;
        averageScore: number;
        averageLatencyMs: number;
    };
    timestamp: string;
}
export declare class RLEvaluator {
    private config;
    private brain;
    private agentConfig;
    constructor(config: RLConfig, agentConfig: AgentConfig);
    /**
     * Evaluate a single response from the orchestrator.
     */
    evaluateResponse(query: string, result: OrchestrateResponse, pageWidgets: PageWidget[]): Promise<RLEvaluation>;
    /**
     * Convert evaluation to feedback payload for the RL API.
     */
    generateFeedback(evaluation: RLEvaluation): FeedbackPayload;
    /**
     * Compare two responses for A/B testing.
     */
    compareAB(query: string, resultA: OrchestrateResponse, resultB: OrchestrateResponse, pageWidgetsA: PageWidget[], pageWidgetsB: PageWidget[]): Promise<ABComparison>;
    /**
     * Create a summary from a batch of evaluations.
     */
    summarizeBatch(evaluations: RLEvaluation[]): EvaluationBatch;
    private checkWidgetCount;
    private checkScenarioRelevance;
    private checkDataAccuracy;
    private checkResponseQuality;
    private computeLatencyScore;
    private generateInteractions;
    private suggestCorrection;
    private buildReasoning;
}
export interface PageWidget {
    scenario: string;
    fixture?: string;
    size?: string;
    textContent?: string;
}
//# sourceMappingURL=rl-evaluator.d.ts.map