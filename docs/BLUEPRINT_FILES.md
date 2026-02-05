# Command Center — Blueprint & Specification Files

**Files that define what the system should do, how it should behave, and what quality bar it should meet.**

---

## System Architecture & Domain Definition

| File | What it defines |
|---|---|
| `frontend/src/types/index.ts` | The full 4-layer architecture as types — every event, every state, every data shape the system expects |
| `frontend/src/lib/personaplex/persona.ts` | The AI's intended scope and personality — restricted to industrial operations only |
| `frontend/src/lib/personaplex/protocol.ts` | The binary WebSocket contract between frontend and PersonaPlex server |
| `backend/layer2/dimensions.py` | All physical domains the system understands — POWER, ENERGY, TEMPERATURE, PRESSURE, FLOW, etc. with unit conversion rules |

---

## Widget Catalog & Visual Variants (what the dashboard can show)

| File | What it defines |
|---|---|
| `backend/layer2/widget_catalog.py` | **Master list of all 18+ widget scenarios** the system can produce, with sizing rules, domain mappings, and selection weights |
| `backend/layer2/widget_schemas.py` | **Expected data shape for every widget type** — required fields, types, valid ranges. Defines what "correct" widget data looks like |
| `backend/layer2/llm_fixture_selector.py` | **FIXTURE_DESCRIPTIONS** — the complete catalog of visual variants per scenario (9 KPI variants, 5 alert variants, 6 trend variants, etc.) with human-readable descriptions of when to use each |
| `backend/layer2/fixture_selector.py` | The rules for which visual variant fits which data context — a design specification for visual diversity |
| `frontend/src/components/layer4/fixtureData.ts` | **Demo data for every fixture variant** — defines what each visual should look like when rendered with ideal data |
| `frontend/src/components/layer4/widgetRegistry.ts` | Maps scenario names to React components — the canonical list of what's implemented on the frontend |
| `frontend/src/components/layer3/defaultLayout.ts` | **The intended first-impression dashboard** — 4 KPI tiles + 1 trend + 1 alerts panel for a "project engineer" persona |
| `frontend/src/app/widgets/SampleDashboard.tsx` | **5 pre-built reference dashboards** (Monitor Equipment, Energy Consumption, Maintenance Status, Compare Devices, Power Quality) showing ideal widget compositions |

---

## Expected Behavior & Quality Bar

| File | What it defines |
|---|---|
| `backend/layer2/audit_tests.py` | **Accuracy expectations** — which queries should map to which intents, domains, and widget types |
| `backend/benchmarks/benchmark_suite.py` | **Performance expectations** — latency targets for STT, RAG, TTS, and end-to-end pipeline |
| `frontend/e2e/helpers/test-utils.ts` | **30 realistic scenarios** (expected domains + min widgets), **3 multi-turn stress conversations** (10 turns each), **18 adversarial inputs** (SQL injection, XSS, gibberish, contradictions), and **widget trigger queries** mapping each query to its expected widget |
| `frontend/e2e/tests/mega-validation-phase2.spec.ts` | **Release gate criteria** — 45s render budget (relaxed from 10s for local LLM latency), 50K DOM node cap, 30 FPS minimum, adversarial resilience, widget rendering for all scenarios |
| `backend/layer2/reconciliation/types.py` | **Mismatch taxonomy** — all ways widget data can go wrong, categorized into STRUCTURAL, REPRESENTATIONAL, AMBIGUOUS, SEMANTIC_CONFLICT |
| `backend/layer2/reconciliation/errors.py` | **All possible failure modes** — the complete error hierarchy defining every way reconciliation can fail and what to do about each |
| `backend/layer2/reconciliation/prompts.py` | **LLM reasoning expectations** — how the AI should resolve ambiguous data, with examples of correct and incorrect responses |
| `backend/layer2/tests.py` | **Layer 2 regression suite** — 19 valid widget scenarios, 2 banned scenarios (helpview, pulseview), intent test cases mapping queries to expected types/domains/characteristics, schema validation tests, widget selector constraints (max widgets, valid sizes, banned exclusion), orchestrator response structure checks |
| `tests/conftest.py` | **Shared test fixtures** — `api_client` (DRF test client), `sample_transcript`, `mock_ollama`, `mock_chromadb`, `sample_equipment_data` — the canonical test data shapes |
| `tests/test_intent_parser.py` | **Intent parser contract** — expected type detection (query, action, greeting), domain detection (industrial, alerts, people, supply, tasks), entity extraction (devices, numbers, time), characteristic detection (trend, comparison, distribution), out-of-scope handling, confidence scoring |
| `tests/test_rag_pipeline.py` | **RAG pipeline contract** — document storage/retrieval, embedding service, vector search accuracy, LLM service integration, pipeline statistics |
| `tests/test_api_endpoints.py` | **API endpoint contract** — expected behavior for `/api/layer2/orchestrate/`, `/api/layer2/filler/`, `/api/layer2/rag/industrial/`, `/api/layer2/rag/industrial/health/`, `/api/layer2/proactive/` |
| `tests/test_models.py` | **Data model contract** — expected fields and relationships for RAGPipeline, RAGQuery, RAGResult, UserMemory, all industrial equipment models (Transformer, Pump, Chiller, etc.), Alert and Maintenance models |
| `tests/ai_accuracy_test.py` | **AI accuracy benchmark** — intent classification, domain detection, entity extraction, characteristic detection, RAG retrieval accuracy, out-of-scope detection with pass thresholds |
| `tests/ai_speed_test.py` | **AI performance benchmark** — intent parser response time, RAG vector search speed, embedding generation speed, database query speed, concurrent request handling, memory usage under load, LLM response time with pass thresholds |
| `frontend/e2e/tests/exhaustive-audit.spec.ts` | **Full UI audit spec** — performance budgets (cold nav ≤3s, warm ≤1.5s, UI interaction ≤500ms, AI round-trip ≤45s), defect evidence collection with screenshots, every UI interaction validated with speed verdicts |
| `frontend/e2e/tests/widget-exhaustion.spec.ts` | **Widget exhaustion test** — every widget scenario must render within performance budget, validates all 19 scenarios can be displayed |

---

## Data Domain & Content Expectations

| File | What it defines |
|---|---|
| `backend/industrial/management/commands/populate_industrial_db.py` | **The virtual factory blueprint** — 500+ pieces of equipment across 12 types, with buildings, floors, zones, manufacturers |
| `backend/industrial/management/commands/generate_rich_data.py` | **Operational history expectations** — 500+ alerts, 2000+ maintenance records, 1500+ documents, 5000+ readings |
| `backend/layer2/data_collector.py` | **RAG strategy per widget type** — defines what data each widget scenario needs (single_metric, alert_query, time_series, comparison, etc.) |

---

## Simulation & Training Specifications

| File | What it defines |
|---|---|
| `scripts/simulation/run_simulation.py` | **Question bank** organized by category — the queries the system is expected to handle well |
| `scripts/simulation/run_exhaustive.py` | **Complete coverage matrix** — every question × every scenario × every fixture variant |
| `scripts/simulation/export_training_data.py` | **Training data format spec** — how human ratings translate into SFT and DPO training pairs |
| `backend/rl/config.py` | **Training presets** (default, small_gpu, high_quality) — defines the expected training configurations |

---

*The `widget_catalog.py` + `widget_schemas.py` + `llm_fixture_selector.py` trio is the single most important spec — it defines every widget, every variant, and every data contract.*

---

## Pipeline Architecture Documents

| File | What it defines |
|---|---|
| `docs/RAG_PIPELINE.md` | **Complete 8-stage pipeline specification** — Voice Input → Transcription → Intent Parse → Widget Select → Data Collect → Fixture Pick → Layout Pack → Voice Response. Defines 18 primary_characteristic values, 12 RAG strategies, 19 scenarios (80 fixture variants), short-circuit rules, widget constraints (max 10 widgets, max 24 height units, max 4 KPIs), layout packing algorithm (12-column grid, upsize-to-fill), and the full output JSON format |
| `docs/AUDIT_CHANGES_EXPLAINED.md` | **Post-audit architecture decisions** — 49+ issues fixed across 3 audit rounds (2026-02-04). Documents thread-safety patterns (lazy init with locks), memory leak fixes (Object URL cleanup, AudioContext disposal), error handling hierarchies, data validation pipelines, determinism guarantees, and async operation patterns. Lists every file changed with before/after diffs |
| `docs/RL_TRAINING.md` | **RL training and deployment pipeline** — Feedback Collection → DPO Training → LoRA Fine-tuning → GGUF Export → Ollama Deployment. Defines hardware requirements (16GB+ VRAM training, 8GB inference), training presets (default, small_gpu, high_quality), and the continuous learning loop from user ratings to deployed model |
| `tests/README.md` | **Test structure and pass/fail criteria** — Defines accuracy thresholds (Intent ≥70%, Domain ≥60%, Entity ≥50%, Characteristic ≥60%, Out-of-Scope ≥60%) and performance thresholds (Intent <10ms, RAG <200ms, Embedding <100ms, DB <50ms, Concurrent >100 req/sec, Memory <50MB, LLM <5000ms) |

---

## Vision, Roadmap & Future Expansions

| File | What it defines |
|---|---|
| `README.md` | **NeuractOS vision document** — Defines Command Center as the "one-and-all industrial operations app." Specifies the full 4-layer architecture (Voice → AI+RAG → Blob → Widgets), Blob as "dumb executor" (no decision-making), 100vh×100vw canvas with no global scroll, responsive layout (desktop/laptop/tablet/mobile), system trigger rules (alert fired, threshold breach, scheduled event, role change, time-of-day, webhook), relevance decay curves (5min decay to 0.2 baseline), and user override behaviors (pin, hide, show, manual resize, reset) |
| `README.md` — Keycloak Roles | **Role-based experience specs** — Floor Manager (production metrics, device status, alarms), Supply Chain Lead (inventory, POs, vendor status), HR Admin (attendance, scheduling, leave), Maintenance Tech (device health, work orders), Executive (high-level KPIs, cross-domain summary), Full Admin (everything). Widgets are permission-gated via Keycloak capabilities |
| `README.md` — Capability Chips | **Planned feature** — Visual indicators docked to Ledger Panel showing current Keycloak scopes, trust level for actions (co-sign requirements), and missing capabilities for hidden widgets |
| `README.md` — Ledger Panel | **Planned feature** — Persistent dock for proposals awaiting approval, action audit trail, co-signature requests, and governance visibility |
| `README.md` — Domain Coverage | **7 planned domains** — Industrial Monitoring (LoggerDeploy), Supply Chain (Supply Chain Service), People Management (People Service), Project Management (Project Service), Messaging (Messaging Service), Reporting (NeuraReport), Browser/Chatbot (Blob + Services) |
| `README.md` — Widget Lifecycle | **Planned widget contract** — Discovery → Filtering (Keycloak) → Placement (Blob layout) → Hydration (data fetch) → Rendering → Updates (NATS real-time). Each widget must implement `onMount`, `onResize`, `onDataUpdate`, `onUnmount` with `requiredCapabilities` for permission gating |
| `README.md` — Tech Stack | **Target integration points** — Next.js 14 + React 18 (frontend), Django 5.x (backend), NATS JetStream (events), Keycloak (auth), Ledger Gateway (governance), World Graph (unified graph DB), Spot/Three.js (visual AI), PersonaPlex (voice), RTX 6000 Blackwell (GPU) |

---

## Pending Integrations & Stub Domains

These files reveal what's built vs. what's planned but not yet connected:

| File | What it reveals |
|---|---|
| `backend/layer2/orchestrator.py` (lines 994-998) | **`[F4]` markers** — Supply and People domains explicitly using demo data with `_data_source: "demo"` and `_integration_status: "pending"` markers. Supply chain API, HR system API, and Task system API are not yet connected |
| `backend/layer2/orchestrator.py` (lines 1146-1221) | **5 stub data methods** — `_get_industrial_stub_data()`, `_get_alerts_stub_data()`, `_get_supply_stub_data()`, `_get_people_stub_data()`, `_get_tasks_stub_data()` each return hardcoded demo data as fallbacks when real data sources aren't available |
| `backend/layer2/views.py` (line 64) | **Production migration note** — `# Stub: In production, this would query LoggerDeploy / PostgreSQL for metrics, devices, device_status tables` |
| `README.md` — RAG Agents table | **5 planned RAG agents** — Industrial (LoggerDeploy → metrics, devices, device_status), Supply (Supply Chain → inventory, alerts, rfq, po), People (HR → employees, schedule, attendance), Tasks (Projects → tasks, milestones, assignments), Alerts (Monitoring → alerts, notifications, thresholds). Currently only Industrial and Alerts have real data; Supply, People, and Tasks are stubs |

---

## Performance SLA Budgets

These files define the speed targets the system must hit:

| File | What it specifies |
|---|---|
| `backend/layer2/audit_tests.py` (lines 464-469) | **Backend latency budgets** — Intent Parsing: ≤500ms, RAG Query: ≤2000ms, Widget Selection: ≤3000ms (includes LLM), Total Orchestrator: ≤8000ms |
| `frontend/e2e/tests/exhaustive-audit.spec.ts` (lines 97-102) | **Frontend performance budgets** — Cold page navigation: ≤3000ms, Warm page navigation: ≤1500ms, UI interaction (React re-render): ≤500ms, Full AI round-trip (local LLM): ≤45000ms |
| `frontend/e2e/tests/mega-validation-phase2.spec.ts` (line 494) | **Layout render budget** — Dashboard must fully render within 45,000ms (relaxed from 10,000ms for local LLM), DOM must have <50K nodes, animation must maintain ≥30 FPS |
| `tests/README.md` — Performance thresholds | **Component-level targets** — Intent parser: <10ms, RAG search: <200ms, Embedding generation: <100ms, Database query: <50ms, Concurrent handling: >100 req/sec with 10 workers, Memory usage: <50MB for 500 operations, LLM response: <5000ms |

---

## Feature Flags & Environment Variables

| File | What it specifies |
|---|---|
| `docs/RAG_PIPELINE.md` — Environment Variables | **Pipeline-level toggles** — `PIPELINE_V2` (enable v2 LLM pipeline vs v1 regex), `WIDGET_SELECT_QUALITY` (use 70B model for widget selection), `OLLAMA_MODEL_FAST` (8B for intent+widget), `OLLAMA_MODEL_QUALITY` (70B for voice response), `RAG_EMBEDDING_MODEL` (BAAI/bge-base-en-v1.5 for vector search) |
| `README.md` — Environment Variables | **System-wide feature flags** — `SPOTVOX_MODE` (4layer vs legacy fallback), `ENABLE_BLOB`, `ENABLE_LEDGER`, `ENABLE_RAG`, `RAG_*_ENABLED` per domain (industrial, supply, people, tasks, alerts), `SPOTVOX_ALWAYS_ON` (always-listening mode), `BLOB_TRANSITION_DURATION` |
| `backend/layer2/widget_selector.py` (line 32) | **Layout constraint** — `MAX_HEIGHT_UNITS = 24` (scrollable dashboard height budget) |
| `backend/layer2/widget_catalog.py` (line 9) | **Height cost system** — short=1, medium=2, tall=3, x-tall=4 height units per widget |

---

## Audit-Driven Architecture Patterns

The comprehensive audit (2026-02-04) established these patterns as code-level specifications:

| Pattern | Where enforced | What it specifies |
|---|---|---|
| Thread-safe singleton | `orchestrator.py` | All shared state (LLM clients, ChromaDB, pipeline cache) must use `threading.Lock()` with lazy initialization |
| Deterministic selection | `widget_selector.py` | `sorted()` on widget lists before processing; no `random.choice` without seed; same input → same output guaranteed |
| Schema validation gate | `data_collector.py`, `widget_schemas.py` | Every widget's data must pass `_validate_widget_data()` before reaching the frontend |
| Explicit demo markers | `orchestrator.py` | Any stub/demo data must carry `_data_source: "demo"` and `_integration_status: "pending"` so frontend can detect it |
| Object URL cleanup | `useKokoroTTS.ts`, `useSTT.ts` | All `URL.createObjectURL()` calls must have corresponding `URL.revokeObjectURL()` in cleanup |
| Ref-based state access | `useVoicePipeline.ts` | Event handlers must read from `useRef` (not stale closure state) to avoid race conditions |
| 5-stage reconciliation | `backend/layer2/reconciliation/` | CLASSIFY → REWRITE → RESOLVE → NORMALIZE → VALIDATE pipeline for handling data/schema mismatches |

---

*This document catalogs every file in the Command Center codebase that serves as a specification, blueprint, plan, or quality gate. Together, these files define the complete intended behavior of the system — from high-level vision (README.md) down to per-widget data contracts (widget_schemas.py).*
