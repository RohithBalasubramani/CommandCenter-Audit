import { RAGPipeline } from "../types";
import { RAGQuery, RAGResult } from "@/types";

/**
 * Industrial RAG Pipeline — Layer 2B
 *
 * Queries LoggerDeploy for:
 * - Device metrics (voltage, temperature, pressure, etc.)
 * - Device status (online/offline/warning)
 * - Alert history
 *
 * Data source: LoggerDeploy → PostgreSQL
 * Tables: metrics, devices, device_status
 */
export class IndustrialRAGPipeline implements RAGPipeline {
  domain = "industrial" as const;
  enabled = true;

  private apiBaseUrl: string;

  constructor(apiBaseUrl?: string) {
    this.apiBaseUrl =
      apiBaseUrl ||
      process.env.NEXT_PUBLIC_API_URL ||
      "http://localhost:8000";
  }

  async execute(query: RAGQuery): Promise<RAGResult> {
    try {
      const response = await fetch(
        `${this.apiBaseUrl}/api/layer2/rag/industrial/`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            query: query.query,
            context: query.context || {},
          }),
        }
      );

      if (!response.ok) {
        throw new Error(`Industrial RAG returned ${response.status}`);
      }

      const data = await response.json();

      return {
        domain: "industrial",
        rawData: data,
        timestamp: Date.now(),
      };
    } catch (error) {
      return {
        domain: "industrial",
        rawData: {},
        timestamp: Date.now(),
        error:
          error instanceof Error
            ? error.message
            : "Industrial RAG query failed",
      };
    }
  }

  async healthCheck(): Promise<boolean> {
    try {
      const response = await fetch(
        `${this.apiBaseUrl}/api/layer2/rag/industrial/health/`
      );
      return response.ok;
    } catch {
      return false;
    }
  }
}
