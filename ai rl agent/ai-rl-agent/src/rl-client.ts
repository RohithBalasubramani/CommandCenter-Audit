/**
 * RL API Client — HTTP client for Command Center RL backend endpoints.
 *
 * Provides typed access to:
 * - /api/layer2/orchestrate/    — Send queries, get layout + widgets
 * - /api/layer2/feedback/       — Submit ratings, interactions, corrections
 * - /api/layer2/approve-training/ — Approve LoRA training
 * - /api/layer2/rl-status/      — RL system status
 * - /api/layer2/rag/industrial/health/ — RAG health check
 */

// ─── Types ──────────────────────────────────────────────────────────

export interface OrchestrateRequest {
  transcript: string
  session_id?: string
  context?: Record<string, any>
  user_id?: string
}

export interface WidgetData {
  scenario: string
  size?: string
  why?: string
  fixture?: string
  data?: Record<string, any>
  heightHint?: number
}

export interface OrchestrateResponse {
  voice_response: string
  filler_text: string
  layout_json: {
    heading?: string
    widgets: WidgetData[]
  }
  context_update: Record<string, any>
  intent: {
    domain?: string
    action?: string
    entities?: string[]
    confidence?: number
  }
  query_id: string
  processing_time_ms: number
}

export interface FeedbackRequest {
  query_id: string
  rating: 'up' | 'down'
  interactions?: Array<{
    widget_index: number
    action: string
    duration_ms: number
  }>
  correction?: string
}

export interface FeedbackResponse {
  status: string
  updated: boolean
}

export interface RLStatus {
  running: boolean
  buffer: {
    total: number
    rated: number
    unrated: number
    positive: number
    negative: number
  }
  trainer: {
    tier1_steps: number
    tier2_runs: number
    last_train_time?: string
    dpo_pairs_ready: number
    scorer_loss?: number
  }
  config: {
    train_widget_selector: boolean
    train_fixture_selector: boolean
    train_interval: number
    min_batch_size: number
  }
}

export interface ApproveTrainingResponse {
  status: string
  file: string
}

export interface HealthResponse {
  status: string
  [key: string]: any
}

export interface RLClientConfig {
  apiBaseUrl: string
  feedbackApiKey?: string
  timeoutMs?: number
}

// ─── Client ─────────────────────────────────────────────────────────

export class RLClient {
  private baseUrl: string
  private feedbackApiKey: string
  private timeoutMs: number

  constructor(config: RLClientConfig) {
    this.baseUrl = config.apiBaseUrl.replace(/\/$/, '')
    this.feedbackApiKey = config.feedbackApiKey || ''
    this.timeoutMs = config.timeoutMs || 60_000
  }

  private async request<T>(
    method: 'GET' | 'POST',
    path: string,
    body?: Record<string, any>,
    extraHeaders?: Record<string, string>,
  ): Promise<T> {
    const url = `${this.baseUrl}${path}`
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...extraHeaders,
    }

    const controller = new AbortController()
    const timeout = setTimeout(() => controller.abort(), this.timeoutMs)

    try {
      const resp = await fetch(url, {
        method,
        headers,
        body: body ? JSON.stringify(body) : undefined,
        signal: controller.signal,
      })

      clearTimeout(timeout)

      if (!resp.ok) {
        const errBody = await resp.text().catch(() => '')
        throw new Error(`HTTP ${resp.status} ${resp.statusText}: ${errBody}`)
      }

      return (await resp.json()) as T
    } catch (err: any) {
      clearTimeout(timeout)
      if (err.name === 'AbortError') {
        throw new Error(`Request to ${path} timed out after ${this.timeoutMs}ms`)
      }
      throw err
    }
  }

  /**
   * Send a query to the orchestrator and get the layout response.
   */
  async orchestrate(
    transcript: string,
    sessionId?: string,
    context?: Record<string, any>,
    userId?: string,
  ): Promise<OrchestrateResponse> {
    const body: OrchestrateRequest = {
      transcript,
      session_id: sessionId,
      context: context || {},
      user_id: userId || 'rl-agent',
    }
    return this.request<OrchestrateResponse>('POST', '/api/layer2/orchestrate/', body)
  }

  /**
   * Submit feedback for a query response.
   * Retries with exponential backoff on 429 (rate-limited) responses.
   */
  async submitFeedback(feedback: FeedbackRequest, maxRetries = 3): Promise<FeedbackResponse> {
    const headers: Record<string, string> = {}
    if (this.feedbackApiKey) {
      headers['X-Feedback-Key'] = this.feedbackApiKey
    }

    for (let attempt = 0; attempt <= maxRetries; attempt++) {
      try {
        return await this.request<FeedbackResponse>('POST', '/api/layer2/feedback/', feedback, headers)
      } catch (err: any) {
        const is429 = err.message?.includes('429')
        if (is429 && attempt < maxRetries) {
          // Exponential backoff: 4s, 8s, 16s
          const delay = Math.pow(2, attempt + 2) * 1000
          await new Promise(resolve => setTimeout(resolve, delay))
          continue
        }
        throw err
      }
    }

    throw new Error('submitFeedback: exhausted retries')
  }

  /**
   * Approve pending LoRA training.
   */
  async approveTraining(): Promise<ApproveTrainingResponse> {
    return this.request<ApproveTrainingResponse>('POST', '/api/layer2/approve-training/')
  }

  /**
   * Get current RL system status.
   */
  async getStatus(): Promise<RLStatus> {
    return this.request<RLStatus>('GET', '/api/layer2/rl-status/')
  }

  /**
   * Check RAG pipeline health.
   */
  async getHealth(): Promise<HealthResponse> {
    return this.request<HealthResponse>('GET', '/api/layer2/rag/industrial/health/')
  }

  /**
   * Check if both frontend and backend are reachable.
   */
  async checkServers(frontendUrl: string): Promise<{ frontend: boolean; backend: boolean }> {
    const check = async (url: string): Promise<boolean> => {
      try {
        const controller = new AbortController()
        const timeout = setTimeout(() => controller.abort(), 5000)
        const resp = await fetch(url, { signal: controller.signal })
        clearTimeout(timeout)
        return resp.status < 500
      } catch {
        return false
      }
    }

    const [frontend, backend] = await Promise.all([
      check(frontendUrl),
      check(`${this.baseUrl}/api/layer2/rl-status/`),
    ])

    return { frontend, backend }
  }
}
