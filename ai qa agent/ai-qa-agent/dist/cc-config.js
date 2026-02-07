"use strict";
/**
 * Command Center — AI QA Agent Configuration
 *
 * Tailored for the 4-layer industrial dashboard:
 *   Layer 1: Voice I/O (STT/TTS, PTT, Ctrl+Shift+K text input)
 *   Layer 2: AI Orchestrator (Django + Ollama LLM + RAG)
 *   Layer 3: Blob Layout (12-col CSS grid, BlobGrid)
 *   Layer 4: 19 Widget types (kpi, trend, alerts, etc.)
 *
 * Frontend: Next.js 14 + Tailwind + MUI on port 3100
 * Backend: Django on port 8100
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.ccRunnerConfig = exports.ccAgentConfig = void 0;
const config_1 = require("./config");
// ─── Command Center Agent Configuration ──────────────────────────────
exports.ccAgentConfig = (0, config_1.createConfig)({
    appName: 'Command Center',
    baseUrl: 'http://localhost:3100',
    apiBaseUrl: 'http://localhost:8100',
    uiFramework: 'tailwind',
    // Extend tailwind preset with CC-specific selectors
    customSelectors: {
        buttons: [
            'button',
            '[role="button"]',
            '[type="submit"]',
            '[type="button"]',
            '[data-testid="text-input-toggle"]',
            '[data-testid="submit-query"]',
        ],
        textInputs: [
            'input[type="text"]',
            'textarea',
            '[data-testid="text-input"]',
        ],
        selects: ['select', '[role="combobox"]', '[role="listbox"]'],
        checkboxes: ['input[type="checkbox"]', 'input[type="radio"]', '[role="checkbox"]', '[role="switch"]'],
        links: ['a[href]'],
        tabs: ['[role="tab"]'],
        menuItems: ['[role="menuitem"]', '[role="option"]'],
        toasts: ['[role="alert"]', '[role="status"]'],
        errors: ['[role="alert"]', '.text-red-500', '.text-red-600', '.text-red-400'],
        modals: ['[role="dialog"]', '[aria-modal="true"]'],
        loading: ['[role="progressbar"]', '.animate-spin', '.animate-pulse'],
    },
    llm: {
        model: 'sonnet',
        useVision: true,
        maxTokens: 1024,
        timeout: 900_000, // 15 min — some multi-turn scenarios take a while
        temperature: 0.1,
    },
    screenshotEveryStep: true,
    actionDelay: 1500, // CC backend (Ollama LLM) takes 2-10s per query
    defaultPersona: 'default',
    apiRoutesPattern: /\/(api|layer2)\b/,
    maxElementsInObservation: 80,
    pageLoadTimeout: 60_000, // Next.js CSR hydration can be slow on cold start
    actionTimeout: 15_000,
    debug: true,
    evidenceDir: './evidence/cc',
    learningDir: './evidence/cc/learning',
    // Failure mitigation
    verifyAfterAction: true,
    waitForStable: true,
    stabilityTimeout: 8_000, // framer-motion widget transitions (~300ms + stagger)
    detectActionReplay: true,
    maxRepeatedActions: 4,
});
// ─── Runner Configuration ────────────────────────────────────────────
exports.ccRunnerConfig = (0, config_1.createRunnerConfig)({
    agent: exports.ccAgentConfig,
    maxRetries: 1,
    parallelCount: 1,
    browser: 'chromium',
    headed: false,
    recordVideo: false,
    recordTrace: true,
    viewport: { width: 1440, height: 900 },
    permissions: ['microphone'],
    ignoreHTTPSErrors: true,
});
//# sourceMappingURL=cc-config.js.map