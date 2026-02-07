/**
 * BrowserAgent — Framework-agnostic Playwright-based browser controller.
 *
 * This is the "hands" of the AI test agent. It can:
 * - Take screenshots and observe the current page state
 * - Click buttons, type into fields, select dropdown options
 * - Navigate to URLs, scroll the page
 * - Capture network traffic (API calls)
 * - Upload files, press keyboard keys
 *
 * The BrowserAgent does NOT decide what to do — that's the AgentBrain's job.
 * This class simply executes actions and reports observations.
 *
 * Framework-agnostic: Uses configuration to adapt to MUI, Tailwind, Bootstrap, etc.
 */
import { type Page } from '@playwright/test';
import type { AgentAction, PageObservation, VerifyAssertion } from './types';
import type { AgentConfig } from './config';
export declare class BrowserAgent {
    private page;
    private config;
    private selectors;
    private apiCalls;
    private requestBodies;
    private consoleErrors;
    private evidenceDir;
    private screenshotCount;
    private apiRoutePattern;
    constructor(page: Page, config: AgentConfig, evidenceDir: string);
    /**
     * Attach request+response listeners to capture API calls.
     */
    private setupNetworkCapture;
    /**
     * Capture browser console errors so the agent knows about JS crashes.
     */
    private setupConsoleCapture;
    /** Take a screenshot and save it as evidence */
    takeScreenshot(label?: string): Promise<string>;
    /** Take a screenshot and return as base64 for LLM vision */
    getScreenshotBase64(): Promise<string>;
    /** Observe the current page state — this is what the LLM "sees" */
    observe(): Promise<PageObservation>;
    /**
     * Get all interactive elements currently visible on the page.
     * Uses configuration-driven selectors for framework agnosticism.
     */
    private getInteractiveElements;
    /** Get visible toast/snackbar messages */
    private getToasts;
    /** Get visible error messages */
    private getErrors;
    /** Get the main page heading */
    private getHeading;
    /** Execute an action decided by the AgentBrain */
    execute(action: AgentAction): Promise<{
        success: boolean;
        error?: string;
    }>;
    private resolveLocator;
    /**
     * Execute click with multi-strategy fallback:
     * 1. Scroll into view
     * 2. Regular click
     * 3. Force click (bypasses actionability checks)
     * 4. Coordinate-based click fallback
     */
    private executeClick;
    private executeType;
    /**
     * Navigate with retry on timeout/connection refused.
     */
    private executeNavigate;
    private executeScroll;
    private executeSelect;
    private executeUpload;
    private executeWait;
    /**
     * Execute a keyboard key press (Escape, Enter, Tab, etc.)
     */
    private executeKey;
    /**
     * Hover over an element (for tooltips, menus)
     */
    private executeHover;
    /**
     * Drag and drop
     */
    private executeDrag;
    /** Run a verification check */
    verify(assertion: VerifyAssertion): Promise<{
        passed: boolean;
        actual?: string;
    }>;
    /** Make a direct API call (bypassing the browser) */
    apiCall(method: string, endpoint: string, body?: Record<string, unknown>, headers?: Record<string, string>): Promise<{
        status: number;
        data: unknown;
    }>;
    /** Save the network capture log */
    saveNetworkLog(scenarioId: string): Promise<string>;
    /** Get the page instance for direct access */
    getPage(): Page;
}
//# sourceMappingURL=browser-agent.d.ts.map