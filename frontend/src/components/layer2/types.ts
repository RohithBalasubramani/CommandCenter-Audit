import { RAGDomain, RAGQuery, RAGResult } from "@/types";

/**
 * RAGPipeline — Interface that all RAG pipelines must implement.
 * Each pipeline handles one domain's database queries.
 *
 * To add a new pipeline:
 * 1. Create a new file in ./pipelines/ (e.g., supply.ts)
 * 2. Implement the RAGPipeline interface
 * 3. Register it in the pipeline registry (orchestrator.ts)
 */
export interface RAGPipeline {
  domain: RAGDomain;
  enabled: boolean;

  /** Execute a query against this domain's data source */
  execute(query: RAGQuery): Promise<RAGResult>;

  /** Health check — can this pipeline reach its data source? */
  healthCheck(): Promise<boolean>;
}

/** Registry entry for a RAG pipeline */
export interface PipelineRegistryEntry {
  pipeline: RAGPipeline;
  priority: number;
}
