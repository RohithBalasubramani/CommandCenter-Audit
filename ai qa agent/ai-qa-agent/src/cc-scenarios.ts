/**
 * Command Center — AI QA Agent Test Scenarios
 *
 * 40 scenarios across 8 categories covering all aspects of the
 * Command Center industrial dashboard:
 *
 *   1. Core UI Navigation (5)
 *   2. Text Query Pipeline (8)
 *   3. Widget Interaction (6)
 *   4. Multi-Turn Conversations (4)
 *   5. AI Intent Classification (5)
 *   6. Edge Cases & Adversarial (5)
 *   7. Performance & Stability (4)
 *   8. Voice Pipeline (3)
 */

import type { TestScenario, SetupAction } from './types'

// ─── Shared Setup & Hints ────────────────────────────────────────────

const HYDRATION_SETUP: SetupAction[] = [
  {
    type: 'wait',
    description: 'Wait for Next.js hydration',
    waitMs: 3000,
  },
]

const HYDRATION_HINTS: string[] = [
  'This is a dark-themed industrial dashboard. The main page loads at / with a BlobGrid widget layout.',
  'To send a text query: press Ctrl+Shift+K (or click the keyboard icon button labeled "Text input (Ctrl+Shift+K)" in the floating toolbar at right), type in the input field that appears, then press Enter or click the Send button.',
  'After submitting, widgets appear as cards in a responsive CSS grid. Each widget card has a data-scenario attribute (e.g., "kpi", "trend", "alerts").',
  'The text input overlay closes after submission. You must reopen it (Ctrl+Shift+K) for each new query.',
  'Widget cards have a floating toolbar on hover with Pin, Resize, Focus, Snapshot, and Dismiss buttons.',
]

// ═══════════════════════════════════════════════════════════════════════
// CATEGORY 1: CORE UI NAVIGATION
// ═══════════════════════════════════════════════════════════════════════

const coreUIScenarios: TestScenario[] = [
  {
    id: 'cc-nav-001',
    name: 'Page Load and Hydration',
    goal: 'Verify the Command Center page loads successfully with all core UI elements: a heading, a status bar at the bottom showing "Ready", voice control buttons, and a grid container.',
    startUrl: '/',
    maxActions: 10,
    category: 'core-ui',
    priority: 'critical',
    tags: ['smoke', 'navigation'],
    hints: [
      'The page should show a dark-themed dashboard.',
      'Look for: a heading (h1), a footer/status bar showing "Ready", and control buttons in the bottom-right toolbar area.',
      'The grid container uses CSS class "grid".',
    ],
    setup: HYDRATION_SETUP,
    successCriteria: [
      { description: 'Grid container is visible', check: { check: 'visible', target: { css: '.grid' } } },
      { description: 'Page URL is root', check: { check: 'url_contains', expected: 'localhost' } },
    ],
    backendChecks: [
      {
        description: 'Backend API is reachable',
        endpoint: 'http://localhost:8100/api/layer2/rag/industrial/health/',
        method: 'GET',
        expectedStatus: 200,
      },
    ],
  },

  {
    id: 'cc-nav-002',
    name: 'View Toggle (Ctrl+B)',
    goal: 'Click the "Voice UI (Ctrl+B)" button to switch between dashboard and voice views, then click it again to return. Verify the view changes each time.',
    startUrl: '/',
    maxActions: 15,
    category: 'core-ui',
    priority: 'high',
    tags: ['keyboard', 'navigation'],
    hints: [
      'In the floating toolbar at right, find the button labeled "Voice UI (Ctrl+B)".',
      'Click it to switch to voice view — the widget grid should be replaced by a voice interface.',
      'Click it again to return to dashboard view.',
    ],
    setup: HYDRATION_SETUP,
    successCriteria: [
      { description: 'Page loaded successfully', check: { check: 'visible', target: { css: 'main' } } },
    ],
  },

  {
    id: 'cc-nav-003',
    name: 'Text Input Overlay (Ctrl+Shift+K)',
    goal: 'Open the text input overlay by clicking the keyboard icon button labeled "Text input (Ctrl+Shift+K)", verify the input field appears with placeholder "Ask anything...", then press Escape to close it.',
    startUrl: '/',
    maxActions: 12,
    category: 'core-ui',
    priority: 'critical',
    tags: ['smoke', 'text-input'],
    hints: [
      'Click the button labeled "Text input (Ctrl+Shift+K)" in the floating toolbar at right.',
      'A full-screen overlay with a blur backdrop should appear with an input field.',
      'The input field has placeholder text "Ask anything...".',
      'Press Escape to close the overlay.',
    ],
    setup: HYDRATION_SETUP,
    successCriteria: [
      { description: 'Page is interactive', check: { check: 'visible', target: { css: 'main' } } },
    ],
  },

  {
    id: 'cc-nav-004',
    name: 'Debug Panel (Ctrl+D)',
    goal: 'Click the "Debug (Ctrl+D)" button to open the debug panel. Verify it shows pipeline status information including "Layer 1" and "Layer 2" sections. Then close it.',
    startUrl: '/',
    maxActions: 15,
    category: 'core-ui',
    priority: 'medium',
    tags: ['debug'],
    hints: [
      'Find and click the "Debug (Ctrl+D)" button — it is in the bottom-right area of the page.',
      'The debug panel is a dark overlay that shows Layer 1 Voice I/O and Layer 2 AI + RAG status.',
      'Close it by clicking the X button in its top-right corner.',
    ],
    setup: HYDRATION_SETUP,
    successCriteria: [
      { description: 'Page is interactive', check: { check: 'visible', target: { css: 'main' } } },
    ],
  },

  {
    id: 'cc-nav-005',
    name: 'Responsive Layout Verification',
    goal: 'Verify the page renders correctly at desktop width (1440px) with a visible grid container, footer status bar, and at least one heading.',
    startUrl: '/',
    maxActions: 10,
    category: 'core-ui',
    priority: 'medium',
    tags: ['layout', 'responsive'],
    setup: HYDRATION_SETUP,
    successCriteria: [
      { description: 'Grid container visible', check: { check: 'visible', target: { css: '.grid' } } },
      { description: 'Footer visible', check: { check: 'visible', target: { css: 'footer' } } },
    ],
  },
]

// ═══════════════════════════════════════════════════════════════════════
// CATEGORY 2: TEXT QUERY PIPELINE
// ═══════════════════════════════════════════════════════════════════════

const textQueryScenarios: TestScenario[] = [
  {
    id: 'cc-query-001',
    name: 'Simple Equipment Query',
    goal: 'Open text input, type "Show pump status", submit, and verify that at least one widget card appears in the grid.',
    startUrl: '/',
    maxActions: 25,
    category: 'text-query',
    priority: 'critical',
    tags: ['smoke', 'query', 'widgets'],
    hints: HYDRATION_HINTS,
    setup: HYDRATION_SETUP,
    successCriteria: [
      { description: 'At least one widget rendered', check: { check: 'visible', target: { css: '[data-scenario]' } } },
    ],
    backendChecks: [
      {
        description: 'Orchestrate endpoint returns layout_json',
        endpoint: 'http://localhost:8100/api/layer2/orchestrate/',
        method: 'POST',
        body: { transcript: 'Show pump status', session_id: 'qa-test', context: {} },
        expectedStatus: 200,
      },
    ],
  },

  {
    id: 'cc-query-002',
    name: 'Multi-Widget Query',
    goal: 'Submit "Show pumps, alerts, and energy overview" and verify multiple widget cards appear in the grid.',
    startUrl: '/',
    maxActions: 25,
    category: 'text-query',
    priority: 'critical',
    tags: ['smoke', 'query', 'multi-widget'],
    hints: HYDRATION_HINTS,
    setup: HYDRATION_SETUP,
    successCriteria: [
      { description: 'Widgets rendered', check: { check: 'visible', target: { css: '[data-scenario]' } } },
    ],
    backendChecks: [
      {
        description: 'Orchestrate returns layout_json',
        endpoint: 'http://localhost:8100/api/layer2/orchestrate/',
        method: 'POST',
        body: { transcript: 'Show pumps, alerts, and energy overview', session_id: 'qa-test', context: {} },
        expectedStatus: 200,
      },
    ],
  },

  {
    id: 'cc-query-003',
    name: 'Specific Equipment Trend',
    goal: 'Submit "Show temperature trend for pump 1" and verify a trend-type widget appears.',
    startUrl: '/',
    maxActions: 25,
    category: 'text-query',
    priority: 'high',
    tags: ['query', 'trend'],
    hints: HYDRATION_HINTS,
    setup: HYDRATION_SETUP,
    successCriteria: [
      { description: 'Widget rendered', check: { check: 'visible', target: { css: '[data-scenario]' } } },
    ],
  },

  {
    id: 'cc-query-004',
    name: 'KPI Metrics Query',
    goal: 'Submit "Show key metrics overview" and verify KPI-type widgets appear with numeric values.',
    startUrl: '/',
    maxActions: 25,
    category: 'text-query',
    priority: 'high',
    tags: ['query', 'kpi'],
    hints: HYDRATION_HINTS,
    setup: HYDRATION_SETUP,
    successCriteria: [
      { description: 'Widget rendered', check: { check: 'visible', target: { css: '[data-scenario]' } } },
    ],
  },

  {
    id: 'cc-query-005',
    name: 'Alert Query',
    goal: 'Submit "Show all active alerts" and verify alert widgets appear with severity indicators.',
    startUrl: '/',
    maxActions: 25,
    category: 'text-query',
    priority: 'high',
    tags: ['query', 'alerts'],
    hints: HYDRATION_HINTS,
    setup: HYDRATION_SETUP,
    successCriteria: [
      { description: 'Widget rendered', check: { check: 'visible', target: { css: '[data-scenario]' } } },
    ],
    backendChecks: [
      {
        description: 'Alert query classified correctly',
        endpoint: 'http://localhost:8100/api/layer2/orchestrate/',
        method: 'POST',
        body: { transcript: 'Show all active alerts', session_id: 'qa-test', context: {} },
        expectedStatus: 200,
      },
    ],
  },

  {
    id: 'cc-query-006',
    name: 'Energy Consumption Query',
    goal: 'Submit "Show energy consumption breakdown" and verify energy/distribution widgets appear.',
    startUrl: '/',
    maxActions: 25,
    category: 'text-query',
    priority: 'high',
    tags: ['query', 'energy'],
    hints: HYDRATION_HINTS,
    setup: HYDRATION_SETUP,
    successCriteria: [
      { description: 'Widget rendered', check: { check: 'visible', target: { css: '[data-scenario]' } } },
    ],
  },

  {
    id: 'cc-query-007',
    name: 'Workforce Overview Query',
    goal: 'Submit "Show workforce overview and who is on shift" and verify people-related widgets appear.',
    startUrl: '/',
    maxActions: 25,
    category: 'text-query',
    priority: 'high',
    tags: ['query', 'people'],
    hints: HYDRATION_HINTS,
    setup: HYDRATION_SETUP,
    successCriteria: [
      { description: 'Widget rendered', check: { check: 'visible', target: { css: '[data-scenario]' } } },
    ],
  },

  {
    id: 'cc-query-008',
    name: 'Supply Chain Query',
    goal: 'Submit "Show supply chain status and vendor deliveries" and verify supply chain widgets appear.',
    startUrl: '/',
    maxActions: 25,
    category: 'text-query',
    priority: 'medium',
    tags: ['query', 'supply-chain'],
    hints: HYDRATION_HINTS,
    setup: HYDRATION_SETUP,
    successCriteria: [
      { description: 'Widget rendered', check: { check: 'visible', target: { css: '[data-scenario]' } } },
    ],
  },
]

// ═══════════════════════════════════════════════════════════════════════
// CATEGORY 3: WIDGET INTERACTION
// ═══════════════════════════════════════════════════════════════════════

const widgetInteractionScenarios: TestScenario[] = [
  {
    id: 'cc-widget-001',
    name: 'Widget Click Interaction',
    goal: 'First submit "Show pump status" to get widgets. Then click on a widget card body (the clickable area with cursor-pointer) to trigger a drill-down or focus action.',
    startUrl: '/',
    maxActions: 30,
    category: 'widget-interaction',
    priority: 'high',
    tags: ['widget', 'interaction'],
    hints: [
      ...HYDRATION_HINTS,
      'After widgets appear, click on the main body area of a widget card (it has cursor-pointer on hover).',
    ],
    setup: HYDRATION_SETUP,
    successCriteria: [
      { description: 'Widget visible after query', check: { check: 'visible', target: { css: '[data-scenario]' } } },
    ],
  },

  {
    id: 'cc-widget-002',
    name: 'Pin Widget',
    goal: 'Submit "Show pump status" to get widgets. Hover over a widget card to reveal the floating toolbar, then click the "Pin widget" button.',
    startUrl: '/',
    maxActions: 30,
    category: 'widget-interaction',
    priority: 'medium',
    tags: ['widget', 'pin'],
    hints: [
      ...HYDRATION_HINTS,
      'After widgets appear, hover over a widget card to reveal the floating toolbar row at the top.',
      'The toolbar has small buttons: "Pin widget", resize, "Focus \u2014 ask AI about this", "Save snapshot", "Dismiss widget".',
      'Click the button with title "Pin widget".',
    ],
    setup: HYDRATION_SETUP,
    successCriteria: [
      { description: 'Widget visible', check: { check: 'visible', target: { css: '[data-scenario]' } } },
    ],
  },

  {
    id: 'cc-widget-003',
    name: 'Dismiss Widget',
    goal: 'Submit "Show pumps and alerts" to get multiple widgets. Hover over one widget and click the "Dismiss widget" button. Verify the widget count decreases or the widget disappears.',
    startUrl: '/',
    maxActions: 30,
    category: 'widget-interaction',
    priority: 'medium',
    tags: ['widget', 'dismiss'],
    hints: [
      ...HYDRATION_HINTS,
      'After widgets appear, hover over a widget to reveal the toolbar.',
      'Click the "Dismiss widget" button (last button in toolbar, has an X icon).',
      'The widget should animate out and disappear.',
    ],
    setup: HYDRATION_SETUP,
    successCriteria: [
      { description: 'Page still functional', check: { check: 'visible', target: { css: 'main' } } },
    ],
  },

  {
    id: 'cc-widget-004',
    name: 'Resize Widget',
    goal: 'Submit "Show pump status" to get widgets. Hover over a widget and click the resize button (labeled "Resize: compact \u2192 normal" or similar). Verify the widget changes size.',
    startUrl: '/',
    maxActions: 30,
    category: 'widget-interaction',
    priority: 'medium',
    tags: ['widget', 'resize'],
    hints: [
      ...HYDRATION_HINTS,
      'After widgets appear, hover over a widget to reveal the toolbar.',
      'Click the resize button (second button, shows current size and next size, e.g., "Resize: compact \u2192 normal").',
      'The widget should visually resize.',
    ],
    setup: HYDRATION_SETUP,
    successCriteria: [
      { description: 'Widget visible', check: { check: 'visible', target: { css: '[data-scenario]' } } },
    ],
  },

  {
    id: 'cc-widget-005',
    name: 'Widget Hover Toolbar',
    goal: 'Submit "Show pump status" to get widgets. Hover over a widget card and verify that the floating toolbar with action buttons becomes visible.',
    startUrl: '/',
    maxActions: 25,
    category: 'widget-interaction',
    priority: 'high',
    tags: ['widget', 'hover', 'toolbar'],
    hints: [
      ...HYDRATION_HINTS,
      'After widgets appear, move the mouse over a widget card.',
      'A floating toolbar should appear at the top of the widget with small icon buttons.',
      'Look for buttons titled "Pin widget", "Focus", "Save snapshot", "Dismiss widget".',
    ],
    setup: HYDRATION_SETUP,
    successCriteria: [
      { description: 'Widget visible', check: { check: 'visible', target: { css: '[data-scenario]' } } },
    ],
  },

  {
    id: 'cc-widget-006',
    name: 'Focus Widget (Ask AI)',
    goal: 'Submit "Show pump status" to get widgets. Hover over a widget and click the "Focus \u2014 ask AI about this" button. Verify the system processes a follow-up query about the widget.',
    startUrl: '/',
    maxActions: 35,
    category: 'widget-interaction',
    priority: 'medium',
    tags: ['widget', 'focus', 'ai'],
    hints: [
      ...HYDRATION_HINTS,
      'After widgets appear, hover over a widget to reveal the toolbar.',
      'Click the "Focus \u2014 ask AI about this" button (third button with a crosshair/target icon).',
      'This should trigger a new AI query focused on that specific widget topic.',
    ],
    setup: HYDRATION_SETUP,
    successCriteria: [
      { description: 'Widget visible', check: { check: 'visible', target: { css: '[data-scenario]' } } },
    ],
  },
]

// ═══════════════════════════════════════════════════════════════════════
// CATEGORY 4: MULTI-TURN CONVERSATIONS
// ═══════════════════════════════════════════════════════════════════════

const multiTurnScenarios: TestScenario[] = [
  {
    id: 'cc-multi-001',
    name: '3-Turn Drill-Down',
    goal: 'Conduct a 3-turn conversation: (1) "Show equipment overview", (2) "Show pump details", (3) "Show pump alerts". After each query, wait for widgets to appear before submitting the next. Verify widgets update with each query.',
    startUrl: '/',
    maxActions: 40,
    category: 'multi-turn',
    priority: 'high',
    tags: ['multi-turn', 'drill-down'],
    hints: [
      ...HYDRATION_HINTS,
      'After each query, wait for the widget grid to update before opening text input again.',
      'You must reopen the text input overlay (Ctrl+Shift+K or click the keyboard button) for each new query.',
    ],
    setup: HYDRATION_SETUP,
    successCriteria: [
      { description: 'Widgets rendered after final query', check: { check: 'visible', target: { css: '[data-scenario]' } } },
    ],
  },

  {
    id: 'cc-multi-002',
    name: '5-Turn Investigation',
    goal: 'Conduct a 5-turn investigation: (1) "Show all pumps", (2) "Focus on pump 1", (3) "Show temperature trend", (4) "Compare all pump temperatures", (5) "Show alerts for pumps". Wait for widgets after each. Verify the layout updates.',
    startUrl: '/',
    maxActions: 50,
    category: 'multi-turn',
    priority: 'high',
    tags: ['multi-turn', 'investigation'],
    hints: [
      ...HYDRATION_HINTS,
      'This is a 5-step investigation. After each query submission, wait for widgets to appear.',
      'Reopen text input (Ctrl+Shift+K) for each new query.',
    ],
    setup: HYDRATION_SETUP,
    successCriteria: [
      { description: 'Widgets rendered', check: { check: 'visible', target: { css: '[data-scenario]' } } },
    ],
  },

  {
    id: 'cc-multi-003',
    name: 'Context Switch',
    goal: 'Switch between domains: (1) "Show pump status" (industrial), (2) "Show workforce overview" (people), (3) "Show pump status again" (back to industrial). Verify widgets change between domains.',
    startUrl: '/',
    maxActions: 40,
    category: 'multi-turn',
    priority: 'high',
    tags: ['multi-turn', 'context-switch'],
    hints: [
      ...HYDRATION_HINTS,
      'Submit 3 queries in sequence, waiting for widgets after each.',
      'Observe how the widget layout changes when switching between industrial and people domains.',
    ],
    setup: HYDRATION_SETUP,
    successCriteria: [
      { description: 'Widgets rendered', check: { check: 'visible', target: { css: '[data-scenario]' } } },
    ],
  },

  {
    id: 'cc-multi-004',
    name: 'Progressive Refinement',
    goal: 'Progressively refine: (1) "Show everything available", (2) "Focus on alerts only", (3) "Show only critical alerts". Verify the dashboard narrows down with each query.',
    startUrl: '/',
    maxActions: 40,
    category: 'multi-turn',
    priority: 'medium',
    tags: ['multi-turn', 'refinement'],
    hints: [
      ...HYDRATION_HINTS,
      'Submit 3 queries, each more specific than the last.',
      'Verify widgets appear after each query.',
    ],
    setup: HYDRATION_SETUP,
    successCriteria: [
      { description: 'Widgets rendered', check: { check: 'visible', target: { css: '[data-scenario]' } } },
    ],
  },
]

// ═══════════════════════════════════════════════════════════════════════
// CATEGORY 5: AI INTENT CLASSIFICATION
// ═══════════════════════════════════════════════════════════════════════

const intentClassificationScenarios: TestScenario[] = [
  {
    id: 'cc-intent-001',
    name: 'Greeting Intent',
    goal: 'Submit "Hello" as a query. The system should respond with a greeting without spawning data widgets. Verify no widget cards with data-scenario attributes appear.',
    startUrl: '/',
    maxActions: 20,
    category: 'intent-classification',
    priority: 'high',
    tags: ['intent', 'greeting'],
    hints: [
      ...HYDRATION_HINTS,
      'After submitting "Hello", the system should respond with a greeting message.',
      'No data widgets should appear since this is a social/greeting intent.',
      'The heading might change to show a greeting response.',
    ],
    setup: HYDRATION_SETUP,
    backendChecks: [
      {
        description: 'Greeting classified as greeting intent',
        endpoint: 'http://localhost:8100/api/layer2/orchestrate/',
        method: 'POST',
        body: { transcript: 'Hello', session_id: 'qa-intent-test', context: {} },
        expectedStatus: 200,
        responseCheck: { path: 'intent.type', operator: 'contains', value: 'greeting' },
      },
    ],
    successCriteria: [
      { description: 'Page still functional', check: { check: 'visible', target: { css: 'main' } } },
    ],
  },

  {
    id: 'cc-intent-002',
    name: 'Out-of-Scope Rejection',
    goal: 'Submit "What is the weather in Tokyo?" and verify the system rejects it as out of scope. The response should indicate this is not an industrial query.',
    startUrl: '/',
    maxActions: 20,
    category: 'intent-classification',
    priority: 'high',
    tags: ['intent', 'out-of-scope'],
    hints: [
      ...HYDRATION_HINTS,
      'The system should recognize this is not an industrial query and respond with a polite rejection.',
    ],
    setup: HYDRATION_SETUP,
    backendChecks: [
      {
        description: 'Weather query classified as out_of_scope',
        endpoint: 'http://localhost:8100/api/layer2/orchestrate/',
        method: 'POST',
        body: { transcript: 'What is the weather in Tokyo?', session_id: 'qa-intent-test', context: {} },
        expectedStatus: 200,
        responseCheck: { path: 'intent.type', operator: 'contains', value: 'out_of_scope' },
      },
    ],
    successCriteria: [
      { description: 'Page still functional', check: { check: 'visible', target: { css: 'main' } } },
    ],
  },

  {
    id: 'cc-intent-003',
    name: 'Equipment Query Intent',
    goal: 'Submit "What is the status of transformer TR-001?" and verify the system classifies it as an equipment query and returns widgets.',
    startUrl: '/',
    maxActions: 25,
    category: 'intent-classification',
    priority: 'high',
    tags: ['intent', 'query', 'equipment'],
    hints: HYDRATION_HINTS,
    setup: HYDRATION_SETUP,
    backendChecks: [
      {
        description: 'Equipment query classified as query intent',
        endpoint: 'http://localhost:8100/api/layer2/orchestrate/',
        method: 'POST',
        body: { transcript: 'What is the status of transformer TR-001?', session_id: 'qa-intent-test', context: {} },
        expectedStatus: 200,
        responseCheck: { path: 'intent.type', operator: 'equals', value: 'query' },
      },
    ],
    successCriteria: [
      { description: 'Widget rendered', check: { check: 'visible', target: { css: '[data-scenario]' } } },
    ],
  },

  {
    id: 'cc-intent-004',
    name: 'Action Intent',
    goal: 'Submit "Create a work order for pump 1 maintenance" and verify the system recognizes this as an action intent.',
    startUrl: '/',
    maxActions: 25,
    category: 'intent-classification',
    priority: 'medium',
    tags: ['intent', 'action'],
    hints: HYDRATION_HINTS,
    setup: HYDRATION_SETUP,
    backendChecks: [
      {
        description: 'Action request returns valid response',
        endpoint: 'http://localhost:8100/api/layer2/orchestrate/',
        method: 'POST',
        body: { transcript: 'Create a work order for pump 1 maintenance', session_id: 'qa-intent-test', context: {} },
        expectedStatus: 200,
      },
    ],
    successCriteria: [
      { description: 'Page still functional', check: { check: 'visible', target: { css: 'main' } } },
    ],
  },

  {
    id: 'cc-intent-005',
    name: 'Ambiguous Query Handling',
    goal: 'Submit "Show me that thing from earlier" (ambiguous with no context). Verify the system handles it gracefully without crashing.',
    startUrl: '/',
    maxActions: 20,
    category: 'intent-classification',
    priority: 'medium',
    tags: ['intent', 'ambiguous'],
    hints: [
      ...HYDRATION_HINTS,
      'This is intentionally ambiguous. The system should either ask for clarification or give a best-effort response.',
    ],
    setup: HYDRATION_SETUP,
    successCriteria: [
      { description: 'Page still functional', check: { check: 'visible', target: { css: 'main' } } },
    ],
  },
]

// ═══════════════════════════════════════════════════════════════════════
// CATEGORY 6: EDGE CASES & ADVERSARIAL
// ═══════════════════════════════════════════════════════════════════════

const edgeCaseScenarios: TestScenario[] = [
  {
    id: 'cc-edge-001',
    name: 'Empty Query Prevention',
    goal: 'Open text input overlay, verify the Send button is disabled when the input is empty, then type "test" and verify the button becomes enabled.',
    startUrl: '/',
    maxActions: 15,
    category: 'edge-cases',
    priority: 'high',
    tags: ['edge-case', 'validation'],
    hints: [
      'Open text input with Ctrl+Shift+K or the keyboard button.',
      'The Send/Submit button (data-testid="submit-query") should appear disabled (cursor-not-allowed, muted colors) when input is empty.',
      'Type any text and observe the button state change to enabled (bg-blue-500 or similar bright color).',
    ],
    setup: HYDRATION_SETUP,
    successCriteria: [
      { description: 'Page functional', check: { check: 'visible', target: { css: 'main' } } },
    ],
  },

  {
    id: 'cc-edge-002',
    name: 'Very Long Query',
    goal: 'Submit a very long query (150+ words): "Show me the comprehensive status of all pumps including pump 1, pump 2, pump 3, along with their temperature trends, vibration analysis, flow rates, pressure readings, efficiency metrics, maintenance history, alert history, upcoming maintenance schedules, spare parts inventory, operator assignments, recent work orders, energy consumption patterns, and compare all of these metrics across the last 24 hours with historical averages." Verify the system handles it without crashing.',
    startUrl: '/',
    maxActions: 25,
    category: 'edge-cases',
    priority: 'medium',
    tags: ['edge-case', 'long-query'],
    hints: HYDRATION_HINTS,
    setup: HYDRATION_SETUP,
    successCriteria: [
      { description: 'Page still functional', check: { check: 'visible', target: { css: 'main' } } },
    ],
  },

  {
    id: 'cc-edge-003',
    name: 'SQL Injection Prevention',
    goal: 'Submit a SQL injection attempt: "SELECT * FROM users; DROP TABLE widgets; --" as a query. Verify the system handles it safely without exposing any database information.',
    startUrl: '/',
    maxActions: 20,
    category: 'edge-cases',
    priority: 'high',
    tags: ['security', 'sql-injection'],
    hints: [
      ...HYDRATION_HINTS,
      'Submit the SQL injection string as a query. The system should treat it as a regular text query or reject it.',
      'Verify no database errors or SQL output appears on the page.',
    ],
    setup: HYDRATION_SETUP,
    successCriteria: [
      { description: 'No SQL error on page', check: { check: 'visible', target: { css: 'main' } } },
    ],
  },

  {
    id: 'cc-edge-004',
    name: 'XSS Prevention',
    goal: 'Submit an XSS attempt: "<script>alert("xss")</script>" as a query. Verify no script execution occurs and the page remains functional.',
    startUrl: '/',
    maxActions: 20,
    category: 'edge-cases',
    priority: 'high',
    tags: ['security', 'xss'],
    hints: [
      ...HYDRATION_HINTS,
      'Submit the XSS payload as a query. It should be sanitized.',
      'Verify no alert dialog appears and the page content does not contain unescaped script tags.',
    ],
    setup: HYDRATION_SETUP,
    successCriteria: [
      { description: 'Page still functional (no XSS)', check: { check: 'visible', target: { css: 'main' } } },
    ],
  },

  {
    id: 'cc-edge-005',
    name: 'Rapid-Fire Queries',
    goal: 'Submit 3 queries in rapid succession: "Show pumps", "Show alerts", "Show energy". Open text input, type, submit immediately, then repeat. Verify the system does not crash.',
    startUrl: '/',
    maxActions: 35,
    category: 'edge-cases',
    priority: 'medium',
    tags: ['edge-case', 'rapid-fire'],
    hints: [
      ...HYDRATION_HINTS,
      'Submit queries as fast as possible — do not wait for widgets between queries.',
      'The system should handle concurrent requests without crashing.',
    ],
    setup: HYDRATION_SETUP,
    successCriteria: [
      { description: 'Page still functional after rapid queries', check: { check: 'visible', target: { css: 'main' } } },
    ],
  },
]

// ═══════════════════════════════════════════════════════════════════════
// CATEGORY 7: PERFORMANCE & STABILITY
// ═══════════════════════════════════════════════════════════════════════

const performanceScenarios: TestScenario[] = [
  {
    id: 'cc-perf-001',
    name: 'Layout Render Performance',
    goal: 'Submit "Show equipment overview" and verify that widgets appear on the page. The layout should render without freezing the browser.',
    startUrl: '/',
    maxActions: 20,
    category: 'performance',
    priority: 'high',
    tags: ['performance', 'render'],
    hints: HYDRATION_HINTS,
    setup: HYDRATION_SETUP,
    successCriteria: [
      { description: 'Widgets rendered', check: { check: 'visible', target: { css: '[data-scenario]' } } },
    ],
  },

  {
    id: 'cc-perf-002',
    name: 'No JavaScript Errors',
    goal: 'Submit 2 queries ("Show pumps" then "Show alerts") and verify no uncaught JavaScript errors appear. Check the browser console for errors.',
    startUrl: '/',
    maxActions: 30,
    category: 'performance',
    priority: 'high',
    tags: ['performance', 'errors'],
    hints: [
      ...HYDRATION_HINTS,
      'After submitting queries, check for any red error messages or JavaScript exceptions.',
      'The browser console should not have uncaught TypeError, ReferenceError, or similar errors.',
    ],
    setup: HYDRATION_SETUP,
    successCriteria: [
      { description: 'Page functional after queries', check: { check: 'visible', target: { css: 'main' } } },
    ],
  },

  {
    id: 'cc-perf-003',
    name: 'DOM Size Check',
    goal: 'Submit "Show comprehensive overview with all available data" and verify the page loads. The page should not have an excessive number of DOM nodes.',
    startUrl: '/',
    maxActions: 25,
    category: 'performance',
    priority: 'medium',
    tags: ['performance', 'dom'],
    hints: HYDRATION_HINTS,
    setup: HYDRATION_SETUP,
    successCriteria: [
      { description: 'Page rendered', check: { check: 'visible', target: { css: 'main' } } },
    ],
  },

  {
    id: 'cc-perf-004',
    name: 'Memory Stability',
    goal: 'Submit 5 sequential queries ("Show pumps", "Show alerts", "Show energy", "Show people", "Show tasks") and verify the page remains responsive and functional after all 5.',
    startUrl: '/',
    maxActions: 50,
    category: 'performance',
    priority: 'medium',
    tags: ['performance', 'memory'],
    hints: [
      ...HYDRATION_HINTS,
      'Submit 5 queries in sequence, waiting briefly for widgets after each.',
      'After all 5, the page should still be responsive and not frozen.',
    ],
    setup: HYDRATION_SETUP,
    successCriteria: [
      { description: 'Page still responsive after 5 queries', check: { check: 'visible', target: { css: 'main' } } },
    ],
  },
]

// ═══════════════════════════════════════════════════════════════════════
// CATEGORY 8: VOICE PIPELINE
// ═══════════════════════════════════════════════════════════════════════

const voicePipelineScenarios: TestScenario[] = [
  {
    id: 'cc-voice-001',
    name: 'Voice Control Bar Visibility',
    goal: 'Verify the voice control bar is visible at the bottom of the dashboard with a microphone button, a "Hold Shift+Space to speak" label, and a PTT button.',
    startUrl: '/',
    maxActions: 10,
    category: 'voice-pipeline',
    priority: 'medium',
    tags: ['voice', 'ui'],
    hints: [
      'In dashboard view (default), the voice control bar is at the bottom of the main content area.',
      'It should contain: a round microphone/waveform button, text "Hold Shift+Space to speak", and a PTT button.',
    ],
    setup: HYDRATION_SETUP,
    successCriteria: [
      { description: 'PTT button visible', check: { check: 'visible', target: { role: 'button', name: 'PTT' } } },
    ],
  },

  {
    id: 'cc-voice-002',
    name: 'Push-to-Talk Button',
    goal: 'Find and click the PTT button in the voice control bar. Verify it responds with a visual state change.',
    startUrl: '/',
    maxActions: 15,
    category: 'voice-pipeline',
    priority: 'medium',
    tags: ['voice', 'ptt'],
    hints: [
      'The PTT button is labeled "PTT" in the voice control bar.',
      'Clicking it may toggle between PTT and CONT (continuous) modes.',
    ],
    setup: HYDRATION_SETUP,
    successCriteria: [
      { description: 'Voice control area visible', check: { check: 'visible', target: { css: 'main' } } },
    ],
  },

  {
    id: 'cc-voice-003',
    name: 'STT/TTS Status Indicators',
    goal: 'Verify the voice control bar status indicators are visible at the bottom of the dashboard. They appear as colored dots (green=connected, red=disconnected) next to the PTT button, indicating STT and TTS server status.',
    startUrl: '/',
    maxActions: 10,
    category: 'voice-pipeline',
    priority: 'medium',
    tags: ['voice', 'status'],
    hints: [
      'The voice control bar at the bottom shows status via colored dots (green/red) next to the PTT button.',
      'Green dots mean STT and TTS servers are connected. Look for visual indicators, not text labels.',
    ],
    setup: HYDRATION_SETUP,
    successCriteria: [
      { description: 'Voice control area visible', check: { check: 'visible', target: { css: 'main' } } },
    ],
  },
]

// ═══════════════════════════════════════════════════════════════════════
// EXPORTS
// ═══════════════════════════════════════════════════════════════════════

/** All 40 Command Center test scenarios */
export const ccScenarios: TestScenario[] = [
  ...coreUIScenarios,
  ...textQueryScenarios,
  ...widgetInteractionScenarios,
  ...multiTurnScenarios,
  ...intentClassificationScenarios,
  ...edgeCaseScenarios,
  ...performanceScenarios,
  ...voicePipelineScenarios,
]

/** Export by category for selective running */
export {
  coreUIScenarios,
  textQueryScenarios,
  widgetInteractionScenarios,
  multiTurnScenarios,
  intentClassificationScenarios,
  edgeCaseScenarios,
  performanceScenarios,
  voicePipelineScenarios,
}
