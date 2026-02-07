/**
 * AgentBrain — LLM-powered decision engine using Claude Code CLI.
 *
 * This is the "brain" of the AI test agent. It:
 * - Observes the page state (DOM, screenshot, API calls)
 * - Decides what action to take next
 * - Tracks progress toward the goal
 * - Detects when the agent is stuck
 * - Learns from past successes and failures
 *
 * State-of-the-art features (research-informed):
 * - Goal Ledger: tracks required outcomes, detects when stuck
 * - Critic + Actor: every step asks "did I make progress?" not just "what next?"
 * - Failure Heuristics: detects silent failures, repeated screens, no-change states
 * - Perception Log: records what the user "experienced" — not just actions taken
 * - Element Shuffling: when stuck, shuffle elements so Claude notices different ones
 * - Re-plan Trigger: when stuck, forces Claude to step back and re-think
 * - Failure Categorization: structured failure analysis for debugging
 * - Action Caching: replay successful action sequences
 * - Persona Modifiers: test UX from different user perspectives
 * - Cross-session Learning: remember lessons from previous test runs
 * - Separate Critic Agent: periodic meta-evaluation of progress
 *
 * Framework-agnostic: Uses configuration to adapt to any web app.
 * Uses `claude` CLI (Claude Code subscription) — zero extra API cost.
 */
import { spawn } from 'child_process'
import * as fs from 'fs'
import * as path from 'path'
import * as os from 'os'
import type {
  AgentAction,
  PageObservation,
  TestScenario,
  ActionLogEntry,
  FailureCategory,
  PersonaModifier,
  QaAgentProfile,
  GoalLedger,
  PerceptionEntry,
  CachedActionSequence,
  LessonLearned,
} from './types'
import type { AgentConfig } from './config'

// ─── Brain Configuration ─────────────────────────────────────────────

interface BrainConfig {
  appName: string
  model: string
  maxTokens?: number
  useVision?: boolean
  screenshotDir?: string
  learningDir?: string
  timeout?: number
  debug?: boolean
}

const VALID_ACTIONS = new Set([
  'click',
  'type',
  'navigate',
  'scroll',
  'select',
  'upload',
  'wait',
  'verify',
  'api_call',
  'screenshot',
  'key',
  'hover',
  'drag',
  'done',
  'read',
])

const STOPWORDS = new Set([
  'the', 'and', 'for', 'with', 'from', 'that', 'this', 'into', 'onto', 'your', 'you',
  'have', 'has', 'had', 'were', 'was', 'will', 'would', 'should', 'could', 'must', 'can',
  'are', 'not', 'but', 'all', 'any', 'there', 'their', 'then', 'than', 'when', 'what',
  'where', 'which', 'after', 'before', 'about', 'over', 'under', 'near', 'page', 'screen',
])

// ─── The Brain ───────────────────────────────────────────────────────

export class AgentBrain {
  private config: BrainConfig
  private systemPrompt = ''
  private recentHistory: string[] = []
  private actionHistory: ActionLogEntry[] = []
  private stepCount = 0
  private maxRetries = 3
  private maxHistoryLines = 50

  // Goal tracking
  private ledger: GoalLedger = {
    goal: '',
    requiredOutcomes: [],
    completedOutcomes: [],
    stuckScore: 0,
    stepsSinceProgress: 0,
  }

  // Perception tracking
  private perceptionLog: PerceptionEntry[] = []
  private lastUrl = ''
  private lastElementCount = 0
  private lastHeading = ''
  private sameScreenCount = 0

  // Action caching
  private actionCache: CachedActionSequence[] = []
  private currentActionSequence: Array<{ type: string; target?: any; value?: string }> = []

  // Persona
  private persona: PersonaModifier = 'default'

  // Cross-session learning
  private lessons: LessonLearned[] = []

  // Critic
  private stepsSinceCritic = 0
  private criticInterval = 10

  // Current scenario ID
  private scenarioId = ''
  private qaProfile: QaAgentProfile = 'general-purpose'
  private scenarioMaxActions = 30

  // SOTA exploration controls
  private actionSignatures: string[] = []
  private targetUseCount: Map<string, number> = new Map()
  private targetFailureCount: Map<string, number> = new Map()

  constructor(agentConfig: AgentConfig) {
    const screenshotDir = agentConfig.llm.useVision
      ? path.join(os.tmpdir(), 'ai-qa-agent-screenshots')
      : undefined
    if (screenshotDir) {
      fs.mkdirSync(screenshotDir, { recursive: true })
    }

    const learningDir = agentConfig.learningDir || path.join(os.tmpdir(), 'ai-qa-agent-learning')
    fs.mkdirSync(learningDir, { recursive: true })

    this.config = {
      appName: agentConfig.appName,
      model: agentConfig.llm.model || process.env.AI_TEST_MODEL || 'sonnet',
      maxTokens: agentConfig.llm.maxTokens ?? 1024,
      useVision: agentConfig.llm.useVision ?? true,
      screenshotDir,
      learningDir,
      timeout: agentConfig.llm.timeout || 600_000,
      debug: agentConfig.debug ?? false,
    }

    this.loadLessons()
    this.loadActionCache()
  }

  /** Initialize the brain with a test scenario */
  initScenario(scenario: TestScenario) {
    this.recentHistory = []
    this.actionHistory = []
    this.perceptionLog = []
    this.stepCount = 0
    this.stepsSinceCritic = 0
    this.lastUrl = ''
    this.lastElementCount = 0
    this.lastHeading = ''
    this.sameScreenCount = 0
    this.currentActionSequence = []
    this.scenarioId = scenario.id
    this.scenarioMaxActions = scenario.maxActions
    this.actionSignatures = []
    this.targetUseCount.clear()
    this.targetFailureCount.clear()
    this.qaProfile = scenario.qaProfile || this.inferProfileFromConfig()

    this.persona = scenario.persona || 'default'

    this.ledger = {
      goal: scenario.goal,
      requiredOutcomes: scenario.successCriteria.map(c => c.description),
      completedOutcomes: [],
      stuckScore: 0,
      stepsSinceProgress: 0,
    }

    this.systemPrompt = this.buildSystemPrompt(scenario)
  }

  /** Decide the next action based on current page state */
  async decideAction(observation: PageObservation): Promise<AgentAction> {
    this.stepCount++
    this.stepsSinceCritic++
    this.markOutcomesFromObservation(observation)

    // Failure heuristics: detect stuck/loop states
    const stuckSignals = this.detectStuckState(observation)
    this.criticInterval = this.ledger.stuckScore >= 4 ? 5 : 10

    // Save screenshot for Claude CLI vision
    let screenshotPath: string | undefined
    if (this.config.useVision && observation.screenshot && this.config.screenshotDir) {
      screenshotPath = path.join(
        this.config.screenshotDir,
        `step-${String(this.stepCount).padStart(3, '0')}.png`
      )
      fs.writeFileSync(screenshotPath, Buffer.from(observation.screenshot, 'base64'))
    }

    // Re-plan trigger when stuck
    const replanPrompt = this.ledger.stuckScore >= 4 ? this.buildReplanPrompt() : ''

    // Build observation with stuck signals injected
    const obsText = this.buildObservationText(observation, screenshotPath, stuckSignals, replanPrompt)
    this.recentHistory.push(obsText)
    this.trimHistory()

    // Run critic every N steps
    if (this.stepsSinceCritic >= this.criticInterval && this.stepCount > 3) {
      const criticFeedback = await this.runCritic(observation)
      if (criticFeedback) {
        this.recentHistory.push(`[CRITIC AGENT] ${criticFeedback}`)
        this.stepsSinceCritic = 0
      }
    }

    const prompt = this.buildPrompt()

    let action = await this.decideWithRetries(prompt, observation)
    action = this.normalizeAction(action, observation)

    if (this.shouldDiversify(action)) {
      action = this.buildDiversifiedAction(observation, action)
    }

    // Update goal ledger
    this.updateLedger(action)

    // Cache action
    if (action.type !== 'done' && action.type !== 'screenshot') {
      this.currentActionSequence.push({
        type: action.type,
        target: action.target,
        value: action.value,
      })
    }

    // Auto-bail if critically stuck
    if (this.ledger.stuckScore >= 8 && action.type !== 'done') {
      if (this.config.debug) {
        console.log(`    Agent stuck (score=${this.ledger.stuckScore}) — forcing done`)
      }
      action = {
        type: 'done',
        reasoning: `STUCK: ${this.ledger.stepsSinceProgress} steps without progress. Same screen ${this.sameScreenCount} times. Abandoning task.`,
      }
    }

    this.recentHistory.push(`[Assistant] Action: ${JSON.stringify(action)}`)
    return action
  }

  /** Feed action result back to the brain */
  recordResult(action: AgentAction, result: { success: boolean; error?: string }, duration: number) {
    const entry: ActionLogEntry = {
      step: this.stepCount,
      timestamp: new Date().toISOString(),
      action,
      result: result.success ? 'success' : 'failed',
      error: result.error,
      duration,
    }
    this.actionHistory.push(entry)

    const signature = this.buildActionSignature(action)
    this.actionSignatures.push(signature)
    if (this.actionSignatures.length > 40) {
      this.actionSignatures.shift()
    }

    const targetKey = this.buildTargetKey(action.target)
    if (targetKey) {
      this.targetUseCount.set(targetKey, (this.targetUseCount.get(targetKey) || 0) + 1)
      if (result.success) {
        if ((this.targetFailureCount.get(targetKey) || 0) > 0) {
          this.targetFailureCount.set(targetKey, (this.targetFailureCount.get(targetKey) || 1) - 1)
        }
      } else {
        this.targetFailureCount.set(targetKey, (this.targetFailureCount.get(targetKey) || 0) + 1)
      }
    }

    let resultMsg: string
    if (result.success) {
      if (action.progress) this.markOutcomesFromText(action.progress)
      if (action.reasoning) this.markOutcomesFromText(action.reasoning)
      if (this.isLikelyProgressAction(action)) {
        this.ledger.stepsSinceProgress = 0
        this.ledger.stuckScore = Math.max(0, this.ledger.stuckScore - 1)
      }
      resultMsg = `[Result] Action succeeded (${duration}ms)`
    } else {
      resultMsg = `[Result] Action FAILED: ${result.error}`
      this.ledger.stepsSinceProgress++
      this.ledger.stuckScore += 1
    }
    this.recentHistory.push(resultMsg)
  }

  /** Save action cache and lessons after scenario completes */
  finalizeScenario(success: boolean) {
    // Save successful action sequences
    if (success && this.currentActionSequence.length > 0) {
      this.actionCache.push({
        scenarioId: this.scenarioId,
        actions: this.currentActionSequence,
        success: true,
        timestamp: new Date().toISOString(),
      })
      this.saveActionCache()
    }

    // Extract lessons from failures
    if (!success && this.stepCount > 3) {
      const failedActions = this.actionHistory.filter(a => a.result === 'failed')
      const confusedSteps = this.perceptionLog.filter(p => p.confusionSignals.length > 0)
      if (failedActions.length > 0 || confusedSteps.length > 0) {
        const lesson = this.extractLesson(failedActions, confusedSteps)
        if (lesson) {
          this.lessons.push({
            scenarioId: this.scenarioId,
            lesson,
            timestamp: new Date().toISOString(),
          })
          this.saveLessons()
        }
      }
    }
  }

  /** Categorize a failure for structured reporting */
  categorizeFailure(error?: string, actionLog?: ActionLogEntry[]): FailureCategory {
    if (!error && !actionLog?.length) return 'unknown'

    const errorLower = (error || '').toLowerCase()
    const lastActions = (actionLog || []).slice(-5)

    // Browser/page crashed
    if (errorLower.includes('closed') || errorLower.includes('target closed') || errorLower.includes('browser')) {
      return 'browser_crash'
    }

    // LLM failures
    if (errorLower.includes('claude cli') || errorLower.includes('spawn error') || errorLower.includes('llm')) {
      return 'llm_error'
    }

    // Timeout
    if (errorLower.includes('timeout') || errorLower.includes('maximum actions')) {
      return 'timeout'
    }

    // Stuck loop
    if (errorLower.includes('stuck') || errorLower.includes('without progress') || errorLower.includes('same screen')) {
      return 'stuck_loop'
    }

    // Element not found
    const notFoundCount = lastActions.filter(a =>
      a.error?.includes('not found') || a.error?.includes('no element') || a.error?.includes('No valid selector')
    ).length
    if (notFoundCount >= 2) return 'element_not_found'

    // Element not interactable
    const notInteractableCount = lastActions.filter(a =>
      a.error?.includes('not interactable') || a.error?.includes('disabled') || a.error?.includes('covered')
    ).length
    if (notInteractableCount >= 2) return 'element_not_interactable'

    // Navigation error
    if (errorLower.includes('navigate') || errorLower.includes('err_connection') || errorLower.includes('net::')) {
      return 'navigation_error'
    }

    // Network/API error
    if (errorLower.includes('api') || errorLower.includes('network') || errorLower.includes('fetch')) {
      return 'network_error'
    }

    // Auth error
    if (errorLower.includes('auth') || errorLower.includes('401') || errorLower.includes('403') || errorLower.includes('forbidden')) {
      return 'auth_error'
    }

    // Form error
    const formErrorCount = lastActions.filter(a =>
      a.action.type === 'type' && a.result === 'failed'
    ).length
    if (formErrorCount >= 1) return 'form_error'

    // Assertion failures
    if (errorLower.includes('criteria') || errorLower.includes('assertion')) {
      return 'assertion_failed'
    }

    return 'unknown'
  }

  getActionHistory(): ActionLogEntry[] { return this.actionHistory }
  getPerceptionLog(): PerceptionEntry[] { return this.perceptionLog }
  getLedger(): GoalLedger { return { ...this.ledger } }

  getConversation(): Array<{ role: string; content: string }> {
    return this.recentHistory.map(line => ({
      role: line.startsWith('[Assistant]') ? 'assistant' : 'user',
      content: line,
    }))
  }

  // ─── Failure Heuristics ─────────────────────────────────────────────

  private detectStuckState(obs: PageObservation): string[] {
    const signals: string[] = []

    // Same URL + same heading + similar element count = same screen
    const sameUrl = obs.url === this.lastUrl
    const sameHeading = obs.heading === this.lastHeading
    const similarElements = Math.abs(obs.interactiveElements.length - this.lastElementCount) < 3

    if (sameUrl && sameHeading && similarElements) {
      this.sameScreenCount++
      if (this.sameScreenCount >= 3) {
        signals.push(`STUCK: Same screen ${this.sameScreenCount} times. Try something COMPLETELY different.`)
        this.ledger.stuckScore += 2
      }
    } else {
      this.sameScreenCount = 0
    }

    // No progress for many steps
    if (this.ledger.stepsSinceProgress >= 4) {
      signals.push(`NO PROGRESS for ${this.ledger.stepsSinceProgress} steps. Change your approach or give up.`)
      this.ledger.stuckScore += 1
    }

    // Repeated action signature patterns
    const recentSignatures = this.actionSignatures.slice(-6)
    if (recentSignatures.length >= 4) {
      const unique = new Set(recentSignatures)
      if (unique.size <= 2) {
        signals.push('REPEATED ACTION PATTERN: Same action signatures are recurring.')
        this.ledger.stuckScore += 1
      }
    }

    // Hot failure targets
    const hotFailureTargets = Array.from(this.targetFailureCount.entries())
      .filter(([, count]) => count >= 3)
      .slice(0, 2)
      .map(([key, count]) => `${key} (${count} failures)`)
    if (hotFailureTargets.length) {
      signals.push(`HOT FAILURE TARGETS: ${hotFailureTargets.join(', ')}`)
      this.ledger.stuckScore += 1
    }

    // Console errors
    if (obs.consoleErrors?.length) {
      signals.push(`BROWSER ERRORS: ${obs.consoleErrors.slice(0, 3).join(' | ')}`)
    }

    // Track for next comparison
    this.lastUrl = obs.url
    this.lastHeading = obs.heading || ''
    this.lastElementCount = obs.interactiveElements.length

    // Record perception
    this.perceptionLog.push({
      step: this.stepCount,
      url: obs.url,
      screenSummary: `${obs.heading || 'No heading'} — ${obs.interactiveElements.length} elements`,
      visibleCTAs: obs.interactiveElements
        .filter(el => el.role === 'button' || el.role === 'link')
        .slice(0, 5)
        .map(el => el.name),
      confidence: signals.length === 0 ? 0.9 : Math.max(0.2, 0.9 - signals.length * 0.3),
      confusionSignals: signals,
      progressMade: this.ledger.stepsSinceProgress === 0,
    })

    return signals
  }

  private updateLedger(action: AgentAction) {
    this.ledger.stepsSinceProgress++

    if (action.type === 'done') return

    // Navigation = progress
    if (action.type === 'navigate') {
      this.ledger.stepsSinceProgress = 0
      this.ledger.stuckScore = Math.max(0, this.ledger.stuckScore - 1)
    }

    // Typing = progress (filling a form)
    if (action.type === 'type') {
      this.ledger.stepsSinceProgress = 0
      this.ledger.stuckScore = Math.max(0, this.ledger.stuckScore - 1)
    }

    // Clicking submit-like buttons = progress
    if (action.type === 'click' && action.target?.name) {
      const name = action.target.name.toLowerCase()
      if (['save', 'submit', 'add', 'create', 'generate', 'run', 'confirm', 'ok', 'test', 'next', 'continue', 'send'].some(w => name.includes(w))) {
        this.ledger.stepsSinceProgress = 0
      }
    }
  }

  // ─── Re-plan Trigger ────────────────────────────────────────────────

  private buildReplanPrompt(): string {
    const failedActions = this.actionHistory
      .filter(a => a.result === 'failed')
      .slice(-3)
      .map(a => `  - ${a.action.type} on "${a.action.target?.name || a.action.target?.label || '?'}" → ${a.error?.slice(0, 80)}`)

    return `
═══ RE-PLAN REQUIRED ═══
You've been stuck for ${this.ledger.stepsSinceProgress} steps. Step back and THINK.

What you tried that didn't work:
${failedActions.join('\n') || '  (no clear failures, but no progress either)'}

INSTRUCTIONS: Forget your current approach. Look at the screen FRESH.
- What elements are actually visible?
- Is there a completely different path to your goal?
- Could you use the navigation/sidebar to go somewhere else first?
- Maybe the feature you're looking for is in a different section?
═══════════════════════`
  }

  // ─── Critic Agent ───────────────────────────────────────────────────

  private async runCritic(obs: PageObservation): Promise<string | null> {
    const criticPrompt = `You are a CRITIC reviewing an AI test agent's progress. Be harsh but constructive.

GOAL: ${this.ledger.goal}

PROGRESS: ${this.ledger.completedOutcomes.length}/${this.ledger.requiredOutcomes.length} outcomes done
STEPS TAKEN: ${this.stepCount}
STUCK SCORE: ${this.ledger.stuckScore}
CURRENT URL: ${obs.url}
CURRENT PAGE: ${obs.heading || 'unknown'}

RECENT ACTIONS:
${this.actionHistory.slice(-5).map(a =>
  `  Step ${a.step}: ${a.action.type} "${a.action.target?.name || ''}" → ${a.result}${a.error ? ` (${a.error.slice(0, 60)})` : ''}`
).join('\n')}

CONFUSION SIGNALS:
${this.perceptionLog.slice(-3).flatMap(p => p.confusionSignals).join('\n') || '  none'}

In 1-2 sentences, tell the agent:
1. Is it making progress or wasting time?
2. What should it try differently?

Be specific. No fluff. JSON: {"verdict":"progress|stuck|lost","advice":"..."}`

    try {
      const response = await this.callClaudeLightweight(criticPrompt)
      const cleaned = response.replace(/^```(?:json)?\s*/i, '').replace(/\s*```$/i, '')
      const parsed = JSON.parse(cleaned)
      if (parsed.verdict === 'stuck' || parsed.verdict === 'lost') {
        this.ledger.stuckScore += 1
      }
      return `[${parsed.verdict?.toUpperCase()}] ${parsed.advice}`
    } catch {
      return null
    }
  }

  // ─── Prompt Building ────────────────────────────────────────────────

  private buildSystemPrompt(scenario: TestScenario): string {
    const personaText = this.getPersonaText()
    const profileText = this.getProfilePolicy()
    const lessonsText = this.getLessonsForScenario(scenario.id)
    const expectedOutcome = scenario.expectedOutcome
      ? `\nEXPECTED OUTCOME: ${scenario.expectedOutcome}`
      : ''
    const cachedHint = this.getCachedHint(scenario.id)

    return `You are a REAL PERSON testing a web app called ${this.config.appName}. You behave exactly like a normal user — clicking things, filling forms, reading what's on screen.
${personaText}
${profileText}
You do NOT know anything about code, APIs, or the backend. You only know what you can SEE on screen.

YOUR TASK: ${scenario.name}
WHAT YOU WANT TO DO: ${scenario.goal}${expectedOutcome}
${scenario.hints?.length ? `TIPS:\n${scenario.hints.map((h, i) => `${i + 1}. ${h}`).join('\n')}` : ''}
${cachedHint}${lessonsText}
YOU ARE DONE WHEN:
${scenario.successCriteria.map((c, i) => `${i + 1}. ${c.description}`).join('\n')}

RESPOND WITH A JSON OBJECT:
{
  "progress": "What did my last action achieve? Am I closer to my goal?",
  "blocker": "Is anything confusing or blocking me right now? Or 'none'",
  "expectedSignal": "What visible signal should happen if this action succeeds",
  "confidence": 0.0,
  "type": "click|type|navigate|scroll|select|wait|key|hover|screenshot|done",
  "reasoning": "What I'm about to do and why, as a normal user would think",
  "target": { "role": "button", "name": "exact text" },
  "value": "text to type (only for type actions)",
  "key": "Escape|Enter|Tab (only for key actions)"
}

"progress" and "blocker" are REQUIRED — they keep you honest about whether you're making progress.

SPECIAL ACTIONS:
- "key": Press a keyboard key. Use "key": "Escape" to close dialogs/modals, "Enter" to submit, "Tab" to move focus.
- "hover": Hover over an element to trigger tooltips or dropdown menus.
- "done": Use when the task is complete or you're stuck.

EXAMPLES:
{"progress":"Opened the form successfully","blocker":"none","type":"type","reasoning":"filling in the name field","target":{"label":"Name"},"value":"My Test Item"}
{"progress":"Form is filled out","blocker":"none","type":"click","reasoning":"saving the form","target":{"role":"button","name":"Save"}}
{"progress":"Dialog opened","blocker":"none","type":"key","reasoning":"closing the dialog with Escape","key":"Escape"}
{"progress":"Need to see dropdown options","blocker":"none","type":"hover","reasoning":"hovering to reveal menu","target":{"role":"button","name":"More"}}
{"progress":"Can see the new item in the list","blocker":"none","type":"done","reasoning":"task complete — result visible on screen"}

TARGET SELECTORS — Copy from Elements list EXACTLY:
1. { "role": "button", "name": "exact text" } — buttons, links, tabs, menu items
2. { "label": "exact label" } — form fields with labels
3. { "placeholder": "placeholder text" } — form fields with placeholders
4. { "text": "visible text" } — any text on screen
5. Add "nth": 0 if multiple elements share a name (0=first, 1=second)
6. { "coordinates": { "x": 123, "y": 456 } } — pixel click (LAST RESORT if nothing else works)
7. { "css": "..." } — FORBIDDEN. Never invent selectors.

CRITICAL RULES:
- ONE JSON object. Nothing else. No text before or after.
- confidence must be 0.0 to 1.0 and reflect uncertainty.
- Copy element names EXACTLY from the Elements list.
- DO NOT say "done" until you can SEE the result on screen.
- If you click a button and NOTHING happens — that's a UX problem. Note it and try a different approach.
- If you're stuck (same screen 3+ times), try something COMPLETELY different.
- If stuck for 5+ actions, give up honestly: {"type":"done","reasoning":"STUCK: [what blocked me]","progress":"no progress","blocker":"[the problem]"}
- To go back to a page: use {"type": "navigate", "url": "/path", "reasoning": "..."}
- After submitting a form, WAIT and LOOK at what happened before saying done.
- Budget: ${scenario.maxActions} actions max.
${this.config.useVision ? '- Screenshot paths are provided — view them to see the actual screen.' : ''}`
  }

  private inferProfileFromConfig(): QaAgentProfile {
    const app = this.config.appName.toLowerCase()
    if (app.includes('neurareport')) return 'neurareport'
    return 'general-purpose'
  }

  private getProfilePolicy(): string {
    if (this.qaProfile === 'neurareport') {
      return `\nProfile policy: This is NeuraReport. Prioritize sidebar navigation, MUI patterns, and visible workflow outcomes for Connections, Templates, Reports, and Agents.`
    }
    return `\nProfile policy: Stay framework-agnostic, use accessibility-first selectors, and verify outcomes strictly from visible UI evidence.`
  }

  /** Persona modifiers */
  private getPersonaText(): string {
    switch (this.persona) {
      case 'impatient':
        return `\nYour personality: You are IMPATIENT. You click fast, don't read long instructions, expect instant feedback. If something takes more than a moment, you get frustrated and try something else. You skip optional fields.`
      case 'confused':
        return `\nYour personality: You are a CONFUSED first-time user. You hesitate before clicking, misread labels sometimes, and expect very clear guidance. If a button's purpose isn't obvious, you avoid it.`
      case 'power-user':
        return `\nYour personality: You are a POWER USER. You know how apps work, you look for shortcuts, you expect advanced features. You try keyboard shortcuts, right-click menus, and explore settings.`
      case 'accessibility':
        return `\nYour personality: You rely on ACCESSIBILITY features. You navigate by tab key, expect proper ARIA labels, and use screen reader patterns. Elements without labels are bugs.`
      case 'mobile':
        return `\nYour personality: You are on a MOBILE device. You expect large touch targets, swipe gestures, and mobile-friendly layouts. Tiny buttons and hover-dependent features are frustrating.`
      case 'slow-network':
        return `\nYour personality: You are on a SLOW network. You expect loading states, progress indicators, and graceful handling of timeouts. Spinning forever without feedback is unacceptable.`
      default:
        return ''
    }
  }

  private buildObservationText(obs: PageObservation, screenshotPath?: string, stuckSignals?: string[], replanPrompt?: string): string {
    const parts = [
      `[Step ${this.stepCount}] URL: ${obs.url}`,
      obs.heading ? `Page: ${obs.heading}` : '',
      `Profile: ${this.qaProfile}`,
    ]

    // Stuck warnings — prominent
    if (stuckSignals?.length) {
      parts.push('')
      stuckSignals.forEach(s => parts.push(`⚠ ${s}`))
      parts.push('')
    }

    // Re-plan prompt
    if (replanPrompt) {
      parts.push(replanPrompt)
    }

    // Screenshot
    if (screenshotPath) {
      const normalizedPath = screenshotPath.replace(/\\/g, '/')
      parts.push(`SCREENSHOT: "${normalizedPath}" — view this to see the actual screen.`)
    }

    // Element shuffling when stuck
    const maxElements = 25
    let elements = obs.interactiveElements.slice(0, maxElements)
    if (this.sameScreenCount >= 3) {
      elements = this.shuffleArray([...elements])
      parts.push('(Elements shuffled — look at ones you haven\'t tried yet)')
    }

    // Interactive elements
    parts.push(
      `Elements (${obs.interactiveElements.length}):`,
      ...elements.map((el, i) =>
        `  ${i + 1}. [${el.role}] "${el.name}"${el.disabled ? ' (disabled)' : ''}${el.value ? ` val="${el.value}"` : ''}${el.x !== undefined ? ` @${el.x},${el.y}` : ''}`
      ),
    )

    if (obs.interactiveElements.length > maxElements) {
      parts.push(`  ... and ${obs.interactiveElements.length - maxElements} more elements`)
    }

    const untried = obs.interactiveElements
      .filter(el => !!el.name && !el.disabled)
      .filter(el => (this.targetUseCount.get(`${el.role}:${el.name.trim().toLowerCase()}`) || 0) === 0)
      .slice(0, 6)
      .map(el => `[${el.role}] ${el.name}`)
    if (untried.length) {
      parts.push(`Untried candidates: ${untried.join(' | ')}`)
    }

    const repeatedTargets = Array.from(this.targetUseCount.entries())
      .filter(([, count]) => count >= 3)
      .slice(0, 4)
      .map(([target, count]) => `${target}(${count}x)`)
    if (repeatedTargets.length) {
      parts.push(`Repeated targets: ${repeatedTargets.join(', ')}`)
    }

    const recentActions = this.actionHistory.slice(-5)
    if (recentActions.length) {
      parts.push('Recent actions:')
      recentActions.forEach(action => {
        const target = action.action.target?.name || action.action.target?.label || action.action.url || ''
        parts.push(`  - #${action.step}: ${action.action.type} ${target ? `"${String(target).slice(0, 60)}"` : ''} -> ${action.result}${action.error ? ` (${action.error.slice(0, 90)})` : ''}`)
      })
    }

    // User-visible feedback
    if (obs.toasts.length) parts.push(`Messages on screen: ${obs.toasts.join(' | ')}`)
    if (obs.errors.length) parts.push(`Error messages: ${obs.errors.join(' | ')}`)
    if (obs.consoleErrors?.length) {
      parts.push(`Browser console errors: ${obs.consoleErrors.slice(0, 3).join(' | ')}`)
    }

    // Goal progress
    parts.push('')
    parts.push(`GOAL PROGRESS: ${this.ledger.completedOutcomes.length}/${this.ledger.requiredOutcomes.length} outcomes done`)
    const remaining = this.getRemainingOutcomes()
    if (remaining.length) parts.push(`  Still need: ${remaining.join(', ')}`)

    return parts.filter(Boolean).join('\n')
  }

  private buildPrompt(): string {
    const history = this.recentHistory.join('\n\n')
    return `--- CONVERSATION HISTORY ---\n\n${history}\n\nWhat do you do next? RESPOND WITH ONLY A JSON OBJECT.`
  }

  private trimHistory() {
    while (this.recentHistory.length > this.maxHistoryLines) {
      this.recentHistory.shift()
    }
  }

  /**
   * Call Claude CLI asynchronously using spawn.
   */
  private callClaude(prompt: string): Promise<string> {
    const combinedPrompt = `${this.systemPrompt}\n\n---\n\n${prompt}`
    const toolsFlag = this.config.useVision
      ? '--allowedTools "Read"'
      : '--tools ""'
    const cmd = `claude -p --output-format json --model ${this.config.model} ${toolsFlag}`

    return this.spawnClaudeAsync(cmd, combinedPrompt, this.config.timeout || 600_000)
  }

  /** Lightweight Claude call for critic */
  private callClaudeLightweight(prompt: string): Promise<string> {
    const cmd = `claude -p --output-format json --model haiku --tools ""`
    return this.spawnClaudeAsync(cmd, prompt, 60_000)
  }

  /** Async spawn wrapper */
  private spawnClaudeAsync(cmd: string, input: string, timeoutMs: number): Promise<string> {
    return new Promise((resolve, reject) => {
      const child = spawn(cmd, {
        shell: true,
        windowsHide: true,
        env: { ...process.env },
        stdio: ['pipe', 'pipe', 'pipe'],
      })

      let stdout = ''
      let stderr = ''
      let killed = false

      const timer = setTimeout(async () => {
        killed = true
        // Windows-safe kill
        if (process.platform === 'win32' && child.pid) {
          try {
            const { execSync } = require('child_process')
            execSync(`taskkill /pid ${child.pid} /T /F`, { windowsHide: true, stdio: 'ignore' })
          } catch { /* process may already be dead */ }
        } else {
          child.kill('SIGTERM')
          setTimeout(() => {
            try { child.kill('SIGKILL') } catch { /* already dead */ }
          }, 5000)
        }
        reject(new Error(`Claude CLI timed out after ${timeoutMs / 1000}s`))
      }, timeoutMs)

      child.stdout?.on('data', (data: Buffer) => {
        stdout += data.toString()
        if (stdout.length > 2 * 1024 * 1024) {
          killed = true
          child.kill('SIGTERM')
          clearTimeout(timer)
          reject(new Error('Claude CLI output exceeded 2MB'))
        }
      })

      child.stderr?.on('data', (data: Buffer) => {
        stderr += data.toString()
      })

      child.stdin?.write(input)
      child.stdin?.end()

      child.on('close', (code) => {
        clearTimeout(timer)
        if (killed) return

        if (code !== 0) {
          reject(new Error(`Claude CLI exit ${code}: ${stderr.slice(0, 300)}`))
          return
        }

        const output = stdout.trim()
        if (!output) {
          reject(new Error('Claude CLI returned empty output'))
          return
        }

        try {
          const cliResult = JSON.parse(output)
          if (cliResult.is_error) {
            reject(new Error(`Claude CLI error: ${cliResult.result}`))
            return
          }
          resolve(cliResult.result || '')
        } catch (err: any) {
          reject(new Error(`Failed to parse Claude CLI output: ${err.message}\n${output.slice(0, 200)}`))
        }
      })

      child.on('error', (err) => {
        clearTimeout(timer)
        if (!killed) reject(new Error(`Claude CLI spawn error: ${err.message}`))
      })
    })
  }

  private parseAction(llmResponse: string): AgentAction {
    let cleaned = llmResponse.trim()
    cleaned = cleaned.replace(/^```(?:json)?\s*/i, '').replace(/\s*```$/i, '')

    try {
      const parsed = JSON.parse(cleaned)
      if (!parsed.type) throw new Error('Missing "type" field')
      if (!parsed.reasoning) parsed.reasoning = 'No reasoning provided'

      if (parsed.progress) this.markOutcomesFromText(String(parsed.progress))
      if (parsed.reasoning) this.markOutcomesFromText(String(parsed.reasoning))

      return parsed as AgentAction
    } catch (err: any) {
      const jsonMatch = cleaned.match(/\{[\s\S]*\}/)
      if (jsonMatch) {
        try {
          const parsed = JSON.parse(jsonMatch[0])
          if (!parsed.type) throw new Error('Missing "type"')
          return parsed as AgentAction
        } catch { /* fall through */ }
      }
      throw new Error(`Failed to parse action JSON: ${err.message}\nResponse: ${cleaned.slice(0, 200)}`)
    }
  }

  // ─── Element Shuffling ──────────────────────────────────────────────

  private async decideWithRetries(prompt: string, observation: PageObservation): Promise<AgentAction> {
    if (this.shouldUseConsensus()) {
      const consensus = await this.tryConsensusSampling(prompt, observation)
      if (consensus) return consensus
    }

    let fallbackError = 'Unknown model failure'
    for (let attempt = 0; attempt < this.maxRetries; attempt++) {
      try {
        const response = await this.callClaude(prompt)
        return this.parseAction(response)
      } catch (err: any) {
        fallbackError = err.message || fallbackError
        if (this.config.debug) {
          console.warn(`[AgentBrain] Claude attempt ${attempt + 1} failed: ${fallbackError.slice(0, 150)}`)
        }
      }
    }

    return {
      type: 'done',
      reasoning: `Claude CLI failed after ${this.maxRetries} attempts: ${fallbackError.slice(0, 200)}`,
      progress: 'none',
      blocker: fallbackError.slice(0, 120),
      confidence: 0.95,
    }
  }

  private shouldUseConsensus(): boolean {
    const failures = this.actionHistory.slice(-4).filter(a => a.result === 'failed').length
    return this.ledger.stuckScore >= 4 || this.sameScreenCount >= 3 || failures >= 2
  }

  private async tryConsensusSampling(prompt: string, observation: PageObservation): Promise<AgentAction | null> {
    const samples = this.ledger.stuckScore >= 6 ? 3 : 2
    const candidates: AgentAction[] = []

    for (let i = 0; i < samples; i++) {
      try {
        const response = await this.callClaude(`${prompt}\n\nIndependent candidate ${i + 1}/${samples}. Re-evaluate from scratch.`)
        candidates.push(this.parseAction(response))
      } catch {
        // Keep sampling candidates.
      }
    }

    if (candidates.length === 0) return null

    let best = candidates[0]
    let bestScore = this.scoreCandidate(best, observation)
    for (let i = 1; i < candidates.length; i++) {
      const score = this.scoreCandidate(candidates[i], observation)
      if (score > bestScore) {
        best = candidates[i]
        bestScore = score
      }
    }
    return best
  }

  private scoreCandidate(action: AgentAction, observation: PageObservation): number {
    let score = typeof action.confidence === 'number' ? action.confidence * 2 : 1

    if (action.expectedSignal) score += 0.6
    if (action.type === 'done') {
      const remaining = this.getRemainingOutcomes()
      score += remaining.length === 0 ? 2 : -4
    }

    const signature = this.buildActionSignature(action)
    const repeats = this.actionSignatures.slice(-6).filter(s => s === signature).length
    score -= repeats * 1.0

    const key = this.buildTargetKey(action.target)
    if (key) {
      score -= (this.targetFailureCount.get(key) || 0) * 0.8
      if ((this.targetUseCount.get(key) || 0) === 0) score += 0.5
    }

    if (action.target) {
      score += this.isTargetPresent(action.target, observation) ? 1.3 : -1.5
    }

    return score
  }

  private normalizeAction(action: AgentAction, observation: PageObservation): AgentAction {
    const normalized: AgentAction = {
      ...action,
      type: (action.type || 'wait') as any,
      reasoning: action.reasoning?.trim() || 'No reasoning provided',
      progress: action.progress?.trim() || 'none',
      blocker: action.blocker?.trim() || 'none',
      confidence: typeof action.confidence === 'number' ? Math.max(0, Math.min(1, action.confidence)) : 0.6,
    }

    if (normalized.type === ('read' as any)) {
      normalized.type = 'screenshot'
    }

    if (!VALID_ACTIONS.has(normalized.type)) {
      return this.buildWaitFallback(`Invalid action type received: ${normalized.type}`)
    }

    if (!normalized.expectedSignal) {
      normalized.expectedSignal = this.inferExpectedSignal(normalized)
    }

    if (normalized.type === 'done') {
      return this.enforceDoneGate(normalized, observation)
    }

    if (['click', 'type', 'select', 'upload', 'hover', 'drag'].includes(normalized.type) && !normalized.target) {
      return this.buildWaitFallback(`Missing target for ${normalized.type}`)
    }

    if (['type', 'select', 'upload'].includes(normalized.type) && !normalized.value) {
      return this.buildWaitFallback(`Missing value for ${normalized.type}`)
    }

    if (normalized.type === 'verify' && !normalized.assertion) {
      const keyword = this.guessEvidenceKeyword(this.getRemainingOutcomes(), observation)
      if (keyword) {
        normalized.assertion = {
          check: 'text_contains',
          expected: keyword,
        }
      } else {
        return this.buildWaitFallback('Missing assertion for verify action')
      }
    }

    return normalized
  }

  private enforceDoneGate(action: AgentAction, observation: PageObservation): AgentAction {
    this.markOutcomesFromObservation(observation)
    const remaining = this.getRemainingOutcomes()
    if (remaining.length === 0) return action

    const nearBudget = this.stepCount >= Math.max(5, Math.floor(this.scenarioMaxActions * 0.85))
    const isStuckIntent = /stuck|blocked|cannot|can't|give up|no progress/i.test(
      `${action.reasoning} ${action.blocker || ''}`,
    )

    if (isStuckIntent && (nearBudget || this.ledger.stuckScore >= 6)) {
      return {
        ...action,
        blocker: action.blocker && action.blocker !== 'none'
          ? action.blocker
          : `Missing evidence for: ${remaining.slice(0, 2).join('; ')}`,
      }
    }

    const keyword = this.guessEvidenceKeyword(remaining, observation) || remaining[0]
    return {
      type: 'verify',
      reasoning: `Need visible proof before done for: ${remaining[0]}`,
      progress: action.progress || 'not complete',
      blocker: `Missing visible evidence for ${remaining[0]}`,
      expectedSignal: keyword,
      confidence: 0.55,
      assertion: {
        check: 'text_contains',
        expected: keyword,
      },
    }
  }

  private shouldDiversify(action: AgentAction): boolean {
    if (action.type === 'done') return false
    if (this.ledger.stuckScore < 3) return false
    const signature = this.buildActionSignature(action)
    return this.actionSignatures.slice(-6).filter(s => s === signature).length >= 2
  }

  private buildDiversifiedAction(observation: PageObservation, original: AgentAction): AgentAction {
    const candidate = observation.interactiveElements.find(el => {
      if (!el.name || el.disabled) return false
      if (!['button', 'link', 'tab', 'menuitem'].includes(el.role)) return false
      const key = `${el.role}:${el.name.trim().toLowerCase()}`
      return (this.targetUseCount.get(key) || 0) === 0
    })

    if (candidate) {
      return {
        type: 'click',
        reasoning: `Loop prevention: try untried ${candidate.role}`,
        progress: 'none',
        blocker: `repeating ${original.type} pattern`,
        confidence: 0.6,
        expectedSignal: `UI changes after clicking ${candidate.name}`,
        target: {
          role: candidate.role,
          name: candidate.name,
        },
      }
    }

    return {
      type: 'scroll',
      reasoning: 'Loop prevention: discover new below-the-fold elements',
      progress: 'none',
      blocker: `repeating ${original.type} pattern`,
      confidence: 0.5,
      expectedSignal: 'new interactive elements appear',
      direction: 'down',
      amount: 450,
    }
  }

  private buildWaitFallback(reason: string): AgentAction {
    return {
      type: 'wait',
      reasoning: reason,
      progress: 'none',
      blocker: reason,
      confidence: 0.3,
      expectedSignal: 'A clearer state appears',
    }
  }

  private inferExpectedSignal(action: AgentAction): string {
    switch (action.type) {
      case 'click':
        return 'dialog opens, page changes, or state updates'
      case 'type':
        return 'input value visibly updates'
      case 'select':
        return 'selected option appears in control'
      case 'navigate':
        return 'URL changes to target page'
      case 'verify':
        return 'assertion evaluates true'
      case 'wait':
        return 'loading resolves or result appears'
      case 'api_call':
        return 'API returns successful status'
      case 'done':
        return 'all required outcomes are visible'
      default:
        return 'observable UI feedback appears'
    }
  }

  private buildActionSignature(action: AgentAction): string {
    const target = action.target
      ? [
          action.target.role || '',
          action.target.name || '',
          action.target.label || '',
          action.target.text || '',
          action.target.placeholder || '',
          action.target.testId || '',
        ].join('|')
      : ''

    return [
      action.type,
      target,
      action.value || '',
      action.url || '',
      action.key || '',
      action.waitFor || '',
    ].join('::').toLowerCase().slice(0, 220)
  }

  private buildTargetKey(target?: AgentAction['target']): string | undefined {
    if (!target) return undefined
    const key = [
      target.role || '',
      target.name || '',
      target.label || '',
      target.text || '',
      target.placeholder || '',
      target.testId || '',
      target.css || '',
    ].join(':').trim().toLowerCase()
    return key || undefined
  }

  private getRemainingOutcomes(): string[] {
    return this.ledger.requiredOutcomes.filter(outcome => !this.ledger.completedOutcomes.includes(outcome))
  }

  private markOutcomesFromObservation(observation: PageObservation) {
    const corpus = [
      observation.url,
      observation.title,
      observation.heading || '',
      observation.toasts.join(' '),
      observation.errors.join(' '),
      (observation.semanticHints || []).join(' '),
      observation.interactiveElements.map(el => el.name).join(' '),
    ].join(' ')
    this.markOutcomesFromText(corpus)
  }

  private markOutcomesFromText(text: string) {
    const normalized = this.normalizeText(text)
    if (!normalized) return

    for (const outcome of this.ledger.requiredOutcomes) {
      if (this.ledger.completedOutcomes.includes(outcome)) continue

      const keywords = this.extractKeywords(outcome)
      if (keywords.length === 0) continue

      const matchCount = keywords.filter(word => normalized.includes(word)).length
      const threshold = Math.max(1, Math.min(3, Math.ceil(keywords.length * 0.45)))
      if (matchCount >= threshold) {
        this.ledger.completedOutcomes.push(outcome)
        this.ledger.stuckScore = Math.max(0, this.ledger.stuckScore - 1)
      }
    }
  }

  private extractKeywords(text: string): string[] {
    return Array.from(new Set(
      this.normalizeText(text)
        .split(' ')
        .filter(word => word.length >= 4 && !STOPWORDS.has(word)),
    ))
  }

  private normalizeText(text: string): string {
    return String(text || '')
      .toLowerCase()
      .replace(/[^a-z0-9\s]/g, ' ')
      .replace(/\s+/g, ' ')
      .trim()
  }

  private guessEvidenceKeyword(remainingOutcomes: string[], observation: PageObservation): string | undefined {
    const source = [
      ...remainingOutcomes,
      observation.heading || '',
      ...observation.toasts,
      ...observation.errors,
      ...observation.interactiveElements.map(el => el.name),
    ].join(' ')
    const keywords = this.extractKeywords(source)
    return keywords.find(word => word.length >= 5)
  }

  private isLikelyProgressAction(action: AgentAction): boolean {
    if (['navigate', 'type', 'select', 'upload', 'api_call', 'verify'].includes(action.type)) {
      return true
    }

    if (action.type === 'click' && action.target?.name) {
      const name = action.target.name.toLowerCase()
      return ['save', 'submit', 'create', 'add', 'run', 'generate', 'confirm', 'next', 'continue', 'apply']
        .some(token => name.includes(token))
    }

    return false
  }

  private isTargetPresent(target: NonNullable<AgentAction['target']>, observation: PageObservation): boolean {
    const normalizedName = (target.name || target.label || target.text || target.placeholder || '').trim().toLowerCase()

    return observation.interactiveElements.some(el => {
      const roleMatches = !target.role || el.role.toLowerCase() === target.role.toLowerCase()
      if (!roleMatches) return false

      if (!normalizedName) return true
      const elementName = el.name.trim().toLowerCase()
      return elementName === normalizedName
        || elementName.includes(normalizedName)
        || normalizedName.includes(elementName)
    })
  }

  private shuffleArray<T>(array: T[]): T[] {
    for (let i = array.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [array[i], array[j]] = [array[j], array[i]]
    }
    return array
  }

  // ─── Action Caching ─────────────────────────────────────────────────

  private getCachedHint(scenarioId: string): string {
    const cached = this.actionCache.find(c => c.scenarioId === scenarioId && c.success)
    if (!cached) return ''
    const steps = cached.actions.slice(0, 5).map((a, i) =>
      `  ${i + 1}. ${a.type} ${a.target?.name ? `"${a.target.name}"` : ''}${a.value ? ` = "${a.value}"` : ''}`
    ).join('\n')
    return `\nPREVIOUS SUCCESSFUL APPROACH (hint, not mandatory):\n${steps}\n`
  }

  private loadActionCache() {
    const cachePath = path.join(this.config.learningDir!, 'action-cache.json')
    try {
      if (fs.existsSync(cachePath)) {
        this.actionCache = JSON.parse(fs.readFileSync(cachePath, 'utf-8'))
      }
    } catch { /* start fresh */ }
  }

  private saveActionCache() {
    const cachePath = path.join(this.config.learningDir!, 'action-cache.json')
    const toSave = this.actionCache.slice(-20)
    fs.writeFileSync(cachePath, JSON.stringify(toSave, null, 2))
  }

  // ─── Cross-Session Learning ─────────────────────────────────────────

  private getLessonsForScenario(scenarioId: string): string {
    const relevant = this.lessons.filter(l => l.scenarioId === scenarioId)
    if (!relevant.length) return ''
    const text = relevant.slice(-3).map(l => `  - ${l.lesson}`).join('\n')
    return `\nLESSONS FROM PREVIOUS RUNS:\n${text}\n`
  }

  private extractLesson(failedActions: ActionLogEntry[], confusedSteps: PerceptionEntry[]): string | null {
    const parts: string[] = []

    const failedTargets = failedActions.map(a => a.action.target?.name || a.action.target?.label).filter(Boolean)
    if (failedTargets.length > 0) {
      parts.push(`Elements that didn't work: ${Array.from(new Set(failedTargets)).join(', ')}`)
    }

    const confusionReasons = confusedSteps.flatMap(p => p.confusionSignals).filter(Boolean)
    if (confusionReasons.length > 0) {
      parts.push(`Confusion: ${Array.from(new Set(confusionReasons)).slice(0, 2).join('; ')}`)
    }

    return parts.length > 0 ? parts.join('. ') : null
  }

  private loadLessons() {
    const lessonsPath = path.join(this.config.learningDir!, 'lessons.json')
    try {
      if (fs.existsSync(lessonsPath)) {
        this.lessons = JSON.parse(fs.readFileSync(lessonsPath, 'utf-8'))
      }
    } catch { /* start fresh */ }
  }

  private saveLessons() {
    const lessonsPath = path.join(this.config.learningDir!, 'lessons.json')
    const toSave = this.lessons.slice(-50)
    fs.writeFileSync(lessonsPath, JSON.stringify(toSave, null, 2))
  }
}
