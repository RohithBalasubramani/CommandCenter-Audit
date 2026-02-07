"""
Schema Introspector — Runtime schema discovery for all connected databases.

Phase 1B of System-Grounded AI Audit.

Automatically ingests tables, columns, and relations from all connected databases
and persists metadata the AI can query at runtime.

The AI MUST be able to answer:
    "Which table contains this data?"
If it cannot, the system is non-compliant.
"""

import logging
from typing import Optional

from django.apps import apps
from django.db import connection

from layer2.system_registry import (
    get_system_registry,
    DataSource,
    TableSchema,
    ColumnSchema,
    DataSourceType,
    IntegrationStatus,
)

logger = logging.getLogger(__name__)


class SchemaIntrospector:
    """
    Runtime schema discovery for all data sources.

    Traverses Django ORM models and ChromaDB collections to build
    a live view of what data actually exists (not just what's declared).
    """

    def __init__(self):
        self._registry = get_system_registry()

    def introspect_all(self) -> dict:
        """
        Introspect all registered data sources and update row counts / live schema.

        Returns summary of findings.
        """
        results = {
            "django_tables": self._introspect_django(),
            "chromadb_collections": self._introspect_chromadb(),
            "summary": {},
        }

        total_tables = results["django_tables"]["table_count"]
        total_rows = results["django_tables"]["total_rows"]
        total_collections = results["chromadb_collections"]["collection_count"]
        total_docs = results["chromadb_collections"]["total_documents"]

        results["summary"] = {
            "total_tables": total_tables,
            "total_rows": total_rows,
            "total_collections": total_collections,
            "total_documents": total_docs,
            "empty_tables": results["django_tables"]["empty_tables"],
            "empty_collections": results["chromadb_collections"]["empty_collections"],
        }

        logger.info(
            f"[introspect] Complete: {total_tables} tables ({total_rows} rows), "
            f"{total_collections} collections ({total_docs} docs)"
        )
        return results

    def _introspect_django(self) -> dict:
        """Introspect all Django ORM tables."""
        result = {
            "tables": [],
            "table_count": 0,
            "total_rows": 0,
            "empty_tables": [],
        }

        try:
            with connection.cursor() as cursor:
                # Get all tables from SQLite
                cursor.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
                )
                db_tables = [row[0] for row in cursor.fetchall()]

                for table_name in sorted(db_tables):
                    try:
                        cursor.execute(f'SELECT COUNT(*) FROM "{table_name}"')
                        row_count = cursor.fetchone()[0]
                    except Exception:
                        row_count = 0

                    # Get column info
                    columns = []
                    try:
                        cursor.execute(f'PRAGMA table_info("{table_name}")')
                        for col_info in cursor.fetchall():
                            columns.append({
                                "name": col_info[1],
                                "type": col_info[2],
                                "nullable": not col_info[3],
                                "primary_key": bool(col_info[5]),
                            })
                    except Exception:
                        pass

                    table_info = {
                        "name": table_name,
                        "row_count": row_count,
                        "column_count": len(columns),
                        "columns": columns,
                    }
                    result["tables"].append(table_info)
                    result["total_rows"] += row_count

                    if row_count == 0:
                        result["empty_tables"].append(table_name)

                    # Update registry with live row counts
                    for source in self._registry.get_all_sources():
                        for ts in source.tables:
                            if ts.name == table_name:
                                ts.row_count = row_count

                result["table_count"] = len(result["tables"])

        except Exception as e:
            logger.error(f"[introspect] Django introspection failed: {e}")
            result["error"] = str(e)

        return result

    def _introspect_chromadb(self) -> dict:
        """Introspect ChromaDB collections."""
        result = {
            "collections": [],
            "collection_count": 0,
            "total_documents": 0,
            "empty_collections": [],
        }

        try:
            from layer2.rag_pipeline import get_rag_pipeline
            pipeline = get_rag_pipeline()
            vs = pipeline.vector_store

            # List all collections
            try:
                all_collections = vs.client.list_collections()
            except Exception:
                all_collections = []

            for coll in all_collections:
                try:
                    name = coll.name if hasattr(coll, 'name') else str(coll)
                    count = coll.count() if hasattr(coll, 'count') else 0
                except Exception:
                    name = str(coll)
                    count = 0

                coll_info = {
                    "name": name,
                    "document_count": count,
                }
                result["collections"].append(coll_info)
                result["total_documents"] += count

                if count == 0:
                    result["empty_collections"].append(name)

                # Update registry
                for source in self._registry.get_all_sources():
                    for ts in source.tables:
                        if ts.name == name:
                            ts.row_count = count

            result["collection_count"] = len(result["collections"])

        except Exception as e:
            logger.warning(f"[introspect] ChromaDB introspection failed: {e}")
            result["error"] = str(e)

        return result

    def find_table_for_data(self, data_description: str) -> list[dict]:
        """
        Answer: "Which table contains this data?"

        Given a natural-language description, returns matching tables
        from the registry with confidence.
        """
        data_lower = data_description.lower()
        matches = []

        for source in self._registry.get_all_sources():
            for table in source.tables:
                score = 0
                reasons = []

                # Check table name match
                table_lower = table.name.lower().replace("_", " ")
                for word in data_lower.split():
                    if word in table_lower:
                        score += 3
                        reasons.append(f"table name contains '{word}'")

                # Check table description
                if table.description:
                    desc_lower = table.description.lower()
                    for word in data_lower.split():
                        if len(word) > 2 and word in desc_lower:
                            score += 2
                            reasons.append(f"description contains '{word}'")

                # Check column names
                for col in table.columns:
                    col_lower = col.name.lower().replace("_", " ")
                    for word in data_lower.split():
                        if len(word) > 2 and word in col_lower:
                            score += 1
                            reasons.append(f"column '{col.name}' matches '{word}'")

                    # Check column units
                    if col.unit:
                        unit_lower = col.unit.lower()
                        if unit_lower in data_lower:
                            score += 2
                            reasons.append(f"unit '{col.unit}' matches")

                if score > 0:
                    matches.append({
                        "source_id": source.id,
                        "source_name": source.name,
                        "integration_status": source.integration_status.value,
                        "table_name": table.name,
                        "table_description": table.description,
                        "row_count": table.row_count,
                        "relevance_score": score,
                        "match_reasons": reasons[:5],  # Top 5 reasons
                        "is_demo": source.integration_status in (
                            IntegrationStatus.DEMO, IntegrationStatus.STUB
                        ),
                    })

        # Sort by relevance score descending
        matches.sort(key=lambda m: -m["relevance_score"])
        return matches

    def describe_table(self, table_name: str) -> Optional[dict]:
        """
        Traversal action: describe a specific table's schema.

        Returns full column info, row count, and source metadata.
        """
        for source in self._registry.get_all_sources():
            table = source.get_table(table_name)
            if table:
                return {
                    "table_name": table.name,
                    "description": table.description,
                    "primary_key": table.primary_key,
                    "row_count": table.row_count,
                    "columns": [
                        {
                            "name": c.name,
                            "type": c.type,
                            "nullable": c.nullable,
                            "indexed": c.indexed,
                            "unit": c.unit,
                            "description": c.description,
                        }
                        for c in table.columns
                    ],
                    "source": {
                        "id": source.id,
                        "name": source.name,
                        "type": source.source_type.value,
                        "integration_status": source.integration_status.value,
                    },
                }
        return None

    def list_databases(self) -> list[dict]:
        """
        Traversal action: list all databases/data sources.

        Returns summary of each registered source.
        """
        return [
            {
                "id": s.id,
                "name": s.name,
                "type": s.source_type.value,
                "integration_status": s.integration_status.value,
                "domains": s.domains,
                "table_count": len(s.tables),
                "authoritative_for": s.authoritative_for,
                "priority": s.priority,
            }
            for s in self._registry.get_all_sources()
        ]

    def preview_rows(self, table_name: str, limit: int = 5) -> Optional[dict]:
        """
        Traversal action: preview rows from a Django ORM table.

        Returns first N rows as dicts.
        """
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    f'SELECT * FROM "{table_name}" LIMIT %s', [limit]
                )
                columns = [col[0] for col in cursor.description]
                rows = [dict(zip(columns, row)) for row in cursor.fetchall()]

                return {
                    "table_name": table_name,
                    "columns": columns,
                    "row_count": len(rows),
                    "rows": rows,
                }
        except Exception as e:
            logger.warning(f"[introspect] preview_rows({table_name}) failed: {e}")
            return None
