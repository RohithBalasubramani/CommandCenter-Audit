# AI QA Agent

A state-of-the-art, framework-agnostic AI testing agent powered by Claude Code CLI.

## Features

- **AI-Powered Testing**: Uses Claude to make intelligent decisions like a real user
- **Framework Agnostic**: Works with React, Vue, Angular, plain HTML, and more
- **UI Framework Presets**: Built-in support for MUI, Tailwind, Bootstrap, Ant Design, Chakra, shadcn/ui
- **Vision Support**: Takes screenshots and uses Claude's vision capabilities
- **Smart Stuck Detection**: Automatically detects when the agent is stuck and re-plans
- **Cross-Session Learning**: Remembers lessons from previous test runs
- **Action Caching**: Replays successful action sequences for faster tests
- **Persona Modifiers**: Test UX from different user perspectives (impatient, confused, power-user, accessibility)
- **Detailed Evidence**: Screenshots, network logs, LLM conversations, perception logs
- **Failure Categorization**: Structured failure analysis for debugging

## Installation

```bash
npm install @neurareport/ai-qa-agent @playwright/test
```

## Prerequisites

- Node.js 18+
- Claude Code CLI installed and authenticated (`npm install -g @anthropic-ai/claude-code`)
- Playwright Test

## Quick Start

```typescript
import { AITestRunner, createConfig, type TestScenario } from '@neurareport/ai-qa-agent'
import { test, expect } from '@playwright/test'

// Create configuration for your app
const config = createConfig({
  appName: 'My App',
  baseUrl: 'http://localhost:3000',
  uiFramework: 'tailwind', // or 'mui', 'bootstrap', 'antd', etc.
  llm: {
    model: 'sonnet',
    useVision: true,
  },
})

// Define a test scenario
const loginScenario: TestScenario = {
  id: 'login-001',
  name: 'User can log in',
  goal: 'Log in to the application using valid credentials and reach the dashboard',
  startUrl: '/login',
  maxActions: 20,
  hints: [
    'Enter email in the email field',
    'Enter password in the password field',
    'Click the login button',
  ],
  successCriteria: [
    {
      description: 'User is redirected to dashboard',
      check: { check: 'url_contains', expected: '/dashboard' },
    },
    {
      description: 'Welcome message is visible',
      check: { check: 'text_contains', expected: 'Welcome' },
    },
  ],
}

// Run the test
test('AI Agent: User Login', async ({ page }) => {
  const runner = new AITestRunner(page, {
    agent: config,
    evidenceBaseDir: './test-evidence/login',
  })

  const result = await runner.runScenario(loginScenario)

  expect(result.status).toBe('pass')
})
```

## Configuration

### Agent Configuration

```typescript
const config = createConfig({
  // Required
  appName: 'My App',
  baseUrl: 'http://localhost:3000',

  // UI Framework (determines element selectors)
  uiFramework: 'mui', // 'mui' | 'tailwind' | 'bootstrap' | 'antd' | 'chakra' | 'shadcn' | 'plain' | 'custom'

  // LLM Configuration
  llm: {
    model: 'sonnet',      // 'sonnet' | 'opus' | 'haiku'
    useVision: true,      // Enable screenshot analysis
    timeout: 600_000,     // 10 minutes per LLM call
  },

  // Optional settings
  apiBaseUrl: 'http://localhost:8000',  // If different from baseUrl
  screenshotEveryStep: true,
  actionDelay: 500,                      // ms between actions
  defaultPersona: 'default',             // 'default' | 'impatient' | 'confused' | 'power-user' | 'accessibility'
  maxElementsInObservation: 100,
  pageLoadTimeout: 30_000,
  actionTimeout: 10_000,
  debug: false,
})
```

### Custom Element Selectors

```typescript
const config = createConfig({
  appName: 'My App',
  baseUrl: 'http://localhost:3000',
  uiFramework: 'custom',
  customSelectors: {
    buttons: ['button', '.my-button', '[data-action]'],
    textInputs: ['input.my-input', 'textarea'],
    selects: ['.my-dropdown', '[role="listbox"]'],
    toasts: ['.my-notification', '.toast'],
    errors: ['.error-message', '.my-error'],
    // ... other selectors
  },
})
```

## Test Scenarios

### Basic Scenario

```typescript
const scenario: TestScenario = {
  id: 'create-post-001',
  name: 'Create a new blog post',
  goal: 'Create a new blog post with title and content',
  startUrl: '/posts/new',
  maxActions: 30,
  successCriteria: [
    {
      description: 'Post is saved and visible',
      check: { check: 'toast_message', expected: 'Post created' },
    },
  ],
}
```

### Scenario with Persona

```typescript
const scenario: TestScenario = {
  id: 'checkout-accessibility',
  name: 'Checkout with screen reader',
  goal: 'Complete checkout using only keyboard navigation',
  startUrl: '/cart',
  maxActions: 40,
  persona: 'accessibility', // Tests ARIA labels, keyboard navigation
  successCriteria: [
    {
      description: 'Order confirmation visible',
      check: { check: 'text_contains', expected: 'Order confirmed' },
    },
  ],
}
```

### Scenario with QA Profile Policy

```typescript
const scenario: TestScenario = {
  id: 'admin-flow-001',
  name: 'Admin flow sanity',
  goal: 'Complete the admin flow and verify success signals',
  startUrl: '/admin',
  maxActions: 30,
  qaProfile: 'general-purpose', // or 'neurareport'
  successCriteria: [
    { description: 'Success state is visible', check: { check: 'text_contains', expected: 'Success' } },
  ],
}
```

### Scenario with Setup/Teardown

```typescript
const scenario: TestScenario = {
  id: 'edit-user-001',
  name: 'Edit user profile',
  goal: 'Update the user display name',
  startUrl: '/profile',
  maxActions: 25,
  setup: [
    {
      type: 'api_call',
      description: 'Create test user',
      endpoint: '/api/users',
      method: 'POST',
      body: { name: 'Test User', email: 'test@example.com' },
    },
  ],
  teardown: [
    {
      type: 'api_call',
      description: 'Delete test user',
      endpoint: '/api/users/test@example.com',
      method: 'DELETE',
      runOnFailure: true,
    },
  ],
  successCriteria: [
    {
      description: 'Profile updated message shown',
      check: { check: 'toast_message', expected: 'Profile updated' },
    },
  ],
}
```

### Scenario with Backend Checks

```typescript
const scenario: TestScenario = {
  id: 'payment-001',
  name: 'Process payment',
  goal: 'Complete a payment transaction',
  startUrl: '/checkout',
  maxActions: 35,
  successCriteria: [
    {
      description: 'Payment success page visible',
      check: { check: 'url_contains', expected: '/success' },
    },
  ],
  backendChecks: [
    {
      description: 'Transaction recorded in database',
      endpoint: '/api/transactions/latest',
      method: 'GET',
      expectedStatus: 200,
      responseCheck: {
        path: 'status',
        operator: 'equals',
        value: 'completed',
      },
    },
  ],
}
```

## Running Multiple Scenarios

```typescript
import { runScenarios, generateAuditReport } from '@neurareport/ai-qa-agent'

test('Full App Audit', async ({ page }) => {
  const scenarios = [loginScenario, createPostScenario, editProfileScenario]

  const results = await runScenarios(page, scenarios, {
    agent: config,
    evidenceBaseDir: './test-evidence/audit',
  }, {
    maxRetries: 2, // Retry failed tests
    onScenarioComplete: (result) => {
      console.log(`${result.scenarioName}: ${result.status}`)
    },
  })

  // Generate audit report
  const report = generateAuditReport(results, 'My App', '1.0.0')
  console.log(report.summary)

  // Assert overall pass rate
  expect(report.passRate).toBeGreaterThanOrEqual(80)
})
```

## Personas

Test your UX from different user perspectives:

| Persona | Behavior |
|---------|----------|
| `default` | Normal user behavior |
| `impatient` | Clicks fast, skips instructions, expects instant feedback |
| `confused` | Hesitates, misreads labels, avoids unclear buttons |
| `power-user` | Uses keyboard shortcuts, explores advanced features |
| `accessibility` | Keyboard-only navigation, expects ARIA labels |
| `mobile` | Expects touch-friendly targets, swipe gestures |
| `slow-network` | Expects loading states, progress indicators |

## QA Profiles

| Profile | Policy |
|---------|--------|
| `general-purpose` | Framework-agnostic strategy and accessibility-first selectors |
| `neurareport` | NeuraReport-specific navigation and MUI workflow heuristics |

## Evidence & Debugging

Each test run generates:

- **Screenshots**: Before/after each action
- **Action Log**: Every action with reasoning and result
- **LLM Conversation**: Full conversation with Claude
- **Perception Log**: What the agent "saw" at each step
- **Goal Ledger**: Progress tracking toward success criteria
- **Network Log**: All API calls captured

Evidence is saved to your `evidenceBaseDir`:

```
test-evidence/
  login-001/
    screenshots/
      001-initial.png
      002-step-001-type.png
      003-step-002-click.png
      ...
    network/
      login-001-network.json
    login-001-action-log.json
    login-001-llm-conversation.json
    login-001-perception.json
    login-001-goal-ledger.json
    login-001-result.json
```

## Failure Categories

When tests fail, they're categorized for easier debugging:

| Category | Description |
|----------|-------------|
| `element_not_found` | Target element doesn't exist |
| `element_not_interactable` | Element exists but can't be clicked |
| `navigation_error` | Page failed to load |
| `form_error` | Form validation or submission failed |
| `timeout` | Action or page timed out |
| `stuck_loop` | Agent repeated same actions without progress |
| `assertion_failed` | Success criteria not met |
| `browser_crash` | Page or browser closed unexpectedly |
| `llm_error` | Claude CLI failed to respond |
| `network_error` | API call failed |
| `auth_error` | Authentication/authorization failed |

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      AITestRunner                           │
│  Orchestrates the test execution loop                       │
└─────────────────────────────────────────────────────────────┘
                          │
          ┌───────────────┴───────────────┐
          ▼                               ▼
┌─────────────────────┐       ┌─────────────────────┐
│    BrowserAgent     │       │     AgentBrain      │
│  "Hands" - executes │       │  "Brain" - decides  │
│  actions in browser │       │  what to do next    │
└─────────────────────┘       └─────────────────────┘
          │                               │
          │                               ▼
          │                   ┌─────────────────────┐
          │                   │    Claude CLI       │
          │                   │  (via claude -p)    │
          │                   └─────────────────────┘
          ▼
┌─────────────────────┐
│     Playwright      │
│   Browser Control   │
└─────────────────────┘
```

## License

MIT
