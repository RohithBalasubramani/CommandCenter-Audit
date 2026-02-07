"use strict";
/**
 * RL Agent Configuration for Command Center
 *
 * Extends the CC QA agent config with RL-specific settings
 * for evaluation thresholds, API endpoints, and training parameters.
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.EXPECTED_SCENARIOS = exports.EVAL_WEIGHTS = exports.rlConfig = exports.rlRunnerConfig = exports.rlAgentConfig = void 0;
// ─── Agent Config ───────────────────────────────────────────────────
exports.rlAgentConfig = {
    appName: 'Command Center RL Agent',
    baseUrl: 'http://localhost:3100',
    apiBaseUrl: 'http://localhost:8100',
    uiFramework: 'tailwind',
    customSelectors: {
        buttons: ['button', '[role="button"]', '.btn'],
        textInputs: ['input[type="text"]', 'textarea', '[contenteditable]'],
        selects: ['select', '[role="combobox"]', '[role="listbox"]'],
        checkboxes: ['input[type="checkbox"]', '[role="checkbox"]'],
        links: ['a[href]', '[role="link"]'],
        tabs: ['[role="tab"]'],
        menuItems: ['[role="menuitem"]'],
        toasts: ['.toast', '[role="alert"]', '.notification'],
        errors: ['.error', '.text-red-500', '[role="alert"]'],
        modals: ['dialog', '[role="dialog"]', '.modal'],
        loading: ['.loading', '.spinner', '[aria-busy="true"]'],
    },
    llm: {
        model: 'sonnet',
        useVision: true,
        maxTokens: 1024,
        timeout: 900_000,
        temperature: 0.1,
    },
    actionDelay: 1500,
    actionTimeout: 15_000,
    pageLoadTimeout: 60_000,
    stabilityTimeout: 8_000,
    screenshotEveryStep: true,
    verifyAfterAction: true,
    waitForStable: true,
    detectActionReplay: true,
    maxRepeatedActions: 4,
    evidenceDir: './evidence/rl',
};
exports.rlRunnerConfig = {
    agent: exports.rlAgentConfig,
    maxRetries: 1,
    parallelCount: 1,
    browser: 'chromium',
    headed: false,
    recordTrace: true,
    recordVideo: false,
    viewport: { width: 1440, height: 900 },
    permissions: ['microphone'],
};
// ─── RL Evaluation Settings ─────────────────────────────────────────
exports.rlConfig = {
    apiBaseUrl: process.env.RL_API_BASE_URL || 'http://localhost:8100',
    feedbackApiKey: process.env.FEEDBACK_API_KEY || '',
    evaluationThreshold: 0.6,
    latencyBudgetMs: 8_000,
    maxEvalRetries: 2,
    batchSize: 10,
    cooldownMs: 2_000,
};
// ─── Scoring Weights ────────────────────────────────────────────────
exports.EVAL_WEIGHTS = {
    widgetCountMatch: 0.15,
    scenarioRelevance: 0.35,
    dataAccuracy: 0.25,
    responseQuality: 0.15,
    latencyScore: 0.10,
};
// ─── Expected Widget Mappings ───────────────────────────────────────
// Maps query intent keywords to expected widget scenarios
exports.EXPECTED_SCENARIOS = {
    pump: ['equipment_status', 'kpi', 'trend'],
    temperature: ['trend', 'kpi', 'gauge'],
    alert: ['alerts', 'kpi'],
    alarm: ['alerts'],
    energy: ['energy_breakdown', 'kpi', 'trend', 'comparison'],
    transformer: ['equipment_status', 'kpi', 'distribution'],
    chiller: ['equipment_status', 'kpi', 'efficiency'],
    hvac: ['equipment_status', 'kpi'],
    maintenance: ['maintenance_schedule', 'equipment_status', 'alerts'],
    shift: ['shift_schedule', 'personnel'],
    inventory: ['inventory_status', 'kpi'],
    work_order: ['work_orders', 'kpi'],
};
//# sourceMappingURL=rl-config.js.map