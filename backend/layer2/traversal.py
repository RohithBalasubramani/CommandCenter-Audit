"""
Traversal Actions — Phase 3 of System-Grounded AI Audit.

The AI MUST operate via explicit traversal actions, NOT inference.
Answers MUST be derived AFTER traversal. If the AI answers without
traversal when traversal is possible, that is a MAJOR DEFECT.

This module provides all traversal actions the AI can execute:
- list_databases()
- describe_table(db, table)
- preview_rows(db, table, limit)
- search_collection(collection, query)
- check_entity_exists(entity)
- get_metric_reading(entity, metric)
- get_alert_state(entity)
"""

import logging
import time
from dataclasses import dataclass, field
from typing import Optional, Any

from django.db import connection

logger = logging.getLogger(__name__)


@dataclass
class TraversalStep:
    """A single traversal action and its result."""
    action: str                       # e.g., "list_databases", "describe_table"
    args: dict = field(default_factory=dict)
    result: Any = None
    source_id: str = ""               # Which data source was queried
    duration_ms: int = 0
    success: bool = True
    error: str = ""
    timestamp: float = 0.0

    def to_dict(self) -> dict:
        return {
            "action": self.action,
            "args": self.args,
            "source_id": self.source_id,
            "duration_ms": self.duration_ms,
            "success": self.success,
            "error": self.error,
        }


@dataclass
class TraversalContext:
    """Accumulated context from a sequence of traversal actions."""
    steps: list[TraversalStep] = field(default_factory=list)
    data_found: dict = field(default_factory=dict)  # {entity/metric: value}
    sources_queried: set = field(default_factory=set)
    total_duration_ms: int = 0

    def add_step(self, step: TraversalStep) -> None:
        self.steps.append(step)
        self.sources_queried.add(step.source_id)
        self.total_duration_ms += step.duration_ms

    @property
    def step_count(self) -> int:
        return len(self.steps)

    @property
    def has_data(self) -> bool:
        return len(self.data_found) > 0

    def to_dict(self) -> dict:
        return {
            "step_count": self.step_count,
            "steps": [s.to_dict() for s in self.steps],
            "sources_queried": list(self.sources_queried),
            "total_duration_ms": self.total_duration_ms,
            "data_keys": list(self.data_found.keys()),
        }


class TraversalEngine:
    """
    Engine for executing explicit traversal actions against data sources.

    Every action is logged. Every result is attributed to a source.
    The AI cannot claim data it hasn't traversed.
    """

    def __init__(self):
        self._context = TraversalContext()
        from layer2.system_registry import get_system_registry
        self._registry = get_system_registry()

    @property
    def context(self) -> TraversalContext:
        return self._context

    def reset(self) -> None:
        """Reset traversal context for a new query."""
        self._context = TraversalContext()

    def list_databases(self) -> TraversalStep:
        """List all registered databases/data sources."""
        start = time.time()
        step = TraversalStep(action="list_databases", timestamp=start)

        try:
            from layer2.schema_introspector import SchemaIntrospector
            introspector = SchemaIntrospector()
            result = introspector.list_databases()
            step.result = result
            step.source_id = "system_registry"
            step.success = True
        except Exception as e:
            step.success = False
            step.error = str(e)

        step.duration_ms = int((time.time() - start) * 1000)
        self._context.add_step(step)
        return step

    def describe_table(self, table_name: str) -> TraversalStep:
        """Describe a specific table's schema."""
        start = time.time()
        step = TraversalStep(
            action="describe_table",
            args={"table_name": table_name},
            timestamp=start,
        )

        try:
            from layer2.schema_introspector import SchemaIntrospector
            introspector = SchemaIntrospector()
            result = introspector.describe_table(table_name)
            if result:
                step.result = result
                step.source_id = result["source"]["id"]
                step.success = True
            else:
                step.success = False
                step.error = f"Table '{table_name}' not found in any registered source"
        except Exception as e:
            step.success = False
            step.error = str(e)

        step.duration_ms = int((time.time() - start) * 1000)
        self._context.add_step(step)
        return step

    def preview_rows(self, table_name: str, limit: int = 5) -> TraversalStep:
        """Preview rows from a database table."""
        start = time.time()
        step = TraversalStep(
            action="preview_rows",
            args={"table_name": table_name, "limit": limit},
            timestamp=start,
        )

        try:
            from layer2.schema_introspector import SchemaIntrospector
            introspector = SchemaIntrospector()
            result = introspector.preview_rows(table_name, limit)
            if result:
                step.result = result
                # Find source
                source = self._registry.get_source_for_table(table_name)
                step.source_id = source.id if source else "unknown"
                step.success = True
            else:
                step.success = False
                step.error = f"Could not preview rows from '{table_name}'"
        except Exception as e:
            step.success = False
            step.error = str(e)

        step.duration_ms = int((time.time() - start) * 1000)
        self._context.add_step(step)
        return step

    def search_collection(
        self, collection_name: str, query: str, n_results: int = 5
    ) -> TraversalStep:
        """Search a ChromaDB collection."""
        start = time.time()
        step = TraversalStep(
            action="search_collection",
            args={"collection": collection_name, "query": query, "n_results": n_results},
            timestamp=start,
        )

        try:
            from layer2.rag_pipeline import get_rag_pipeline
            pipeline = get_rag_pipeline()
            vs = pipeline.vector_store
            results = vs.search(collection_name, query, n_results=n_results)

            step.result = {
                "count": len(results),
                "documents": [
                    {
                        "id": r.id,
                        "content_preview": r.content[:200],
                        "metadata": r.metadata,
                        "score": r.score,
                    }
                    for r in results
                ],
            }
            step.source_id = "chromadb.industrial"
            step.success = True

            # Store found data
            for r in results:
                entity_id = r.metadata.get("equipment_id", r.id)
                self._context.data_found[entity_id] = {
                    "content": r.content[:200],
                    "metadata": r.metadata,
                    "source": "chromadb",
                    "score": r.score,
                }

        except Exception as e:
            step.success = False
            step.error = str(e)

        step.duration_ms = int((time.time() - start) * 1000)
        self._context.add_step(step)
        return step

    def check_entity_exists(self, entity_name: str) -> TraversalStep:
        """Check if an entity exists in any registered source."""
        start = time.time()
        step = TraversalStep(
            action="check_entity_exists",
            args={"entity_name": entity_name},
            timestamp=start,
        )

        found_in = []
        try:
            with connection.cursor() as cursor:
                # Check all equipment tables
                for source in self._registry.get_all_sources():
                    if source.source_type.value != "django_orm":
                        continue
                    for table in source.tables:
                        has_eq_id = any(c.name == "equipment_id" for c in table.columns)
                        has_name = any(c.name == "name" for c in table.columns)
                        if not (has_eq_id or has_name):
                            continue
                        try:
                            conditions = []
                            params = []
                            if has_eq_id:
                                conditions.append("equipment_id LIKE %s")
                                params.append(f"%{entity_name}%")
                            if has_name:
                                conditions.append("name LIKE %s")
                                params.append(f"%{entity_name}%")

                            where = " OR ".join(conditions)
                            cursor.execute(
                                f'SELECT COUNT(*) FROM "{table.name}" WHERE {where}',
                                params,
                            )
                            count = cursor.fetchone()[0]
                            if count > 0:
                                found_in.append({
                                    "table": table.name,
                                    "source": source.id,
                                    "count": count,
                                })
                        except Exception:
                            continue

            step.result = {
                "exists": len(found_in) > 0,
                "found_in": found_in,
            }
            step.source_id = found_in[0]["source"] if found_in else "django.industrial"
            step.success = True

        except Exception as e:
            step.success = False
            step.error = str(e)

        step.duration_ms = int((time.time() - start) * 1000)
        self._context.add_step(step)
        return step

    def get_metric_reading(
        self, entity_name: str, metric: str
    ) -> TraversalStep:
        """Get a specific metric reading for an entity from the database."""
        start = time.time()
        step = TraversalStep(
            action="get_metric_reading",
            args={"entity_name": entity_name, "metric": metric},
            timestamp=start,
        )

        try:
            with connection.cursor() as cursor:
                # Search through equipment tables for the entity
                for source in self._registry.get_all_sources():
                    if source.source_type.value != "django_orm":
                        continue
                    for table in source.tables:
                        # Check if this table has the requested metric column
                        metric_col = None
                        for col in table.columns:
                            col_name_lower = col.name.lower().replace("_", "")
                            metric_lower = metric.lower().replace("_", "").replace(" ", "")
                            if metric_lower in col_name_lower or col_name_lower in metric_lower:
                                metric_col = col
                                break

                        if not metric_col:
                            continue

                        # Check if entity exists in this table
                        has_eq_id = any(c.name == "equipment_id" for c in table.columns)
                        has_name = any(c.name == "name" for c in table.columns)
                        if not (has_eq_id or has_name):
                            continue

                        try:
                            conditions = []
                            params = []
                            if has_eq_id:
                                conditions.append("equipment_id LIKE %s")
                                params.append(f"%{entity_name}%")
                            if has_name:
                                conditions.append("name LIKE %s")
                                params.append(f"%{entity_name}%")

                            where = " OR ".join(conditions)
                            cols_to_fetch = ["equipment_id", "name", metric_col.name]
                            cols_sql = ", ".join(
                                f'"{c}"' for c in cols_to_fetch
                                if any(tc.name == c for tc in table.columns)
                            )

                            cursor.execute(
                                f'SELECT {cols_sql} FROM "{table.name}" WHERE {where} LIMIT 1',
                                params,
                            )
                            row = cursor.fetchone()
                            if row:
                                col_names = [desc[0] for desc in cursor.description]
                                reading = dict(zip(col_names, row))
                                step.result = {
                                    "found": True,
                                    "table": table.name,
                                    "reading": reading,
                                    "metric_column": metric_col.name,
                                    "unit": metric_col.unit,
                                }
                                step.source_id = source.id
                                step.success = True

                                # Store in context
                                key = f"{entity_name}.{metric}"
                                self._context.data_found[key] = {
                                    "value": reading.get(metric_col.name),
                                    "unit": metric_col.unit,
                                    "source": source.id,
                                    "table": table.name,
                                }

                                step.duration_ms = int((time.time() - start) * 1000)
                                self._context.add_step(step)
                                return step
                        except Exception:
                            continue

            # Not found
            step.result = {"found": False}
            step.success = True
            step.source_id = "django.industrial"

        except Exception as e:
            step.success = False
            step.error = str(e)

        step.duration_ms = int((time.time() - start) * 1000)
        self._context.add_step(step)
        return step

    def get_alert_state(self, entity_name: Optional[str] = None) -> TraversalStep:
        """Get active alerts, optionally filtered by entity."""
        start = time.time()
        step = TraversalStep(
            action="get_alert_state",
            args={"entity_name": entity_name},
            timestamp=start,
        )

        try:
            with connection.cursor() as cursor:
                if entity_name:
                    cursor.execute(
                        'SELECT COUNT(*) FROM "industrial_alert" '
                        'WHERE resolved_at IS NULL AND '
                        '(equipment_id LIKE %s OR equipment_name LIKE %s)',
                        [f"%{entity_name}%", f"%{entity_name}%"],
                    )
                else:
                    cursor.execute(
                        'SELECT COUNT(*) FROM "industrial_alert" '
                        'WHERE resolved_at IS NULL'
                    )
                active_count = cursor.fetchone()[0]

                # Get severity breakdown
                if entity_name:
                    cursor.execute(
                        'SELECT severity, COUNT(*) FROM "industrial_alert" '
                        'WHERE resolved_at IS NULL AND '
                        '(equipment_id LIKE %s OR equipment_name LIKE %s) '
                        'GROUP BY severity',
                        [f"%{entity_name}%", f"%{entity_name}%"],
                    )
                else:
                    cursor.execute(
                        'SELECT severity, COUNT(*) FROM "industrial_alert" '
                        'WHERE resolved_at IS NULL GROUP BY severity'
                    )
                severity_breakdown = dict(cursor.fetchall())

                step.result = {
                    "active_alert_count": active_count,
                    "severity_breakdown": severity_breakdown,
                    "entity_filter": entity_name,
                }
                step.source_id = "django.industrial"
                step.success = True

                # Store in context
                key = f"alerts:{entity_name or 'all'}"
                self._context.data_found[key] = step.result

        except Exception as e:
            step.success = False
            step.error = str(e)

        step.duration_ms = int((time.time() - start) * 1000)
        self._context.add_step(step)
        return step

    def verify_data_origin(self, data: dict, claimed_source: str) -> TraversalStep:
        """
        Verify that data actually originated from the claimed source.

        This is a post-hoc verification — checks that the data in a response
        can be traced back to an actual traversal.
        """
        start = time.time()
        step = TraversalStep(
            action="verify_data_origin",
            args={"claimed_source": claimed_source},
            timestamp=start,
        )

        # Check if any traversal step actually queried this source
        queried_sources = {s.source_id for s in self._context.steps}
        if claimed_source not in queried_sources:
            step.result = {
                "verified": False,
                "reason": f"Source '{claimed_source}' was never queried during traversal",
                "queried_sources": list(queried_sources),
            }
            step.success = True
        else:
            step.result = {
                "verified": True,
                "queried_sources": list(queried_sources),
            }
            step.success = True

        step.source_id = "verification"
        step.duration_ms = int((time.time() - start) * 1000)
        self._context.add_step(step)
        return step
