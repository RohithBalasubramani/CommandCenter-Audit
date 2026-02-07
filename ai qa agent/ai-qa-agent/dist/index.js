"use strict";
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
Object.defineProperty(exports, "__esModule", { value: true });
exports.runScenarios = exports.generateAuditReport = exports.AITestRunner = exports.AgentBrain = exports.BrowserAgent = exports.getElementSelectors = exports.createRunnerConfig = exports.createConfig = exports.DEFAULT_RUNNER_CONFIG = exports.DEFAULT_AGENT_CONFIG = exports.DEFAULT_LLM_CONFIG = exports.FRAMEWORK_PRESETS = void 0;
var config_1 = require("./config");
Object.defineProperty(exports, "FRAMEWORK_PRESETS", { enumerable: true, get: function () { return config_1.FRAMEWORK_PRESETS; } });
Object.defineProperty(exports, "DEFAULT_LLM_CONFIG", { enumerable: true, get: function () { return config_1.DEFAULT_LLM_CONFIG; } });
Object.defineProperty(exports, "DEFAULT_AGENT_CONFIG", { enumerable: true, get: function () { return config_1.DEFAULT_AGENT_CONFIG; } });
Object.defineProperty(exports, "DEFAULT_RUNNER_CONFIG", { enumerable: true, get: function () { return config_1.DEFAULT_RUNNER_CONFIG; } });
Object.defineProperty(exports, "createConfig", { enumerable: true, get: function () { return config_1.createConfig; } });
Object.defineProperty(exports, "createRunnerConfig", { enumerable: true, get: function () { return config_1.createRunnerConfig; } });
Object.defineProperty(exports, "getElementSelectors", { enumerable: true, get: function () { return config_1.getElementSelectors; } });
// ─── Browser Agent ───────────────────────────────────────────────────
var browser_agent_1 = require("./browser-agent");
Object.defineProperty(exports, "BrowserAgent", { enumerable: true, get: function () { return browser_agent_1.BrowserAgent; } });
// ─── Agent Brain ─────────────────────────────────────────────────────
var agent_brain_1 = require("./agent-brain");
Object.defineProperty(exports, "AgentBrain", { enumerable: true, get: function () { return agent_brain_1.AgentBrain; } });
var test_runner_1 = require("./test-runner");
Object.defineProperty(exports, "AITestRunner", { enumerable: true, get: function () { return test_runner_1.AITestRunner; } });
Object.defineProperty(exports, "generateAuditReport", { enumerable: true, get: function () { return test_runner_1.generateAuditReport; } });
Object.defineProperty(exports, "runScenarios", { enumerable: true, get: function () { return test_runner_1.runScenarios; } });
//# sourceMappingURL=index.js.map