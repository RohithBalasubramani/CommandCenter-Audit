/**
 * Layer 2 Client — Frontend interface to the AI Orchestrator
 *
 * This module handles communication between Layer 1 (Voice I/O) and
 * Layer 2 (AI + RAG) backend.
 *
 * Flow:
 * 1. Layer 1 sends transcript → Layer 2 orchestrate endpoint
 * 2. Layer 2 returns filler + processes in background
 * 3. Layer 2 returns intelligent response + layout JSON
 * 4. Layer 1 speaks the response, Layer 3 updates widgets
 */

import { config } from "../config";

// ============================================================
// Types
// ============================================================

export interface Layer2Intent {
  type: "query" | "action" | "greeting" | "clarification";
  domains: string[];
  entities: Record<string, unknown>;
  confidence: number;
}

export interface Layer2RAGResult {
  domain: string;
  success: boolean;
  data: Record<string, unknown>;
  error?: string;
  execution_time_ms: number;
}

export interface Layer2WidgetCommand {
  id: string;
  relevance: number;
  size: "hero" | "expanded" | "normal" | "compact" | "hidden";
  position: string;
  data: unknown;
}

export interface Layer2LayoutJSON {
  widgets: Layer2WidgetCommand[];
  transitions: Record<string, string>;
}

export interface Layer2Response {
  voice_response: string;
  filler_text: string;
  layout_json: Layer2LayoutJSON;
  context_update: Record<string, unknown>;
  intent: Layer2Intent | null;
  rag_results: Layer2RAGResult[];
  processing_time_ms: number;
}

export interface ProactiveTrigger {
  has_trigger: boolean;
  trigger_text: string | null;
}

// ============================================================
// API Client
// ============================================================

const API_BASE = config.api.baseUrl;

/**
 * Send transcript to Layer 2 for processing.
 *
 * This is the main entry point for Layer 1 → Layer 2 communication.
 */
export async function orchestrate(
  transcript: string,
  sessionId?: string,
  context?: Record<string, unknown>
): Promise<Layer2Response> {
  const response = await fetch(`${API_BASE}/api/layer2/orchestrate/`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      transcript,
      session_id: sessionId,
      context: context || {},
    }),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.error || `Layer 2 error: ${response.status}`);
  }

  return response.json();
}

/**
 * Get filler text to speak while waiting for full response.
 *
 * Call this immediately when user finishes speaking,
 * then call orchestrate() for the full response.
 */
export async function getFiller(
  intentType: string = "query",
  domains: string[] = ["industrial"]
): Promise<string> {
  const response = await fetch(`${API_BASE}/api/layer2/filler/`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      intent_type: intentType,
      domains,
    }),
  });

  if (!response.ok) {
    // Return default filler on error
    return "One moment...";
  }

  const data = await response.json();
  return data.filler_text || "Let me check that for you.";
}

/**
 * Check for proactive triggers from system context.
 *
 * Layer 1 can call this periodically or when system state changes
 * to get proactive questions to ask the user.
 */
export async function checkProactiveTrigger(
  systemContext: Record<string, unknown>
): Promise<ProactiveTrigger> {
  const response = await fetch(`${API_BASE}/api/layer2/proactive/`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      system_context: systemContext,
    }),
  });

  if (!response.ok) {
    return { has_trigger: false, trigger_text: null };
  }

  return response.json();
}

// ============================================================
// Layer 2 Service Class
// ============================================================

/**
 * Layer2Service — Manages communication with the AI orchestrator.
 *
 * Provides a higher-level interface for Layer 1 integration.
 */
export class Layer2Service {
  private context: Record<string, unknown> = {};
  private sessionId: string | null = null;
  private onFillerCallback: ((filler: string) => void) | null = null;
  private onResponseCallback: ((response: Layer2Response) => void) | null =
    null;
  private onLayoutCallback: ((layout: Layer2LayoutJSON) => void) | null = null;

  /**
   * Set the session ID for transcript tracking.
   */
  setSessionId(sessionId: string) {
    this.sessionId = sessionId;
  }

  /**
   * Update the conversation context.
   */
  updateContext(update: Record<string, unknown>) {
    this.context = { ...this.context, ...update };
  }

  /**
   * Register callback for filler text (speak while processing).
   */
  onFiller(callback: (filler: string) => void) {
    this.onFillerCallback = callback;
  }

  /**
   * Register callback for voice response (speak the answer).
   */
  onResponse(callback: (response: Layer2Response) => void) {
    this.onResponseCallback = callback;
  }

  /**
   * Register callback for layout updates (send to Blob).
   */
  onLayout(callback: (layout: Layer2LayoutJSON) => void) {
    this.onLayoutCallback = callback;
  }

  /**
   * Process a transcript through Layer 2.
   *
   * This method:
   * 1. Immediately gets and returns filler text
   * 2. Sends transcript to orchestrator
   * 3. Calls callbacks when response is ready
   */
  async processTranscript(transcript: string): Promise<Layer2Response> {
    console.info("[Layer2] Processing transcript:", transcript);

    // Quick intent detection for filler
    const intentType = this.detectIntentType(transcript);
    const domains = this.detectDomains(transcript);

    // Get filler text immediately (non-blocking)
    getFiller(intentType, domains)
      .then((filler) => {
        if (this.onFillerCallback && filler) {
          console.info("[Layer2] Filler:", filler);
          this.onFillerCallback(filler);
        }
      })
      .catch((err) => {
        console.warn("[Layer2] Failed to get filler:", err);
      });

    // Process through orchestrator
    try {
      const response = await orchestrate(
        transcript,
        this.sessionId || undefined,
        this.context
      );

      console.info("[Layer2] Response:", response);

      // Update context
      if (response.context_update) {
        this.updateContext(response.context_update);
      }

      // Call callbacks
      if (this.onResponseCallback) {
        this.onResponseCallback(response);
      }

      if (this.onLayoutCallback && response.layout_json) {
        this.onLayoutCallback(response.layout_json);
      }

      return response;
    } catch (error) {
      console.error("[Layer2] Orchestration failed:", error);
      throw error;
    }
  }

  /**
   * Quick intent type detection (for filler selection).
   */
  private detectIntentType(text: string): string {
    const lower = text.toLowerCase();

    if (/\b(hello|hi|hey|good morning|good afternoon)\b/.test(lower)) {
      return "greeting";
    }

    if (/\b(start|stop|turn|set|change|update)\b/.test(lower)) {
      return "action";
    }

    return "query";
  }

  /**
   * Quick domain detection (for filler selection).
   */
  private detectDomains(text: string): string[] {
    const lower = text.toLowerCase();
    const domains: string[] = [];

    if (/\b(pump|motor|temperature|voltage|device|machine)\b/.test(lower)) {
      domains.push("industrial");
    }

    if (/\b(alert|alarm|warning|error)\b/.test(lower)) {
      domains.push("alerts");
    }

    if (/\b(inventory|stock|order|supplier)\b/.test(lower)) {
      domains.push("supply");
    }

    if (/\b(employee|staff|shift|schedule)\b/.test(lower)) {
      domains.push("people");
    }

    if (/\b(task|project|deadline)\b/.test(lower)) {
      domains.push("tasks");
    }

    return domains.length > 0 ? domains : ["industrial"];
  }

  /**
   * Check for proactive triggers and return trigger text if any.
   */
  async checkProactive(
    systemContext: Record<string, unknown>
  ): Promise<string | null> {
    const trigger = await checkProactiveTrigger(systemContext);
    return trigger.has_trigger ? trigger.trigger_text : null;
  }
}

// Singleton instance
let _layer2Service: Layer2Service | null = null;

export function getLayer2Service(): Layer2Service {
  if (!_layer2Service) {
    _layer2Service = new Layer2Service();
  }
  return _layer2Service;
}
