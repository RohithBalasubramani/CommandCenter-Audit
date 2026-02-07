"""
System Registry — Authoritative, machine-readable map of all data sources.

Phase 1 of System-Grounded AI Audit.

This registry is the SINGLE SOURCE OF TRUTH for:
- All databases (Django ORM, ChromaDB, SQLite, etc.)
- All schemas, tables, columns
- All services and APIs
- Domain ownership (which domain owns which data)
- Demo vs real integration markers (explicit)

The AI agent MUST consult this registry before answering any query.
If a data source is not registered here, it does not exist for the agent.
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

logger = logging.getLogger(__name__)


class DataSourceType(Enum):
    """Type of data source."""
    DJANGO_ORM = "django_orm"          # Django model backed by SQLite/PostgreSQL
    CHROMADB = "chromadb"              # ChromaDB vector collection
    OLLAMA_LLM = "ollama_llm"         # Ollama LLM service
    REST_API = "rest_api"             # External REST API
    FILE_SYSTEM = "file_system"       # File-based data


class IntegrationStatus(Enum):
    """Whether this data source is real or demo/stub."""
    REAL = "real"                      # Live production data
    DEMO = "demo"                     # Demo/seed data (synthetic)
    STUB = "stub"                     # Stub endpoint (returns hardcoded/empty)
    HYBRID = "hybrid"                 # Mix of real schema + demo data


@dataclass
class ColumnSchema:
    """Schema for a single column/field."""
    name: str
    type: str                         # "str", "int", "float", "bool", "datetime", "json", "uuid"
    nullable: bool = False
    indexed: bool = False
    description: str = ""
    unit: str = ""                    # Physical unit if applicable (kW, °C, %, etc.)


@dataclass
class TableSchema:
    """Schema for a single table/collection."""
    name: str
    columns: list[ColumnSchema] = field(default_factory=list)
    row_count: int = 0                # Populated at runtime by introspection
    description: str = ""
    primary_key: str = "id"


@dataclass
class DataSource:
    """A registered data source in the system."""
    id: str                           # Unique identifier (e.g., "django.industrial.transformer")
    name: str                         # Human-readable name
    source_type: DataSourceType
    integration_status: IntegrationStatus
    domains: list[str]                # Which domains this serves ["industrial", "alerts", etc.]
    tables: list[TableSchema] = field(default_factory=list)
    connection_info: dict = field(default_factory=dict)  # Host, port, path, etc.
    description: str = ""
    authoritative_for: list[str] = field(default_factory=list)  # What queries this is THE answer for
    priority: int = 1                 # Higher = preferred when multiple sources exist

    def has_table(self, table_name: str) -> bool:
        return any(t.name == table_name for t in self.tables)

    def get_table(self, table_name: str) -> Optional[TableSchema]:
        for t in self.tables:
            if t.name == table_name:
                return t
        return None


@dataclass
class DomainOwnership:
    """Maps a domain to its authoritative data sources."""
    domain: str
    description: str
    primary_source_id: str            # THE authoritative source for this domain
    secondary_source_ids: list[str] = field(default_factory=list)
    query_patterns: list[str] = field(default_factory=list)  # Regex patterns this domain handles


class SystemRegistry:
    """
    Machine-readable registry of all data sources in the system.

    This is the gatekeeper — the AI agent MUST resolve through this registry
    before attempting to answer any query.
    """

    def __init__(self):
        self._sources: dict[str, DataSource] = {}
        self._domains: dict[str, DomainOwnership] = {}
        self._initialized = False

    def register_source(self, source: DataSource) -> None:
        """Register a data source."""
        self._sources[source.id] = source
        logger.info(
            f"[registry] Registered source: {source.id} "
            f"(type={source.source_type.value}, status={source.integration_status.value}, "
            f"domains={source.domains})"
        )

    def register_domain(self, ownership: DomainOwnership) -> None:
        """Register domain ownership."""
        self._domains[ownership.domain] = ownership
        logger.info(
            f"[registry] Registered domain: {ownership.domain} "
            f"→ primary={ownership.primary_source_id}"
        )

    def get_source(self, source_id: str) -> Optional[DataSource]:
        """Get a registered source by ID."""
        return self._sources.get(source_id)

    def get_sources_for_domain(self, domain: str) -> list[DataSource]:
        """Get all sources that serve a given domain, ordered by priority."""
        sources = [s for s in self._sources.values() if domain in s.domains]
        return sorted(sources, key=lambda s: -s.priority)

    def get_authoritative_source(self, domain: str) -> Optional[DataSource]:
        """Get the single authoritative source for a domain."""
        ownership = self._domains.get(domain)
        if not ownership:
            return None
        return self._sources.get(ownership.primary_source_id)

    def get_source_for_table(self, table_name: str) -> Optional[DataSource]:
        """Find which source contains a given table."""
        for source in self._sources.values():
            if source.has_table(table_name):
                return source
        return None

    def get_all_sources(self) -> list[DataSource]:
        """Get all registered sources."""
        return list(self._sources.values())

    def get_all_domains(self) -> dict[str, DomainOwnership]:
        """Get all registered domains."""
        return dict(self._domains)

    def is_demo_source(self, source_id: str) -> bool:
        """Check if a source is demo/stub (not real production data)."""
        source = self._sources.get(source_id)
        if not source:
            return True  # Unknown sources are treated as demo
        return source.integration_status in (IntegrationStatus.DEMO, IntegrationStatus.STUB)

    def resolve_query_domain(self, query_domains: list[str]) -> dict:
        """
        For a list of domains in a query, resolve the authoritative source for each.

        Returns:
            {
                "resolved": {domain: DataSource, ...},
                "unresolved": [domain, ...],
                "demo_warning": [domain, ...],  # Domains with only demo data
            }
        """
        resolved = {}
        unresolved = []
        demo_warning = []

        for domain in query_domains:
            source = self.get_authoritative_source(domain)
            if source is None:
                # Try secondary: any source that claims this domain
                candidates = self.get_sources_for_domain(domain)
                if candidates:
                    source = candidates[0]
                else:
                    unresolved.append(domain)
                    continue

            resolved[domain] = source

            if source.integration_status in (IntegrationStatus.DEMO, IntegrationStatus.STUB):
                demo_warning.append(domain)

        return {
            "resolved": resolved,
            "unresolved": unresolved,
            "demo_warning": demo_warning,
        }

    def validate_completeness(self) -> tuple[bool, list[str]]:
        """
        Startup validation: verify registry is complete.

        HARD RULE: If this fails, the system must not boot.
        Returns (valid, errors).
        """
        errors = []

        # Must have at least one data source
        if not self._sources:
            errors.append("BLOCKER: No data sources registered")

        # Every domain must have a primary source
        for domain, ownership in self._domains.items():
            if ownership.primary_source_id not in self._sources:
                errors.append(
                    f"BLOCKER: Domain '{domain}' primary source "
                    f"'{ownership.primary_source_id}' not registered"
                )

        # Every source must have explicit integration_status
        for sid, source in self._sources.items():
            if source.integration_status is None:
                errors.append(f"BLOCKER: Source '{sid}' has no integration_status")

        # LLM must not be authoritative
        for sid, source in self._sources.items():
            if source.source_type == DataSourceType.OLLAMA_LLM:
                if source.authoritative_for:
                    errors.append(
                        f"BLOCKER: LLM source '{sid}' claims authoritative_for={source.authoritative_for}"
                    )
                if source.domains:
                    errors.append(
                        f"BLOCKER: LLM source '{sid}' claims data domains={source.domains}"
                    )

        # Stub sources must not be authoritative
        for sid, source in self._sources.items():
            if source.integration_status == IntegrationStatus.STUB:
                if source.authoritative_for:
                    errors.append(
                        f"BLOCKER: Stub source '{sid}' claims authoritative_for={source.authoritative_for}"
                    )

        # Must have at least the core domains
        required_domains = {"industrial", "alerts"}
        missing_domains = required_domains - set(self._domains.keys())
        if missing_domains:
            errors.append(f"BLOCKER: Missing core domains: {missing_domains}")

        return (len(errors) == 0, errors)

    def to_dict(self) -> dict:
        """Serialize the entire registry to a dict (for API/debugging)."""
        return {
            "sources": {
                sid: {
                    "id": s.id,
                    "name": s.name,
                    "type": s.source_type.value,
                    "integration_status": s.integration_status.value,
                    "domains": s.domains,
                    "tables": [
                        {
                            "name": t.name,
                            "columns": [
                                {"name": c.name, "type": c.type, "unit": c.unit}
                                for c in t.columns
                            ],
                            "row_count": t.row_count,
                        }
                        for t in s.tables
                    ],
                    "authoritative_for": s.authoritative_for,
                    "priority": s.priority,
                }
                for sid, s in self._sources.items()
            },
            "domains": {
                d: {
                    "domain": own.domain,
                    "primary_source": own.primary_source_id,
                    "secondary_sources": own.secondary_source_ids,
                }
                for d, own in self._domains.items()
            },
        }


# ═══════════════════════════════════════════════════════════════════════════════
# SINGLETON + INITIALIZATION
# ═══════════════════════════════════════════════════════════════════════════════

_registry_instance: Optional[SystemRegistry] = None


def get_system_registry() -> SystemRegistry:
    """Get the singleton system registry, initializing if needed."""
    global _registry_instance
    if _registry_instance is None:
        _registry_instance = SystemRegistry()
        _initialize_registry(_registry_instance)
    return _registry_instance


def _initialize_registry(registry: SystemRegistry) -> None:
    """
    Initialize the registry with all known data sources.

    This is the AUTHORITATIVE declaration of what data exists in the system.
    If it's not registered here, the AI cannot use it.
    """

    # ─── Django ORM: Industrial Equipment ───
    _register_django_industrial(registry)

    # ─── Django ORM: Actions ───
    _register_django_actions(registry)

    # ─── Django ORM: Layer2 Models ───
    _register_django_layer2(registry)

    # ─── ChromaDB: Vector Collections ───
    _register_chromadb_collections(registry)

    # ─── Ollama LLM Service ───
    _register_ollama(registry)

    # ─── Industrial RAG API (Stub) ───
    _register_industrial_rag_stub(registry)

    # ─── Domain Ownership ───
    _register_domain_ownership(registry)

    # ─── Startup Validation (HARD RULE) ───
    valid, errors = registry.validate_completeness()
    if not valid:
        for err in errors:
            logger.error(f"[registry] {err}")
        raise RuntimeError(
            f"System registry validation FAILED with {len(errors)} error(s). "
            f"The AI agent cannot start with an incomplete registry. "
            f"Errors: {errors}"
        )

    registry._initialized = True
    logger.info(
        f"[registry] Initialization complete: "
        f"{len(registry._sources)} sources, {len(registry._domains)} domains — "
        f"validation PASSED"
    )


def _register_django_industrial(registry: SystemRegistry) -> None:
    """Register all Django industrial equipment models."""

    # Common base columns (inherited by all equipment)
    base_columns = [
        ColumnSchema("id", "uuid", description="Primary key"),
        ColumnSchema("equipment_id", "str", indexed=True, description="Unique equipment identifier"),
        ColumnSchema("name", "str", description="Equipment name"),
        ColumnSchema("description", "str", nullable=True),
        ColumnSchema("location", "str", description="Physical location"),
        ColumnSchema("building", "str", nullable=True),
        ColumnSchema("floor", "str", nullable=True),
        ColumnSchema("zone", "str", nullable=True),
        ColumnSchema("manufacturer", "str", nullable=True),
        ColumnSchema("model_number", "str", nullable=True),
        ColumnSchema("status", "str", description="running|stopped|maintenance|fault|standby|offline"),
        ColumnSchema("criticality", "str", description="critical|high|medium|low"),
        ColumnSchema("health_score", "int", description="0-100 health score"),
        ColumnSchema("running_hours", "float", unit="hours"),
        ColumnSchema("last_maintenance", "datetime", nullable=True),
        ColumnSchema("next_maintenance", "datetime", nullable=True),
        ColumnSchema("created_at", "datetime"),
        ColumnSchema("updated_at", "datetime"),
    ]

    equipment_tables = [
        TableSchema(
            name="industrial_transformer",
            columns=base_columns + [
                ColumnSchema("transformer_type", "str", description="distribution|power|dry_type|oil_filled|auto"),
                ColumnSchema("capacity_kva", "float", unit="kVA"),
                ColumnSchema("primary_voltage", "float", unit="V"),
                ColumnSchema("secondary_voltage", "float", unit="V"),
                ColumnSchema("load_percent", "float", unit="%"),
                ColumnSchema("oil_temperature", "float", unit="°C"),
                ColumnSchema("winding_temperature", "float", unit="°C"),
                ColumnSchema("power_factor", "float"),
            ],
            description="Power transformers (distribution, step-up, step-down)",
        ),
        TableSchema(
            name="industrial_dieselgenerator",
            columns=base_columns + [
                ColumnSchema("capacity_kva", "float", unit="kVA"),
                ColumnSchema("rated_power_kw", "float", unit="kW"),
                ColumnSchema("current_load_kw", "float", unit="kW"),
                ColumnSchema("fuel_level_percent", "float", unit="%"),
                ColumnSchema("coolant_temperature", "float", unit="°C"),
                ColumnSchema("battery_voltage", "float", unit="V"),
                ColumnSchema("run_hours_since_service", "float", unit="hours"),
            ],
            description="Diesel generator sets",
        ),
        TableSchema(
            name="industrial_electricalpanel",
            columns=base_columns + [
                ColumnSchema("panel_type", "str", description="mcc|pcc|apfc|db|mldb|smdb"),
                ColumnSchema("rated_current", "float", unit="A"),
                ColumnSchema("voltage_r", "float", unit="V"),
                ColumnSchema("voltage_y", "float", unit="V"),
                ColumnSchema("voltage_b", "float", unit="V"),
                ColumnSchema("current_r", "float", unit="A"),
                ColumnSchema("current_y", "float", unit="A"),
                ColumnSchema("current_b", "float", unit="A"),
                ColumnSchema("power_factor", "float"),
                ColumnSchema("frequency", "float", unit="Hz"),
            ],
            description="Electrical panels (MCC, PCC, APFC, DB)",
        ),
        TableSchema(
            name="industrial_ups",
            columns=base_columns + [
                ColumnSchema("capacity_kva", "float", unit="kVA"),
                ColumnSchema("load_percent", "float", unit="%"),
                ColumnSchema("battery_percent", "float", unit="%"),
                ColumnSchema("input_voltage", "float", unit="V"),
                ColumnSchema("output_voltage", "float", unit="V"),
                ColumnSchema("on_battery", "bool"),
                ColumnSchema("battery_runtime_minutes", "float", unit="min"),
            ],
            description="UPS systems",
        ),
        TableSchema(
            name="industrial_chiller",
            columns=base_columns + [
                ColumnSchema("capacity_tr", "float", unit="TR"),
                ColumnSchema("load_percent", "float", unit="%"),
                ColumnSchema("cop", "float", description="Coefficient of Performance"),
                ColumnSchema("chilled_water_supply_temp", "float", unit="°C"),
                ColumnSchema("chilled_water_return_temp", "float", unit="°C"),
                ColumnSchema("compressor_current", "float", unit="A"),
            ],
            description="Chillers (HVAC)",
        ),
        TableSchema(
            name="industrial_ahu",
            columns=base_columns + [
                ColumnSchema("supply_air_temp", "float", unit="°C"),
                ColumnSchema("return_air_temp", "float", unit="°C"),
                ColumnSchema("fan_speed_percent", "float", unit="%"),
                ColumnSchema("filter_dp", "float", unit="Pa"),
                ColumnSchema("damper_position", "float", unit="%"),
            ],
            description="Air Handling Units (HVAC)",
        ),
        TableSchema(
            name="industrial_coolingtower",
            columns=base_columns + [
                ColumnSchema("inlet_temperature", "float", unit="°C"),
                ColumnSchema("outlet_temperature", "float", unit="°C"),
                ColumnSchema("fan_speed_percent", "float", unit="%"),
                ColumnSchema("water_level_percent", "float", unit="%"),
                ColumnSchema("approach_temp", "float", unit="°C"),
            ],
            description="Cooling towers (HVAC)",
        ),
        TableSchema(
            name="industrial_pump",
            columns=base_columns + [
                ColumnSchema("pump_type", "str"),
                ColumnSchema("rated_flow", "float", unit="m³/h"),
                ColumnSchema("rated_head", "float", unit="m"),
                ColumnSchema("current_flow", "float", unit="m³/h"),
                ColumnSchema("discharge_pressure", "float", unit="bar"),
                ColumnSchema("vibration_level", "float", unit="mm/s"),
                ColumnSchema("bearing_temperature", "float", unit="°C"),
            ],
            description="Pumps (centrifugal, submersible, etc.)",
        ),
        TableSchema(
            name="industrial_compressor",
            columns=base_columns + [
                ColumnSchema("compressor_type", "str"),
                ColumnSchema("rated_pressure", "float", unit="bar"),
                ColumnSchema("discharge_pressure", "float", unit="bar"),
                ColumnSchema("oil_temperature", "float", unit="°C"),
                ColumnSchema("motor_current", "float", unit="A"),
            ],
            description="Air/gas compressors",
        ),
        TableSchema(
            name="industrial_motor",
            columns=base_columns + [
                ColumnSchema("rated_power_hp", "float", unit="HP"),
                ColumnSchema("rated_rpm", "float", unit="RPM"),
                ColumnSchema("current_r", "float", unit="A"),
                ColumnSchema("current_y", "float", unit="A"),
                ColumnSchema("current_b", "float", unit="A"),
                ColumnSchema("winding_temperature", "float", unit="°C"),
                ColumnSchema("vibration_level", "float", unit="mm/s"),
            ],
            description="Electric motors",
        ),
        TableSchema(
            name="industrial_energymeter",
            columns=base_columns + [
                ColumnSchema("voltage_r", "float", unit="V"),
                ColumnSchema("voltage_y", "float", unit="V"),
                ColumnSchema("voltage_b", "float", unit="V"),
                ColumnSchema("current_r", "float", unit="A"),
                ColumnSchema("current_y", "float", unit="A"),
                ColumnSchema("current_b", "float", unit="A"),
                ColumnSchema("power_kw", "float", unit="kW"),
                ColumnSchema("power_factor", "float"),
                ColumnSchema("frequency", "float", unit="Hz"),
                ColumnSchema("kwh_total", "float", unit="kWh"),
                ColumnSchema("max_demand_kw", "float", unit="kW"),
            ],
            description="Energy meters (power monitoring)",
        ),
        TableSchema(
            name="industrial_alert",
            columns=[
                ColumnSchema("id", "uuid"),
                ColumnSchema("equipment_id", "str", indexed=True),
                ColumnSchema("equipment_name", "str"),
                ColumnSchema("equipment_type", "str"),
                ColumnSchema("alert_type", "str", description="threshold|fault|maintenance|communication|safety"),
                ColumnSchema("severity", "str", description="critical|high|medium|low|info"),
                ColumnSchema("message", "str"),
                ColumnSchema("value", "float", nullable=True),
                ColumnSchema("threshold", "float", nullable=True),
                ColumnSchema("unit", "str", nullable=True),
                ColumnSchema("acknowledged", "bool"),
                ColumnSchema("resolved_at", "datetime", nullable=True),
                ColumnSchema("triggered_at", "datetime"),
            ],
            description="Equipment alerts and alarms",
        ),
        TableSchema(
            name="industrial_maintenancerecord",
            columns=[
                ColumnSchema("id", "uuid"),
                ColumnSchema("equipment_id", "str", indexed=True),
                ColumnSchema("equipment_name", "str"),
                ColumnSchema("maintenance_type", "str", description="preventive|corrective|breakdown|predictive|inspection"),
                ColumnSchema("description", "str"),
                ColumnSchema("scheduled_date", "datetime"),
                ColumnSchema("started_at", "datetime", nullable=True),
                ColumnSchema("completed_at", "datetime", nullable=True),
                ColumnSchema("downtime_hours", "float"),
                ColumnSchema("cost", "float", unit="currency"),
                ColumnSchema("vendor", "str", nullable=True),
                ColumnSchema("technician", "str", nullable=True),
            ],
            description="Maintenance records and work history",
        ),
    ]

    registry.register_source(DataSource(
        id="django.industrial",
        name="Industrial Equipment Database (Django ORM / SQLite)",
        source_type=DataSourceType.DJANGO_ORM,
        integration_status=IntegrationStatus.HYBRID,  # Real schema, demo seed data
        domains=["industrial", "alerts"],
        tables=equipment_tables,
        connection_info={"engine": "sqlite3", "path": "db.sqlite3"},
        description=(
            "Django ORM models for all industrial equipment. Schema is production-ready. "
            "Data is seeded from management commands (demo quality, not live PLC/SCADA). "
            "Contains: transformers, generators, panels, UPS, HVAC, pumps, compressors, "
            "motors, energy meters, alerts, maintenance records."
        ),
        authoritative_for=[
            "equipment_status", "equipment_metadata", "equipment_health",
            "alert_history", "maintenance_history", "equipment_inventory",
        ],
        priority=10,
    ))


def _register_django_actions(registry: SystemRegistry) -> None:
    """Register Django action models."""
    registry.register_source(DataSource(
        id="django.actions",
        name="Actions Database (Django ORM / SQLite)",
        source_type=DataSourceType.DJANGO_ORM,
        integration_status=IntegrationStatus.REAL,
        domains=["tasks"],
        tables=[
            TableSchema(
                name="actions_reminder",
                columns=[
                    ColumnSchema("id", "uuid"),
                    ColumnSchema("message", "str"),
                    ColumnSchema("trigger_time", "datetime"),
                    ColumnSchema("recurring", "bool"),
                    ColumnSchema("entity", "str", nullable=True),
                    ColumnSchema("created_at", "datetime"),
                ],
                description="Scheduled reminders",
            ),
            TableSchema(
                name="actions_message",
                columns=[
                    ColumnSchema("id", "uuid"),
                    ColumnSchema("recipient", "str"),
                    ColumnSchema("content", "str"),
                    ColumnSchema("channel", "str"),
                    ColumnSchema("sent_at", "datetime"),
                ],
                description="Sent messages",
            ),
            TableSchema(
                name="actions_devicecommand",
                columns=[
                    ColumnSchema("id", "uuid"),
                    ColumnSchema("device_type", "str"),
                    ColumnSchema("device_name", "str"),
                    ColumnSchema("command", "str"),
                    ColumnSchema("parameters", "json"),
                    ColumnSchema("status", "str"),
                    ColumnSchema("requires_confirmation", "bool"),
                ],
                description="Device control commands",
            ),
        ],
        connection_info={"engine": "sqlite3", "path": "db.sqlite3"},
        description="User actions: reminders, messages, device commands",
        authoritative_for=["reminders", "messages", "device_commands"],
        priority=10,
    ))


def _register_django_layer2(registry: SystemRegistry) -> None:
    """Register Layer2 Django models."""
    registry.register_source(DataSource(
        id="django.layer2",
        name="Layer2 Metadata (Django ORM / SQLite)",
        source_type=DataSourceType.DJANGO_ORM,
        integration_status=IntegrationStatus.REAL,
        domains=["industrial", "alerts", "supply", "people", "tasks"],
        tables=[
            TableSchema(
                name="layer2_ragpipeline",
                columns=[
                    ColumnSchema("id", "uuid"),
                    ColumnSchema("domain", "str"),
                    ColumnSchema("enabled", "bool"),
                    ColumnSchema("priority", "int"),
                    ColumnSchema("endpoint_url", "str"),
                ],
                description="RAG pipeline registry",
            ),
            TableSchema(
                name="layer2_ragquery",
                columns=[
                    ColumnSchema("id", "uuid"),
                    ColumnSchema("pipeline_id", "uuid"),
                    ColumnSchema("transcript_id", "uuid"),
                    ColumnSchema("query_text", "str"),
                    ColumnSchema("intent", "json"),
                    ColumnSchema("created_at", "datetime"),
                ],
                description="RAG query execution log",
            ),
            TableSchema(
                name="layer2_usermemory",
                columns=[
                    ColumnSchema("id", "int"),
                    ColumnSchema("user_id", "str", indexed=True),
                    ColumnSchema("query", "str"),
                    ColumnSchema("primary_characteristic", "str"),
                    ColumnSchema("domains", "json"),
                    ColumnSchema("entities_mentioned", "json"),
                    ColumnSchema("scenarios_used", "json"),
                    ColumnSchema("created_at", "datetime"),
                ],
                description="User interaction memory (ring buffer, max 20)",
            ),
        ],
        connection_info={"engine": "sqlite3", "path": "db.sqlite3"},
        description="Layer2 operational metadata: RAG pipelines, query logs, user memory",
        authoritative_for=["rag_pipeline_status", "query_history", "user_memory"],
        priority=5,
    ))


def _register_chromadb_collections(registry: SystemRegistry) -> None:
    """Register ChromaDB vector collections."""
    collections = [
        TableSchema(
            name="industrial_equipment",
            columns=[
                ColumnSchema("id", "str", description="Document ID"),
                ColumnSchema("content", "str", description="Document text"),
                ColumnSchema("embedding", "float[]", description="768-dim BGE vector"),
                ColumnSchema("metadata", "json", description="Equipment metadata"),
            ],
            description="Vector-indexed equipment metadata and specs",
        ),
        TableSchema(
            name="industrial_alerts",
            columns=[
                ColumnSchema("id", "str"),
                ColumnSchema("content", "str"),
                ColumnSchema("embedding", "float[]"),
                ColumnSchema("metadata", "json"),
            ],
            description="Vector-indexed alert messages",
        ),
        TableSchema(
            name="maintenance_records",
            columns=[
                ColumnSchema("id", "str"),
                ColumnSchema("content", "str"),
                ColumnSchema("embedding", "float[]"),
                ColumnSchema("metadata", "json"),
            ],
            description="Vector-indexed maintenance history",
        ),
        TableSchema(
            name="operational_documents",
            columns=[
                ColumnSchema("id", "str"),
                ColumnSchema("content", "str"),
                ColumnSchema("embedding", "float[]"),
                ColumnSchema("metadata", "json"),
            ],
            description="Vector-indexed plant manuals and SOPs",
        ),
        TableSchema(
            name="shift_logs",
            columns=[
                ColumnSchema("id", "str"),
                ColumnSchema("content", "str"),
                ColumnSchema("embedding", "float[]"),
                ColumnSchema("metadata", "json"),
            ],
            description="Vector-indexed shift handover notes",
        ),
        TableSchema(
            name="work_orders",
            columns=[
                ColumnSchema("id", "str"),
                ColumnSchema("content", "str"),
                ColumnSchema("embedding", "float[]"),
                ColumnSchema("metadata", "json"),
            ],
            description="Vector-indexed work order descriptions",
        ),
    ]

    registry.register_source(DataSource(
        id="chromadb.industrial",
        name="ChromaDB Vector Store (Industrial)",
        source_type=DataSourceType.CHROMADB,
        integration_status=IntegrationStatus.HYBRID,  # Real embeddings, demo documents
        domains=["industrial", "alerts"],
        tables=collections,
        connection_info={"persist_dir": "chroma_db/", "embedding_model": "BAAI/bge-base-en-v1.5"},
        description=(
            "ChromaDB persistent vector store. Documents are embedded using BGE-base-en-v1.5 "
            "(768-dim). Used for semantic search in RAG pipeline. Data is seeded from Django "
            "models — accuracy depends on seed quality."
        ),
        authoritative_for=[
            "semantic_search", "document_retrieval", "entity_lookup",
        ],
        priority=5,  # Lower priority than Django ORM for structured queries
    ))


def _register_ollama(registry: SystemRegistry) -> None:
    """Register Ollama LLM service."""
    import os
    registry.register_source(DataSource(
        id="ollama.llm",
        name="Ollama LLM Service",
        source_type=DataSourceType.OLLAMA_LLM,
        integration_status=IntegrationStatus.REAL,
        domains=[],  # LLM is a processing service, not a data source
        tables=[],
        connection_info={
            "base_url": os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
            "model_fast": os.getenv("OLLAMA_MODEL_FAST", "llama3.1:8b"),
            "model_quality": os.getenv("OLLAMA_MODEL_QUALITY", "llama3.3"),
        },
        description=(
            "Ollama LLM service for intent parsing, widget selection, and voice generation. "
            "NOT a data source — generates responses, does not store data. "
            "MUST NOT be treated as authoritative for factual queries."
        ),
        authoritative_for=[],  # LLM is NEVER authoritative for data
        priority=0,
    ))


def _register_industrial_rag_stub(registry: SystemRegistry) -> None:
    """Register the industrial RAG API endpoint (currently a stub)."""
    registry.register_source(DataSource(
        id="api.industrial_rag",
        name="Industrial RAG API (STUB)",
        source_type=DataSourceType.REST_API,
        integration_status=IntegrationStatus.STUB,  # EXPLICITLY marked as stub
        domains=["industrial"],
        tables=[],
        connection_info={"endpoint": "/api/layer2/rag/industrial/"},
        description=(
            "STUB ENDPOINT. Returns empty/hardcoded data. "
            "In production, this would query LoggerDeploy/PostgreSQL for live metrics. "
            "DO NOT use as authoritative source — data is not real."
        ),
        authoritative_for=[],  # Stub is NEVER authoritative
        priority=0,
    ))


def _register_domain_ownership(registry: SystemRegistry) -> None:
    """Register which source is authoritative for each domain."""

    registry.register_domain(DomainOwnership(
        domain="industrial",
        description="Industrial equipment monitoring, status, health, metrics",
        primary_source_id="django.industrial",
        secondary_source_ids=["chromadb.industrial"],
        query_patterns=[
            r"(?:status|health|load|temperature|pressure|voltage|current|power|energy)",
            r"(?:transformer|generator|panel|ups|chiller|ahu|pump|compressor|motor|meter)",
            r"(?:equipment|device|machine|sensor)",
        ],
    ))

    registry.register_domain(DomainOwnership(
        domain="alerts",
        description="Equipment alerts, alarms, threshold breaches",
        primary_source_id="django.industrial",
        secondary_source_ids=["chromadb.industrial"],
        query_patterns=[
            r"(?:alert|alarm|warning|critical|fault|failure|anomaly|threshold|breach|trip)",
        ],
    ))

    registry.register_domain(DomainOwnership(
        domain="tasks",
        description="Work orders, reminders, device commands",
        primary_source_id="django.actions",
        secondary_source_ids=[],
        query_patterns=[
            r"(?:task|reminder|work order|command|schedule|assign)",
        ],
    ))

    registry.register_domain(DomainOwnership(
        domain="supply",
        description="Supply chain, inventory, procurement",
        primary_source_id="django.industrial",  # No dedicated supply DB yet
        secondary_source_ids=[],
        query_patterns=[
            r"(?:inventory|stock|supplier|vendor|purchase|procurement|shipment)",
        ],
    ))

    registry.register_domain(DomainOwnership(
        domain="people",
        description="Workforce, shifts, attendance, HR",
        primary_source_id="django.industrial",  # No dedicated people DB yet
        secondary_source_ids=[],
        query_patterns=[
            r"(?:employee|worker|staff|team|shift|attendance|leave|hr)",
        ],
    ))
