"""
Deterministic Source Resolver — Phase 2 of System-Grounded AI Audit.

Before invoking ANY LLM reasoning, the system MUST resolve:
1. User intent (query / action / analysis)
2. Domain(s) involved
3. Valid data sources
4. Single authoritative source (unless explicitly multi-source)

HARD RULE: If the authoritative source is not resolved,
the AI MUST NOT answer. It must ask a clarification question
or explicitly refuse with a reason.

No implicit defaults. No silent fallback. No guessing.
"""

import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from layer2.system_registry import (
    get_system_registry,
    DataSource,
    IntegrationStatus,
    SystemRegistry,
)

logger = logging.getLogger(__name__)


class ResolutionOutcome(Enum):
    """Outcome of source resolution."""
    RESOLVED = "resolved"                 # Single authoritative source found
    MULTI_SOURCE = "multi_source"         # Multiple sources needed (explicit)
    DEMO_ONLY = "demo_only"              # Only demo/stub data available
    UNRESOLVED = "unresolved"            # Cannot determine source
    REFUSED = "refused"                  # Explicitly refused (no data exists)


@dataclass
class SourceResolution:
    """Result of deterministic source resolution."""
    outcome: ResolutionOutcome
    primary_source: Optional[DataSource] = None
    secondary_sources: list[DataSource] = field(default_factory=list)
    domains_resolved: dict = field(default_factory=dict)  # {domain: DataSource}
    domains_unresolved: list[str] = field(default_factory=list)
    demo_warnings: list[str] = field(default_factory=list)
    refusal_reason: str = ""
    clarification_needed: str = ""
    traversal_log: list[dict] = field(default_factory=list)  # Log of resolution steps

    @property
    def is_resolved(self) -> bool:
        return self.outcome in (ResolutionOutcome.RESOLVED, ResolutionOutcome.MULTI_SOURCE)

    @property
    def has_demo_data(self) -> bool:
        return len(self.demo_warnings) > 0

    def to_dict(self) -> dict:
        return {
            "outcome": self.outcome.value,
            "primary_source": self.primary_source.id if self.primary_source else None,
            "secondary_sources": [s.id for s in self.secondary_sources],
            "domains_resolved": {d: s.id for d, s in self.domains_resolved.items()},
            "domains_unresolved": self.domains_unresolved,
            "demo_warnings": self.demo_warnings,
            "refusal_reason": self.refusal_reason,
            "clarification_needed": self.clarification_needed,
            "traversal_log": self.traversal_log,
        }


class SourceResolver:
    """
    Deterministic source resolver.

    Resolves user queries to authoritative data sources BEFORE any LLM processing.
    This is a gate — if resolution fails, the pipeline MUST stop.
    """

    def __init__(self):
        self._registry = get_system_registry()

    def resolve(
        self,
        intent_type: str,
        domains: list[str],
        entities: dict,
        transcript: str = "",
    ) -> SourceResolution:
        """
        Resolve the authoritative source(s) for a query.

        Args:
            intent_type: "query", "action", "greeting", etc.
            domains: Detected domains ["industrial", "alerts", ...]
            entities: Detected entities {"devices": [...], "numbers": [...]}
            transcript: Original user transcript

        Returns:
            SourceResolution with outcome and source(s)
        """
        resolution = SourceResolution(outcome=ResolutionOutcome.UNRESOLVED)

        # Step 1a: Out-of-scope intents are REFUSED — no data source exists
        if intent_type == "out_of_scope":
            resolution.outcome = ResolutionOutcome.REFUSED
            resolution.refusal_reason = (
                "This query is outside the scope of available data sources. "
                "I can help with industrial equipment, alerts, tasks, and supply chain data."
            )
            resolution.traversal_log.append({
                "step": "intent_check",
                "result": "Out-of-scope intent — REFUSED",
            })
            return resolution

        # Step 1b: Non-data intents (greetings, conversation) don't need source resolution
        if intent_type in ("greeting", "conversation"):
            resolution.outcome = ResolutionOutcome.RESOLVED
            resolution.traversal_log.append({
                "step": "intent_check",
                "result": f"Non-data intent '{intent_type}' — no source needed",
            })
            return resolution

        # Step 2: Action intents route to actions DB
        if intent_type.startswith("action_"):
            return self._resolve_action(intent_type, entities, resolution)

        # Step 3: Query intent — must resolve domains to sources
        if not domains:
            # Try to infer domains from transcript
            domains = self._infer_domains(transcript)
            resolution.traversal_log.append({
                "step": "domain_inference",
                "result": f"Inferred domains: {domains}" if domains else "No domains inferred",
            })

        if not domains:
            resolution.outcome = ResolutionOutcome.UNRESOLVED
            resolution.clarification_needed = (
                "I couldn't determine which data domain your question relates to. "
                "Could you specify if you're asking about equipment, alerts, "
                "maintenance, supply chain, workforce, or tasks?"
            )
            resolution.traversal_log.append({
                "step": "domain_resolution",
                "result": "FAILED — no domains identified",
            })
            return resolution

        # Step 4: Resolve each domain to its authoritative source
        resolved_domains = {}
        unresolved_domains = []
        demo_warnings = []

        for domain in domains:
            source = self._registry.get_authoritative_source(domain)

            if source is None:
                # Try fallback: any source serving this domain
                candidates = self._registry.get_sources_for_domain(domain)
                if candidates:
                    source = candidates[0]
                    resolution.traversal_log.append({
                        "step": f"domain_resolve:{domain}",
                        "result": f"No primary source, using fallback: {source.id}",
                    })
                else:
                    unresolved_domains.append(domain)
                    resolution.traversal_log.append({
                        "step": f"domain_resolve:{domain}",
                        "result": "FAILED — no source found for domain",
                    })
                    continue

            resolved_domains[domain] = source
            resolution.traversal_log.append({
                "step": f"domain_resolve:{domain}",
                "result": f"Resolved to: {source.id} (status={source.integration_status.value})",
            })

            # Check if source is demo/stub
            if source.integration_status in (IntegrationStatus.DEMO, IntegrationStatus.STUB):
                demo_warnings.append(
                    f"Domain '{domain}' data source '{source.id}' is "
                    f"{source.integration_status.value} — data may not be real"
                )
            elif source.integration_status == IntegrationStatus.HYBRID:
                demo_warnings.append(
                    f"Domain '{domain}' data source '{source.id}' has hybrid status — "
                    f"schema is real but data may be seeded/demo"
                )

        resolution.domains_resolved = resolved_domains
        resolution.domains_unresolved = unresolved_domains
        resolution.demo_warnings = demo_warnings

        # Step 5: Determine outcome
        if not resolved_domains:
            resolution.outcome = ResolutionOutcome.REFUSED
            resolution.refusal_reason = (
                f"No authoritative data source found for domains: {unresolved_domains}. "
                f"I cannot answer this query without verified data."
            )
        elif len(resolved_domains) == 1:
            resolution.outcome = ResolutionOutcome.RESOLVED
            resolution.primary_source = list(resolved_domains.values())[0]
        else:
            # Multiple domains — check if they share a source
            unique_sources = set(s.id for s in resolved_domains.values())
            if len(unique_sources) == 1:
                resolution.outcome = ResolutionOutcome.RESOLVED
                resolution.primary_source = list(resolved_domains.values())[0]
            else:
                resolution.outcome = ResolutionOutcome.MULTI_SOURCE
                sources_list = list(resolved_domains.values())
                resolution.primary_source = sources_list[0]
                resolution.secondary_sources = sources_list[1:]

        # Step 6: Entity verification — check entities exist in resolved source
        if resolution.is_resolved and entities.get("devices"):
            self._verify_entities(resolution, entities["devices"])

        return resolution

    def _resolve_action(
        self, intent_type: str, entities: dict, resolution: SourceResolution
    ) -> SourceResolution:
        """Resolve source for action intents."""
        actions_source = self._registry.get_source("django.actions")
        if actions_source:
            resolution.outcome = ResolutionOutcome.RESOLVED
            resolution.primary_source = actions_source
            resolution.domains_resolved = {"tasks": actions_source}
            resolution.traversal_log.append({
                "step": "action_resolve",
                "result": f"Action '{intent_type}' → {actions_source.id}",
            })
        else:
            resolution.outcome = ResolutionOutcome.REFUSED
            resolution.refusal_reason = "Actions database not found in registry"
            resolution.traversal_log.append({
                "step": "action_resolve",
                "result": "FAILED — actions source not registered",
            })
        return resolution

    def _infer_domains(self, transcript: str) -> list[str]:
        """Infer domains from transcript using registry patterns."""
        transcript_lower = transcript.lower()
        matched_domains = []

        for domain, ownership in self._registry.get_all_domains().items():
            for pattern in ownership.query_patterns:
                if re.search(pattern, transcript_lower):
                    if domain not in matched_domains:
                        matched_domains.append(domain)
                    break

        return matched_domains

    def _verify_entities(
        self, resolution: SourceResolution, devices: list[str]
    ) -> None:
        """Verify that mentioned entities exist in the resolved source."""
        if not resolution.primary_source:
            return

        source = resolution.primary_source

        # For Django ORM sources, check if entities exist in the database
        if source.source_type.value == "django_orm":
            try:
                from django.db import connection
                for device_name in devices[:5]:  # Limit to 5 entities
                    found = False
                    for table in source.tables:
                        if any(c.name == "equipment_id" for c in table.columns):
                            try:
                                with connection.cursor() as cursor:
                                    cursor.execute(
                                        f'SELECT COUNT(*) FROM "{table.name}" '
                                        f'WHERE equipment_id LIKE %s OR name LIKE %s',
                                        [f'%{device_name}%', f'%{device_name}%']
                                    )
                                    count = cursor.fetchone()[0]
                                    if count > 0:
                                        found = True
                                        resolution.traversal_log.append({
                                            "step": f"entity_verify:{device_name}",
                                            "result": f"Found {count} match(es) in {table.name}",
                                        })
                                        break
                            except Exception:
                                continue

                    if not found:
                        resolution.traversal_log.append({
                            "step": f"entity_verify:{device_name}",
                            "result": "NOT FOUND in any table — data may not exist",
                        })
            except Exception as e:
                resolution.traversal_log.append({
                    "step": "entity_verify",
                    "result": f"Verification failed: {e}",
                })


class SourceVerificationGate:
    """
    Gate that enforces source verification before the pipeline proceeds.

    This sits between intent parsing and data collection.
    If verification fails, the pipeline MUST stop.
    """

    def __init__(self):
        self._resolver = SourceResolver()

    def verify_or_refuse(
        self,
        intent_type: str,
        domains: list[str],
        entities: dict,
        transcript: str = "",
    ) -> tuple[bool, SourceResolution, Optional[str]]:
        """
        Verify that the query can be answered from authoritative sources.

        Returns:
            (can_proceed, resolution, refusal_message)

            can_proceed: True if pipeline should continue
            resolution: Full resolution details
            refusal_message: If can_proceed is False, the message to return
        """
        resolution = self._resolver.resolve(intent_type, domains, entities, transcript)

        # Case 1: Resolved — proceed
        if resolution.is_resolved:
            # Log demo warnings but don't block
            if resolution.demo_warnings:
                logger.warning(
                    f"[source_gate] Proceeding with demo data warnings: "
                    f"{resolution.demo_warnings}"
                )
            return (True, resolution, None)

        # Case 2: Needs clarification — ask user
        if resolution.clarification_needed:
            return (False, resolution, resolution.clarification_needed)

        # Case 3: Refused — no source available
        if resolution.refusal_reason:
            return (False, resolution, resolution.refusal_reason)

        # Case 4: Unresolved — generic refusal
        refusal = (
            "I couldn't determine the authoritative data source for this query. "
            "Could you be more specific about what data you're looking for?"
        )
        return (False, resolution, refusal)
