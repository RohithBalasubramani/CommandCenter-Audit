"""
Grounding Audit Trail — Phase 5 of System-Grounded AI Audit.

Logs every query's traversal path, source resolution, and data origin.
Enables post-hoc analysis of:
- Wrong-source incidents
- Traversal skips
- Demo data usage
- Resolution failures

This is the learning system — it records what the AI did so we can
improve source resolution and penalize guessing.
"""

import json
import logging
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Audit log directory
_BACKEND_DIR = Path(__file__).parent.parent
AUDIT_LOG_DIR = _BACKEND_DIR / "grounding_audit_logs"


@dataclass
class GroundingAuditEntry:
    """A single audit entry for one query."""
    query_id: str
    timestamp: str = ""
    transcript: str = ""

    # Source resolution
    resolution_outcome: str = ""          # resolved, unresolved, refused, demo_only
    primary_source_id: str = ""
    domains_resolved: dict = field(default_factory=dict)
    domains_unresolved: list = field(default_factory=list)
    demo_warnings: list = field(default_factory=list)

    # Traversal
    traversal_steps: list = field(default_factory=list)
    traversal_step_count: int = 0
    sources_queried: list = field(default_factory=list)
    traversal_duration_ms: int = 0

    # Data origin
    data_verified: bool = False
    data_origin_source: str = ""
    used_demo_data: bool = False
    used_synthetic_data: bool = False

    # Outcome
    response_type: str = ""               # dashboard, refusal, clarification, greeting
    widget_count: int = 0
    confidence: float = 0.0

    # Defects detected
    defects: list = field(default_factory=list)

    def add_defect(self, defect_type: str, description: str, severity: str = "major"):
        self.defects.append({
            "type": defect_type,
            "description": description,
            "severity": severity,
            "timestamp": datetime.now().isoformat(),
        })


class GroundingAuditor:
    """
    Records and analyzes grounding audit data.

    Every query processed by the orchestrator gets an audit entry.
    Defects are flagged in real-time.
    """

    def __init__(self):
        self._entries: list[GroundingAuditEntry] = []
        self._ensure_log_dir()

    def _ensure_log_dir(self):
        try:
            AUDIT_LOG_DIR.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.warning(f"[grounding_audit] Could not create log dir: {e}")

    def start_entry(self, query_id: str, transcript: str) -> GroundingAuditEntry:
        """Start a new audit entry for a query."""
        entry = GroundingAuditEntry(
            query_id=query_id,
            timestamp=datetime.now().isoformat(),
            transcript=transcript,
        )
        self._entries.append(entry)
        return entry

    def record_resolution(self, entry: GroundingAuditEntry, resolution) -> None:
        """Record source resolution results."""
        entry.resolution_outcome = resolution.outcome.value
        entry.primary_source_id = resolution.primary_source.id if resolution.primary_source else ""
        entry.domains_resolved = {d: s.id for d, s in resolution.domains_resolved.items()}
        entry.domains_unresolved = resolution.domains_unresolved
        entry.demo_warnings = resolution.demo_warnings

        # Defect: unresolved domains
        for domain in resolution.domains_unresolved:
            entry.add_defect(
                "unresolved_domain",
                f"Domain '{domain}' has no authoritative source",
                severity="critical",
            )

        # Defect: demo data used
        if resolution.demo_warnings:
            entry.add_defect(
                "demo_data_used",
                f"Demo/stub data sources used: {resolution.demo_warnings}",
                severity="warning",
            )
            entry.used_demo_data = True

    def record_traversal(self, entry: GroundingAuditEntry, traversal_context) -> None:
        """Record traversal actions and results."""
        entry.traversal_steps = [s.to_dict() for s in traversal_context.steps]
        entry.traversal_step_count = traversal_context.step_count
        entry.sources_queried = list(traversal_context.sources_queried)
        entry.traversal_duration_ms = traversal_context.total_duration_ms

        # Defect: no traversal performed for a data query
        if traversal_context.step_count == 0 and entry.response_type == "dashboard":
            entry.add_defect(
                "no_traversal",
                "Dashboard response generated without any traversal actions",
                severity="critical",
            )

    def record_response(
        self,
        entry: GroundingAuditEntry,
        response_type: str,
        widget_count: int = 0,
        confidence: float = 0.0,
    ) -> None:
        """Record the response outcome."""
        entry.response_type = response_type
        entry.widget_count = widget_count
        entry.confidence = confidence

    def record_data_origin(
        self,
        entry: GroundingAuditEntry,
        source_id: str,
        verified: bool,
        used_synthetic: bool = False,
    ) -> None:
        """Record data origin verification."""
        entry.data_origin_source = source_id
        entry.data_verified = verified
        entry.used_synthetic_data = used_synthetic

        if not verified:
            entry.add_defect(
                "unverified_data_origin",
                f"Data origin from '{source_id}' could not be verified",
                severity="major",
            )

        if used_synthetic:
            entry.add_defect(
                "synthetic_data_used",
                "Synthetic/generated data was used in the response",
                severity="warning",
            )

    def finalize_entry(self, entry: GroundingAuditEntry) -> None:
        """Finalize and persist an audit entry."""
        # Write to log file
        try:
            log_file = AUDIT_LOG_DIR / f"audit_{entry.query_id}.json"
            with open(log_file, "w") as f:
                json.dump(asdict(entry), f, indent=2, default=str)
        except Exception as e:
            logger.warning(f"[grounding_audit] Failed to write audit log: {e}")

        # Log summary
        defect_count = len(entry.defects)
        if defect_count > 0:
            logger.warning(
                f"[grounding_audit] Query {entry.query_id}: "
                f"{defect_count} defect(s) detected — "
                f"{[d['type'] for d in entry.defects]}"
            )
        else:
            logger.info(
                f"[grounding_audit] Query {entry.query_id}: CLEAN — "
                f"outcome={entry.resolution_outcome}, "
                f"traversal_steps={entry.traversal_step_count}, "
                f"response={entry.response_type}"
            )

    def get_recent_entries(self, limit: int = 20) -> list[dict]:
        """Get recent audit entries."""
        return [asdict(e) for e in self._entries[-limit:]]

    def get_defect_summary(self) -> dict:
        """Get summary of all defects across recent entries."""
        defect_counts = {}
        total_entries = len(self._entries)
        defective_entries = 0

        for entry in self._entries:
            if entry.defects:
                defective_entries += 1
            for defect in entry.defects:
                dtype = defect["type"]
                if dtype not in defect_counts:
                    defect_counts[dtype] = {"count": 0, "severity": defect["severity"]}
                defect_counts[dtype]["count"] += 1

        return {
            "total_entries": total_entries,
            "defective_entries": defective_entries,
            "defect_rate": (defective_entries / total_entries * 100) if total_entries > 0 else 0,
            "defect_types": defect_counts,
        }


# Singleton
_auditor_instance: Optional[GroundingAuditor] = None


def get_grounding_auditor() -> GroundingAuditor:
    global _auditor_instance
    if _auditor_instance is None:
        _auditor_instance = GroundingAuditor()
    return _auditor_instance
