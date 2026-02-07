"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", { value: true });
exports.BrowserAgent = void 0;
const fs = __importStar(require("fs"));
const path = __importStar(require("path"));
const config_1 = require("./config");
class BrowserAgent {
    page;
    config;
    selectors;
    apiCalls = [];
    requestBodies = new Map();
    consoleErrors = [];
    evidenceDir;
    screenshotCount = 0;
    apiRoutePattern;
    constructor(page, config, evidenceDir) {
        this.page = page;
        this.config = config;
        this.selectors = (0, config_1.getElementSelectors)(config);
        this.evidenceDir = evidenceDir;
        // Build API route pattern from config
        if (config.apiRoutesPattern) {
            this.apiRoutePattern = typeof config.apiRoutesPattern === 'string'
                ? new RegExp(config.apiRoutesPattern)
                : config.apiRoutesPattern;
        }
        else {
            // Default: match /api/ or common REST patterns
            this.apiRoutePattern = /\/(api|graphql|v\d+)\b/;
        }
        fs.mkdirSync(path.join(evidenceDir, 'screenshots'), { recursive: true });
        fs.mkdirSync(path.join(evidenceDir, 'network'), { recursive: true });
        this.setupNetworkCapture();
        this.setupConsoleCapture();
    }
    /**
     * Attach request+response listeners to capture API calls.
     */
    setupNetworkCapture() {
        this.page.on('request', (request) => {
            const url = request.url();
            if (!this.apiRoutePattern.test(url))
                return;
            const postData = request.postData();
            if (postData) {
                this.requestBodies.set(`${request.method()}:${url}`, postData.slice(0, 1000));
            }
        });
        this.page.on('response', async (response) => {
            const url = response.url();
            if (!this.apiRoutePattern.test(url))
                return;
            const request = response.request();
            let responsePreview = '';
            let contentType = '';
            try {
                contentType = response.headers()['content-type'] || '';
                if (contentType.includes('json')) {
                    const body = await response.json().catch(() => null);
                    responsePreview = JSON.stringify(body).slice(0, 500);
                }
                else {
                    responsePreview = (await response.text().catch(() => '')).slice(0, 500);
                }
            }
            catch { /* streaming or binary */ }
            const reqKey = `${request.method()}:${url}`;
            this.apiCalls.push({
                method: request.method(),
                url,
                status: response.status(),
                responseTime: 0,
                responsePreview,
                requestBody: this.requestBodies.get(reqKey),
                contentType,
            });
            this.requestBodies.delete(reqKey);
        });
    }
    /**
     * Capture browser console errors so the agent knows about JS crashes.
     */
    setupConsoleCapture() {
        this.page.on('console', (msg) => {
            if (msg.type() === 'error') {
                const text = msg.text().slice(0, 300);
                // Skip noisy/irrelevant errors
                if (text.includes('favicon') || text.includes('net::ERR_'))
                    return;
                this.consoleErrors.push(text);
            }
        });
        this.page.on('pageerror', (err) => {
            this.consoleErrors.push(`Uncaught: ${err.message.slice(0, 300)}`);
        });
    }
    /** Take a screenshot and save it as evidence */
    async takeScreenshot(label) {
        this.screenshotCount++;
        const filename = `${String(this.screenshotCount).padStart(3, '0')}-${label || 'step'}.png`;
        const filepath = path.join(this.evidenceDir, 'screenshots', filename);
        try {
            await this.page.screenshot({ path: filepath, fullPage: false });
        }
        catch {
            if (this.config.debug) {
                console.warn(`[BrowserAgent] Screenshot failed: ${label}`);
            }
        }
        return filepath;
    }
    /** Take a screenshot and return as base64 for LLM vision */
    async getScreenshotBase64() {
        try {
            const buffer = await Promise.race([
                this.page.screenshot({ fullPage: false }),
                new Promise((_, reject) => setTimeout(() => reject(new Error('Screenshot timeout')), 10_000)),
            ]);
            return buffer.toString('base64');
        }
        catch {
            return '';
        }
    }
    /** Observe the current page state — this is what the LLM "sees" */
    async observe() {
        const url = this.page.url();
        const title = await this.page.title();
        const interactiveElements = await this.getInteractiveElements();
        const toasts = await this.getToasts();
        const errors = await this.getErrors();
        const heading = await this.getHeading();
        // Get and reset API calls
        const recentApiCalls = [...this.apiCalls];
        this.apiCalls = [];
        // Get and reset console errors
        const consoleErrors = [...this.consoleErrors];
        this.consoleErrors = [];
        // Screenshot for LLM vision
        const screenshot = this.config.llm.useVision
            ? await this.getScreenshotBase64()
            : undefined;
        // Semantic hints from API activity
        const semanticHints = [];
        for (const call of recentApiCalls) {
            if (call.status >= 400) {
                semanticHints.push(`Backend error: ${call.method} ${call.url} → ${call.status}`);
            }
            if (call.method === 'POST' && call.status < 300 && call.responsePreview) {
                try {
                    const resp = JSON.parse(call.responsePreview);
                    if (resp.id) {
                        semanticHints.push(`Resource created: ID=${resp.id}`);
                    }
                }
                catch { /* not JSON */ }
            }
        }
        // Viewport and scroll position
        const viewport = this.page.viewportSize() || undefined;
        const scrollPosition = await this.page.evaluate(() => ({
            x: window.scrollX,
            y: window.scrollY,
        })).catch(() => undefined);
        return {
            url,
            title,
            interactiveElements,
            toasts,
            screenshot,
            recentApiCalls,
            errors,
            heading,
            semanticHints,
            consoleErrors,
            viewport,
            scrollPosition,
        };
    }
    /**
     * Get all interactive elements currently visible on the page.
     * Uses configuration-driven selectors for framework agnosticism.
     */
    async getInteractiveElements() {
        const EVAL_TIMEOUT = 15_000;
        const selectors = this.selectors;
        const maxElements = this.config.maxElementsInObservation || 100;
        const skipTexts = this.config.skipElementsContaining || [];
        return Promise.race([
            this.page.evaluate(({ selectors, maxElements, skipTexts }) => {
                const elements = [];
                function isDisabled(el) {
                    return el.disabled === true
                        || el.getAttribute('aria-disabled') === 'true'
                        || el.classList.contains('Mui-disabled')
                        || el.classList.contains('disabled')
                        || el.closest('button')?.disabled === true;
                }
                function getCenter(el) {
                    const rect = el.getBoundingClientRect();
                    return {
                        x: Math.round(rect.left + rect.width / 2),
                        y: Math.round(rect.top + rect.height / 2),
                    };
                }
                function shouldSkip(text) {
                    const lower = text.toLowerCase();
                    return skipTexts.some((skip) => lower.includes(skip.toLowerCase()));
                }
                function getLabel(el) {
                    return (el.textContent?.trim().slice(0, 80) ||
                        el.getAttribute('aria-label') ||
                        el.getAttribute('title') ||
                        el.getAttribute('placeholder') ||
                        '');
                }
                // Buttons
                const buttonSelectors = selectors.buttons.join(', ');
                if (buttonSelectors) {
                    document.querySelectorAll(buttonSelectors).forEach((el) => {
                        const htmlEl = el;
                        if (!htmlEl.offsetParent)
                            return;
                        const name = getLabel(htmlEl);
                        if (shouldSkip(name))
                            return;
                        const center = getCenter(htmlEl);
                        elements.push({
                            role: 'button',
                            name,
                            disabled: isDisabled(htmlEl),
                            testId: htmlEl.dataset.testid || undefined,
                            tagName: htmlEl.tagName.toLowerCase(),
                            ...center,
                        });
                    });
                }
                // Text inputs
                const inputSelectors = selectors.textInputs.join(', ');
                if (inputSelectors) {
                    document.querySelectorAll(inputSelectors).forEach((el) => {
                        const htmlEl = el;
                        if (!htmlEl.offsetParent)
                            return;
                        const label = htmlEl.getAttribute('aria-label')
                            || document.querySelector(`label[for="${htmlEl.id}"]`)?.textContent?.trim()
                            || htmlEl.placeholder
                            || htmlEl.closest('.MuiFormControl-root')?.querySelector('label')?.textContent?.trim()
                            || '';
                        if (shouldSkip(label))
                            return;
                        elements.push({
                            role: 'textbox',
                            name: label.slice(0, 80),
                            type: htmlEl.type,
                            value: htmlEl.value?.slice(0, 50),
                            disabled: isDisabled(htmlEl),
                            required: htmlEl.required,
                            placeholder: htmlEl.placeholder,
                            testId: htmlEl.dataset.testid || undefined,
                            tagName: 'input',
                        });
                    });
                }
                // Select/combobox
                const selectSelectors = selectors.selects.join(', ');
                if (selectSelectors) {
                    document.querySelectorAll(selectSelectors).forEach((el) => {
                        const htmlEl = el;
                        if (!htmlEl.offsetParent)
                            return;
                        const name = htmlEl.getAttribute('aria-label')
                            || htmlEl.closest('.MuiFormControl-root')?.querySelector('label')?.textContent?.trim()
                            || htmlEl.textContent?.trim().slice(0, 80)
                            || '';
                        if (shouldSkip(name))
                            return;
                        elements.push({
                            role: 'combobox',
                            name,
                            disabled: isDisabled(htmlEl),
                            testId: htmlEl.dataset.testid || undefined,
                            tagName: htmlEl.tagName.toLowerCase(),
                        });
                    });
                }
                // Links
                const linkSelectors = selectors.links.join(', ');
                if (linkSelectors) {
                    document.querySelectorAll(linkSelectors).forEach((el) => {
                        const htmlEl = el;
                        if (!htmlEl.offsetParent)
                            return;
                        const name = getLabel(htmlEl);
                        if (shouldSkip(name))
                            return;
                        elements.push({
                            role: 'link',
                            name,
                            tagName: 'a',
                        });
                    });
                }
                // Tabs
                const tabSelectors = selectors.tabs.join(', ');
                if (tabSelectors) {
                    document.querySelectorAll(tabSelectors).forEach((el) => {
                        const htmlEl = el;
                        if (!htmlEl.offsetParent)
                            return;
                        const name = getLabel(htmlEl);
                        if (shouldSkip(name))
                            return;
                        elements.push({
                            role: 'tab',
                            name,
                            selected: el.getAttribute('aria-selected') === 'true',
                            tagName: htmlEl.tagName.toLowerCase(),
                        });
                    });
                }
                // Checkboxes
                const checkboxSelectors = selectors.checkboxes.join(', ');
                if (checkboxSelectors) {
                    document.querySelectorAll(checkboxSelectors).forEach((el) => {
                        const htmlEl = el;
                        if (!htmlEl.offsetParent)
                            return;
                        const label = htmlEl.getAttribute('aria-label')
                            || htmlEl.closest('.MuiFormControlLabel-root')?.textContent?.trim().slice(0, 80)
                            || document.querySelector(`label[for="${htmlEl.id}"]`)?.textContent?.trim()
                            || '';
                        if (shouldSkip(label))
                            return;
                        elements.push({
                            role: 'checkbox',
                            name: label,
                            checked: htmlEl.checked,
                            disabled: isDisabled(htmlEl),
                            tagName: 'input',
                        });
                    });
                }
                // Menu items
                const menuSelectors = selectors.menuItems.join(', ');
                if (menuSelectors) {
                    document.querySelectorAll(menuSelectors).forEach((el) => {
                        const htmlEl = el;
                        if (!htmlEl.offsetParent)
                            return;
                        const name = getLabel(htmlEl);
                        if (shouldSkip(name))
                            return;
                        elements.push({
                            role: 'menuitem',
                            name,
                            tagName: htmlEl.tagName.toLowerCase(),
                        });
                    });
                }
                // Column headers (sortable tables)
                document.querySelectorAll('th[role="columnheader"], .MuiTableSortLabel-root').forEach((el) => {
                    const htmlEl = el;
                    if (!htmlEl.offsetParent)
                        return;
                    elements.push({
                        role: 'columnheader',
                        name: htmlEl.textContent?.trim().slice(0, 80) || '',
                        tagName: htmlEl.tagName.toLowerCase(),
                    });
                });
                return elements.slice(0, maxElements);
            }, { selectors, maxElements, skipTexts }),
            new Promise((_, reject) => setTimeout(() => reject(new Error('getInteractiveElements timed out')), EVAL_TIMEOUT)),
        ]).catch(() => []);
    }
    /** Get visible toast/snackbar messages */
    async getToasts() {
        const toastSelectors = this.selectors.toasts.join(', ');
        if (!toastSelectors)
            return [];
        return Promise.race([
            this.page.evaluate((selector) => {
                const toasts = [];
                document.querySelectorAll(selector).forEach((el) => {
                    const text = el.textContent?.trim();
                    if (text)
                        toasts.push(text.slice(0, 200));
                });
                return toasts;
            }, toastSelectors),
            new Promise((resolve) => setTimeout(() => resolve([]), 5000)),
        ]);
    }
    /** Get visible error messages */
    async getErrors() {
        const errorSelectors = this.selectors.errors.join(', ');
        if (!errorSelectors)
            return [];
        return Promise.race([
            this.page.evaluate((selector) => {
                const errors = [];
                document.querySelectorAll(selector).forEach((el) => {
                    const text = el.textContent?.trim();
                    if (text)
                        errors.push(text.slice(0, 200));
                });
                return errors;
            }, errorSelectors),
            new Promise((resolve) => setTimeout(() => resolve([]), 5000)),
        ]);
    }
    /** Get the main page heading */
    async getHeading() {
        return Promise.race([
            this.page.evaluate(() => {
                const h = document.querySelector('h1, h2, [role="heading"]');
                return h?.textContent?.trim().slice(0, 100) || undefined;
            }),
            new Promise((resolve) => setTimeout(() => resolve(undefined), 5000)),
        ]);
    }
    // ─── Action execution ──────────────────────────────────────────────
    /** Execute an action decided by the AgentBrain */
    async execute(action) {
        try {
            switch (action.type) {
                case 'click':
                    return await this.executeClick(action);
                case 'type':
                    return await this.executeType(action);
                case 'navigate':
                    return await this.executeNavigate(action);
                case 'scroll':
                    return await this.executeScroll(action);
                case 'select':
                    return await this.executeSelect(action);
                case 'upload':
                    return await this.executeUpload(action);
                case 'wait':
                    return await this.executeWait(action);
                case 'key':
                    return await this.executeKey(action);
                case 'hover':
                    return await this.executeHover(action);
                case 'drag':
                    return await this.executeDrag(action);
                case 'screenshot':
                    await this.takeScreenshot(action.reasoning?.replace(/\s+/g, '-').slice(0, 40) || 'capture');
                    return { success: true };
                case 'done':
                    return { success: true };
                default:
                    return { success: false, error: `Unknown action type: ${action.type}` };
            }
        }
        catch (err) {
            return { success: false, error: err.message?.slice(0, 300) };
        }
    }
    resolveLocator(target) {
        if (!target)
            throw new Error('No target specified for action');
        const nthIndex = target.nth;
        const timeout = this.config.actionTimeout || 10_000;
        if (target.role && target.name) {
            const loc = this.page.getByRole(target.role, { name: target.name });
            return typeof nthIndex === 'number' ? loc.nth(nthIndex) : loc.first();
        }
        if (target.label) {
            const loc = this.page.getByLabel(target.label);
            return typeof nthIndex === 'number' ? loc.nth(nthIndex) : loc.first();
        }
        if (target.placeholder) {
            const loc = this.page.getByPlaceholder(target.placeholder);
            return typeof nthIndex === 'number' ? loc.nth(nthIndex) : loc.first();
        }
        if (target.testId) {
            return this.page.getByTestId(target.testId);
        }
        if (target.text) {
            const loc = this.page.getByText(target.text);
            return typeof nthIndex === 'number' ? loc.nth(nthIndex) : loc.first();
        }
        if (target.css) {
            return this.page.locator(target.css).first();
        }
        throw new Error('No valid selector in target');
    }
    /**
     * Execute click with multi-strategy fallback:
     * 1. Scroll into view
     * 2. Regular click
     * 3. Force click (bypasses actionability checks)
     * 4. Coordinate-based click fallback
     */
    async executeClick(action) {
        const timeout = this.config.actionTimeout || 10_000;
        // Direct coordinate click if coordinates are provided
        if (action.target?.coordinates) {
            await this.page.mouse.click(action.target.coordinates.x, action.target.coordinates.y);
            await this.page.waitForTimeout(500);
            return { success: true };
        }
        const locator = this.resolveLocator(action.target);
        // Step 1: Scroll into view
        try {
            await locator.scrollIntoViewIfNeeded({ timeout: 3000 });
        }
        catch { /* fixed/sticky elements — continue */ }
        // Step 2: Try regular click
        try {
            await locator.click({ timeout });
        }
        catch (clickErr) {
            // Step 3: Force click as fallback
            try {
                await locator.click({ force: true, timeout });
            }
            catch {
                // Step 4: Coordinate-based click fallback
                try {
                    const box = await locator.boundingBox();
                    if (box) {
                        await this.page.mouse.click(box.x + box.width / 2, box.y + box.height / 2);
                    }
                    else {
                        throw clickErr;
                    }
                }
                catch {
                    throw clickErr;
                }
            }
        }
        await this.page.waitForTimeout(500);
        return { success: true };
    }
    async executeType(action) {
        if (!action.value)
            return { success: false, error: 'No value to type' };
        const timeout = this.config.actionTimeout || 10_000;
        if (action.target?.label) {
            const field = this.page.getByLabel(action.target.label);
            await field.fill(action.value, { timeout });
        }
        else if (action.target?.placeholder) {
            const field = this.page.getByPlaceholder(action.target.placeholder);
            await field.fill(action.value, { timeout });
        }
        else {
            const locator = this.resolveLocator(action.target);
            await locator.fill(action.value, { timeout });
        }
        return { success: true };
    }
    /**
     * Navigate with retry on timeout/connection refused.
     */
    async executeNavigate(action) {
        if (!action.url)
            return { success: false, error: 'No URL to navigate to' };
        // Resolve relative URLs
        const url = action.url.startsWith('http')
            ? action.url
            : `${this.config.baseUrl}${action.url}`;
        const timeout = this.config.pageLoadTimeout || 30_000;
        let retries = 3;
        while (retries > 0) {
            try {
                await this.page.goto(url, { waitUntil: 'domcontentloaded', timeout });
                await this.page.waitForTimeout(1000);
                return { success: true };
            }
            catch (err) {
                retries--;
                const isRetryable = err.message?.includes('Timeout') || err.message?.includes('ERR_CONNECTION_REFUSED');
                if (retries === 0 || !isRetryable)
                    throw err;
                const waitTime = err.message?.includes('ERR_CONNECTION_REFUSED') ? 15000 : 3000;
                await this.page.waitForTimeout(waitTime);
            }
        }
        return { success: true };
    }
    async executeScroll(action) {
        const amount = action.amount || 300;
        let deltaX = 0;
        let deltaY = 0;
        switch (action.direction) {
            case 'up':
                deltaY = -amount;
                break;
            case 'down':
                deltaY = amount;
                break;
            case 'left':
                deltaX = -amount;
                break;
            case 'right':
                deltaX = amount;
                break;
            default:
                deltaY = amount;
        }
        await this.page.mouse.wheel(deltaX, deltaY);
        await this.page.waitForTimeout(300);
        return { success: true };
    }
    async executeSelect(action) {
        if (!action.value)
            return { success: false, error: 'No option value to select' };
        const timeout = this.config.actionTimeout || 10_000;
        // Click the select/combobox to open dropdown
        const locator = this.resolveLocator(action.target);
        await locator.click({ timeout });
        await this.page.waitForTimeout(300);
        // Wait for options and click the target option
        await this.page.getByRole('option').first().waitFor({ state: 'visible', timeout });
        await this.page.getByRole('option', { name: action.value }).first().click();
        await this.page.waitForTimeout(300);
        return { success: true };
    }
    async executeUpload(action) {
        if (!action.value)
            return { success: false, error: 'No file path to upload' };
        const locator = this.resolveLocator(action.target);
        const [fileChooser] = await Promise.all([
            this.page.waitForEvent('filechooser'),
            locator.click(),
        ]);
        await fileChooser.setFiles(action.value);
        await this.page.waitForTimeout(1000);
        return { success: true };
    }
    async executeWait(action) {
        const timeout = this.config.pageLoadTimeout || 30_000;
        if (action.waitFor) {
            await this.page.getByText(action.waitFor).first().waitFor({
                state: 'visible',
                timeout,
            });
        }
        else {
            await this.page.waitForTimeout(2000);
        }
        return { success: true };
    }
    /**
     * Execute a keyboard key press (Escape, Enter, Tab, etc.)
     */
    async executeKey(action) {
        const key = action.key || 'Escape';
        await this.page.keyboard.press(key);
        await this.page.waitForTimeout(300);
        return { success: true };
    }
    /**
     * Hover over an element (for tooltips, menus)
     */
    async executeHover(action) {
        const locator = this.resolveLocator(action.target);
        await locator.hover({ timeout: this.config.actionTimeout || 10_000 });
        await this.page.waitForTimeout(500);
        return { success: true };
    }
    /**
     * Drag and drop
     */
    async executeDrag(action) {
        const sourceLocator = this.resolveLocator(action.target);
        if (action.dragTo && 'x' in action.dragTo && 'y' in action.dragTo) {
            // Drag to coordinates
            const box = await sourceLocator.boundingBox();
            if (!box)
                return { success: false, error: 'Could not get source element position' };
            await this.page.mouse.move(box.x + box.width / 2, box.y + box.height / 2);
            await this.page.mouse.down();
            await this.page.mouse.move(action.dragTo.x, action.dragTo.y);
            await this.page.mouse.up();
        }
        else if (action.dragTo) {
            // Drag to element
            const targetLocator = this.resolveLocator(action.dragTo);
            await sourceLocator.dragTo(targetLocator);
        }
        else {
            return { success: false, error: 'No drag target specified' };
        }
        await this.page.waitForTimeout(500);
        return { success: true };
    }
    /** Run a verification check */
    async verify(assertion) {
        if (!assertion)
            return { passed: false, actual: 'No assertion provided' };
        try {
            switch (assertion.check) {
                case 'visible': {
                    const loc = assertion.target ? this.resolveLocator(assertion.target) : null;
                    if (!loc)
                        return { passed: false, actual: 'No target for visibility check' };
                    const isVisible = await loc.isVisible();
                    return { passed: isVisible, actual: String(isVisible) };
                }
                case 'hidden': {
                    const loc = assertion.target ? this.resolveLocator(assertion.target) : null;
                    if (!loc)
                        return { passed: false, actual: 'No target for hidden check' };
                    const isHidden = !(await loc.isVisible());
                    return { passed: isHidden, actual: String(isHidden) };
                }
                case 'text_contains': {
                    const pageText = await this.page.textContent('body') || '';
                    const contains = pageText.includes(assertion.expected || '');
                    return { passed: contains, actual: contains ? 'found' : 'not found' };
                }
                case 'text_equals': {
                    const loc = assertion.target ? this.resolveLocator(assertion.target) : null;
                    if (!loc)
                        return { passed: false, actual: 'No target for text check' };
                    const text = await loc.textContent() || '';
                    const equals = text.trim() === assertion.expected;
                    return { passed: equals, actual: text };
                }
                case 'url_contains': {
                    const url = this.page.url();
                    const contains = url.includes(assertion.expected || '');
                    return { passed: contains, actual: url };
                }
                case 'url_equals': {
                    const url = this.page.url();
                    const equals = url === assertion.expected;
                    return { passed: equals, actual: url };
                }
                case 'page_title': {
                    const title = await this.page.title();
                    const matches = title.includes(assertion.expected || '');
                    return { passed: matches, actual: title };
                }
                case 'toast_message': {
                    const toasts = await this.getToasts();
                    const found = toasts.some(t => t.toLowerCase().includes((assertion.expected || '').toLowerCase()));
                    return { passed: found, actual: toasts.join('; ') || 'no toasts' };
                }
                case 'count': {
                    const loc = assertion.target ? this.resolveLocator(assertion.target) : null;
                    if (!loc)
                        return { passed: false, actual: 'No target for count check' };
                    const count = await loc.count();
                    const expected = assertion.expected;
                    const tolerance = assertion.tolerance || 0;
                    const passed = Math.abs(count - expected) <= tolerance;
                    return { passed, actual: String(count) };
                }
                case 'api_response': {
                    const lastCall = this.apiCalls[this.apiCalls.length - 1];
                    if (!lastCall)
                        return { passed: false, actual: 'no API calls captured' };
                    return { passed: lastCall.status < 400, actual: `${lastCall.method} ${lastCall.url} → ${lastCall.status}` };
                }
                case 'attribute_equals': {
                    const loc = assertion.target ? this.resolveLocator(assertion.target) : null;
                    if (!loc)
                        return { passed: false, actual: 'No target for attribute check' };
                    const value = await loc.getAttribute(assertion.attribute || '');
                    const equals = value === assertion.expected;
                    return { passed: equals, actual: value || 'null' };
                }
                case 'css_property': {
                    const loc = assertion.target ? this.resolveLocator(assertion.target) : null;
                    if (!loc)
                        return { passed: false, actual: 'No target for CSS check' };
                    const element = await loc.elementHandle();
                    if (!element)
                        return { passed: false, actual: 'Element not found' };
                    const value = await element.evaluate((el, prop) => window.getComputedStyle(el).getPropertyValue(prop), assertion.property || '');
                    const matches = value === assertion.expected;
                    return { passed: matches, actual: value };
                }
                default:
                    return { passed: false, actual: `Unknown check type: ${assertion.check}` };
            }
        }
        catch (err) {
            return { passed: false, actual: err.message };
        }
    }
    /** Make a direct API call (bypassing the browser) */
    async apiCall(method, endpoint, body, headers) {
        const baseUrl = this.config.apiBaseUrl || this.config.baseUrl;
        const url = endpoint.startsWith('http') ? endpoint : `${baseUrl}${endpoint}`;
        const response = await this.page.request.fetch(url, {
            method,
            data: body,
            headers: {
                'Content-Type': 'application/json',
                ...this.config.apiHeaders,
                ...headers,
            },
            timeout: 30_000,
        });
        let data;
        try {
            data = await response.json();
        }
        catch {
            data = await response.text();
        }
        return { status: response.status(), data };
    }
    /** Save the network capture log */
    async saveNetworkLog(scenarioId) {
        const logPath = path.join(this.evidenceDir, 'network', `${scenarioId}-network.json`);
        fs.writeFileSync(logPath, JSON.stringify(this.apiCalls, null, 2));
        return logPath;
    }
    /** Get the page instance for direct access */
    getPage() {
        return this.page;
    }
}
exports.BrowserAgent = BrowserAgent;
//# sourceMappingURL=browser-agent.js.map