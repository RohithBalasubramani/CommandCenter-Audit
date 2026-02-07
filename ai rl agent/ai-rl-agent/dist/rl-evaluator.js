"use strict";
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
Object.defineProperty(exports, "__esModule", { value: true });
exports.RLEvaluator = void 0;
const rl_config_js_1 = require("./rl-config.js");
// ─── Evaluator ──────────────────────────────────────────────────────
class RLEvaluator {
    config;
    brain = null;
    agentConfig;
    constructor(config, agentConfig) {
        this.config = config;
        this.agentConfig = agentConfig;
    }
    /**
     * Evaluate a single response from the orchestrator.
     */
    async evaluateResponse(query, result, pageWidgets) {
        const widgetCountMatch = this.checkWidgetCount(result, pageWidgets);
        const scenarioRelevance = this.checkScenarioRelevance(query, result);
        const dataAccuracy = this.checkDataAccuracy(result, pageWidgets);
        const responseQuality = await this.checkResponseQuality(query, result);
        const latencyScore = this.computeLatencyScore(result.processing_time_ms);
        const overallScore = widgetCountMatch ? 1.0 * rl_config_js_1.EVAL_WEIGHTS.widgetCountMatch : 0 +
            scenarioRelevance * rl_config_js_1.EVAL_WEIGHTS.scenarioRelevance +
            dataAccuracy * rl_config_js_1.EVAL_WEIGHTS.dataAccuracy +
            responseQuality * rl_config_js_1.EVAL_WEIGHTS.responseQuality +
            latencyScore * rl_config_js_1.EVAL_WEIGHTS.latencyScore;
        // Normalize: widgetCountMatch contributes its weight as 0 or 1
        const normalizedScore = (widgetCountMatch ? rl_config_js_1.EVAL_WEIGHTS.widgetCountMatch : 0) +
            scenarioRelevance * rl_config_js_1.EVAL_WEIGHTS.scenarioRelevance +
            dataAccuracy * rl_config_js_1.EVAL_WEIGHTS.dataAccuracy +
            responseQuality * rl_config_js_1.EVAL_WEIGHTS.responseQuality +
            latencyScore * rl_config_js_1.EVAL_WEIGHTS.latencyScore;
        const rating = normalizedScore >= this.config.evaluationThreshold ? 'up' : 'down';
        const interactions = this.generateInteractions(result, normalizedScore);
        const correction = rating === 'down'
            ? this.suggestCorrection(query, result)
            : undefined;
        const reasoning = this.buildReasoning(query, widgetCountMatch, scenarioRelevance, dataAccuracy, responseQuality, latencyScore, normalizedScore, rating);
        return {
            queryId: result.query_id,
            query,
            overallScore: normalizedScore,
            rating,
            widgetCountMatch,
            scenarioRelevance,
            dataAccuracy,
            responseQuality,
            latencyScore,
            interactions,
            correction,
            reasoning,
            timestamp: new Date().toISOString(),
            processingTimeMs: result.processing_time_ms,
        };
    }
    /**
     * Convert evaluation to feedback payload for the RL API.
     */
    generateFeedback(evaluation) {
        return {
            query_id: evaluation.queryId,
            rating: evaluation.rating,
            interactions: evaluation.interactions,
            correction: evaluation.correction,
        };
    }
    /**
     * Compare two responses for A/B testing.
     */
    async compareAB(query, resultA, resultB, pageWidgetsA, pageWidgetsB) {
        const evalA = await this.evaluateResponse(query, resultA, pageWidgetsA);
        const evalB = await this.evaluateResponse(query, resultB, pageWidgetsB);
        const scoreDelta = evalA.overallScore - evalB.overallScore;
        const winner = Math.abs(scoreDelta) < 0.05 ? 'tie' : scoreDelta > 0 ? 'A' : 'B';
        return {
            query,
            resultA: evalA,
            resultB: evalB,
            winner,
            scoreDelta,
            reasoning: `A scored ${evalA.overallScore.toFixed(3)} vs B scored ${evalB.overallScore.toFixed(3)}. ` +
                `Winner: ${winner}. Delta: ${Math.abs(scoreDelta).toFixed(3)}`,
        };
    }
    /**
     * Create a summary from a batch of evaluations.
     */
    summarizeBatch(evaluations) {
        const passed = evaluations.filter(e => e.rating === 'up').length;
        const totalLatency = evaluations.reduce((sum, e) => sum + e.processingTimeMs, 0);
        const totalScore = evaluations.reduce((sum, e) => sum + e.overallScore, 0);
        return {
            evaluations,
            summary: {
                total: evaluations.length,
                passed,
                failed: evaluations.length - passed,
                averageScore: evaluations.length > 0 ? totalScore / evaluations.length : 0,
                averageLatencyMs: evaluations.length > 0 ? totalLatency / evaluations.length : 0,
            },
            timestamp: new Date().toISOString(),
        };
    }
    // ─── Private Evaluation Methods ─────────────────────────────────
    checkWidgetCount(result, pageWidgets) {
        const expected = result.layout_json?.widgets?.length || 0;
        const actual = pageWidgets.length;
        // Allow ±1 difference (hero widget might merge or split)
        return Math.abs(expected - actual) <= 1;
    }
    checkScenarioRelevance(query, result) {
        const widgets = result.layout_json?.widgets || [];
        if (widgets.length === 0)
            return 0.5; // No widgets is neutral
        const queryLower = query.toLowerCase();
        const matchedScenarios = [];
        for (const [keyword, expectedScenarios] of Object.entries(rl_config_js_1.EXPECTED_SCENARIOS)) {
            if (queryLower.includes(keyword)) {
                matchedScenarios.push(...expectedScenarios);
            }
        }
        if (matchedScenarios.length === 0)
            return 0.7; // Unknown query type, give benefit of doubt
        // Check how many returned widgets have relevant scenarios
        let relevantCount = 0;
        for (const widget of widgets) {
            const scenario = widget.scenario?.toLowerCase() || '';
            if (matchedScenarios.some(ms => scenario.includes(ms) || ms.includes(scenario))) {
                relevantCount++;
            }
        }
        return widgets.length > 0 ? relevantCount / widgets.length : 0;
    }
    checkDataAccuracy(result, pageWidgets) {
        const widgets = result.layout_json?.widgets || [];
        if (widgets.length === 0 || pageWidgets.length === 0)
            return 0.5;
        let matchCount = 0;
        const checkCount = Math.min(widgets.length, pageWidgets.length);
        for (let i = 0; i < checkCount; i++) {
            const expected = widgets[i];
            const actual = pageWidgets[i];
            // Check scenario matches
            if (actual.scenario && expected.scenario) {
                const scenarioMatch = actual.scenario.toLowerCase() === expected.scenario.toLowerCase() ||
                    actual.scenario.toLowerCase().includes(expected.scenario.toLowerCase());
                if (scenarioMatch)
                    matchCount++;
            }
        }
        return checkCount > 0 ? matchCount / checkCount : 0.5;
    }
    async checkResponseQuality(query, result) {
        const voice = result.voice_response || '';
        if (!voice)
            return 0.3;
        let score = 0.5; // Base score for having a response
        // Length check: too short is bad, reasonable length is good
        if (voice.length > 20 && voice.length < 2000)
            score += 0.2;
        if (voice.length >= 2000)
            score += 0.1;
        // Check if voice response references query terms
        const queryWords = query.toLowerCase().split(/\s+/).filter(w => w.length > 3);
        const voiceLower = voice.toLowerCase();
        const mentionedWords = queryWords.filter(w => voiceLower.includes(w));
        if (queryWords.length > 0) {
            score += 0.3 * (mentionedWords.length / queryWords.length);
        }
        return Math.min(1.0, score);
    }
    computeLatencyScore(processingTimeMs) {
        const budget = this.config.latencyBudgetMs;
        if (processingTimeMs <= budget)
            return 1.0;
        if (processingTimeMs <= budget * 2) {
            return 1.0 - 0.5 * ((processingTimeMs - budget) / budget);
        }
        if (processingTimeMs <= budget * 4) {
            return 0.5 - 0.5 * ((processingTimeMs - budget * 2) / (budget * 2));
        }
        return 0.0;
    }
    generateInteractions(result, score) {
        const widgets = result.layout_json?.widgets || [];
        const interactions = [];
        for (let i = 0; i < widgets.length; i++) {
            // Simulate user engagement based on quality score
            // Higher-scored responses get more engagement (longer durations)
            const engagementMultiplier = score > 0.6 ? 2.0 : 0.5;
            const baseDuration = 3000 + Math.floor(Math.random() * 5000);
            interactions.push({
                widget_index: i,
                action: 'view',
                duration_ms: Math.floor(baseDuration * engagementMultiplier),
            });
            // First widget gets an expand action if score is good
            if (i === 0 && score > 0.5) {
                interactions.push({
                    widget_index: i,
                    action: 'expand',
                    duration_ms: Math.floor(5000 * engagementMultiplier),
                });
            }
        }
        return interactions;
    }
    suggestCorrection(query, result) {
        const widgets = result.layout_json?.widgets || [];
        if (widgets.length === 0)
            return 'No widgets returned for this query';
        const queryLower = query.toLowerCase();
        const suggestions = [];
        // Check for safety-critical queries without alerts
        if ((queryLower.includes('alert') || queryLower.includes('alarm') || queryLower.includes('warning')) &&
            !widgets.some(w => w.scenario?.toLowerCase().includes('alert'))) {
            suggestions.push('Query mentions alerts but no alert widget was included');
        }
        // Check for comparison queries without comparison widget
        if (queryLower.includes('compare') &&
            !widgets.some(w => w.scenario?.toLowerCase().includes('comparison'))) {
            suggestions.push('Query asks for comparison but no comparison widget was included');
        }
        // Check for trend queries without trend widget
        if (queryLower.includes('trend') &&
            !widgets.some(w => w.scenario?.toLowerCase().includes('trend'))) {
            suggestions.push('Query asks for trend but no trend widget was included');
        }
        return suggestions.length > 0 ? suggestions.join('; ') : undefined;
    }
    buildReasoning(query, widgetCountMatch, scenarioRelevance, dataAccuracy, responseQuality, latencyScore, overallScore, rating) {
        const parts = [
            `Query: "${query.slice(0, 80)}"`,
            `Widget count ${widgetCountMatch ? 'matches' : 'MISMATCH'}`,
            `Scenario relevance: ${(scenarioRelevance * 100).toFixed(0)}%`,
            `Data accuracy: ${(dataAccuracy * 100).toFixed(0)}%`,
            `Response quality: ${(responseQuality * 100).toFixed(0)}%`,
            `Latency score: ${(latencyScore * 100).toFixed(0)}%`,
            `Overall: ${(overallScore * 100).toFixed(1)}% → ${rating}`,
        ];
        return parts.join(' | ');
    }
}
exports.RLEvaluator = RLEvaluator;
//# sourceMappingURL=rl-evaluator.js.map