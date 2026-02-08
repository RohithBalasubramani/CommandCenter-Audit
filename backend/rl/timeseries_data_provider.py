"""
RL Training Data Provider for Command Center PostgreSQL Database

Provides training data access for reinforcement learning (RL) and
Direct Preference Optimization (DPO) from the historical equipment data.

This module supports:
1. Sampling training examples from 3 years of historical data
2. Creating state-action-reward triplets for RL
3. Generating preference pairs for DPO training
4. Balanced sampling across equipment types and time periods
5. Anomaly-enriched datasets for robust training
"""

import logging
import random
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import pytz

from industrial.timeseries_access import (
    get_timeseries_access,
    TimeSeriesQuery,
    IST,
    ALL_EQUIPMENT_PREFIXES
)

logger = logging.getLogger(__name__)


class RLTimeSeriesDataProvider:
    """
    Provides training data from PostgreSQL for RL/DPO training.

    Features:
    - Random sampling across 3 years of data
    - Stratified sampling by equipment type
    - Temporal diversity (different seasons, shifts, load conditions)
    - Anomaly-enriched samples for robust training
    """

    def __init__(self):
        self.tsa = get_timeseries_access()
        self._equipment_cache = None

    def get_all_equipment(self, refresh: bool = False) -> List[str]:
        """
        Get list of all equipment tables (cached).

        Args:
            refresh: Force refresh of cache

        Returns:
            List of equipment IDs
        """
        if self._equipment_cache is None or refresh:
            self._equipment_cache = self.tsa.get_equipment_list()
            logger.info(f"Loaded {len(self._equipment_cache)} equipment tables")

        return self._equipment_cache

    def sample_random_timepoint(
        self,
        start_date: datetime = datetime(2023, 2, 1, tzinfo=IST),
        end_date: datetime = datetime(2026, 2, 1, tzinfo=IST)
    ) -> datetime:
        """
        Sample a random timestamp from the data range.

        Args:
            start_date: Earliest possible timestamp
            end_date: Latest possible timestamp

        Returns:
            Random timestamp
        """
        delta = end_date - start_date
        random_seconds = random.randint(0, int(delta.total_seconds()))
        return start_date + timedelta(seconds=random_seconds)

    def sample_equipment_state(
        self,
        equipment_id: Optional[str] = None,
        timestamp: Optional[datetime] = None,
        equipment_type: Optional[str] = None
    ) -> Optional[Dict]:
        """
        Sample a random equipment state (one timestamp snapshot).

        Args:
            equipment_id: Specific equipment (None = random)
            timestamp: Specific timestamp (None = random)
            equipment_type: Filter by equipment type prefix (e.g., 'chiller')

        Returns:
            Dictionary with equipment state at the timestamp
        """
        try:
            # Select equipment
            if equipment_id is None:
                if equipment_type:
                    equipment_list = self.tsa.get_equipment_list(prefix=equipment_type)
                else:
                    equipment_list = self.get_all_equipment()

                if not equipment_list:
                    logger.warning(f"No equipment found for type: {equipment_type}")
                    return None

                equipment_id = random.choice(equipment_list)

            # Select timestamp
            if timestamp is None:
                timestamp = self.sample_random_timepoint()

            # Query single data point
            query = TimeSeriesQuery(
                equipment_id=equipment_id,
                start_time=timestamp,
                end_time=timestamp + timedelta(minutes=1)
            )

            result = self.tsa.query_timeseries(query)

            if result.data:
                return {
                    'equipment_id': equipment_id,
                    'timestamp': timestamp,
                    'state': result.data[0]
                }

            return None

        except Exception as e:
            logger.error(f"Error sampling equipment state: {e}")
            return None

    def sample_equipment_trajectory(
        self,
        equipment_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        duration_hours: int = 1,
        interval_minutes: int = 15
    ) -> List[Dict]:
        """
        Sample a trajectory (sequence of states) for an equipment.

        Args:
            equipment_id: Equipment to sample (None = random)
            start_time: Trajectory start time (None = random)
            duration_hours: Length of trajectory in hours
            interval_minutes: Sampling interval in minutes

        Returns:
            List of state dictionaries (chronological order)
        """
        try:
            # Select equipment
            if equipment_id is None:
                equipment_id = random.choice(self.get_all_equipment())

            # Select start time
            if start_time is None:
                # Ensure we don't go past the end of data
                max_start = datetime(2026, 2, 1, tzinfo=IST) - timedelta(hours=duration_hours)
                start_time = self.sample_random_timepoint(
                    end_date=max_start
                )

            end_time = start_time + timedelta(hours=duration_hours)

            # Query trajectory
            query = TimeSeriesQuery(
                equipment_id=equipment_id,
                start_time=start_time,
                end_time=end_time,
                aggregation='avg',
                interval=f'{interval_minutes} minutes'
            )

            result = self.tsa.query_timeseries(query)

            return [
                {
                    'equipment_id': equipment_id,
                    'timestamp': row['ts'],
                    'state': row
                }
                for row in result.data
            ]

        except Exception as e:
            logger.error(f"Error sampling trajectory: {e}")
            return []

    def sample_comparison_pair(
        self,
        equipment_type: str,
        metric: str,
        duration_hours: int = 1
    ) -> Optional[Tuple[Dict, Dict, str]]:
        """
        Sample a preference pair for DPO training.

        Returns two equipment states and a preference label based on the metric.

        Args:
            equipment_type: Equipment type prefix (e.g., 'chiller', 'ahu')
            metric: Column to compare (e.g., 'active_power_kw', 'efficiency_percent')
            duration_hours: Duration to aggregate over

        Returns:
            Tuple of (state_a, state_b, preference) where preference is 'a' or 'b'
            None if sampling fails
        """
        try:
            equipment_list = self.tsa.get_equipment_list(prefix=equipment_type)
            if len(equipment_list) < 2:
                logger.warning(f"Not enough equipment for comparison: {equipment_type}")
                return None

            # Sample two different equipment
            eq_a, eq_b = random.sample(equipment_list, 2)

            # Sample same time period for fair comparison
            timestamp = self.sample_random_timepoint()

            # Get states
            query_a = TimeSeriesQuery(
                equipment_id=eq_a,
                start_time=timestamp,
                end_time=timestamp + timedelta(hours=duration_hours),
                aggregation='avg',
                interval=f'{duration_hours} hours'
            )

            query_b = TimeSeriesQuery(
                equipment_id=eq_b,
                start_time=timestamp,
                end_time=timestamp + timedelta(hours=duration_hours),
                aggregation='avg',
                interval=f'{duration_hours} hours'
            )

            result_a = self.tsa.query_timeseries(query_a)
            result_b = self.tsa.query_timeseries(query_b)

            if not result_a.data or not result_b.data:
                return None

            state_a = {
                'equipment_id': eq_a,
                'timestamp': timestamp,
                'state': result_a.data[0]
            }

            state_b = {
                'equipment_id': eq_b,
                'timestamp': timestamp,
                'state': result_b.data[0]
            }

            # Determine preference based on metric
            # Lower is better for power consumption, higher for efficiency
            value_a = state_a['state'].get(metric)
            value_b = state_b['state'].get(metric)

            if value_a is None or value_b is None:
                return None

            # For power metrics, lower is better
            if 'power' in metric.lower() or 'current' in metric.lower():
                preference = 'a' if value_a < value_b else 'b'
            # For efficiency metrics, higher is better
            elif 'efficiency' in metric.lower() or 'pf' in metric.lower():
                preference = 'a' if value_a > value_b else 'b'
            else:
                # Default: lower is better
                preference = 'a' if value_a < value_b else 'b'

            return (state_a, state_b, preference)

        except Exception as e:
            logger.error(f"Error sampling comparison pair: {e}")
            return None

    def sample_anomaly_examples(
        self,
        equipment_type: Optional[str] = None,
        count: int = 100,
        threshold_multiplier: float = 2.0
    ) -> List[Dict]:
        """
        Sample anomalous states for robust training.

        Args:
            equipment_type: Equipment type prefix (None = all types)
            count: Number of anomalies to sample
            threshold_multiplier: Multiplier for anomaly detection

        Returns:
            List of anomalous state dictionaries
        """
        anomalies = []

        try:
            # Sample random equipment and time ranges
            for _ in range(count):
                if equipment_type:
                    equipment_list = self.tsa.get_equipment_list(prefix=equipment_type)
                else:
                    equipment_list = self.get_all_equipment()

                if not equipment_list:
                    continue

                equipment_id = random.choice(equipment_list)

                # Sample random time period
                start_time = self.sample_random_timepoint()
                end_time = start_time + timedelta(hours=24)

                # Get columns for this equipment
                columns = self.tsa.get_table_columns(equipment_id)
                numeric_cols = [
                    c for c in columns
                    if c not in ['ts', 'id'] and (
                        'power' in c or 'current' in c or 'temperature' in c
                    )
                ]

                if not numeric_cols:
                    continue

                # Pick a random column to check
                column = random.choice(numeric_cols)

                # Get statistics
                stats = self.tsa.get_aggregated_stats(
                    equipment_id,
                    start_time,
                    end_time,
                    columns=[column]
                )

                if not stats or f'{column}_avg' not in stats:
                    continue

                avg_value = stats[f'{column}_avg']
                threshold = avg_value * threshold_multiplier

                # Find anomalies
                anom_data = self.tsa.get_anomalies(
                    equipment_id,
                    start_time,
                    end_time,
                    column,
                    threshold,
                    operator='>'
                )

                for anom in anom_data[:5]:  # Take up to 5 from this equipment
                    anomalies.append({
                        'equipment_id': equipment_id,
                        'timestamp': anom.get('ts'),
                        'state': anom,
                        'anomaly_column': column,
                        'threshold': threshold,
                        'is_anomaly': True
                    })

                if len(anomalies) >= count:
                    break

        except Exception as e:
            logger.error(f"Error sampling anomalies: {e}")

        return anomalies[:count]

    def create_training_batch(
        self,
        batch_size: int = 32,
        equipment_types: Optional[List[str]] = None,
        include_anomalies: bool = True,
        anomaly_ratio: float = 0.1
    ) -> List[Dict]:
        """
        Create a balanced training batch with diverse examples.

        Args:
            batch_size: Number of examples in batch
            equipment_types: List of equipment type prefixes to include
            include_anomalies: Whether to include anomalous examples
            anomaly_ratio: Fraction of batch that should be anomalies

        Returns:
            List of training examples
        """
        batch = []

        if equipment_types is None:
            equipment_types = ALL_EQUIPMENT_PREFIXES[:5]  # Sample subset

        # Calculate split
        if include_anomalies:
            n_anomalies = int(batch_size * anomaly_ratio)
            n_normal = batch_size - n_anomalies
        else:
            n_normal = batch_size
            n_anomalies = 0

        # Sample normal examples
        for _ in range(n_normal):
            eq_type = random.choice(equipment_types)
            state = self.sample_equipment_state(equipment_type=eq_type)
            if state:
                state['is_anomaly'] = False
                batch.append(state)

        # Sample anomalous examples
        if n_anomalies > 0:
            eq_type = random.choice(equipment_types)
            anomalies = self.sample_anomaly_examples(
                equipment_type=eq_type,
                count=n_anomalies
            )
            batch.extend(anomalies)

        # Shuffle
        random.shuffle(batch)

        return batch

    def get_training_statistics(self) -> Dict:
        """
        Get statistics about available training data.

        Returns:
            Dictionary with dataset statistics
        """
        try:
            equipment_list = self.get_all_equipment()

            # Count by type
            type_counts = {}
            for eq_id in equipment_list:
                eq_type = eq_id.rsplit('_', 1)[0]  # e.g., 'chiller_001' -> 'chiller'
                type_counts[eq_type] = type_counts.get(eq_type, 0) + 1

            return {
                'total_equipment': len(equipment_list),
                'equipment_types': len(type_counts),
                'type_breakdown': type_counts,
                'total_timepoints_per_equipment': 1_578_240,
                'total_rows': len(equipment_list) * 1_578_240,
                'time_range': '2023-02-01 to 2026-02-01',
                'interval': '1 minute',
                'database_size_gb': 276
            }

        except Exception as e:
            logger.error(f"Error getting training statistics: {e}")
            return {'error': str(e)}


# Singleton instance
_rl_data_provider = None


def get_rl_data_provider() -> RLTimeSeriesDataProvider:
    """Get singleton RLTimeSeriesDataProvider instance."""
    global _rl_data_provider
    if _rl_data_provider is None:
        _rl_data_provider = RLTimeSeriesDataProvider()
    return _rl_data_provider
