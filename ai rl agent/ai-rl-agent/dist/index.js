"use strict";
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
Object.defineProperty(exports, "__esModule", { value: true });
exports.EVAL_QUERIES = exports.rlScenarios = exports.EXPECTED_SCENARIOS = exports.EVAL_WEIGHTS = exports.rlConfig = exports.rlRunnerConfig = exports.rlAgentConfig = exports.RLEvaluator = exports.RLClient = exports.runScenarios = exports.generateAuditReport = exports.AITestRunner = exports.AgentBrain = exports.BrowserAgent = exports.getElementSelectors = exports.createRunnerConfig = exports.createConfig = exports.DEFAULT_RUNNER_CONFIG = exports.DEFAULT_AGENT_CONFIG = exports.DEFAULT_LLM_CONFIG = exports.FRAMEWORK_PRESETS = void 0;
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
// ─── RL Client ──────────────────────────────────────────────────────
var rl_client_1 = require("./rl-client");
Object.defineProperty(exports, "RLClient", { enumerable: true, get: function () { return rl_client_1.RLClient; } });
// ─── RL Evaluator ───────────────────────────────────────────────────
var rl_evaluator_1 = require("./rl-evaluator");
Object.defineProperty(exports, "RLEvaluator", { enumerable: true, get: function () { return rl_evaluator_1.RLEvaluator; } });
// ─── RL Config ──────────────────────────────────────────────────────
var rl_config_1 = require("./rl-config");
Object.defineProperty(exports, "rlAgentConfig", { enumerable: true, get: function () { return rl_config_1.rlAgentConfig; } });
Object.defineProperty(exports, "rlRunnerConfig", { enumerable: true, get: function () { return rl_config_1.rlRunnerConfig; } });
Object.defineProperty(exports, "rlConfig", { enumerable: true, get: function () { return rl_config_1.rlConfig; } });
Object.defineProperty(exports, "EVAL_WEIGHTS", { enumerable: true, get: function () { return rl_config_1.EVAL_WEIGHTS; } });
Object.defineProperty(exports, "EXPECTED_SCENARIOS", { enumerable: true, get: function () { return rl_config_1.EXPECTED_SCENARIOS; } });
// ─── RL Scenarios ───────────────────────────────────────────────────
var rl_scenarios_1 = require("./rl-scenarios");
Object.defineProperty(exports, "rlScenarios", { enumerable: true, get: function () { return rl_scenarios_1.rlScenarios; } });
Object.defineProperty(exports, "EVAL_QUERIES", { enumerable: true, get: function () { return rl_scenarios_1.EVAL_QUERIES; } });
//# sourceMappingURL=index.js.map