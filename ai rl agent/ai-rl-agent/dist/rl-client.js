"use strict";
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
Object.defineProperty(exports, "__esModule", { value: true });
exports.RLClient = void 0;
// ─── Client ─────────────────────────────────────────────────────────
class RLClient {
    baseUrl;
    feedbackApiKey;
    timeoutMs;
    constructor(config) {
        this.baseUrl = config.apiBaseUrl.replace(/\/$/, '');
        this.feedbackApiKey = config.feedbackApiKey || '';
        this.timeoutMs = config.timeoutMs || 60_000;
    }
    async request(method, path, body, extraHeaders) {
        const url = `${this.baseUrl}${path}`;
        const headers = {
            'Content-Type': 'application/json',
            ...extraHeaders,
        };
        const controller = new AbortController();
        const timeout = setTimeout(() => controller.abort(), this.timeoutMs);
        try {
            const resp = await fetch(url, {
                method,
                headers,
                body: body ? JSON.stringify(body) : undefined,
                signal: controller.signal,
            });
            clearTimeout(timeout);
            if (!resp.ok) {
                const errBody = await resp.text().catch(() => '');
                throw new Error(`HTTP ${resp.status} ${resp.statusText}: ${errBody}`);
            }
            return (await resp.json());
        }
        catch (err) {
            clearTimeout(timeout);
            if (err.name === 'AbortError') {
                throw new Error(`Request to ${path} timed out after ${this.timeoutMs}ms`);
            }
            throw err;
        }
    }
    /**
     * Send a query to the orchestrator and get the layout response.
     */
    async orchestrate(transcript, sessionId, context, userId) {
        const body = {
            transcript,
            session_id: sessionId,
            context: context || {},
            user_id: userId || 'rl-agent',
        };
        return this.request('POST', '/api/layer2/orchestrate/', body);
    }
    /**
     * Submit feedback for a query response.
     */
    async submitFeedback(feedback) {
        const headers = {};
        if (this.feedbackApiKey) {
            headers['X-Feedback-Key'] = this.feedbackApiKey;
        }
        return this.request('POST', '/api/layer2/feedback/', feedback, headers);
    }
    /**
     * Approve pending LoRA training.
     */
    async approveTraining() {
        return this.request('POST', '/api/layer2/approve-training/');
    }
    /**
     * Get current RL system status.
     */
    async getStatus() {
        return this.request('GET', '/api/layer2/rl-status/');
    }
    /**
     * Check RAG pipeline health.
     */
    async getHealth() {
        return this.request('GET', '/api/layer2/rag/industrial/health/');
    }
    /**
     * Check if both frontend and backend are reachable.
     */
    async checkServers(frontendUrl) {
        const check = async (url) => {
            try {
                const controller = new AbortController();
                const timeout = setTimeout(() => controller.abort(), 5000);
                const resp = await fetch(url, { signal: controller.signal });
                clearTimeout(timeout);
                return resp.status < 500;
            }
            catch {
                return false;
            }
        };
        const [frontend, backend] = await Promise.all([
            check(frontendUrl),
            check(`${this.baseUrl}/api/layer2/rl-status/`),
        ]);
        return { frontend, backend };
    }
}
exports.RLClient = RLClient;
//# sourceMappingURL=rl-client.js.map