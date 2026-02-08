"""
Time-Series RAG Integration for Command Center PostgreSQL Database

Integrates the historical equipment data from PostgreSQL with the RAG pipeline,
allowing the AI to answer questions about equipment performance, trends,
anomalies, and historical behavior.

This module:
1. Queries time-series data from PostgreSQL
2. Formats it for RAG context
3. Provides equipment history for LLM responses
4. Supports trend analysis and anomaly detection queries
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import pytz

from industrial.timeseries_access import (
    get_timeseries_access,
    TimeSeriesQuery,
    IST
)

logger = logging.getLogger(__name__)


class TimeSeriesRAGProvider:
    """
    Provides time-series data as context for RAG queries.

    Integrates with the existing RAG pipeline to answer questions like:
    - "What was the power consumption of chiller_001 yesterday?"
    - "Show me the temperature trend for transformer trf_005 last week"
    - "Find anomalies in DG fuel consumption in January"
    - "Compare energy usage between ahu_010 and ahu_015"
    """

    def __init__(self):
        self.tsa = get_timeseries_access()

    def get_equipment_summary(self, equipment_id: str) -> str:
        """
        Get a text summary of current equipment status for RAG context.

        Args:
            equipment_id: Equipment table name (e.g., 'chiller_001')

        Returns:
            Formatted text summary suitable for LLM context
        """
        try:
            # Get latest reading
            latest = self.tsa.get_latest_reading(equipment_id)
            if not latest:
                return f"No data available for {equipment_id}"

            # Get metadata
            metadata = self.tsa.get_equipment_metadata(equipment_id)

            # Format summary
            lines = [f"Equipment: {equipment_id}"]

            if metadata:
                if 'name' in metadata:
                    lines.append(f"Name: {metadata['name']}")
                if 'location' in metadata:
                    lines.append(f"Location: {metadata['location']}")
                if 'equipment_type' in metadata:
                    lines.append(f"Type: {metadata['equipment_type']}")

            lines.append(f"\nLatest Reading ({latest.get('ts', 'N/A')}):")

            # Format key parameters
            for key, value in latest.items():
                if key not in ['ts', 'id'] and value is not None:
                    # Format numeric values
                    if isinstance(value, float):
                        lines.append(f"  {key}: {value:.2f}")
                    else:
                        lines.append(f"  {key}: {value}")

            return '\n'.join(lines)

        except Exception as e:
            logger.error(f"Error getting equipment summary for {equipment_id}: {e}")
            return f"Error retrieving data for {equipment_id}"

    def get_historical_trend(
        self,
        equipment_id: str,
        column: str,
        hours: int = 24,
        interval: str = '1 hour'
    ) -> Dict:
        """
        Get historical trend data for a specific parameter.

        Args:
            equipment_id: Equipment table name
            column: Column to analyze (e.g., 'active_power_kw')
            hours: Number of hours to look back
            interval: Aggregation interval (e.g., '1 hour', '15 minutes')

        Returns:
            Dictionary with trend data and statistics
        """
        try:
            end_time = datetime.now(IST)
            start_time = end_time - timedelta(hours=hours)

            # Query aggregated data
            query = TimeSeriesQuery(
                equipment_id=equipment_id,
                start_time=start_time,
                end_time=end_time,
                columns=['ts', column],
                aggregation='avg',
                interval=interval
            )

            result = self.tsa.query_timeseries(query)

            # Calculate statistics
            values = [row[column] for row in result.data if row.get(column) is not None]

            if not values:
                return {
                    'equipment_id': equipment_id,
                    'column': column,
                    'error': 'No data available'
                }

            stats = {
                'equipment_id': equipment_id,
                'column': column,
                'period_hours': hours,
                'interval': interval,
                'data_points': len(values),
                'min': min(values),
                'max': max(values),
                'avg': sum(values) / len(values),
                'latest': values[-1] if values else None,
                'trend_data': result.data[:100],  # Limit for context size
                'query_time_ms': result.query_time_ms
            }

            return stats

        except Exception as e:
            logger.error(f"Error getting trend for {equipment_id}.{column}: {e}")
            return {'error': str(e)}

    def format_trend_for_rag(self, trend: Dict) -> str:
        """
        Format trend data as text for RAG context.

        Args:
            trend: Trend dictionary from get_historical_trend()

        Returns:
            Formatted text suitable for LLM context
        """
        if 'error' in trend:
            return f"Error: {trend['error']}"

        lines = [
            f"Historical Trend: {trend['equipment_id']} - {trend['column']}",
            f"Period: Last {trend['period_hours']} hours (interval: {trend['interval']})",
            f"Data Points: {trend['data_points']}",
            f"\nStatistics:",
            f"  Minimum: {trend['min']:.2f}",
            f"  Maximum: {trend['max']:.2f}",
            f"  Average: {trend['avg']:.2f}",
            f"  Latest: {trend['latest']:.2f}",
        ]

        # Add sample data points
        if trend.get('trend_data'):
            lines.append("\nRecent Values:")
            for point in trend['trend_data'][-10:]:  # Last 10 points
                ts = point.get('ts', 'N/A')
                value = point.get(trend['column'], 'N/A')
                if isinstance(value, float):
                    lines.append(f"  {ts}: {value:.2f}")
                else:
                    lines.append(f"  {ts}: {value}")

        return '\n'.join(lines)

    def find_anomalies_context(
        self,
        equipment_id: str,
        column: str,
        hours: int = 24,
        threshold_multiplier: float = 2.0
    ) -> str:
        """
        Find anomalies and format as RAG context.

        Args:
            equipment_id: Equipment table name
            column: Column to check for anomalies
            hours: Number of hours to analyze
            threshold_multiplier: Multiplier for avg to detect anomalies

        Returns:
            Formatted text describing anomalies
        """
        try:
            end_time = datetime.now(IST)
            start_time = end_time - timedelta(hours=hours)

            # Get statistics
            stats = self.tsa.get_aggregated_stats(
                equipment_id,
                start_time,
                end_time,
                columns=[column]
            )

            if not stats or f'{column}_avg' not in stats:
                return f"No data available for {equipment_id}.{column}"

            avg_value = stats[f'{column}_avg']
            threshold = avg_value * threshold_multiplier

            # Find anomalies
            anomalies = self.tsa.get_anomalies(
                equipment_id,
                start_time,
                end_time,
                column,
                threshold,
                operator='>'
            )

            if not anomalies:
                return (
                    f"No anomalies detected for {equipment_id}.{column} "
                    f"(threshold: {threshold:.2f}, based on avg: {avg_value:.2f})"
                )

            lines = [
                f"Anomaly Detection: {equipment_id}.{column}",
                f"Period: Last {hours} hours",
                f"Average Value: {avg_value:.2f}",
                f"Threshold: {threshold:.2f} ({threshold_multiplier}x average)",
                f"Anomalies Found: {len(anomalies)}",
                "\nAnomalous Readings:"
            ]

            # Show first 10 anomalies
            for anomaly in anomalies[:10]:
                ts = anomaly.get('ts', 'N/A')
                value = anomaly.get(column, 'N/A')
                if isinstance(value, float):
                    lines.append(f"  {ts}: {value:.2f} (exceeded threshold)")
                else:
                    lines.append(f"  {ts}: {value}")

            if len(anomalies) > 10:
                lines.append(f"  ... and {len(anomalies) - 10} more")

            return '\n'.join(lines)

        except Exception as e:
            logger.error(f"Error finding anomalies for {equipment_id}.{column}: {e}")
            return f"Error detecting anomalies: {str(e)}"

    def get_comparison_context(
        self,
        equipment_ids: List[str],
        column: str,
        hours: int = 24
    ) -> str:
        """
        Compare a parameter across multiple equipment.

        Args:
            equipment_ids: List of equipment table names
            column: Column to compare
            hours: Number of hours to analyze

        Returns:
            Formatted comparison text for RAG context
        """
        try:
            end_time = datetime.now(IST)
            start_time = end_time - timedelta(hours=hours)

            comparisons = []

            for eq_id in equipment_ids:
                stats = self.tsa.get_aggregated_stats(
                    eq_id,
                    start_time,
                    end_time,
                    columns=[column]
                )

                if stats and f'{column}_avg' in stats:
                    comparisons.append({
                        'equipment_id': eq_id,
                        'avg': stats[f'{column}_avg'],
                        'min': stats[f'{column}_min'],
                        'max': stats[f'{column}_max'],
                    })

            if not comparisons:
                return f"No data available for comparison of {column}"

            lines = [
                f"Equipment Comparison: {column}",
                f"Period: Last {hours} hours",
                "\nResults:"
            ]

            # Sort by average value
            comparisons.sort(key=lambda x: x['avg'], reverse=True)

            for comp in comparisons:
                lines.append(
                    f"  {comp['equipment_id']}: "
                    f"avg={comp['avg']:.2f}, min={comp['min']:.2f}, max={comp['max']:.2f}"
                )

            return '\n'.join(lines)

        except Exception as e:
            logger.error(f"Error comparing equipment: {e}")
            return f"Error performing comparison: {str(e)}"

    def get_alerts_context(
        self,
        equipment_id: Optional[str] = None,
        hours: int = 24,
        severity: Optional[str] = None
    ) -> str:
        """
        Get recent alerts for RAG context.

        Args:
            equipment_id: Filter by equipment (None = all)
            hours: Number of hours to look back
            severity: Filter by severity

        Returns:
            Formatted alerts text
        """
        try:
            end_time = datetime.now(IST)
            start_time = end_time - timedelta(hours=hours)

            alerts = self.tsa.get_alerts(
                equipment_id=equipment_id,
                start_time=start_time,
                end_time=end_time,
                severity=severity
            )

            if not alerts:
                filter_desc = f" for {equipment_id}" if equipment_id else ""
                return f"No alerts found{filter_desc} in the last {hours} hours"

            lines = [
                f"Recent Alerts ({len(alerts)} found)",
                f"Period: Last {hours} hours",
            ]

            if equipment_id:
                lines.append(f"Equipment: {equipment_id}")

            if severity:
                lines.append(f"Severity: {severity}")

            lines.append("\nAlerts:")

            for alert in alerts[:20]:  # Show first 20
                ts = alert.get('timestamp', 'N/A')
                eq = alert.get('equipment_id', 'N/A')
                sev = alert.get('severity', 'N/A')
                msg = alert.get('message', 'N/A')
                lines.append(f"  [{ts}] {eq} ({sev}): {msg}")

            if len(alerts) > 20:
                lines.append(f"  ... and {len(alerts) - 20} more alerts")

            return '\n'.join(lines)

        except Exception as e:
            logger.error(f"Error getting alerts: {e}")
            return f"Error retrieving alerts: {str(e)}"


# Singleton instance
_timeseries_rag = None


def get_timeseries_rag() -> TimeSeriesRAGProvider:
    """Get singleton TimeSeriesRAGProvider instance."""
    global _timeseries_rag
    if _timeseries_rag is None:
        _timeseries_rag = TimeSeriesRAGProvider()
    return _timeseries_rag
