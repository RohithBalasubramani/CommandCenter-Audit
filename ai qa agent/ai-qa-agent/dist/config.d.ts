/**
 * Configuration schema for the AI QA Agent.
 *
 * The agent is designed to be framework-agnostic and highly configurable.
 * All app-specific behavior is driven by configuration, not hardcoded logic.
 */
import type { PersonaModifier } from './types';
export type UIFramework = 'mui' | 'tailwind' | 'bootstrap' | 'antd' | 'chakra' | 'shadcn' | 'radix' | 'headless' | 'plain' | 'custom';
export interface ElementDiscoveryConfig {
    /** Selectors for buttons */
    buttons: string[];
    /** Selectors for text inputs */
    textInputs: string[];
    /** Selectors for select/dropdown elements */
    selects: string[];
    /** Selectors for checkboxes/switches */
    checkboxes: string[];
    /** Selectors for links */
    links: string[];
    /** Selectors for tabs */
    tabs: string[];
    /** Selectors for menu items */
    menuItems: string[];
    /** Selectors for toasts/notifications */
    toasts: string[];
    /** Selectors for error messages */
    errors: string[];
    /** Selectors for modals/dialogs */
    modals: string[];
    /** Selectors for loading indicators */
    loading: string[];
    /** Function to check if element is disabled */
    isDisabled?: (el: HTMLElement) => boolean;
    /** Function to get element label/name */
    getLabel?: (el: HTMLElement) => string;
}
export declare const FRAMEWORK_PRESETS: Record<UIFramework, ElementDiscoveryConfig>;
export interface LLMConfig {
    /** Model to use (sonnet, opus, haiku, or full model ID) */
    model: string;
    /** Maximum tokens for response */
    maxTokens?: number;
    /** Timeout for LLM calls in ms */
    timeout?: number;
    /** Whether to use vision (screenshots) */
    useVision?: boolean;
    /** Temperature for creativity (0-1) */
    temperature?: number;
}
export interface AgentConfig {
    /** Name of the application being tested */
    appName: string;
    /** Base URL of the application */
    baseUrl: string;
    /** Backend API base URL (if different from baseUrl) */
    apiBaseUrl?: string;
    /** UI framework being used */
    uiFramework: UIFramework;
    /** Custom element discovery selectors (overrides framework preset) */
    customSelectors?: Partial<ElementDiscoveryConfig>;
    /** LLM configuration */
    llm: LLMConfig;
    /** Directory for evidence output */
    evidenceDir?: string;
    /** Directory for cross-session learning data */
    learningDir?: string;
    /** Whether to take screenshots at every step */
    screenshotEveryStep?: boolean;
    /** Delay between actions in ms */
    actionDelay?: number;
    /** Default persona for tests */
    defaultPersona?: PersonaModifier;
    /** API routes pattern for network capture (regex or string) */
    apiRoutesPattern?: string | RegExp;
    /** Headers to include in API calls (e.g., auth tokens) */
    apiHeaders?: Record<string, string>;
    /** Maximum elements to show in observation (default: 100) */
    maxElementsInObservation?: number;
    /** Skip elements containing these texts */
    skipElementsContaining?: string[];
    /** Global timeout for page loads in ms */
    pageLoadTimeout?: number;
    /** Global timeout for actions in ms */
    actionTimeout?: number;
    /** Enable debug logging */
    debug?: boolean;
    /** Enable post-action verification (checks if action had expected effect) */
    verifyAfterAction?: boolean;
    /** Wait for page stability before observing */
    waitForStable?: boolean;
    /** Maximum time to wait for page stability in ms */
    stabilityTimeout?: number;
    /** Detect and warn on repeated identical actions */
    detectActionReplay?: boolean;
    /** Maximum identical actions before forcing abort */
    maxRepeatedActions?: number;
    /** Enable deterministic mode for reproducible tests */
    deterministicMode?: boolean;
    /** Random seed for deterministic mode */
    randomSeed?: number;
}
export interface RunnerConfig {
    /** Base agent configuration */
    agent: AgentConfig;
    /** Maximum retries for flaky tests */
    maxRetries?: number;
    /** Parallel test execution count */
    parallelCount?: number;
    /** Browser to use */
    browser?: 'chromium' | 'firefox' | 'webkit';
    /** Headed mode (show browser) */
    headed?: boolean;
    /** Slow motion delay in ms */
    slowMo?: number;
    /** Record video */
    recordVideo?: boolean;
    /** Record trace */
    recordTrace?: boolean;
    /** Viewport dimensions */
    viewport?: {
        width: number;
        height: number;
    };
    /** Locale */
    locale?: string;
    /** Timezone */
    timezone?: string;
    /** Geolocation */
    geolocation?: {
        latitude: number;
        longitude: number;
    };
    /** Permissions to grant */
    permissions?: string[];
    /** Extra HTTP headers */
    extraHTTPHeaders?: Record<string, string>;
    /** Ignore HTTPS errors */
    ignoreHTTPSErrors?: boolean;
    /** Device emulation */
    device?: string;
}
export declare const DEFAULT_LLM_CONFIG: LLMConfig;
export declare const DEFAULT_AGENT_CONFIG: Partial<AgentConfig>;
export declare const DEFAULT_RUNNER_CONFIG: Partial<RunnerConfig>;
export declare function createConfig(config: Partial<AgentConfig> & {
    appName: string;
    baseUrl: string;
}): AgentConfig;
export declare function createRunnerConfig(config: Partial<RunnerConfig> & {
    agent: AgentConfig;
}): RunnerConfig;
export declare function getElementSelectors(config: AgentConfig): ElementDiscoveryConfig;
//# sourceMappingURL=config.d.ts.map