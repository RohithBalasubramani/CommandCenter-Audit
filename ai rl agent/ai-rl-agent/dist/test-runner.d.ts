import type { Page } from '@playwright/test';
import { BrowserAgent } from './browser-agent';
import { AgentBrain } from './agent-brain';
import type { TestScenario, ScenarioResult, AuditReport } from './types';
import type { AgentConfig } from './config';
export interface AITestRunnerConfig {
    /** Base agent configuration */
    agent: AgentConfig;
    /** Directory for all evidence output */
    evidenceBaseDir: string;
    /** Whether to take screenshots at every step (default: true) */
    screenshotEveryStep?: boolean;
    /** Delay between actions in ms (default: 500) */
    actionDelay?: number;
}
export declare class AITestRunner {
    private browser;
    private brain;
    private config;
    private page;
    constructor(page: Page, config: AITestRunnerConfig);
    /** Run a single scenario and return the result */
    runScenario(scenario: TestScenario): Promise<ScenarioResult>;
    /** Execute a single step (observe → decide → execute → screenshot) */
    private runSingleStep;
    /** Run setup action */
    private runSetupAction;
    /** Run teardown action */
    private runTeardownAction;
    /** Run backend API checks defined in the scenario */
    private runBackendChecks;
    /** Evaluate success criteria against current page state */
    private evaluateCriteria;
    /** Build the scenario result object */
    private buildResult;
    /** Get the browser agent for direct access */
    getBrowserAgent(): BrowserAgent;
    /** Get the brain for direct access */
    getBrain(): AgentBrain;
}
export declare function generateAuditReport(results: ScenarioResult[], appName: string, appVersion?: string): AuditReport;
/** Run multiple scenarios with retry support */
export declare function runScenarios(page: Page, scenarios: TestScenario[], config: AITestRunnerConfig, options?: {
    maxRetries?: number;
    onScenarioComplete?: (result: ScenarioResult) => void;
}): Promise<ScenarioResult[]>;
//# sourceMappingURL=test-runner.d.ts.map