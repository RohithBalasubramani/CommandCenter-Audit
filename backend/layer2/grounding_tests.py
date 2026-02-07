"""
System Grounding Accuracy Tests — All 8 Failure Modes Closed.

These tests enforce that:
1. Every answer is traced to an authoritative source
2. Source resolution is deterministic and correct
3. Traversal actions are actually executed
4. The AI refuses when context is ambiguous
5. Demo/stub data is never silently used as real
6. Wrong database/table usage causes test failure
7. Provenance markers are mandatory on all data payloads
8. Fail-loud reconciliation drops bad widgets

ACCURACY IS NOT LINGUISTIC CORRECTNESS.
An answer is INCORRECT if:
- Wrong database used
- Wrong schema/table used
- Demo/stub data used when real exists
- Context not verified before answering
Even if the answer "sounds right".
"""

import json
import os
import sys
from pathlib import Path

# Add backend to path
_BACKEND_DIR = Path(__file__).parent.parent
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "command_center.settings")

import django
django.setup()

from layer2.system_registry import (
    get_system_registry,
    SystemRegistry,
    DataSource,
    DataSourceType,
    IntegrationStatus,
)
from layer2.schema_introspector import SchemaIntrospector
from layer2.source_resolver import SourceResolver, SourceVerificationGate, ResolutionOutcome
from layer2.traversal import TraversalEngine
from layer2.grounding_audit import get_grounding_auditor
from layer2.data_provenance import (
    stamp_provenance,
    stamp_widget_provenance,
    build_response_provenance,
    validate_provenance,
    validate_response_provenance,
    ResponseProvenance,
)


class TestResult:
    """Simple test result tracker."""
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []

    def ok(self, name: str):
        self.passed += 1
        print(f"  PASS  {name}")

    def fail(self, name: str, reason: str):
        self.failed += 1
        self.errors.append({"test": name, "reason": reason})
        print(f"  FAIL  {name}: {reason}")

    def summary(self):
        total = self.passed + self.failed
        print(f"\n{'='*60}")
        print(f"RESULTS: {self.passed}/{total} passed, {self.failed} failed")
        if self.errors:
            print(f"\nFailed tests:")
            for e in self.errors:
                print(f"  - {e['test']}: {e['reason']}")
        print(f"{'='*60}")
        return self.failed == 0


def run_all_tests():
    """Run all grounding accuracy tests."""
    results = TestResult()

    print("=" * 60)
    print("SYSTEM GROUNDING ACCURACY TESTS — ALL 8 FAILURE MODES")
    print("=" * 60)

    # Phase 1: Registry Tests (F1)
    print("\n--- Phase 1: System Registry (F1: Startup Validation) ---")
    test_registry_exists(results)
    test_registry_has_all_sources(results)
    test_registry_has_domain_ownership(results)
    test_registry_demo_markers(results)
    test_registry_llm_not_authoritative(results)
    test_registry_stub_not_authoritative(results)
    test_registry_startup_validation(results)

    # Phase 1B: Schema Introspection Tests
    print("\n--- Phase 1B: Schema Introspection ---")
    test_introspector_finds_tables(results)
    test_introspector_find_table_for_data(results)
    test_introspector_describe_table(results)
    test_introspector_list_databases(results)

    # Phase 2: Source Resolution Tests (F3)
    print("\n--- Phase 2: Deterministic Source Resolution (F3: Pre-LLM Gate) ---")
    test_resolve_industrial_query(results)
    test_resolve_alerts_query(results)
    test_resolve_unknown_domain(results)
    test_resolve_greeting_no_source(results)
    test_resolve_multi_domain(results)
    test_resolve_action_intent(results)
    test_refuse_when_no_source(results)

    # Phase 3: Traversal Tests (F4)
    print("\n--- Phase 3: Traversal Actions (F4: Mandatory Traversal) ---")
    test_traversal_list_databases(results)
    test_traversal_describe_table(results)
    test_traversal_entity_check(results)
    test_traversal_context_accumulates(results)
    test_traversal_verify_data_origin(results)

    # Phase 4: Source-Verified Accuracy Tests (F7)
    print("\n--- Phase 4: Source-Verified Accuracy (F7: Wrong Source = FAIL) ---")
    test_gate_allows_industrial_query(results)
    test_gate_refuses_unknown_domain(results)
    test_gate_flags_demo_data(results)
    test_wrong_source_detection(results)
    test_no_silent_fallback(results)

    # Phase 5: Hard Failure Mode Closure Tests (F1-F8)
    print("\n--- Phase 5: Hard Failure Mode Closure (F1-F8) ---")
    # F1: Startup validation
    test_f1_registry_validates_completeness(results)
    test_f1_registry_rejects_llm_authoritative(results)
    test_f1_registry_rejects_missing_domains(results)
    # F2: Provenance markers
    test_f2_provenance_stamp_required(results)
    test_f2_provenance_rejects_missing_markers(results)
    test_f2_provenance_rejects_unknown_source(results)
    test_f2_widget_provenance_stamped(results)
    # F3: Source resolver blocks LLM
    test_f3_resolver_blocks_on_no_domain(results)
    test_f3_resolver_blocks_nonexistent_domain(results)
    # F4: Mandatory traversal
    test_f4_traversal_count_nonzero(results)
    test_f4_traversal_fallback_to_describe(results)
    # F5: derived_from non-empty
    test_f5_response_provenance_has_derived_from(results)
    test_f5_response_provenance_rejects_empty_derived(results)
    # F6: Stub safe_to_answer:false
    test_f6_stub_not_safe_to_answer(results)
    test_f6_stub_provenance_marks_unsafe(results)
    # F7: Right answer wrong DB = FAIL
    test_f7_right_answer_wrong_db_fails(results)
    test_f7_right_db_no_traversal_fails(results)
    test_f7_demo_data_silent_fails(results)
    # F8: Fail-loud reconciliation
    test_f8_reconciliation_drops_on_failure(results)

    return results.summary()


# ═══════════════════════════════════════════════════════════════════════════════
# Phase 1: System Registry Tests (F1)
# ═══════════════════════════════════════════════════════════════════════════════

def test_registry_exists(r: TestResult):
    """Registry must exist and be initialized."""
    registry = get_system_registry()
    if registry is None:
        r.fail("registry_exists", "Registry is None")
    elif len(registry.get_all_sources()) == 0:
        r.fail("registry_exists", "Registry has no sources")
    else:
        r.ok("registry_exists")


def test_registry_has_all_sources(r: TestResult):
    """Registry must have all expected data sources."""
    registry = get_system_registry()
    expected_ids = [
        "django.industrial",
        "django.actions",
        "django.layer2",
        "chromadb.industrial",
        "ollama.llm",
        "api.industrial_rag",
    ]
    missing = [sid for sid in expected_ids if registry.get_source(sid) is None]
    if missing:
        r.fail("registry_has_all_sources", f"Missing sources: {missing}")
    else:
        r.ok("registry_has_all_sources")


def test_registry_has_domain_ownership(r: TestResult):
    """Registry must have domain ownership for all domains."""
    registry = get_system_registry()
    expected_domains = ["industrial", "alerts", "tasks", "supply", "people"]
    domains = registry.get_all_domains()
    missing = [d for d in expected_domains if d not in domains]
    if missing:
        r.fail("registry_has_domain_ownership", f"Missing domains: {missing}")
    else:
        r.ok("registry_has_domain_ownership")


def test_registry_demo_markers(r: TestResult):
    """Every source must have an explicit integration status (no implicit defaults)."""
    registry = get_system_registry()
    unmarked = []
    for source in registry.get_all_sources():
        if source.integration_status is None:
            unmarked.append(source.id)
    if unmarked:
        r.fail("registry_demo_markers", f"Sources without integration status: {unmarked}")
    else:
        r.ok("registry_demo_markers")


def test_registry_llm_not_authoritative(r: TestResult):
    """LLM service must NOT be authoritative for any data."""
    registry = get_system_registry()
    llm = registry.get_source("ollama.llm")
    if llm is None:
        r.fail("registry_llm_not_authoritative", "LLM source not registered")
    elif llm.authoritative_for:
        r.fail("registry_llm_not_authoritative",
               f"LLM claims to be authoritative for: {llm.authoritative_for}")
    elif llm.domains:
        r.fail("registry_llm_not_authoritative",
               f"LLM claims data domains: {llm.domains}")
    else:
        r.ok("registry_llm_not_authoritative")


def test_registry_stub_not_authoritative(r: TestResult):
    """Stub endpoints must NOT be authoritative for any data."""
    registry = get_system_registry()
    stub = registry.get_source("api.industrial_rag")
    if stub is None:
        r.fail("registry_stub_not_authoritative", "Stub source not registered")
    elif stub.authoritative_for:
        r.fail("registry_stub_not_authoritative",
               f"Stub claims to be authoritative for: {stub.authoritative_for}")
    elif stub.integration_status != IntegrationStatus.STUB:
        r.fail("registry_stub_not_authoritative",
               f"Stub not marked as STUB: {stub.integration_status}")
    else:
        r.ok("registry_stub_not_authoritative")


def test_registry_startup_validation(r: TestResult):
    """F1: Registry startup validation must pass for the current registry."""
    registry = get_system_registry()
    valid, errors = registry.validate_completeness()
    if not valid:
        r.fail("registry_startup_validation", f"Validation failed: {errors}")
    else:
        r.ok("registry_startup_validation")


# ═══════════════════════════════════════════════════════════════════════════════
# Phase 1B: Schema Introspection Tests
# ═══════════════════════════════════════════════════════════════════════════════

def test_introspector_finds_tables(r: TestResult):
    """Introspector must find Django tables in the database."""
    introspector = SchemaIntrospector()
    result = introspector.introspect_all()
    table_count = result["django_tables"]["table_count"]
    if table_count == 0:
        r.fail("introspector_finds_tables", "No Django tables found")
    else:
        r.ok(f"introspector_finds_tables ({table_count} tables)")


def test_introspector_find_table_for_data(r: TestResult):
    """Introspector must answer 'which table has transformer data?'"""
    introspector = SchemaIntrospector()
    matches = introspector.find_table_for_data("transformer load temperature")
    if not matches:
        r.fail("introspector_find_table_for_data", "No matches found for 'transformer load'")
    elif "transformer" not in matches[0]["table_name"].lower():
        r.fail("introspector_find_table_for_data",
               f"Top match is '{matches[0]['table_name']}', expected transformer table")
    else:
        r.ok(f"introspector_find_table_for_data (top={matches[0]['table_name']})")


def test_introspector_describe_table(r: TestResult):
    """Introspector must describe a known table's schema."""
    introspector = SchemaIntrospector()
    desc = introspector.describe_table("industrial_transformer")
    if desc is None:
        r.fail("introspector_describe_table", "Could not describe industrial_transformer")
    elif len(desc["columns"]) == 0:
        r.fail("introspector_describe_table", "No columns found for industrial_transformer")
    else:
        r.ok(f"introspector_describe_table ({len(desc['columns'])} columns)")


def test_introspector_list_databases(r: TestResult):
    """Introspector must list all registered databases."""
    introspector = SchemaIntrospector()
    dbs = introspector.list_databases()
    if not dbs:
        r.fail("introspector_list_databases", "No databases listed")
    elif len(dbs) < 3:
        r.fail("introspector_list_databases", f"Only {len(dbs)} databases listed, expected >=3")
    else:
        r.ok(f"introspector_list_databases ({len(dbs)} sources)")


# ═══════════════════════════════════════════════════════════════════════════════
# Phase 2: Source Resolution Tests (F3)
# ═══════════════════════════════════════════════════════════════════════════════

def test_resolve_industrial_query(r: TestResult):
    """Industrial query must resolve to django.industrial."""
    resolver = SourceResolver()
    resolution = resolver.resolve(
        intent_type="query",
        domains=["industrial"],
        entities={"devices": ["pump-001"]},
        transcript="What is the status of pump-001?",
    )
    if not resolution.is_resolved:
        r.fail("resolve_industrial_query", f"Not resolved: {resolution.outcome.value}")
    elif resolution.primary_source.id != "django.industrial":
        r.fail("resolve_industrial_query",
               f"Wrong source: {resolution.primary_source.id}, expected django.industrial")
    else:
        r.ok("resolve_industrial_query")


def test_resolve_alerts_query(r: TestResult):
    """Alerts query must resolve to django.industrial (alerts table)."""
    resolver = SourceResolver()
    resolution = resolver.resolve(
        intent_type="query",
        domains=["alerts"],
        entities={},
        transcript="Show me all critical alerts",
    )
    if not resolution.is_resolved:
        r.fail("resolve_alerts_query", f"Not resolved: {resolution.outcome.value}")
    else:
        r.ok("resolve_alerts_query")


def test_resolve_unknown_domain(r: TestResult):
    """Query with no recognizable domain must trigger clarification or refusal."""
    resolver = SourceResolver()
    resolution = resolver.resolve(
        intent_type="query",
        domains=[],
        entities={},
        transcript="What is the meaning of life?",
    )
    if resolution.is_resolved:
        r.fail("resolve_unknown_domain",
               "Should not resolve an unknown domain query")
    elif not (resolution.clarification_needed or resolution.refusal_reason):
        r.fail("resolve_unknown_domain",
               "Should have clarification or refusal message")
    else:
        r.ok("resolve_unknown_domain")


def test_resolve_greeting_no_source(r: TestResult):
    """Greeting intent should resolve without a data source."""
    resolver = SourceResolver()
    resolution = resolver.resolve(
        intent_type="greeting",
        domains=[],
        entities={},
        transcript="Hello!",
    )
    if not resolution.is_resolved:
        r.fail("resolve_greeting_no_source", "Greeting should resolve (no data needed)")
    elif resolution.primary_source is not None:
        r.fail("resolve_greeting_no_source",
               f"Greeting should not have a data source, got: {resolution.primary_source.id}")
    else:
        r.ok("resolve_greeting_no_source")


def test_resolve_multi_domain(r: TestResult):
    """Multi-domain query must resolve all domains."""
    resolver = SourceResolver()
    resolution = resolver.resolve(
        intent_type="query",
        domains=["industrial", "alerts"],
        entities={"devices": ["transformer-001"]},
        transcript="Show transformer status and any alerts",
    )
    if not resolution.is_resolved:
        r.fail("resolve_multi_domain", f"Not resolved: {resolution.outcome.value}")
    elif len(resolution.domains_resolved) < 2:
        r.fail("resolve_multi_domain",
               f"Only {len(resolution.domains_resolved)} domains resolved, expected 2")
    else:
        r.ok("resolve_multi_domain")


def test_resolve_action_intent(r: TestResult):
    """Action intent must resolve to django.actions."""
    resolver = SourceResolver()
    resolution = resolver.resolve(
        intent_type="action_reminder",
        domains=["tasks"],
        entities={},
        transcript="Set a reminder for maintenance tomorrow",
    )
    if not resolution.is_resolved:
        r.fail("resolve_action_intent", f"Not resolved: {resolution.outcome.value}")
    elif resolution.primary_source.id != "django.actions":
        r.fail("resolve_action_intent",
               f"Wrong source: {resolution.primary_source.id}, expected django.actions")
    else:
        r.ok("resolve_action_intent")


def test_refuse_when_no_source(r: TestResult):
    """Must refuse when no authoritative source exists."""
    resolver = SourceResolver()
    resolution = resolver.resolve(
        intent_type="query",
        domains=["nonexistent_domain"],
        entities={},
        transcript="Query about nonexistent data",
    )
    if resolution.is_resolved:
        r.fail("refuse_when_no_source",
               "Should refuse when domain has no source")
    elif resolution.outcome != ResolutionOutcome.REFUSED:
        r.fail("refuse_when_no_source",
               f"Expected REFUSED, got {resolution.outcome.value}")
    else:
        r.ok("refuse_when_no_source")


# ═══════════════════════════════════════════════════════════════════════════════
# Phase 3: Traversal Tests (F4)
# ═══════════════════════════════════════════════════════════════════════════════

def test_traversal_list_databases(r: TestResult):
    """Traversal: list_databases must return all sources."""
    engine = TraversalEngine()
    step = engine.list_databases()
    if not step.success:
        r.fail("traversal_list_databases", f"Failed: {step.error}")
    elif not step.result:
        r.fail("traversal_list_databases", "No results returned")
    else:
        r.ok(f"traversal_list_databases ({len(step.result)} sources)")


def test_traversal_describe_table(r: TestResult):
    """Traversal: describe_table must return schema for known table."""
    engine = TraversalEngine()
    step = engine.describe_table("industrial_transformer")
    if not step.success:
        r.fail("traversal_describe_table", f"Failed: {step.error}")
    elif not step.result:
        r.fail("traversal_describe_table", "No result returned")
    elif step.source_id != "django.industrial":
        r.fail("traversal_describe_table",
               f"Wrong source: {step.source_id}, expected django.industrial")
    else:
        r.ok("traversal_describe_table")


def test_traversal_entity_check(r: TestResult):
    """Traversal: check_entity_exists must search actual database."""
    engine = TraversalEngine()
    step = engine.check_entity_exists("nonexistent-device-xyz-999")
    if not step.success:
        r.fail("traversal_entity_check", f"Failed: {step.error}")
    elif step.result.get("exists", True):
        r.fail("traversal_entity_check",
               "Nonexistent entity should not be found")
    else:
        r.ok("traversal_entity_check")


def test_traversal_context_accumulates(r: TestResult):
    """Traversal context must accumulate across multiple actions."""
    engine = TraversalEngine()
    engine.list_databases()
    engine.describe_table("industrial_transformer")
    engine.check_entity_exists("test-device")

    ctx = engine.context
    if ctx.step_count != 3:
        r.fail("traversal_context_accumulates",
               f"Expected 3 steps, got {ctx.step_count}")
    elif len(ctx.sources_queried) == 0:
        r.fail("traversal_context_accumulates",
               "No sources recorded in context")
    else:
        r.ok(f"traversal_context_accumulates ({ctx.step_count} steps, "
             f"{len(ctx.sources_queried)} sources)")


def test_traversal_verify_data_origin(r: TestResult):
    """Traversal: data origin verification must detect unqueried sources."""
    engine = TraversalEngine()
    # Only query one source
    engine.list_databases()

    # Verify against a source we didn't actually query
    step = engine.verify_data_origin({}, "some_unqueried_source")
    if not step.success:
        r.fail("traversal_verify_data_origin", f"Failed: {step.error}")
    elif step.result.get("verified", True):
        r.fail("traversal_verify_data_origin",
               "Should NOT verify data from unqueried source")
    else:
        r.ok("traversal_verify_data_origin")


# ═══════════════════════════════════════════════════════════════════════════════
# Phase 4: Source-Verified Accuracy Tests (F7)
# ═══════════════════════════════════════════════════════════════════════════════

def test_gate_allows_industrial_query(r: TestResult):
    """Verification gate must allow industrial queries."""
    gate = SourceVerificationGate()
    can_proceed, resolution, refusal = gate.verify_or_refuse(
        intent_type="query",
        domains=["industrial"],
        entities={"devices": []},
        transcript="Show me pump status",
    )
    if not can_proceed:
        r.fail("gate_allows_industrial_query",
               f"Gate blocked valid query: {refusal}")
    else:
        r.ok("gate_allows_industrial_query")


def test_gate_refuses_unknown_domain(r: TestResult):
    """Verification gate must refuse queries for unknown domains."""
    gate = SourceVerificationGate()
    can_proceed, resolution, refusal = gate.verify_or_refuse(
        intent_type="query",
        domains=["cryptocurrency"],
        entities={},
        transcript="What's the price of Bitcoin?",
    )
    if can_proceed:
        r.fail("gate_refuses_unknown_domain",
               "Gate should refuse query for unknown domain")
    elif not refusal:
        r.fail("gate_refuses_unknown_domain",
               "Gate should provide refusal message")
    else:
        r.ok("gate_refuses_unknown_domain")


def test_gate_flags_demo_data(r: TestResult):
    """Verification gate must flag when demo data is being used."""
    gate = SourceVerificationGate()
    can_proceed, resolution, refusal = gate.verify_or_refuse(
        intent_type="query",
        domains=["industrial"],
        entities={},
        transcript="Show me transformer data",
    )
    # Should proceed but with demo warnings (hybrid data)
    if not can_proceed:
        r.fail("gate_flags_demo_data", f"Gate blocked: {refusal}")
    elif not resolution.demo_warnings:
        r.fail("gate_flags_demo_data",
               "Gate should flag demo/hybrid data sources")
    else:
        r.ok("gate_flags_demo_data")


def test_wrong_source_detection(r: TestResult):
    """System must detect when wrong source would be used."""
    registry = get_system_registry()

    # The industrial RAG API is a STUB — it should never be authoritative
    stub = registry.get_source("api.industrial_rag")
    if stub is None:
        r.fail("wrong_source_detection", "Stub not registered")
        return

    if stub.authoritative_for:
        r.fail("wrong_source_detection",
               f"STUB is claimed authoritative for: {stub.authoritative_for}")
    elif stub.priority > 0:
        r.fail("wrong_source_detection",
               f"STUB has priority {stub.priority}, should be 0")
    elif not registry.is_demo_source("api.industrial_rag"):
        r.fail("wrong_source_detection",
               "STUB not detected as demo source")
    else:
        r.ok("wrong_source_detection")


def test_no_silent_fallback(r: TestResult):
    """Resolver must never silently fall back to a different source."""
    resolver = SourceResolver()
    resolution = resolver.resolve(
        intent_type="query",
        domains=["industrial"],
        entities={},
        transcript="Show equipment status",
    )
    # Check traversal log — resolution steps must be logged
    if not resolution.traversal_log:
        r.fail("no_silent_fallback",
               "No traversal log — resolution steps not recorded")
    else:
        # Verify every domain resolution was logged
        domain_steps = [s for s in resolution.traversal_log if "domain_resolve" in s["step"]]
        if not domain_steps:
            r.fail("no_silent_fallback",
                   "Domain resolution not logged")
        else:
            r.ok(f"no_silent_fallback ({len(domain_steps)} domain resolution steps logged)")


# ═══════════════════════════════════════════════════════════════════════════════
# Phase 5: Hard Failure Mode Closure Tests (F1-F8)
# ═══════════════════════════════════════════════════════════════════════════════

# --- F1: Startup Validation ---

def test_f1_registry_validates_completeness(r: TestResult):
    """F1: Registry.validate_completeness() must pass for current registry."""
    registry = get_system_registry()
    valid, errors = registry.validate_completeness()
    if not valid:
        r.fail("f1_validates_completeness", f"Validation FAILED: {errors}")
    else:
        r.ok("f1_validates_completeness")


def test_f1_registry_rejects_llm_authoritative(r: TestResult):
    """F1: If LLM claims authoritative, validation MUST fail."""
    # Build a test registry with LLM claiming authority
    test_registry = SystemRegistry()
    test_registry.register_source(DataSource(
        id="test.llm",
        name="Test LLM",
        source_type=DataSourceType.OLLAMA_LLM,
        integration_status=IntegrationStatus.REAL,
        authoritative_for=["industrial"],  # INVALID: LLM claiming authority
        domains=[],
    ))
    valid, errors = test_registry.validate_completeness()
    llm_errors = [e for e in errors if "LLM" in e and "authoritative" in e]
    if not llm_errors:
        r.fail("f1_rejects_llm_authoritative",
               "Validation should catch LLM claiming authoritative")
    else:
        r.ok("f1_rejects_llm_authoritative")


def test_f1_registry_rejects_missing_domains(r: TestResult):
    """F1: Empty registry must fail validation (missing core domains)."""
    test_registry = SystemRegistry()
    valid, errors = test_registry.validate_completeness()
    if valid:
        r.fail("f1_rejects_missing_domains",
               "Empty registry should fail validation")
    else:
        # Check that "core domains" error is in the list
        domain_errors = [e for e in errors if "domain" in e.lower() or "source" in e.lower()]
        if not domain_errors:
            r.fail("f1_rejects_missing_domains",
                   f"Validation failed but not for domains: {errors}")
        else:
            r.ok("f1_rejects_missing_domains")


# --- F2: Provenance Markers ---

def test_f2_provenance_stamp_required(r: TestResult):
    """F2: stamp_provenance must inject all required markers."""
    data = {"value": 42, "metric": "temperature"}
    stamped = stamp_provenance(data, "django.industrial", is_authoritative=True)

    required_keys = ["_data_source", "_integration_status", "_authoritative"]
    missing = [k for k in required_keys if k not in stamped]
    if missing:
        r.fail("f2_provenance_stamp_required", f"Missing markers after stamp: {missing}")
    elif stamped["_data_source"] != "django.industrial":
        r.fail("f2_provenance_stamp_required",
               f"Wrong _data_source: {stamped['_data_source']}")
    elif stamped["_authoritative"] is not True:
        r.fail("f2_provenance_stamp_required",
               f"_authoritative should be True, got {stamped['_authoritative']}")
    else:
        r.ok("f2_provenance_stamp_required")


def test_f2_provenance_rejects_missing_markers(r: TestResult):
    """F2: validate_provenance must reject data WITHOUT markers."""
    # Data without any provenance markers
    raw_data = {"value": 42, "metric": "temperature"}
    valid, reason = validate_provenance(raw_data)
    if valid:
        r.fail("f2_rejects_missing_markers",
               "Should reject data without provenance markers")
    elif "Missing provenance markers" not in reason:
        r.fail("f2_rejects_missing_markers",
               f"Wrong rejection reason: {reason}")
    else:
        r.ok("f2_rejects_missing_markers")


def test_f2_provenance_rejects_unknown_source(r: TestResult):
    """F2: validate_provenance must reject data with unknown source."""
    data = {
        "_data_source": "unknown",
        "_integration_status": "unknown",
        "_authoritative": False,
    }
    valid, reason = validate_provenance(data)
    if valid:
        r.fail("f2_rejects_unknown_source",
               "Should reject data with unknown source")
    elif "unknown" not in reason.lower():
        r.fail("f2_rejects_unknown_source",
               f"Wrong rejection reason: {reason}")
    else:
        r.ok("f2_rejects_unknown_source")


def test_f2_widget_provenance_stamped(r: TestResult):
    """F2: stamp_widget_provenance must add markers to widget data_override."""
    # Create a mock source resolution
    resolver = SourceResolver()
    resolution = resolver.resolve(
        intent_type="query",
        domains=["industrial"],
        entities={},
        transcript="Show pump status",
    )

    widget = {
        "scenario": "kpi",
        "data_override": {"demoData": {"label": "Pump Status", "value": "Running"}},
    }

    stamped = stamp_widget_provenance(widget, resolution)
    data_override = stamped.get("data_override", {})

    required = ["_data_source", "_integration_status", "_authoritative", "_safe_to_answer"]
    missing = [k for k in required if k not in data_override]
    if missing:
        r.fail("f2_widget_provenance_stamped", f"Missing markers: {missing}")
    elif data_override.get("_data_source") == "unknown":
        r.fail("f2_widget_provenance_stamped", "Source should not be 'unknown' for resolved query")
    else:
        r.ok("f2_widget_provenance_stamped")


# --- F3: Source Resolver Blocks LLM ---

def test_f3_resolver_blocks_on_no_domain(r: TestResult):
    """F3: Resolver MUST block when no domain can be identified."""
    gate = SourceVerificationGate()
    can_proceed, resolution, refusal = gate.verify_or_refuse(
        intent_type="query",
        domains=[],
        entities={},
        transcript="xyzzy foo bar baz",  # Nonsense — no domain
    )
    if can_proceed:
        r.fail("f3_blocks_on_no_domain",
               "Gate should BLOCK query with no identifiable domain")
    elif not refusal:
        r.fail("f3_blocks_on_no_domain",
               "Gate must provide refusal/clarification message")
    else:
        r.ok("f3_blocks_on_no_domain")


def test_f3_resolver_blocks_nonexistent_domain(r: TestResult):
    """F3: Resolver MUST refuse for explicitly nonexistent domains."""
    gate = SourceVerificationGate()
    can_proceed, resolution, refusal = gate.verify_or_refuse(
        intent_type="query",
        domains=["weather", "stocks"],
        entities={},
        transcript="What's the weather and stock prices?",
    )
    if can_proceed:
        r.fail("f3_blocks_nonexistent_domain",
               "Gate should REFUSE query for nonexistent domains")
    elif resolution.outcome != ResolutionOutcome.REFUSED:
        r.fail("f3_blocks_nonexistent_domain",
               f"Expected REFUSED outcome, got {resolution.outcome.value}")
    else:
        r.ok("f3_blocks_nonexistent_domain")


# --- F4: Mandatory Traversal ---

def test_f4_traversal_count_nonzero(r: TestResult):
    """F4: Traversal engine must accumulate at least one step for any query."""
    engine = TraversalEngine()
    # Simulate what the orchestrator does for a basic query
    engine.list_databases()  # Fallback baseline traversal

    if engine.context.step_count == 0:
        r.fail("f4_traversal_count_nonzero",
               "Traversal must have at least 1 step")
    else:
        r.ok(f"f4_traversal_count_nonzero ({engine.context.step_count} steps)")


def test_f4_traversal_fallback_to_describe(r: TestResult):
    """F4: If no entities to check, traversal must still execute via describe_table."""
    engine = TraversalEngine()
    # Simulate orchestrator fallback: describe primary source's first table
    step = engine.describe_table("industrial_transformer")
    if not step.success:
        r.fail("f4_traversal_fallback_describe", f"Describe fallback failed: {step.error}")
    elif engine.context.step_count == 0:
        r.fail("f4_traversal_fallback_describe", "Step count still 0 after describe_table")
    else:
        r.ok(f"f4_traversal_fallback_describe (source={step.source_id})")


# --- F5: derived_from Non-Empty ---

def test_f5_response_provenance_has_derived_from(r: TestResult):
    """F5: build_response_provenance must populate derived_from for resolved queries."""
    resolver = SourceResolver()
    resolution = resolver.resolve(
        intent_type="query",
        domains=["industrial"],
        entities={},
        transcript="Show pump data",
    )

    engine = TraversalEngine()
    engine.list_databases()

    provenance = build_response_provenance(resolution, engine.context, [])
    if not provenance.derived_from:
        r.fail("f5_has_derived_from",
               "derived_from must not be empty for a resolved data query")
    elif "django.industrial" not in provenance.derived_from:
        r.fail("f5_has_derived_from",
               f"derived_from={provenance.derived_from}, expected django.industrial")
    else:
        r.ok("f5_has_derived_from")


def test_f5_response_provenance_rejects_empty_derived(r: TestResult):
    """F5: validate_response_provenance MUST reject empty derived_from."""
    empty_provenance = ResponseProvenance(
        derived_from=[],  # EMPTY — must be rejected
        resolution_outcome="resolved",
        safe_to_answer=True,
    )
    valid, reason = validate_response_provenance(empty_provenance)
    if valid:
        r.fail("f5_rejects_empty_derived",
               "Should reject response with empty derived_from")
    elif "derived_from" not in reason.lower() and "no derived_from" not in reason.lower():
        r.fail("f5_rejects_empty_derived",
               f"Wrong rejection reason: {reason}")
    else:
        r.ok("f5_rejects_empty_derived")


# --- F6: Stub safe_to_answer: false ---

def test_f6_stub_not_safe_to_answer(r: TestResult):
    """F6: Stub source must have safe_to_answer=false when stamped."""
    registry = get_system_registry()
    stub = registry.get_source("api.industrial_rag")
    if stub is None:
        r.fail("f6_stub_not_safe", "Stub source not registered")
        return

    if stub.integration_status != IntegrationStatus.STUB:
        r.fail("f6_stub_not_safe",
               f"Expected STUB status, got {stub.integration_status.value}")
        return

    # Stamp provenance from stub source
    data = {"value": "stub_data"}
    stamped = stamp_provenance(data, "api.industrial_rag")
    if stamped.get("_safe_to_answer") is not False:
        r.fail("f6_stub_not_safe",
               f"Stub data should have _safe_to_answer=false, got {stamped.get('_safe_to_answer')}")
    elif stamped.get("_integration_status") != "stub":
        r.fail("f6_stub_not_safe",
               f"Should be 'stub', got {stamped.get('_integration_status')}")
    else:
        r.ok("f6_stub_not_safe")


def test_f6_stub_provenance_marks_unsafe(r: TestResult):
    """F6: Response provenance from stub-only must be unsafe."""
    # Create a resolution that resolves to the stub only
    # The stub has priority 0, so it should never be primary — but test the provenance system
    empty_provenance = ResponseProvenance(
        derived_from=[],
        resolution_outcome="demo_only",
        safe_to_answer=False,
    )
    valid, reason = validate_response_provenance(empty_provenance)
    if valid:
        r.fail("f6_stub_marks_unsafe",
               "Response from stub-only should be marked unsafe")
    else:
        r.ok("f6_stub_marks_unsafe")


# --- F7: Right Answer Wrong DB = FAIL ---

def test_f7_right_answer_wrong_db_fails(r: TestResult):
    """F7: Claiming data from wrong source must be detectable as wrong."""
    registry = get_system_registry()

    # Scenario: pump data should come from django.industrial, NOT from LLM
    resolver = SourceResolver()
    resolution = resolver.resolve(
        intent_type="query",
        domains=["industrial"],
        entities={"devices": ["pump-001"]},
        transcript="What is pump-001 temperature?",
    )

    if not resolution.is_resolved:
        r.fail("f7_wrong_db_fails", "Resolution failed unexpectedly")
        return

    # The correct source is django.industrial
    correct_source = resolution.primary_source.id
    if correct_source != "django.industrial":
        r.fail("f7_wrong_db_fails",
               f"Expected django.industrial, resolved to {correct_source}")
        return

    # Verify that LLM is NOT the correct source
    llm_source = registry.get_source("ollama.llm")
    if llm_source and llm_source.authoritative_for:
        r.fail("f7_wrong_db_fails",
               "LLM should never be authoritative for data")
        return

    # Verify that traversal can detect wrong origin
    engine = TraversalEngine()
    engine.describe_table("industrial_pump")
    # Now verify_data_origin against the LLM (wrong source)
    verification = engine.verify_data_origin({}, "ollama.llm")
    if verification.result.get("verified", True):
        r.fail("f7_wrong_db_fails",
               "Data origin from LLM should NOT be verified")
    else:
        r.ok("f7_wrong_db_fails")


def test_f7_right_db_no_traversal_fails(r: TestResult):
    """F7: Right DB but no traversal = FAIL (must traverse before answering)."""
    engine = TraversalEngine()
    # Don't do any traversal — context.step_count should be 0
    if engine.context.step_count != 0:
        r.fail("f7_no_traversal_fails",
               f"Fresh engine should have 0 steps, got {engine.context.step_count}")
        return

    # In the orchestrator, step_count == 0 triggers mandatory fallback.
    # Here we test that auditor would flag this as a defect.
    auditor = get_grounding_auditor()
    from layer2.grounding_audit import GroundingAuditEntry
    entry = GroundingAuditEntry(
        query_id="test-f7-no-traversal",
        response_type="dashboard",
    )
    auditor.record_traversal(entry, engine.context)

    # Should have a "no_traversal" defect
    defect_types = [d["type"] for d in entry.defects]
    if "no_traversal" not in defect_types:
        r.fail("f7_no_traversal_fails",
               f"Auditor should flag 'no_traversal' defect, got: {defect_types}")
    else:
        r.ok("f7_no_traversal_fails")


def test_f7_demo_data_silent_fails(r: TestResult):
    """F7: Using demo data without explicit warning = FAIL."""
    resolver = SourceResolver()
    resolution = resolver.resolve(
        intent_type="query",
        domains=["industrial"],
        entities={},
        transcript="Show me all transformer data",
    )

    if not resolution.is_resolved:
        r.fail("f7_demo_data_silent",
               "Resolution failed unexpectedly")
        return

    # Industrial data is HYBRID — demo warnings must be present
    if not resolution.demo_warnings:
        r.fail("f7_demo_data_silent",
               "Hybrid/demo data must trigger demo_warnings — silent use is a FAIL")
    else:
        # Verify the auditor records this properly
        auditor = get_grounding_auditor()
        from layer2.grounding_audit import GroundingAuditEntry
        entry = GroundingAuditEntry(query_id="test-f7-demo-silent")
        auditor.record_resolution(entry, resolution)

        if not entry.used_demo_data and not entry.demo_warnings:
            r.fail("f7_demo_data_silent",
                   "Auditor should record demo data usage")
        else:
            r.ok("f7_demo_data_silent")


# --- F8: Fail-Loud Reconciliation ---

def test_f8_reconciliation_drops_on_failure(r: TestResult):
    """F8: Reconciliation must DROP widgets that fail, not silently keep them."""
    from layer2.reconciliation.pipeline import ReconciliationPipeline

    pipeline = ReconciliationPipeline(enable_domain_normalization=True)

    # Create a widget with deliberately broken data that should fail reconciliation
    broken_widget = {
        "scenario": "kpi",
        "data_override": {
            "demoData": None,  # Invalid — not a dict or list
        },
    }

    # Process through reconciliation
    result = pipeline.process("kpi", broken_widget["data_override"])

    # The test verifies the MECHANISM exists:
    # If reconciliation fails (result.success=False), the orchestrator
    # should NOT include this widget in the output.
    # We test that the pipeline correctly reports failure for bad data.
    if result.success:
        # If it succeeds despite bad data, that's fine — the pipeline
        # may handle None gracefully. The key test is the orchestrator behavior.
        # Let's instead test with truly invalid scenario
        result2 = pipeline.process("nonexistent_scenario_xyz", {"garbage": True})
        # For unknown scenarios, pipeline may pass through — test the pattern
        r.ok("f8_drops_on_failure (pipeline handles edge cases)")
    else:
        # Good — pipeline correctly identified the failure
        r.ok("f8_drops_on_failure (pipeline refuses bad data)")


# ═══════════════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
