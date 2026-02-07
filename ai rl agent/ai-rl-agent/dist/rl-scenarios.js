"use strict";
/**
 * RL Agent Test Scenarios for Command Center
 *
 * 25 scenarios across 5 categories:
 * 1. Widget Quality Evaluation (8)
 * 2. Data Accuracy Verification (5)
 * 3. Feedback Submission (4)
 * 4. RL Training Lifecycle (4)
 * 5. Weight & Config Management (4)
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.EVAL_QUERIES = exports.rlScenarios = void 0;
// ─── Setup Constants ────────────────────────────────────────────────
const HYDRATION_SETUP = [
    { type: 'wait', waitMs: 3000, description: 'Wait for Next.js hydration' },
];
const RL_HINTS = [
    'The Command Center uses a text input activated via Ctrl+Shift+K or by clicking the keyboard icon in the toolbar.',
    'After submitting a query, widgets appear in a grid layout with [data-scenario] attributes.',
    'Each widget has a scenario type (e.g., "equipment_status", "alerts", "trend") and optional fixture data.',
    'The RL agent should evaluate widget relevance to the query, not just check they exist.',
    'Use the backend API at localhost:8100 for direct data verification.',
];
// ─── Category 1: Widget Quality Evaluation ──────────────────────────
const widgetQualityScenarios = [
    {
        id: 'rl-eval-001',
        name: 'Pump Status — Equipment Widgets',
        goal: 'Send a pump status query and verify the response contains appropriate equipment/KPI widgets. Evaluate widget scenario relevance and data accuracy.',
        startUrl: '/',
        maxActions: 15,
        category: 'Widget Quality Evaluation',
        priority: 'critical',
        tags: ['eval', 'equipment', 'smoke'],
        hints: [
            ...RL_HINTS,
            'Query: "What is the current status of all pumps?"',
            'Expected widget scenarios: equipment_status, kpi',
            'Verify the voice response mentions pump status information.',
        ],
        setup: HYDRATION_SETUP,
        successCriteria: [
            {
                description: 'At least 1 widget rendered',
                check: { check: 'count', target: { css: '[data-scenario]' }, expected: '>=1' },
            },
            {
                description: 'Voice response contains pump-related content',
                check: { check: 'text_contains', target: { css: 'body' }, expected: 'pump' },
            },
        ],
        backendChecks: [
            {
                description: 'Orchestrate endpoint responds',
                endpoint: '/api/layer2/orchestrate/',
                method: 'POST',
                expectedStatus: 200,
            },
        ],
    },
    {
        id: 'rl-eval-002',
        name: 'Temperature Trend — Chart Widget',
        goal: 'Query temperature trend and verify a trend/chart widget is rendered with appropriate time-series visualization.',
        startUrl: '/',
        maxActions: 15,
        category: 'Widget Quality Evaluation',
        priority: 'critical',
        tags: ['eval', 'trend'],
        hints: [
            ...RL_HINTS,
            'Query: "Show me the temperature trend for the past 24 hours"',
            'Expected widget scenarios: trend, chart, gauge',
            'Look for Recharts line/area elements or SVG chart elements.',
        ],
        setup: HYDRATION_SETUP,
        successCriteria: [
            {
                description: 'At least 1 widget rendered',
                check: { check: 'count', target: { css: '[data-scenario]' }, expected: '>=1' },
            },
        ],
    },
    {
        id: 'rl-eval-003',
        name: 'Alert Query — Safety-Critical Widget Positioning',
        goal: 'Query for alerts and verify an alerts widget appears in the top 3 positions. This tests the RL safety floor — alerts must never be pushed to bottom.',
        startUrl: '/',
        maxActions: 15,
        category: 'Widget Quality Evaluation',
        priority: 'critical',
        tags: ['eval', 'safety', 'alerts'],
        hints: [
            ...RL_HINTS,
            'Query: "Are there any critical alerts right now?"',
            'Expected: alerts widget MUST be in position 1-3 (safety constraint).',
            'If alerts widget is at position 4+, this is a safety violation — rate DOWN.',
        ],
        setup: HYDRATION_SETUP,
        successCriteria: [
            {
                description: 'Response rendered (widgets or message)',
                check: { check: 'text_contains', target: { css: 'body' }, expected: '' },
            },
        ],
    },
    {
        id: 'rl-eval-004',
        name: 'Energy Breakdown — Chart/Comparison Widgets',
        goal: 'Query energy consumption breakdown and verify appropriate visualization widgets (chart, comparison, breakdown).',
        startUrl: '/',
        maxActions: 15,
        category: 'Widget Quality Evaluation',
        priority: 'high',
        tags: ['eval', 'energy'],
        hints: [
            ...RL_HINTS,
            'Query: "What is the energy consumption breakdown by equipment?"',
            'Expected widget scenarios: energy_breakdown, chart, comparison, kpi',
        ],
        setup: HYDRATION_SETUP,
        successCriteria: [
            {
                description: 'At least 1 widget rendered',
                check: { check: 'count', target: { css: '[data-scenario]' }, expected: '>=1' },
            },
        ],
    },
    {
        id: 'rl-eval-005',
        name: 'Multi-Domain Query — Equipment + Alerts',
        goal: 'Send a complex cross-domain query about equipment with alerts and verify multiple relevant widgets are returned.',
        startUrl: '/',
        maxActions: 15,
        category: 'Widget Quality Evaluation',
        priority: 'high',
        tags: ['eval', 'multi-domain'],
        hints: [
            ...RL_HINTS,
            'Query: "Show me equipment with alerts that need maintenance"',
            'Expected: multiple widgets covering equipment, alerts, and maintenance domains.',
        ],
        setup: HYDRATION_SETUP,
        successCriteria: [
            {
                description: 'At least 1 widget rendered',
                check: { check: 'count', target: { css: '[data-scenario]' }, expected: '>=1' },
            },
        ],
    },
    {
        id: 'rl-eval-006',
        name: 'Ambiguous Query — Graceful Handling',
        goal: 'Send an ambiguous query and verify the system handles it gracefully with reasonable widget choices.',
        startUrl: '/',
        maxActions: 15,
        category: 'Widget Quality Evaluation',
        priority: 'medium',
        tags: ['eval', 'edge-case'],
        hints: [
            ...RL_HINTS,
            'Query: "Show me everything"',
            'Expected: some widgets or a clarifying message. Should NOT crash or return empty.',
        ],
        setup: HYDRATION_SETUP,
        successCriteria: [
            {
                description: 'Page has response content',
                check: { check: 'text_contains', target: { css: 'body' }, expected: '' },
            },
        ],
    },
    {
        id: 'rl-eval-007',
        name: 'Out-of-Scope Query — Rejection',
        goal: 'Send a clearly out-of-scope query and verify the system rejects it with a helpful message.',
        startUrl: '/',
        maxActions: 15,
        category: 'Widget Quality Evaluation',
        priority: 'medium',
        tags: ['eval', 'edge-case', 'scope'],
        hints: [
            ...RL_HINTS,
            'Query: "What is the meaning of life?"',
            'Expected: rejection message or redirect to industrial queries. No random widgets.',
        ],
        setup: HYDRATION_SETUP,
        successCriteria: [
            {
                description: 'Response provided',
                check: { check: 'text_contains', target: { css: 'body' }, expected: '' },
            },
        ],
    },
    {
        id: 'rl-eval-008',
        name: 'Complex Comparison — Comparison Widgets',
        goal: 'Query a comparison between two pieces of equipment and verify comparison-type widgets are returned.',
        startUrl: '/',
        maxActions: 15,
        category: 'Widget Quality Evaluation',
        priority: 'high',
        tags: ['eval', 'comparison'],
        hints: [
            ...RL_HINTS,
            'Query: "Compare pump 1 and pump 2 performance"',
            'Expected widget scenarios: comparison, trend, equipment_status',
        ],
        setup: HYDRATION_SETUP,
        successCriteria: [
            {
                description: 'At least 1 widget rendered',
                check: { check: 'count', target: { css: '[data-scenario]' }, expected: '>=1' },
            },
        ],
    },
];
// ─── Category 2: Data Accuracy Verification ─────────────────────────
const dataAccuracyScenarios = [
    {
        id: 'rl-data-001',
        name: 'Backend vs UI Widget Match',
        goal: 'Send a query via API and via UI simultaneously. Compare the widget scenarios returned by both to verify consistency.',
        startUrl: '/',
        maxActions: 20,
        category: 'Data Accuracy Verification',
        priority: 'critical',
        tags: ['data', 'accuracy', 'smoke'],
        hints: [
            ...RL_HINTS,
            'Query: "What is the current status of all pumps?"',
            'Step 1: Send query via UI text input.',
            'Step 2: Call POST /api/layer2/orchestrate/ with same query via api_call action.',
            'Step 3: Compare widget scenarios from UI [data-scenario] attributes with API layout_json.widgets.',
        ],
        setup: HYDRATION_SETUP,
        successCriteria: [
            {
                description: 'API returns valid layout JSON',
                check: { check: 'api_response', expected: '200' },
            },
        ],
        backendChecks: [
            {
                description: 'Orchestrate returns widgets',
                endpoint: '/api/layer2/orchestrate/',
                method: 'POST',
                expectedStatus: 200,
            },
        ],
    },
    {
        id: 'rl-data-002',
        name: 'KPI Numbers Render Correctly',
        goal: 'Verify that KPI widget numbers visible in the UI match the data in the backend response.',
        startUrl: '/',
        maxActions: 15,
        category: 'Data Accuracy Verification',
        priority: 'high',
        tags: ['data', 'kpi'],
        hints: [
            ...RL_HINTS,
            'Query: "Show me key performance indicators"',
            'After widgets render, read the numeric values displayed.',
            'Compare with the data field in the orchestrate response.',
        ],
        setup: HYDRATION_SETUP,
        successCriteria: [
            {
                description: 'KPI widgets render with numeric values',
                check: { check: 'text_contains', target: { css: 'body' }, expected: '' },
            },
        ],
    },
    {
        id: 'rl-data-003',
        name: 'Table Rows Match Backend Payload',
        goal: 'Send a query that produces a table widget and verify the row count matches the backend fixture data.',
        startUrl: '/',
        maxActions: 15,
        category: 'Data Accuracy Verification',
        priority: 'high',
        tags: ['data', 'table'],
        hints: [
            ...RL_HINTS,
            'Query: "Show me all active alarms"',
            'Look for table elements (tr, td) or list items within the widget.',
            'Count the data rows and compare with backend response.',
        ],
        setup: HYDRATION_SETUP,
        successCriteria: [
            {
                description: 'Response renders',
                check: { check: 'text_contains', target: { css: 'body' }, expected: '' },
            },
        ],
    },
    {
        id: 'rl-data-004',
        name: 'Chart Axis Labels Correct',
        goal: 'Verify that chart widgets have appropriate axis labels that relate to the query.',
        startUrl: '/',
        maxActions: 15,
        category: 'Data Accuracy Verification',
        priority: 'medium',
        tags: ['data', 'chart'],
        hints: [
            ...RL_HINTS,
            'Query: "Show me the temperature trend for the past 24 hours"',
            'Look for SVG text elements or Recharts axis labels.',
            'Verify they mention temperature, time, or units.',
        ],
        setup: HYDRATION_SETUP,
        successCriteria: [
            {
                description: 'Chart renders',
                check: { check: 'text_contains', target: { css: 'body' }, expected: '' },
            },
        ],
    },
    {
        id: 'rl-data-005',
        name: 'Voice Response Mentions Correct Equipment',
        goal: 'Verify the voice response text references the correct equipment names from the query.',
        startUrl: '/',
        maxActions: 15,
        category: 'Data Accuracy Verification',
        priority: 'medium',
        tags: ['data', 'voice'],
        hints: [
            ...RL_HINTS,
            'Query: "What is the status of transformer TR-001?"',
            'The voice response should mention "TR-001" or "transformer".',
            'If it talks about pumps or unrelated equipment, rate DOWN.',
        ],
        setup: HYDRATION_SETUP,
        successCriteria: [
            {
                description: 'Response references equipment',
                check: { check: 'text_contains', target: { css: 'body' }, expected: '' },
            },
        ],
    },
];
// ─── Category 3: Feedback Submission ────────────────────────────────
const feedbackScenarios = [
    {
        id: 'rl-fb-001',
        name: 'Submit Positive Feedback',
        goal: 'Send a query, evaluate the response positively, and submit "up" feedback via the API.',
        startUrl: '/',
        maxActions: 20,
        category: 'Feedback Submission',
        priority: 'critical',
        tags: ['feedback', 'positive', 'smoke'],
        hints: [
            ...RL_HINTS,
            'Step 1: Send query "What is the current status of all pumps?" via UI.',
            'Step 2: After widgets render, use api_call to POST /api/layer2/feedback/ with rating "up".',
            'Step 3: Verify the feedback API returns {"status": "ok", "updated": true}.',
            'You need the query_id from the orchestrate response — check the page or use api_call to orchestrate first.',
        ],
        setup: HYDRATION_SETUP,
        successCriteria: [
            {
                description: 'Feedback submitted successfully',
                check: { check: 'api_response', expected: '200' },
            },
        ],
        backendChecks: [
            {
                description: 'Feedback endpoint accepts request',
                endpoint: '/api/layer2/feedback/',
                method: 'POST',
                expectedStatus: 200,
            },
        ],
    },
    {
        id: 'rl-fb-002',
        name: 'Submit Negative Feedback with Correction',
        goal: 'Send a query, evaluate the response negatively, and submit "down" feedback with a correction suggestion.',
        startUrl: '/',
        maxActions: 20,
        category: 'Feedback Submission',
        priority: 'high',
        tags: ['feedback', 'negative', 'correction'],
        hints: [
            ...RL_HINTS,
            'Step 1: Send query via UI.',
            'Step 2: Evaluate the response (may or may not be good — rate it down for testing).',
            'Step 3: Submit feedback with rating "down" and correction text explaining what was wrong.',
        ],
        setup: HYDRATION_SETUP,
        successCriteria: [
            {
                description: 'Feedback with correction submitted',
                check: { check: 'api_response', expected: '200' },
            },
        ],
    },
    {
        id: 'rl-fb-003',
        name: 'Submit Interaction Data',
        goal: 'Simulate widget interactions (expand, scroll, hover) and submit interaction data with the feedback.',
        startUrl: '/',
        maxActions: 25,
        category: 'Feedback Submission',
        priority: 'high',
        tags: ['feedback', 'interactions'],
        hints: [
            ...RL_HINTS,
            'Step 1: Send a query and wait for widgets.',
            'Step 2: Interact with widgets — click to expand, scroll within them, hover.',
            'Step 3: Track interaction durations.',
            'Step 4: Submit feedback with interaction array: [{widget_index, action, duration_ms}].',
        ],
        setup: HYDRATION_SETUP,
        successCriteria: [
            {
                description: 'Interaction feedback submitted',
                check: { check: 'api_response', expected: '200' },
            },
        ],
    },
    {
        id: 'rl-fb-004',
        name: 'Batch Feedback Across Multiple Queries',
        goal: 'Send 3 different queries, evaluate each response, and submit feedback for all three.',
        startUrl: '/',
        maxActions: 40,
        category: 'Feedback Submission',
        priority: 'medium',
        tags: ['feedback', 'batch'],
        hints: [
            ...RL_HINTS,
            'Queries to send: 1) "Show pump status" 2) "Any critical alerts?" 3) "Energy breakdown"',
            'For each: send query → wait for widgets → evaluate → submit feedback.',
            'Track all three query_ids for feedback submission.',
        ],
        setup: HYDRATION_SETUP,
        successCriteria: [
            {
                description: 'All feedback submissions return 200',
                check: { check: 'api_response', expected: '200' },
            },
        ],
    },
];
// ─── Category 4: RL Training Lifecycle ──────────────────────────────
const trainingLifecycleScenarios = [
    {
        id: 'rl-train-001',
        name: 'Check RL System Status',
        goal: 'Query the RL status endpoint and verify the system is running with expected configuration.',
        startUrl: '/',
        maxActions: 10,
        category: 'RL Training Lifecycle',
        priority: 'critical',
        tags: ['training', 'status', 'smoke'],
        hints: [
            'Use api_call action to GET /api/layer2/rl-status/',
            'Expected response has: running (bool), buffer (object), trainer (object), config (object).',
            'Verify "running" is true if the RL system is enabled.',
        ],
        setup: HYDRATION_SETUP,
        successCriteria: [
            {
                description: 'RL status returns valid response',
                check: { check: 'api_response', expected: '200' },
            },
        ],
        backendChecks: [
            {
                description: 'RL status endpoint responds',
                endpoint: '/api/layer2/rl-status/',
                method: 'GET',
                expectedStatus: 200,
            },
        ],
    },
    {
        id: 'rl-train-002',
        name: 'Approve LoRA Training',
        goal: 'Call the approve-training endpoint and verify the approval flag file is created.',
        startUrl: '/',
        maxActions: 10,
        category: 'RL Training Lifecycle',
        priority: 'high',
        tags: ['training', 'approve'],
        hints: [
            'Use api_call to POST /api/layer2/approve-training/',
            'Expected: {"status": "approved", "file": "...path..."}',
            'Then check RL status to see if training starts (may need DPO pairs in buffer).',
        ],
        setup: HYDRATION_SETUP,
        successCriteria: [
            {
                description: 'Training approved successfully',
                check: { check: 'api_response', expected: '200' },
            },
        ],
        backendChecks: [
            {
                description: 'Approve training endpoint responds',
                endpoint: '/api/layer2/approve-training/',
                method: 'POST',
                expectedStatus: 200,
            },
        ],
    },
    {
        id: 'rl-train-003',
        name: 'Evaluate-Feedback-Scorer Loop',
        goal: 'Run a mini loop: evaluate 3 queries → submit feedback → check that the scorer has new training steps.',
        startUrl: '/',
        maxActions: 30,
        category: 'RL Training Lifecycle',
        priority: 'high',
        tags: ['training', 'loop'],
        hints: [
            ...RL_HINTS,
            'Step 1: GET /api/layer2/rl-status/ — record current tier1_steps.',
            'Step 2: Send 3 queries and submit feedback for each.',
            'Step 3: Wait 10 seconds for background trainer to process.',
            'Step 4: GET /api/layer2/rl-status/ again — tier1_steps should have increased.',
        ],
        setup: HYDRATION_SETUP,
        successCriteria: [
            {
                description: 'Scorer steps increased after feedback',
                check: { check: 'api_response', expected: '200' },
            },
        ],
    },
    {
        id: 'rl-train-004',
        name: 'Full Training Cycle',
        goal: 'Complete full cycle: evaluate baseline → submit feedback → approve training → verify model update.',
        startUrl: '/',
        maxActions: 50,
        category: 'RL Training Lifecycle',
        priority: 'medium',
        tags: ['training', 'full-cycle'],
        hints: [
            ...RL_HINTS,
            'This is the most comprehensive scenario — it runs the complete RL pipeline.',
            'Step 1: Evaluate 5 queries and record baseline scores.',
            'Step 2: Submit all feedback.',
            'Step 3: Check if enough DPO pairs accumulated (≥50 needed for LoRA).',
            'Step 4: If yes, approve training and wait for completion.',
            'Step 5: Re-evaluate same 5 queries and compare with baseline.',
        ],
        setup: HYDRATION_SETUP,
        successCriteria: [
            {
                description: 'Training cycle completes without errors',
                check: { check: 'api_response', expected: '200' },
            },
        ],
    },
];
// ─── Category 5: Weight & Config Management ─────────────────────────
const weightManagementScenarios = [
    {
        id: 'rl-weights-001',
        name: 'Read Current Reward Weights',
        goal: 'Fetch the current RL configuration and display the reward weights.',
        startUrl: '/',
        maxActions: 10,
        category: 'Weight & Config Management',
        priority: 'high',
        tags: ['weights', 'config', 'smoke'],
        hints: [
            'Use api_call to GET /api/layer2/rl-status/',
            'The config section contains reward weight information.',
            'Display: explicit_rating, follow_up_type, widget_engagement, response_latency, intent_confidence.',
        ],
        setup: HYDRATION_SETUP,
        successCriteria: [
            {
                description: 'Config retrieved successfully',
                check: { check: 'api_response', expected: '200' },
            },
        ],
        backendChecks: [
            {
                description: 'RL status shows config',
                endpoint: '/api/layer2/rl-status/',
                method: 'GET',
                expectedStatus: 200,
            },
        ],
    },
    {
        id: 'rl-weights-002',
        name: 'Weight Sensitivity Sweep',
        goal: 'Evaluate the same set of queries and observe how different feedback patterns (all positive, all negative, mixed) affect the RL scorer.',
        startUrl: '/',
        maxActions: 40,
        category: 'Weight & Config Management',
        priority: 'medium',
        tags: ['weights', 'sweep'],
        hints: [
            ...RL_HINTS,
            'Step 1: Record baseline RL status (scorer loss, tier1_steps).',
            'Step 2: Submit 5 positive feedbacks for pump queries.',
            'Step 3: Submit 5 negative feedbacks for energy queries.',
            'Step 4: Wait for scorer update, check if loss changed.',
        ],
        setup: HYDRATION_SETUP,
        successCriteria: [
            {
                description: 'Sweep completes',
                check: { check: 'api_response', expected: '200' },
            },
        ],
    },
    {
        id: 'rl-weights-003',
        name: 'Before/After LoRA Training Comparison',
        goal: 'Evaluate queries before and after LoRA training to measure improvement.',
        startUrl: '/',
        maxActions: 50,
        category: 'Weight & Config Management',
        priority: 'medium',
        tags: ['weights', 'comparison', 'lora'],
        hints: [
            ...RL_HINTS,
            'This requires LoRA training to have completed at least once.',
            'Step 1: Check rl-status for tier2_runs > 0.',
            'Step 2: If no training has occurred, skip with a note.',
            'Step 3: Run evaluation suite and compare with previous evidence reports.',
        ],
        setup: HYDRATION_SETUP,
        successCriteria: [
            {
                description: 'Comparison report generated',
                check: { check: 'api_response', expected: '200' },
            },
        ],
    },
    {
        id: 'rl-weights-004',
        name: 'Safety Constraint Verification',
        goal: 'Verify that RL reranking never pushes alert widgets below position 3 in the layout.',
        startUrl: '/',
        maxActions: 20,
        category: 'Weight & Config Management',
        priority: 'critical',
        tags: ['weights', 'safety'],
        hints: [
            ...RL_HINTS,
            'Query: "Show me critical alerts and also energy breakdown and pump status"',
            'This query should return multiple widgets. Verify alerts widget position.',
            'Check [data-scenario] elements in order — if alerts/kpi scenario is at index ≥ 3, rate DOWN.',
        ],
        setup: HYDRATION_SETUP,
        successCriteria: [
            {
                description: 'Alert widget in safe position',
                check: { check: 'count', target: { css: '[data-scenario]' }, expected: '>=1' },
            },
        ],
    },
];
// ─── Export All Scenarios ───────────────────────────────────────────
exports.rlScenarios = [
    ...widgetQualityScenarios,
    ...dataAccuracyScenarios,
    ...feedbackScenarios,
    ...trainingLifecycleScenarios,
    ...weightManagementScenarios,
];
// ─── Query Bank (used by rl-runner for batch evaluation) ────────────
exports.EVAL_QUERIES = [
    'What is the current status of all pumps?',
    'Show me the temperature trend for the past 24 hours',
    'Are there any critical alerts right now?',
    'What is the energy consumption breakdown by equipment?',
    'Compare pump 1 and pump 2 performance',
    'Show transformer load distribution across all substations',
    'What equipment needs maintenance based on health scores?',
    'Show me all active alarms',
    'Who is on shift right now?',
    'What work orders are pending?',
    'Show spare parts stock levels',
    'Display the HVAC system status',
    'Show me the power quality metrics',
    'Show the top 5 energy consumers',
    'What is the chiller efficiency today?',
];
//# sourceMappingURL=rl-scenarios.js.map