import { RAGDomain, RAGQuery, RAGResult, OrchestratorOutput } from "@/types";
import { RAGPipeline, PipelineRegistryEntry } from "./types";
import { IndustrialRAGPipeline } from "./pipelines/industrial";
import { commandCenterBus } from "@/lib/events";

/**
 * Orchestrator — Layer 2A
 *
 * Lightweight intent parser that:
 * 1. Receives transcripts from Layer 1
 * 2. Identifies relevant domains
 * 3. Spawns parallel RAG pipeline queries
 * 4. Collects results for the Layout Decider (2C)
 *
 * Adding new pipelines:
 * 1. Create pipeline in ./pipelines/
 * 2. Call orchestrator.registerPipeline() with the new pipeline
 */
class Orchestrator {
  private registry: Map<RAGDomain, PipelineRegistryEntry> = new Map();

  constructor() {
    // Register the initial Industrial RAG pipeline
    this.registerPipeline(new IndustrialRAGPipeline(), 1);

    // Listen for transcripts from Layer 1
    commandCenterBus.on("TRANSCRIPT_UPDATE", (event) => {
      if (
        event.type === "TRANSCRIPT_UPDATE" &&
        event.transcript.role === "user" &&
        event.transcript.isFinal
      ) {
        this.processTranscript(event.transcript.text);
      }
    });
  }

  /** Register a new RAG pipeline */
  registerPipeline(pipeline: RAGPipeline, priority: number): void {
    this.registry.set(pipeline.domain, { pipeline, priority });
  }

  /** Remove a RAG pipeline */
  unregisterPipeline(domain: RAGDomain): void {
    this.registry.delete(domain);
  }

  /** List all registered pipelines */
  listPipelines(): { domain: RAGDomain; enabled: boolean; priority: number }[] {
    return Array.from(this.registry.entries()).map(([domain, entry]) => ({
      domain,
      enabled: entry.pipeline.enabled,
      priority: entry.priority,
    }));
  }

  /** Parse intent from transcript (lightweight — Layer 2A) */
  parseIntent(transcript: string): OrchestratorOutput {
    const lower = transcript.toLowerCase();

    // Simple keyword-based intent parsing
    // In production, this would be a lightweight model (phi-3)
    const domains: RAGDomain[] = [];
    const spawnRag: RAGQuery[] = [];
    const intents: string[] = [];

    // Industrial domain keywords
    const industrialKeywords = [
      "voltage",
      "current",
      "power",
      "temperature",
      "pressure",
      "pump",
      "motor",
      "device",
      "sensor",
      "grid",
      "meter",
      "gauge",
      "machine",
      "equipment",
      "industrial",
      "factory",
      "plant",
      "metric",
      "reading",
    ];

    // Supply domain keywords
    const supplyKeywords = [
      "inventory",
      "stock",
      "supply",
      "procurement",
      "vendor",
      "order",
      "rfq",
      "purchase",
      "material",
      "warehouse",
    ];

    // People domain keywords
    const peopleKeywords = [
      "employee",
      "staff",
      "attendance",
      "schedule",
      "leave",
      "hr",
      "people",
      "worker",
      "shift",
      "team",
    ];

    // Alerts domain keywords
    const alertKeywords = [
      "alert",
      "alarm",
      "warning",
      "notification",
      "issue",
      "problem",
      "critical",
      "fault",
      "error",
      "anomaly",
    ];

    // Tasks domain keywords
    const taskKeywords = [
      "task",
      "project",
      "milestone",
      "deadline",
      "assignment",
      "progress",
      "timeline",
      "gantt",
    ];

    if (industrialKeywords.some((kw) => lower.includes(kw))) {
      domains.push("industrial");
      intents.push("query_metric");
      spawnRag.push({ domain: "industrial", query: transcript });
    }

    if (supplyKeywords.some((kw) => lower.includes(kw))) {
      domains.push("supply");
      intents.push("query_supply");
      spawnRag.push({ domain: "supply", query: transcript });
    }

    if (peopleKeywords.some((kw) => lower.includes(kw))) {
      domains.push("people");
      intents.push("query_people");
      spawnRag.push({ domain: "people", query: transcript });
    }

    if (alertKeywords.some((kw) => lower.includes(kw))) {
      domains.push("alerts");
      intents.push("query_alerts");
      spawnRag.push({ domain: "alerts", query: transcript });
    }

    if (taskKeywords.some((kw) => lower.includes(kw))) {
      domains.push("tasks");
      intents.push("query_tasks");
      spawnRag.push({ domain: "tasks", query: transcript });
    }

    // If nothing matched, default to industrial
    if (domains.length === 0) {
      domains.push("industrial");
      intents.push("general_query");
      spawnRag.push({ domain: "industrial", query: transcript });
    }

    const allDomains: RAGDomain[] = [
      "industrial",
      "supply",
      "people",
      "tasks",
      "alerts",
    ];
    const skipDomains = allDomains.filter((d) => !domains.includes(d));

    return {
      intent: intents,
      domains,
      spawnRag,
      skipDomains,
    };
  }

  /** Execute RAG queries in parallel (Layer 2B) */
  async executeParallel(queries: RAGQuery[]): Promise<RAGResult[]> {
    const promises = queries
      .filter((q) => {
        const entry = this.registry.get(q.domain);
        return entry && entry.pipeline.enabled;
      })
      .map((q) => {
        const entry = this.registry.get(q.domain)!;
        return entry.pipeline.execute(q);
      });

    const results = await Promise.allSettled(promises);

    return results.map((r, i) => {
      if (r.status === "fulfilled") {
        return r.value;
      }
      return {
        domain: queries[i].domain,
        rawData: {},
        timestamp: Date.now(),
        error: r.reason?.message || "Pipeline execution failed",
      };
    });
  }

  /** Full pipeline: transcript → intent → parallel RAG → emit results */
  async processTranscript(transcript: string): Promise<RAGResult[]> {
    const intent = this.parseIntent(transcript);
    const results = await this.executeParallel(intent.spawnRag);

    // Emit results to the event bus for Layer 2C / Layer 3
    results.forEach((result) => {
      commandCenterBus.emit({ type: "RAG_RESULT", result });
    });

    return results;
  }
}

// Singleton orchestrator
export const orchestrator = new Orchestrator();
