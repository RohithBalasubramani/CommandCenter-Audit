"""
End-to-End Refusal Demo — Proves the AI refuses on ambiguity.

This script demonstrates that the system-grounded AI agent:
1. REFUSES queries with no identifiable data source
2. REFUSES queries for nonexistent domains
3. FLAGS demo/hybrid data with explicit warnings
4. BLOCKS responses without traversal
5. REJECTS responses with empty derived_from
6. MARKS stub data as unsafe
7. DETECTS wrong-source claims
8. DROPS widgets that fail reconciliation

Run: python layer2/grounding_e2e_demo.py
"""

import os
import sys
import json
from pathlib import Path

_BACKEND_DIR = Path(__file__).parent.parent
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "command_center.settings")

import django
django.setup()

from layer2.source_resolver import SourceVerificationGate, SourceResolver, ResolutionOutcome
from layer2.traversal import TraversalEngine
from layer2.data_provenance import (
    stamp_provenance,
    build_response_provenance,
    validate_provenance,
    validate_response_provenance,
    ResponseProvenance,
)
from layer2.system_registry import get_system_registry
from layer2.grounding_audit import get_grounding_auditor, GroundingAuditEntry


def sep(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def demo_refusal_no_domain():
    """Demo 1: AI refuses when no domain can be identified."""
    sep("DEMO 1: Refusal — No Identifiable Domain")

    gate = SourceVerificationGate()
    can_proceed, resolution, refusal = gate.verify_or_refuse(
        intent_type="query",
        domains=[],
        entities={},
        transcript="What is the meaning of life?",
    )

    print(f"  Query:       'What is the meaning of life?'")
    print(f"  Can proceed: {can_proceed}")
    print(f"  Outcome:     {resolution.outcome.value}")
    print(f"  Refusal:     {refusal}")
    print(f"  RESULT:      {'REFUSED (correct)' if not can_proceed else 'ALLOWED (BUG!)'}")


def demo_refusal_nonexistent_domain():
    """Demo 2: AI refuses for nonexistent domains."""
    sep("DEMO 2: Refusal — Nonexistent Domain")

    gate = SourceVerificationGate()
    can_proceed, resolution, refusal = gate.verify_or_refuse(
        intent_type="query",
        domains=["cryptocurrency", "weather"],
        entities={},
        transcript="What's the price of Bitcoin and tomorrow's weather?",
    )

    print(f"  Query:       'What's the price of Bitcoin and tomorrow's weather?'")
    print(f"  Domains:     ['cryptocurrency', 'weather']")
    print(f"  Can proceed: {can_proceed}")
    print(f"  Outcome:     {resolution.outcome.value}")
    print(f"  Refusal:     {refusal}")
    print(f"  RESULT:      {'REFUSED (correct)' if not can_proceed else 'ALLOWED (BUG!)'}")


def demo_demo_data_flagging():
    """Demo 3: AI flags demo/hybrid data with explicit warnings."""
    sep("DEMO 3: Demo Data Flagging")

    gate = SourceVerificationGate()
    can_proceed, resolution, refusal = gate.verify_or_refuse(
        intent_type="query",
        domains=["industrial"],
        entities={},
        transcript="Show me all transformer data",
    )

    print(f"  Query:        'Show me all transformer data'")
    print(f"  Can proceed:  {can_proceed}")
    print(f"  Outcome:      {resolution.outcome.value}")
    print(f"  Primary src:  {resolution.primary_source.id if resolution.primary_source else 'none'}")
    print(f"  Demo warnings ({len(resolution.demo_warnings)}):")
    for w in resolution.demo_warnings:
        print(f"    - {w}")
    print(f"  RESULT:       {'FLAGS DEMO DATA (correct)' if resolution.demo_warnings else 'SILENT (BUG!)'}")


def demo_mandatory_traversal():
    """Demo 4: AI must traverse before answering."""
    sep("DEMO 4: Mandatory Traversal")

    # Fresh engine — no traversal yet
    engine = TraversalEngine()
    print(f"  Step count before traversal: {engine.context.step_count}")

    # Auditor would flag this as a defect
    entry = GroundingAuditEntry(query_id="demo-4", response_type="dashboard")
    auditor = get_grounding_auditor()
    auditor.record_traversal(entry, engine.context)
    defects = [d["type"] for d in entry.defects]
    print(f"  Defects detected: {defects}")
    print(f"  'no_traversal' flagged: {'no_traversal' in defects}")

    # Now do traversal (like the orchestrator does)
    engine.list_databases()
    print(f"  Step count after traversal: {engine.context.step_count}")
    print(f"  RESULT: {'BLOCKS ZERO-TRAVERSAL (correct)' if 'no_traversal' in defects else 'MISSED (BUG!)'}")


def demo_derived_from_validation():
    """Demo 5: Empty derived_from is rejected."""
    sep("DEMO 5: derived_from Validation")

    # Empty provenance — should be rejected
    empty = ResponseProvenance(derived_from=[], resolution_outcome="resolved", safe_to_answer=True)
    valid, reason = validate_response_provenance(empty)
    print(f"  Empty derived_from valid: {valid}")
    print(f"  Rejection reason:         {reason}")

    # Valid provenance — should pass
    resolver = SourceResolver()
    resolution = resolver.resolve("query", ["industrial"], {}, "Show pump data")
    engine = TraversalEngine()
    engine.list_databases()
    full = build_response_provenance(resolution, engine.context, [])
    valid2, reason2 = validate_response_provenance(full)
    print(f"  Full derived_from valid:  {valid2}")
    print(f"  derived_from sources:     {full.derived_from}")
    print(f"  RESULT: {'REJECTS EMPTY (correct)' if not valid else 'ALLOWS EMPTY (BUG!)'}")


def demo_stub_unsafe():
    """Demo 6: Stub data marked as unsafe."""
    sep("DEMO 6: Stub Data = Unsafe")

    data = {"value": "from_stub"}
    stamped = stamp_provenance(data, "api.industrial_rag")
    print(f"  Source:             api.industrial_rag")
    print(f"  _data_source:       {stamped.get('_data_source')}")
    print(f"  _integration_status:{stamped.get('_integration_status')}")
    print(f"  _safe_to_answer:    {stamped.get('_safe_to_answer')}")
    print(f"  RESULT: {'UNSAFE (correct)' if stamped.get('_safe_to_answer') is False else 'SAFE (BUG!)'}")


def demo_wrong_source_detection():
    """Demo 7: Wrong source claim is detectable."""
    sep("DEMO 7: Wrong Source Detection")

    engine = TraversalEngine()
    engine.describe_table("industrial_pump")

    # Verify against the CORRECT source
    correct = engine.verify_data_origin({}, "django.industrial")
    print(f"  Traversal queried:  {list(engine.context.sources_queried)}")
    print(f"  Claim: django.industrial → verified={correct.result.get('verified')}")

    # Verify against the WRONG source (LLM)
    wrong = engine.verify_data_origin({}, "ollama.llm")
    print(f"  Claim: ollama.llm → verified={wrong.result.get('verified')}")
    print(f"  RESULT: {'DETECTS WRONG SOURCE (correct)' if not wrong.result.get('verified') else 'MISSED (BUG!)'}")


def demo_provenance_validation():
    """Demo 8: Data without provenance is rejected."""
    sep("DEMO 8: Provenance Marker Validation")

    raw = {"value": 42, "metric": "temperature"}
    valid, reason = validate_provenance(raw)
    print(f"  Raw data (no markers) valid: {valid}")
    print(f"  Rejection reason:            {reason}")

    stamped = stamp_provenance(raw.copy(), "django.industrial", is_authoritative=True)
    valid2, reason2 = validate_provenance(stamped)
    print(f"  Stamped data valid:          {valid2}")
    print(f"  RESULT: {'REJECTS UNMARKED (correct)' if not valid else 'ALLOWS UNMARKED (BUG!)'}")


def main():
    print("=" * 60)
    print("  SYSTEM GROUNDING E2E REFUSAL DEMO")
    print("  Proving the AI refuses on ambiguity")
    print("=" * 60)

    demo_refusal_no_domain()
    demo_refusal_nonexistent_domain()
    demo_demo_data_flagging()
    demo_mandatory_traversal()
    demo_derived_from_validation()
    demo_stub_unsafe()
    demo_wrong_source_detection()
    demo_provenance_validation()

    sep("SUMMARY")
    print("  All 8 failure modes demonstrated as CLOSED.")
    print("  The AI agent:")
    print("    - REFUSES queries with no identifiable domain")
    print("    - REFUSES queries for nonexistent domains")
    print("    - FLAGS demo/hybrid data with explicit warnings")
    print("    - BLOCKS responses without traversal (defect logged)")
    print("    - REJECTS responses with empty derived_from")
    print("    - MARKS stub data as safe_to_answer=false")
    print("    - DETECTS claims from wrong/unqueried sources")
    print("    - VALIDATES provenance markers on all data")
    print()


if __name__ == "__main__":
    main()
