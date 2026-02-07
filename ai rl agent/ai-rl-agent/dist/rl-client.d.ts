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
export interface OrchestrateRequest {
    transcript: string;
    session_id?: string;
    context?: Record<string, any>;
    user_id?: string;
}
export interface WidgetData {
    scenario: string;
    size?: string;
    why?: string;
    fixture?: string;
    data?: Record<string, any>;
    heightHint?: number;
}
export interface OrchestrateResponse {
    voice_response: string;
    filler_text: string;
    layout_json: {
        heading?: string;
        widgets: WidgetData[];
    };
    context_update: Record<string, any>;
    intent: {
        domain?: string;
        action?: string;
        entities?: string[];
        confidence?: number;
    };
    query_id: string;
    processing_time_ms: number;
}
export interface FeedbackRequest {
    query_id: string;
    rating: 'up' | 'down';
    interactions?: Array<{
        widget_index: number;
        action: string;
        duration_ms: number;
    }>;
    correction?: string;
}
export interface FeedbackResponse {
    status: string;
    updated: boolean;
}
export interface RLStatus {
    running: boolean;
    buffer: {
        total: number;
        rated: number;
        unrated: number;
        positive: number;
        negative: number;
    };
    trainer: {
        tier1_steps: number;
        tier2_runs: number;
        last_train_time?: string;
        dpo_pairs_ready: number;
        scorer_loss?: number;
    };
    config: {
        train_widget_selector: boolean;
        train_fixture_selector: boolean;
        train_interval: number;
        min_batch_size: number;
    };
}
export interface ApproveTrainingResponse {
    status: string;
    file: string;
}
export interface HealthResponse {
    status: string;
    [key: string]: any;
}
export interface RLClientConfig {
    apiBaseUrl: string;
    feedbackApiKey?: string;
    timeoutMs?: number;
}
export declare class RLClient {
    private baseUrl;
    private feedbackApiKey;
    private timeoutMs;
    constructor(config: RLClientConfig);
    private request;
    /**
     * Send a query to the orchestrator and get the layout response.
     */
    orchestrate(transcript: string, sessionId?: string, context?: Record<string, any>, userId?: string): Promise<OrchestrateResponse>;
    /**
     * Submit feedback for a query response.
     */
    submitFeedback(feedback: FeedbackRequest): Promise<FeedbackResponse>;
    /**
     * Approve pending LoRA training.
     */
    approveTraining(): Promise<ApproveTrainingResponse>;
    /**
     * Get current RL system status.
     */
    getStatus(): Promise<RLStatus>;
    /**
     * Check RAG pipeline health.
     */
    getHealth(): Promise<HealthResponse>;
    /**
     * Check if both frontend and backend are reachable.
     */
    checkServers(frontendUrl: string): Promise<{
        frontend: boolean;
        backend: boolean;
    }>;
}
//# sourceMappingURL=rl-client.d.ts.map