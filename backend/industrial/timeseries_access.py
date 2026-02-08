"""
Time-Series Data Access Layer for Command Center PostgreSQL Database

Provides high-level interface for querying 357 equipment tables containing
3 years of 1-minute interval data (~564M rows, 276 GB) from the
command_center_data PostgreSQL database.

Database: command_center_data
Tables: 357 equipment tables (240 LT panels + 117 major equipment)
Time Range: Feb 2023 - Feb 2026
Interval: 1 minute
Rows per table: 1,578,240

Equipment Types:
- LT Panels: lt_mcc_*, lt_pcc_*, lt_apfc_*, lt_db_*, lt_mldb_*, lt_smdb_*,
              lt_vfd_*, lt_plc_*, lt_ats_*, lt_changeover_*
- Equipment: trf_*, dg_*, ups_*, chiller_*, ahu_*, ct_*, pump_*,
             compressor_*, motor_*, em_*
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from django.db import connections
from dataclasses import dataclass
import pytz

logger = logging.getLogger(__name__)

# IST timezone (all timestamps in DB are in IST)
IST = pytz.timezone('Asia/Kolkata')

# Equipment table prefixes
LT_PANEL_PREFIXES = [
    'lt_mcc', 'lt_pcc', 'lt_apfc', 'lt_db', 'lt_mldb', 'lt_smdb',
    'lt_vfd', 'lt_plc', 'lt_ats', 'lt_changeover'
]

EQUIPMENT_PREFIXES = [
    'trf', 'dg', 'ups', 'chiller', 'ahu', 'ct',
    'pump', 'compressor', 'motor', 'em'
]

ALL_EQUIPMENT_PREFIXES = LT_PANEL_PREFIXES + EQUIPMENT_PREFIXES


@dataclass
class TimeSeriesQuery:
    """Time-series query parameters."""
    equipment_id: str  # e.g., 'chiller_001', 'lt_mcc_045'
    start_time: datetime
    end_time: datetime
    columns: Optional[List[str]] = None  # None = all columns
    aggregation: Optional[str] = None  # 'avg', 'min', 'max', 'sum'
    interval: Optional[str] = None  # e.g., '1 hour', '15 minutes'


@dataclass
class TimeSeriesResult:
    """Time-series query result."""
    equipment_id: str
    data: List[Dict]  # List of {ts, column1, column2, ...}
    row_count: int
    query_time_ms: float


class TimeSeriesDataAccess:
    """
    Service for querying equipment time-series data from PostgreSQL.

    All queries use the 'timeseries' database connection configured in settings.
    """

    def __init__(self):
        self.db_alias = 'timeseries'

    def get_equipment_list(self, prefix: Optional[str] = None) -> List[str]:
        """
        Get list of available equipment tables.

        Args:
            prefix: Filter by equipment prefix (e.g., 'chiller', 'lt_mcc')
                    None = return all equipment tables

        Returns:
            List of equipment IDs (table names)
        """
        query = """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
              AND table_type = 'BASE TABLE'
              AND table_name NOT IN (
                  'buildings', 'zones', 'equipment_registry', 'alerts',
                  'maintenance_records', 'energy_configs', 'bms_setpoints',
                  'bms_schedules', 'rl_config', 'rl_training_log'
              )
        """

        if prefix:
            query += f" AND table_name LIKE '{prefix}_%'"

        query += " ORDER BY table_name"

        with connections[self.db_alias].cursor() as cursor:
            cursor.execute(query)
            return [row[0] for row in cursor.fetchall()]

    def get_table_columns(self, equipment_id: str) -> List[str]:
        """
        Get list of columns for an equipment table.

        Args:
            equipment_id: Equipment table name (e.g., 'chiller_001')

        Returns:
            List of column names
        """
        query = """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name = %s
            ORDER BY ordinal_position
        """

        with connections[self.db_alias].cursor() as cursor:
            cursor.execute(query, [equipment_id])
            return [row[0] for row in cursor.fetchall()]

    def get_latest_reading(self, equipment_id: str) -> Optional[Dict]:
        """
        Get the most recent reading for an equipment.

        Args:
            equipment_id: Equipment table name (e.g., 'chiller_001')

        Returns:
            Dictionary with latest reading, or None if table is empty
        """
        query = f"""
            SELECT *
            FROM {equipment_id}
            ORDER BY timestamp DESC
            LIMIT 1
        """

        start_time = datetime.now()
        with connections[self.db_alias].cursor() as cursor:
            cursor.execute(query)
            columns = [col[0] for col in cursor.description]
            row = cursor.fetchone()

            if row:
                query_time = (datetime.now() - start_time).total_seconds() * 1000
                logger.debug(f"Latest reading query for {equipment_id} took {query_time:.2f}ms")
                return dict(zip(columns, row))
            return None

    def query_timeseries(self, query: TimeSeriesQuery) -> TimeSeriesResult:
        """
        Query time-series data for an equipment.

        Args:
            query: TimeSeriesQuery parameters

        Returns:
            TimeSeriesResult with data and metadata

        Example:
            >>> query = TimeSeriesQuery(
            ...     equipment_id='chiller_001',
            ...     start_time=datetime(2024, 6, 15, 0, 0, tzinfo=IST),
            ...     end_time=datetime(2024, 6, 16, 0, 0, tzinfo=IST),
            ...     columns=['ts', 'active_power_kw', 'water_flow_lpm'],
            ...     aggregation='avg',
            ...     interval='1 hour'
            ... )
            >>> result = tsa.query_timeseries(query)
        """
        equipment_id = query.equipment_id
        columns = query.columns or ['*']
        columns_str = ', '.join(columns)

        # Build query based on aggregation
        if query.aggregation and query.interval:
            # Aggregated query
            agg_func = query.aggregation.upper()
            # Build aggregation columns (skip 'ts' from aggregation)
            agg_cols = [c for c in columns if c not in ['timestamp', 'ts'] and c != '*']
            if not agg_cols or '*' in columns:
                # Get all numeric columns
                all_cols = self.get_table_columns(equipment_id)
                # Filter to numeric columns only (skip id, timestamp, and varchar)
                agg_cols = []
                for col in all_cols:
                    if col in ['timestamp', 'ts', 'id']:
                        continue
                    # Query column type
                    col_type_query = f"SELECT data_type FROM information_schema.columns WHERE table_name = '{equipment_id}' AND column_name = '{col}'"
                    cursor.execute(col_type_query)
                    col_type_row = cursor.fetchone()
                    if col_type_row and 'double' in col_type_row[0]:
                        agg_cols.append(col)

            agg_select = ', '.join([
                f"{agg_func}({col}) as {col}" for col in agg_cols
            ])

            sql = f"""
                SELECT
                    date_trunc('{query.interval}', timestamp) as timestamp,
                    {agg_select}
                FROM {equipment_id}
                WHERE timestamp >= %s AND timestamp < %s
                GROUP BY date_trunc('{query.interval}', timestamp)
                ORDER BY 1
            """
        else:
            # Raw query
            sql = f"""
                SELECT {columns_str}
                FROM {equipment_id}
                WHERE timestamp >= %s AND timestamp < %s
                ORDER BY timestamp
            """

        start_time = datetime.now()
        with connections[self.db_alias].cursor() as cursor:
            cursor.execute(sql, [query.start_time, query.end_time])
            columns_fetched = [col[0] for col in cursor.description]
            rows = cursor.fetchall()

            query_time = (datetime.now() - start_time).total_seconds() * 1000

            data = [dict(zip(columns_fetched, row)) for row in rows]

            logger.info(
                f"Query {equipment_id}: {len(data)} rows in {query_time:.2f}ms "
                f"({query.start_time} to {query.end_time})"
            )

            return TimeSeriesResult(
                equipment_id=equipment_id,
                data=data,
                row_count=len(data),
                query_time_ms=query_time
            )

    def get_aggregated_stats(
        self,
        equipment_id: str,
        start_time: datetime,
        end_time: datetime,
        columns: Optional[List[str]] = None
    ) -> Dict:
        """
        Get aggregated statistics (min, max, avg, sum) for an equipment
        over a time period.

        Args:
            equipment_id: Equipment table name
            start_time: Start of time range
            end_time: End of time range
            columns: Columns to aggregate (None = all numeric columns)

        Returns:
            Dictionary with stats for each column
        """
        if columns is None:
            # Get all numeric columns (skip timestamp, id, and VARCHAR columns)
            all_cols = self.get_table_columns(equipment_id)
            columns = [
                c for c in all_cols
                if c not in ['timestamp', 'ts', 'id']
                and not c.endswith('_status')
                and not c.endswith('_state')
                and not c.endswith('_mode')
                and not c.endswith('_alarm')
            ]

        # Build aggregation query
        agg_parts = []
        for col in columns:
            agg_parts.extend([
                f"MIN({col}) as {col}_min",
                f"MAX({col}) as {col}_max",
                f"AVG({col}) as {col}_avg",
                f"SUM({col}) as {col}_sum",
            ])
        agg_select = ', '.join(agg_parts)

        sql = f"""
            SELECT
                COUNT(*) as row_count,
                {agg_select}
            FROM {equipment_id}
            WHERE timestamp >= %s AND timestamp < %s
        """

        with connections[self.db_alias].cursor() as cursor:
            cursor.execute(sql, [start_time, end_time])
            columns_fetched = [col[0] for col in cursor.description]
            row = cursor.fetchone()

            return dict(zip(columns_fetched, row)) if row else {}

    def get_anomalies(
        self,
        equipment_id: str,
        start_time: datetime,
        end_time: datetime,
        threshold_column: str,
        threshold_value: float,
        operator: str = '>'
    ) -> List[Dict]:
        """
        Find anomalous readings based on a threshold.

        Args:
            equipment_id: Equipment table name
            start_time: Start of time range
            end_time: End of time range
            threshold_column: Column to check
            threshold_value: Threshold value
            operator: Comparison operator ('>', '<', '>=', '<=', '!=')

        Returns:
            List of anomalous readings
        """
        sql = f"""
            SELECT *
            FROM {equipment_id}
            WHERE timestamp >= %s AND timestamp < %s
              AND {threshold_column} {operator} %s
            ORDER BY timestamp
        """

        with connections[self.db_alias].cursor() as cursor:
            cursor.execute(sql, [start_time, end_time, threshold_value])
            columns = [col[0] for col in cursor.description]
            rows = cursor.fetchall()

            return [dict(zip(columns, row)) for row in rows]

    def get_equipment_metadata(self, equipment_id: str) -> Optional[Dict]:
        """
        Get metadata for an equipment from the equipment_registry table.

        Args:
            equipment_id: Equipment table name

        Returns:
            Dictionary with equipment metadata
        """
        query = """
            SELECT *
            FROM equipment_registry
            WHERE equipment_id = %s
        """

        with connections[self.db_alias].cursor() as cursor:
            cursor.execute(query, [equipment_id])
            columns = [col[0] for col in cursor.description]
            row = cursor.fetchone()

            return dict(zip(columns, row)) if row else None

    def get_alerts(
        self,
        equipment_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        severity: Optional[str] = None
    ) -> List[Dict]:
        """
        Get alerts from the alerts table.

        Args:
            equipment_id: Filter by equipment (None = all equipment)
            start_time: Filter by time range start
            end_time: Filter by time range end
            severity: Filter by severity ('critical', 'high', 'medium', 'low')

        Returns:
            List of alerts
        """
        conditions = []
        params = []

        if equipment_id:
            conditions.append("equipment_id = %s")
            params.append(equipment_id)

        if start_time:
            conditions.append("timestamp >= %s")
            params.append(start_time)

        if end_time:
            conditions.append("timestamp < %s")
            params.append(end_time)

        if severity:
            conditions.append("severity = %s")
            params.append(severity)

        where_clause = " AND ".join(conditions) if conditions else "1=1"

        query = f"""
            SELECT *
            FROM alerts
            WHERE {where_clause}
            ORDER BY timestamp DESC
            LIMIT 1000
        """

        with connections[self.db_alias].cursor() as cursor:
            cursor.execute(query, params)
            columns = [col[0] for col in cursor.description]
            rows = cursor.fetchall()

            return [dict(zip(columns, row)) for row in rows]

    def execute_raw_query(self, sql: str, params: Optional[List] = None) -> List[Dict]:
        """
        Execute a raw SQL query (for advanced use cases).

        Args:
            sql: SQL query string
            params: Query parameters (for parameterized queries)

        Returns:
            List of result dictionaries

        Warning:
            Use with caution. Prefer the type-safe methods above.
        """
        with connections[self.db_alias].cursor() as cursor:
            cursor.execute(sql, params or [])
            columns = [col[0] for col in cursor.description]
            rows = cursor.fetchall()

            return [dict(zip(columns, row)) for row in rows]


# Singleton instance
_timeseries_access = None


def get_timeseries_access() -> TimeSeriesDataAccess:
    """Get singleton TimeSeriesDataAccess instance."""
    global _timeseries_access
    if _timeseries_access is None:
        _timeseries_access = TimeSeriesDataAccess()
    return _timeseries_access
