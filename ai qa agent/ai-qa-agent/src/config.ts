/**
 * Configuration schema for the AI QA Agent.
 *
 * The agent is designed to be framework-agnostic and highly configurable.
 * All app-specific behavior is driven by configuration, not hardcoded logic.
 */

import type { PersonaModifier } from './types'

// ─── UI Framework Presets ────────────────────────────────────────────

export type UIFramework =
  | 'mui'           // Material-UI / MUI
  | 'tailwind'      // Tailwind CSS (no component library)
  | 'bootstrap'     // Bootstrap
  | 'antd'          // Ant Design
  | 'chakra'        // Chakra UI
  | 'shadcn'        // shadcn/ui
  | 'radix'         // Radix UI primitives
  | 'headless'      // Headless UI
  | 'plain'         // Plain HTML/CSS
  | 'custom'        // Custom selectors provided by user

// ─── Element Discovery Configuration ─────────────────────────────────

export interface ElementDiscoveryConfig {
  /** Selectors for buttons */
  buttons: string[]
  /** Selectors for text inputs */
  textInputs: string[]
  /** Selectors for select/dropdown elements */
  selects: string[]
  /** Selectors for checkboxes/switches */
  checkboxes: string[]
  /** Selectors for links */
  links: string[]
  /** Selectors for tabs */
  tabs: string[]
  /** Selectors for menu items */
  menuItems: string[]
  /** Selectors for toasts/notifications */
  toasts: string[]
  /** Selectors for error messages */
  errors: string[]
  /** Selectors for modals/dialogs */
  modals: string[]
  /** Selectors for loading indicators */
  loading: string[]
  /** Function to check if element is disabled */
  isDisabled?: (el: HTMLElement) => boolean
  /** Function to get element label/name */
  getLabel?: (el: HTMLElement) => string
}

// ─── Framework Presets ───────────────────────────────────────────────

export const FRAMEWORK_PRESETS: Record<UIFramework, ElementDiscoveryConfig> = {
  mui: {
    buttons: ['button', '[role="button"]', '.MuiIconButton-root', '.MuiButton-root', '.MuiFab-root'],
    textInputs: ['input[type="text"]', 'input[type="email"]', 'input[type="password"]', 'input[type="search"]', 'input[type="url"]', 'input[type="number"]', 'textarea', '.MuiInputBase-input'],
    selects: ['[role="combobox"]', 'select', '.MuiSelect-select', '.MuiAutocomplete-root input'],
    checkboxes: ['input[type="checkbox"]', '[role="checkbox"]', '.MuiSwitch-root input', '[role="switch"]', '.MuiCheckbox-root input'],
    links: ['a[href]', '.MuiLink-root'],
    tabs: ['[role="tab"]', '.MuiTab-root'],
    menuItems: ['[role="menuitem"]', '.MuiMenuItem-root', '[role="option"]'],
    toasts: ['.MuiSnackbar-root', '[role="alert"]', '.MuiAlert-root'],
    errors: ['.MuiFormHelperText-root.Mui-error', '.MuiAlert-standardError', '[role="alert"]'],
    modals: ['.MuiDialog-root', '.MuiModal-root', '[role="dialog"]'],
    loading: ['.MuiCircularProgress-root', '.MuiLinearProgress-root', '.MuiSkeleton-root'],
  },
  tailwind: {
    buttons: ['button', '[role="button"]', '[type="submit"]', '[type="button"]'],
    textInputs: ['input[type="text"]', 'input[type="email"]', 'input[type="password"]', 'input[type="search"]', 'input[type="url"]', 'input[type="number"]', 'textarea'],
    selects: ['select', '[role="combobox"]', '[role="listbox"]'],
    checkboxes: ['input[type="checkbox"]', 'input[type="radio"]', '[role="checkbox"]', '[role="switch"]'],
    links: ['a[href]'],
    tabs: ['[role="tab"]'],
    menuItems: ['[role="menuitem"]', '[role="option"]'],
    toasts: ['[role="alert"]', '[role="status"]'],
    errors: ['[role="alert"]', '.text-red-500', '.text-red-600', '.text-error'],
    modals: ['[role="dialog"]', '[aria-modal="true"]'],
    loading: ['[role="progressbar"]', '.animate-spin', '.animate-pulse'],
  },
  bootstrap: {
    buttons: ['button', '.btn', '[role="button"]'],
    textInputs: ['input.form-control', 'textarea.form-control', 'input[type="text"]', 'input[type="email"]', 'input[type="password"]'],
    selects: ['select.form-select', 'select.form-control', '[role="combobox"]'],
    checkboxes: ['.form-check-input', 'input[type="checkbox"]', 'input[type="radio"]'],
    links: ['a[href]', '.nav-link'],
    tabs: ['.nav-tabs .nav-link', '[role="tab"]'],
    menuItems: ['.dropdown-item', '[role="menuitem"]'],
    toasts: ['.toast', '.alert', '[role="alert"]'],
    errors: ['.invalid-feedback', '.alert-danger', '[role="alert"]'],
    modals: ['.modal', '[role="dialog"]'],
    loading: ['.spinner-border', '.spinner-grow', '.placeholder'],
  },
  antd: {
    buttons: ['button', '.ant-btn', '[role="button"]'],
    textInputs: ['.ant-input', 'input[type="text"]', 'textarea.ant-input'],
    selects: ['.ant-select', '[role="combobox"]'],
    checkboxes: ['.ant-checkbox-input', '.ant-switch', '.ant-radio-input'],
    links: ['a[href]', '.ant-anchor-link'],
    tabs: ['.ant-tabs-tab', '[role="tab"]'],
    menuItems: ['.ant-menu-item', '.ant-dropdown-menu-item', '[role="menuitem"]'],
    toasts: ['.ant-message', '.ant-notification', '[role="alert"]'],
    errors: ['.ant-form-item-explain-error', '.ant-alert-error'],
    modals: ['.ant-modal', '[role="dialog"]'],
    loading: ['.ant-spin', '.ant-skeleton'],
  },
  chakra: {
    buttons: ['button', '[role="button"]'],
    textInputs: ['input', 'textarea'],
    selects: ['select', '[role="combobox"]'],
    checkboxes: ['input[type="checkbox"]', '[role="checkbox"]', '[role="switch"]'],
    links: ['a[href]'],
    tabs: ['[role="tab"]'],
    menuItems: ['[role="menuitem"]'],
    toasts: ['[role="alert"]', '[role="status"]'],
    errors: ['[role="alert"]'],
    modals: ['[role="dialog"]', '[aria-modal="true"]'],
    loading: ['[role="progressbar"]'],
  },
  shadcn: {
    buttons: ['button', '[role="button"]'],
    textInputs: ['input', 'textarea'],
    selects: ['[role="combobox"]', 'select'],
    checkboxes: ['[role="checkbox"]', '[role="switch"]', 'input[type="checkbox"]'],
    links: ['a[href]'],
    tabs: ['[role="tab"]'],
    menuItems: ['[role="menuitem"]'],
    toasts: ['[role="alert"]', '[role="status"]'],
    errors: ['[role="alert"]'],
    modals: ['[role="dialog"]', '[role="alertdialog"]'],
    loading: ['[role="progressbar"]'],
  },
  radix: {
    buttons: ['button', '[role="button"]'],
    textInputs: ['input', 'textarea'],
    selects: ['[role="combobox"]', '[data-radix-select-trigger]'],
    checkboxes: ['[role="checkbox"]', '[role="switch"]'],
    links: ['a[href]'],
    tabs: ['[role="tab"]'],
    menuItems: ['[role="menuitem"]'],
    toasts: ['[role="alert"]', '[data-radix-toast-viewport] > *'],
    errors: ['[role="alert"]'],
    modals: ['[role="dialog"]', '[data-radix-dialog-content]'],
    loading: ['[role="progressbar"]'],
  },
  headless: {
    buttons: ['button', '[role="button"]'],
    textInputs: ['input', 'textarea'],
    selects: ['[role="combobox"]', '[role="listbox"]'],
    checkboxes: ['[role="checkbox"]', '[role="switch"]'],
    links: ['a[href]'],
    tabs: ['[role="tab"]'],
    menuItems: ['[role="menuitem"]', '[role="option"]'],
    toasts: ['[role="alert"]', '[role="status"]'],
    errors: ['[role="alert"]'],
    modals: ['[role="dialog"]'],
    loading: ['[role="progressbar"]'],
  },
  plain: {
    buttons: ['button', 'input[type="submit"]', 'input[type="button"]', '[role="button"]'],
    textInputs: ['input[type="text"]', 'input[type="email"]', 'input[type="password"]', 'input[type="search"]', 'input[type="tel"]', 'input[type="url"]', 'input[type="number"]', 'textarea'],
    selects: ['select', '[role="combobox"]', '[role="listbox"]'],
    checkboxes: ['input[type="checkbox"]', 'input[type="radio"]', '[role="checkbox"]', '[role="switch"]'],
    links: ['a[href]'],
    tabs: ['[role="tab"]'],
    menuItems: ['[role="menuitem"]', '[role="option"]'],
    toasts: ['[role="alert"]', '[role="status"]'],
    errors: ['[role="alert"]', '.error', '.error-message'],
    modals: ['[role="dialog"]', '[aria-modal="true"]'],
    loading: ['[role="progressbar"]', '.loading', '.spinner'],
  },
  custom: {
    buttons: [],
    textInputs: [],
    selects: [],
    checkboxes: [],
    links: [],
    tabs: [],
    menuItems: [],
    toasts: [],
    errors: [],
    modals: [],
    loading: [],
  },
}

// ─── LLM Configuration ───────────────────────────────────────────────

export interface LLMConfig {
  /** Model to use (sonnet, opus, haiku, or full model ID) */
  model: string
  /** Maximum tokens for response */
  maxTokens?: number
  /** Timeout for LLM calls in ms */
  timeout?: number
  /** Whether to use vision (screenshots) */
  useVision?: boolean
  /** Temperature for creativity (0-1) */
  temperature?: number
}

// ─── Main Agent Configuration ────────────────────────────────────────

export interface AgentConfig {
  /** Name of the application being tested */
  appName: string
  /** Base URL of the application */
  baseUrl: string
  /** Backend API base URL (if different from baseUrl) */
  apiBaseUrl?: string
  /** UI framework being used */
  uiFramework: UIFramework
  /** Custom element discovery selectors (overrides framework preset) */
  customSelectors?: Partial<ElementDiscoveryConfig>
  /** LLM configuration */
  llm: LLMConfig
  /** Directory for evidence output */
  evidenceDir?: string
  /** Directory for cross-session learning data */
  learningDir?: string
  /** Whether to take screenshots at every step */
  screenshotEveryStep?: boolean
  /** Delay between actions in ms */
  actionDelay?: number
  /** Default persona for tests */
  defaultPersona?: PersonaModifier
  /** API routes pattern for network capture (regex or string) */
  apiRoutesPattern?: string | RegExp
  /** Headers to include in API calls (e.g., auth tokens) */
  apiHeaders?: Record<string, string>
  /** Maximum elements to show in observation (default: 100) */
  maxElementsInObservation?: number
  /** Skip elements containing these texts */
  skipElementsContaining?: string[]
  /** Global timeout for page loads in ms */
  pageLoadTimeout?: number
  /** Global timeout for actions in ms */
  actionTimeout?: number
  /** Enable debug logging */
  debug?: boolean

  // ─── Failure Mode Mitigation Settings ────────────────────────────────

  /** Enable post-action verification (checks if action had expected effect) */
  verifyAfterAction?: boolean
  /** Wait for page stability before observing */
  waitForStable?: boolean
  /** Maximum time to wait for page stability in ms */
  stabilityTimeout?: number
  /** Detect and warn on repeated identical actions */
  detectActionReplay?: boolean
  /** Maximum identical actions before forcing abort */
  maxRepeatedActions?: number
  /** Enable deterministic mode for reproducible tests */
  deterministicMode?: boolean
  /** Random seed for deterministic mode */
  randomSeed?: number
}

// ─── Runner Configuration ────────────────────────────────────────────

export interface RunnerConfig {
  /** Base agent configuration */
  agent: AgentConfig
  /** Maximum retries for flaky tests */
  maxRetries?: number
  /** Parallel test execution count */
  parallelCount?: number
  /** Browser to use */
  browser?: 'chromium' | 'firefox' | 'webkit'
  /** Headed mode (show browser) */
  headed?: boolean
  /** Slow motion delay in ms */
  slowMo?: number
  /** Record video */
  recordVideo?: boolean
  /** Record trace */
  recordTrace?: boolean
  /** Viewport dimensions */
  viewport?: { width: number; height: number }
  /** Locale */
  locale?: string
  /** Timezone */
  timezone?: string
  /** Geolocation */
  geolocation?: { latitude: number; longitude: number }
  /** Permissions to grant */
  permissions?: string[]
  /** Extra HTTP headers */
  extraHTTPHeaders?: Record<string, string>
  /** Ignore HTTPS errors */
  ignoreHTTPSErrors?: boolean
  /** Device emulation */
  device?: string
}

// ─── Default Configuration ───────────────────────────────────────────

export const DEFAULT_LLM_CONFIG: LLMConfig = {
  model: 'sonnet',
  maxTokens: 1024,
  timeout: 600_000, // 10 minutes - don't rush Claude
  useVision: true,
  temperature: 0.1, // low for consistency
}

export const DEFAULT_AGENT_CONFIG: Partial<AgentConfig> = {
  uiFramework: 'plain',
  llm: DEFAULT_LLM_CONFIG,
  screenshotEveryStep: true,
  actionDelay: 500,
  defaultPersona: 'default',
  maxElementsInObservation: 100,
  skipElementsContaining: ['notification', 'cookie'],
  pageLoadTimeout: 30_000,
  actionTimeout: 10_000,
  debug: false,

  // Failure mode mitigations (all enabled by default)
  verifyAfterAction: true,
  waitForStable: true,
  stabilityTimeout: 5_000,
  detectActionReplay: true,
  maxRepeatedActions: 3,
  deterministicMode: false,
  randomSeed: undefined,
}

export const DEFAULT_RUNNER_CONFIG: Partial<RunnerConfig> = {
  maxRetries: 2,
  parallelCount: 1,
  browser: 'chromium',
  headed: false,
  recordVideo: false,
  recordTrace: false,
  viewport: { width: 1280, height: 720 },
  ignoreHTTPSErrors: true,
}

// ─── Configuration Builder ───────────────────────────────────────────

export function createConfig(config: Partial<AgentConfig> & { appName: string; baseUrl: string }): AgentConfig {
  const merged: AgentConfig = {
    ...DEFAULT_AGENT_CONFIG,
    ...config,
    llm: {
      ...DEFAULT_LLM_CONFIG,
      ...config.llm,
    },
  } as AgentConfig

  // Merge custom selectors with framework preset
  if (config.uiFramework && config.uiFramework !== 'custom') {
    const preset = FRAMEWORK_PRESETS[config.uiFramework]
    merged.customSelectors = {
      ...preset,
      ...config.customSelectors,
    }
  }

  return merged
}

export function createRunnerConfig(config: Partial<RunnerConfig> & { agent: AgentConfig }): RunnerConfig {
  return {
    ...DEFAULT_RUNNER_CONFIG,
    ...config,
  } as RunnerConfig
}

// ─── Helper Functions ────────────────────────────────────────────────

export function getElementSelectors(config: AgentConfig): ElementDiscoveryConfig {
  if (config.customSelectors) {
    return config.customSelectors as ElementDiscoveryConfig
  }
  return FRAMEWORK_PRESETS[config.uiFramework] || FRAMEWORK_PRESETS.plain
}
