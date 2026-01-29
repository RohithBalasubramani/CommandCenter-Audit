"""
Layer 2 RAG Pipeline — Retrieval Augmented Generation for Industrial Data

This module provides:
1. Document embedding using sentence-transformers (BGE-M3 or similar)
2. Vector storage using ChromaDB
3. Retrieval and context preparation for LLM
4. LLM integration via Ollama (Qwen3/Phi-4)

Tech Stack:
- Embeddings: sentence-transformers (all-MiniLM-L6-v2 default, BGE-M3 for production)
- Vector DB: ChromaDB (local, persistent)
- LLM: Ollama API (Qwen3, Phi-4, or similar)
"""

import os
import json
import logging
from typing import Optional
from dataclasses import dataclass

# Optional imports - gracefully degrade if not installed
try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

logger = logging.getLogger(__name__)

# ============================================================
# Configuration
# ============================================================

# Embedding model - use lightweight for dev, BGE-M3 for production
EMBEDDING_MODEL = os.getenv("RAG_EMBEDDING_MODEL", "all-MiniLM-L6-v2")
# For production: "BAAI/bge-m3" or "intfloat/e5-mistral-7b-instruct"

# ChromaDB persistence directory
CHROMA_PERSIST_DIR = os.getenv("RAG_CHROMA_DIR", "./chroma_db")

# Ollama settings
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "phi4")  # or "qwen3:30b", "llama3.2"

# Collection names
EQUIPMENT_COLLECTION = "industrial_equipment"
ALERTS_COLLECTION = "industrial_alerts"
MAINTENANCE_COLLECTION = "maintenance_records"


# ============================================================
# Data Classes
# ============================================================

@dataclass
class RAGDocument:
    """Document for RAG indexing."""
    id: str
    content: str
    metadata: dict
    embedding: Optional[list] = None


@dataclass
class RAGSearchResult:
    """Search result from RAG."""
    id: str
    content: str
    metadata: dict
    score: float


@dataclass
class RAGResponse:
    """Complete RAG response with context and LLM answer."""
    query: str
    retrieved_docs: list
    context: str
    llm_response: str
    sources: list


# ============================================================
# Embedding Service
# ============================================================

class EmbeddingService:
    """Service for generating text embeddings."""

    def __init__(self, model_name: str = EMBEDDING_MODEL):
        self.model_name = model_name
        self._model = None

    @property
    def model(self):
        """Lazy load the embedding model."""
        if self._model is None:
            if not SENTENCE_TRANSFORMERS_AVAILABLE:
                raise ImportError(
                    "sentence-transformers not installed. "
                    "Run: pip install sentence-transformers"
                )
            logger.info(f"Loading embedding model: {self.model_name}")
            self._model = SentenceTransformer(self.model_name)
            logger.info("Embedding model loaded successfully")
        return self._model

    def embed(self, text: str) -> list:
        """Generate embedding for a single text."""
        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding.tolist()

    def embed_batch(self, texts: list) -> list:
        """Generate embeddings for multiple texts."""
        embeddings = self.model.encode(texts, convert_to_numpy=True)
        return embeddings.tolist()


# ============================================================
# Vector Store Service
# ============================================================

class VectorStoreService:
    """Service for vector storage and retrieval using ChromaDB."""

    def __init__(self, persist_dir: str = CHROMA_PERSIST_DIR):
        self.persist_dir = persist_dir
        self._client = None
        self._embedding_service = None

    @property
    def client(self):
        """Lazy load ChromaDB client."""
        if self._client is None:
            if not CHROMADB_AVAILABLE:
                raise ImportError(
                    "chromadb not installed. "
                    "Run: pip install chromadb"
                )
            logger.info(f"Initializing ChromaDB at: {self.persist_dir}")
            self._client = chromadb.PersistentClient(path=self.persist_dir)
            logger.info("ChromaDB initialized successfully")
        return self._client

    @property
    def embedding_service(self):
        """Get or create embedding service."""
        if self._embedding_service is None:
            self._embedding_service = EmbeddingService()
        return self._embedding_service

    def get_or_create_collection(self, name: str):
        """Get or create a collection."""
        return self.client.get_or_create_collection(
            name=name,
            metadata={"hnsw:space": "cosine"}
        )

    def add_documents(self, collection_name: str, documents: list[RAGDocument]):
        """Add documents to a collection."""
        collection = self.get_or_create_collection(collection_name)

        ids = []
        embeddings = []
        metadatas = []
        contents = []

        for doc in documents:
            ids.append(doc.id)
            contents.append(doc.content)
            metadatas.append(doc.metadata)

            # Generate embedding if not provided
            if doc.embedding:
                embeddings.append(doc.embedding)
            else:
                embeddings.append(self.embedding_service.embed(doc.content))

        collection.add(
            ids=ids,
            embeddings=embeddings,
            metadatas=metadatas,
            documents=contents,
        )

        logger.info(f"Added {len(documents)} documents to collection: {collection_name}")

    def search(
        self,
        collection_name: str,
        query: str,
        n_results: int = 5,
        filter_metadata: dict = None,
    ) -> list[RAGSearchResult]:
        """Search for similar documents."""
        collection = self.get_or_create_collection(collection_name)

        # Generate query embedding
        query_embedding = self.embedding_service.embed(query)

        # Search
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=filter_metadata,
            include=["documents", "metadatas", "distances"],
        )

        # Convert to RAGSearchResult
        search_results = []
        if results and results["ids"] and results["ids"][0]:
            for i, doc_id in enumerate(results["ids"][0]):
                search_results.append(RAGSearchResult(
                    id=doc_id,
                    content=results["documents"][0][i] if results["documents"] else "",
                    metadata=results["metadatas"][0][i] if results["metadatas"] else {},
                    score=1 - results["distances"][0][i] if results["distances"] else 0,
                ))

        return search_results

    def delete_collection(self, collection_name: str):
        """Delete a collection."""
        try:
            self.client.delete_collection(collection_name)
            logger.info(f"Deleted collection: {collection_name}")
        except Exception as e:
            logger.warning(f"Failed to delete collection {collection_name}: {e}")

    def get_collection_count(self, collection_name: str) -> int:
        """Get document count in a collection."""
        try:
            collection = self.get_or_create_collection(collection_name)
            return collection.count()
        except Exception:
            return 0


# ============================================================
# LLM Service (Ollama)
# ============================================================

class OllamaLLMService:
    """Service for LLM inference via Ollama."""

    def __init__(
        self,
        base_url: str = OLLAMA_BASE_URL,
        model: str = OLLAMA_MODEL,
    ):
        self.base_url = base_url
        self.model = model

    def generate(
        self,
        prompt: str,
        system_prompt: str = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> str:
        """Generate response from LLM."""
        if not REQUESTS_AVAILABLE:
            raise ImportError("requests not installed. Run: pip install requests")

        url = f"{self.base_url}/api/generate"

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }

        if system_prompt:
            payload["system"] = system_prompt

        try:
            response = requests.post(url, json=payload, timeout=60)
            response.raise_for_status()
            result = response.json()
            return result.get("response", "")
        except requests.exceptions.ConnectionError:
            logger.error(f"Failed to connect to Ollama at {self.base_url}")
            return "[LLM unavailable - Ollama not running]"
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            return f"[LLM error: {str(e)}]"

    def chat(
        self,
        messages: list[dict],
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> str:
        """Chat with LLM using message format."""
        if not REQUESTS_AVAILABLE:
            raise ImportError("requests not installed. Run: pip install requests")

        url = f"{self.base_url}/api/chat"

        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }

        try:
            response = requests.post(url, json=payload, timeout=60)
            response.raise_for_status()
            result = response.json()
            return result.get("message", {}).get("content", "")
        except requests.exceptions.ConnectionError:
            logger.error(f"Failed to connect to Ollama at {self.base_url}")
            return "[LLM unavailable - Ollama not running]"
        except Exception as e:
            logger.error(f"LLM chat failed: {e}")
            return f"[LLM error: {str(e)}]"

    def is_available(self) -> bool:
        """Check if Ollama is available."""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except Exception:
            return False


# ============================================================
# Industrial RAG Pipeline
# ============================================================

class IndustrialRAGPipeline:
    """
    Complete RAG pipeline for industrial equipment data.

    Combines:
    - Vector search for relevant equipment/alerts
    - LLM for natural language response generation
    """

    def __init__(self):
        self.vector_store = VectorStoreService()
        self.llm = OllamaLLMService()
        self._indexed = False

    def index_equipment_from_db(self):
        """Index all equipment from Django database."""
        from industrial.models import (
            Transformer, DieselGenerator, ElectricalPanel, UPS,
            Chiller, AHU, CoolingTower, Pump, Compressor, Motor,
            EnergyMeter, Alert, MaintenanceRecord,
        )

        logger.info("Starting equipment indexing...")

        # Index each equipment type
        equipment_models = [
            (Transformer, "transformer"),
            (DieselGenerator, "diesel_generator"),
            (ElectricalPanel, "electrical_panel"),
            (UPS, "ups"),
            (Chiller, "chiller"),
            (AHU, "ahu"),
            (CoolingTower, "cooling_tower"),
            (Pump, "pump"),
            (Compressor, "compressor"),
            (Motor, "motor"),
            (EnergyMeter, "energy_meter"),
        ]

        all_docs = []
        for model, eq_type in equipment_models:
            for eq in model.objects.all():
                doc = self._equipment_to_document(eq, eq_type)
                all_docs.append(doc)

        if all_docs:
            self.vector_store.add_documents(EQUIPMENT_COLLECTION, all_docs)
            logger.info(f"Indexed {len(all_docs)} equipment documents")

        # Index alerts
        alert_docs = []
        for alert in Alert.objects.filter(resolved=False):
            doc = self._alert_to_document(alert)
            alert_docs.append(doc)

        if alert_docs:
            self.vector_store.add_documents(ALERTS_COLLECTION, alert_docs)
            logger.info(f"Indexed {len(alert_docs)} alert documents")

        # Index maintenance records
        maint_docs = []
        for record in MaintenanceRecord.objects.all()[:500]:  # Limit for performance
            doc = self._maintenance_to_document(record)
            maint_docs.append(doc)

        if maint_docs:
            self.vector_store.add_documents(MAINTENANCE_COLLECTION, maint_docs)
            logger.info(f"Indexed {len(maint_docs)} maintenance documents")

        self._indexed = True
        logger.info("Equipment indexing complete!")

    def _equipment_to_document(self, equipment, eq_type: str) -> RAGDocument:
        """Convert equipment model to RAG document."""
        # Build a rich text description
        content_parts = [
            f"{equipment.name} ({equipment.equipment_id})",
            f"Type: {eq_type.replace('_', ' ').title()}",
            f"Location: {equipment.location}",
            f"Building: {equipment.building}" if equipment.building else "",
            f"Status: {equipment.status}",
            f"Health Score: {equipment.health_score}%",
            f"Criticality: {equipment.criticality}",
            equipment.description,
        ]

        # Add type-specific fields
        if hasattr(equipment, 'capacity_kva'):
            content_parts.append(f"Capacity: {equipment.capacity_kva} kVA")
        if hasattr(equipment, 'capacity_kw'):
            content_parts.append(f"Capacity: {equipment.capacity_kw} kW")
        if hasattr(equipment, 'capacity_tr'):
            content_parts.append(f"Capacity: {equipment.capacity_tr} TR")
        if hasattr(equipment, 'load_percent') and equipment.load_percent:
            content_parts.append(f"Current Load: {equipment.load_percent:.1f}%")
        if hasattr(equipment, 'power_consumption_kw') and equipment.power_consumption_kw:
            content_parts.append(f"Power Consumption: {equipment.power_consumption_kw:.1f} kW")

        content = " | ".join([p for p in content_parts if p])

        return RAGDocument(
            id=f"{eq_type}_{equipment.equipment_id}",
            content=content,
            metadata={
                "equipment_id": equipment.equipment_id,
                "equipment_type": eq_type,
                "name": equipment.name,
                "location": equipment.location,
                "building": equipment.building or "",
                "status": equipment.status,
                "criticality": equipment.criticality,
                "health_score": equipment.health_score,
            },
        )

    def _alert_to_document(self, alert) -> RAGDocument:
        """Convert alert model to RAG document."""
        content = (
            f"Alert: {alert.message} | "
            f"Equipment: {alert.equipment_name} ({alert.equipment_id}) | "
            f"Severity: {alert.severity} | "
            f"Type: {alert.alert_type} | "
            f"Parameter: {alert.parameter} | "
            f"Value: {alert.value} {alert.unit} | "
            f"Threshold: {alert.threshold} {alert.unit}"
        )

        return RAGDocument(
            id=f"alert_{alert.id}",
            content=content,
            metadata={
                "equipment_id": alert.equipment_id,
                "equipment_name": alert.equipment_name,
                "severity": alert.severity,
                "alert_type": alert.alert_type,
                "acknowledged": alert.acknowledged,
                "resolved": alert.resolved,
            },
        )

    def _maintenance_to_document(self, record) -> RAGDocument:
        """Convert maintenance record to RAG document."""
        content = (
            f"Maintenance: {record.description} | "
            f"Equipment: {record.equipment_name} ({record.equipment_id}) | "
            f"Type: {record.maintenance_type} | "
            f"Work Done: {record.work_done} | "
            f"Parts Replaced: {record.parts_replaced} | "
            f"Technician: {record.technician}"
        )

        return RAGDocument(
            id=f"maint_{record.id}",
            content=content,
            metadata={
                "equipment_id": record.equipment_id,
                "equipment_name": record.equipment_name,
                "maintenance_type": record.maintenance_type,
            },
        )

    def query(
        self,
        question: str,
        n_results: int = 5,
        include_alerts: bool = True,
        include_maintenance: bool = False,
    ) -> RAGResponse:
        """
        Query the RAG pipeline with a natural language question.

        Returns retrieved context and LLM-generated response.
        """
        logger.info(f"RAG Query: {question}")

        # Search equipment
        equipment_results = self.vector_store.search(
            EQUIPMENT_COLLECTION,
            question,
            n_results=n_results,
        )

        # Search alerts if requested
        alert_results = []
        if include_alerts:
            alert_results = self.vector_store.search(
                ALERTS_COLLECTION,
                question,
                n_results=3,
            )

        # Search maintenance if requested
        maint_results = []
        if include_maintenance:
            maint_results = self.vector_store.search(
                MAINTENANCE_COLLECTION,
                question,
                n_results=3,
            )

        # Combine results
        all_results = equipment_results + alert_results + maint_results

        # Build context for LLM
        context_parts = []
        sources = []

        for result in all_results:
            context_parts.append(f"- {result.content}")
            sources.append({
                "id": result.id,
                "type": result.metadata.get("equipment_type", "unknown"),
                "name": result.metadata.get("name", result.metadata.get("equipment_name", "")),
                "score": result.score,
            })

        context = "\n".join(context_parts)

        # Generate response with LLM
        system_prompt = """You are Command Center, an industrial operations voice assistant.
You help operators with equipment monitoring, production lines, quality control, supply chain, and safety.
IMPORTANT: Keep responses to 2-3 sentences maximum. This will be spoken aloud by a voice system.
Be specific — cite equipment IDs, metric values, and current statuses when available.
Use natural spoken language, not written prose. If you lack data to answer, say so briefly."""

        prompt = f"""Based on the following industrial data:
{context}

Answer the operator's question: {question}

Provide a concise, data-rich spoken response."""

        llm_response = self.llm.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.7,
            max_tokens=256,
        )

        return RAGResponse(
            query=question,
            retrieved_docs=all_results,
            context=context,
            llm_response=llm_response,
            sources=sources,
        )

    def get_stats(self) -> dict:
        """Get statistics about indexed data."""
        return {
            "equipment_count": self.vector_store.get_collection_count(EQUIPMENT_COLLECTION),
            "alerts_count": self.vector_store.get_collection_count(ALERTS_COLLECTION),
            "maintenance_count": self.vector_store.get_collection_count(MAINTENANCE_COLLECTION),
            "llm_available": self.llm.is_available(),
            "llm_model": self.llm.model,
        }

    def clear_index(self):
        """Clear all indexed data."""
        self.vector_store.delete_collection(EQUIPMENT_COLLECTION)
        self.vector_store.delete_collection(ALERTS_COLLECTION)
        self.vector_store.delete_collection(MAINTENANCE_COLLECTION)
        self._indexed = False
        logger.info("Cleared all indexed data")


# ============================================================
# Singleton Instance
# ============================================================

_rag_pipeline: Optional[IndustrialRAGPipeline] = None


def get_rag_pipeline() -> IndustrialRAGPipeline:
    """Get or create the RAG pipeline singleton."""
    global _rag_pipeline
    if _rag_pipeline is None:
        _rag_pipeline = IndustrialRAGPipeline()
    return _rag_pipeline
