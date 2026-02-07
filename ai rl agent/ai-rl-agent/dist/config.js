"use strict";
/**
 * Configuration schema for the AI QA Agent.
 *
 * The agent is designed to be framework-agnostic and highly configurable.
 * All app-specific behavior is driven by configuration, not hardcoded logic.
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.DEFAULT_RUNNER_CONFIG = exports.DEFAULT_AGENT_CONFIG = exports.DEFAULT_LLM_CONFIG = exports.FRAMEWORK_PRESETS = void 0;
exports.createConfig = createConfig;
exports.createRunnerConfig = createRunnerConfig;
exports.getElementSelectors = getElementSelectors;
// ─── Framework Presets ───────────────────────────────────────────────
exports.FRAMEWORK_PRESETS = {
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
};
// ─── Default Configuration ───────────────────────────────────────────
exports.DEFAULT_LLM_CONFIG = {
    model: 'sonnet',
    maxTokens: 1024,
    timeout: 600_000, // 10 minutes - don't rush Claude
    useVision: true,
    temperature: 0.1, // low for consistency
};
exports.DEFAULT_AGENT_CONFIG = {
    uiFramework: 'plain',
    llm: exports.DEFAULT_LLM_CONFIG,
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
};
exports.DEFAULT_RUNNER_CONFIG = {
    maxRetries: 2,
    parallelCount: 1,
    browser: 'chromium',
    headed: false,
    recordVideo: false,
    recordTrace: false,
    viewport: { width: 1280, height: 720 },
    ignoreHTTPSErrors: true,
};
// ─── Configuration Builder ───────────────────────────────────────────
function createConfig(config) {
    const merged = {
        ...exports.DEFAULT_AGENT_CONFIG,
        ...config,
        llm: {
            ...exports.DEFAULT_LLM_CONFIG,
            ...config.llm,
        },
    };
    // Merge custom selectors with framework preset
    if (config.uiFramework && config.uiFramework !== 'custom') {
        const preset = exports.FRAMEWORK_PRESETS[config.uiFramework];
        merged.customSelectors = {
            ...preset,
            ...config.customSelectors,
        };
    }
    return merged;
}
function createRunnerConfig(config) {
    return {
        ...exports.DEFAULT_RUNNER_CONFIG,
        ...config,
    };
}
// ─── Helper Functions ────────────────────────────────────────────────
function getElementSelectors(config) {
    if (config.customSelectors) {
        return config.customSelectors;
    }
    return exports.FRAMEWORK_PRESETS[config.uiFramework] || exports.FRAMEWORK_PRESETS.plain;
}
//# sourceMappingURL=config.js.map