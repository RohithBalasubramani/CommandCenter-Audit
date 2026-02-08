# Command Center PostgreSQL Time-Series Integration

Complete integration of the Command Center PostgreSQL database with the AI system.

## Overview

This integration provides the AI system with access to **3 years of historical equipment data** from 357 equipment tables in the `command_center_data` PostgreSQL database.

### Database Details

- **Database**: `command_center_data`
- **Host**: localhost:5432
- **User**: postgres (no password)
- **Size**: 276 GB
- **Total Rows**: ~564 million
- **Time Range**: Feb 2023 - Feb 2026
- **Interval**: 1 minute
- **Rows per table**: 1,578,240

### Equipment Tables (357 total)

**LT Electrical Panels** (240 tables):
- Motor Control Centers: `lt_mcc_001` to `lt_mcc_070`
- Power Control Centers: `lt_pcc_001` to `lt_pcc_020`
- APFC Panels: `lt_apfc_001` to `lt_apfc_020`
- Distribution Boards: `lt_db_001` to `lt_db_040`
- Main LT Distribution Boards: `lt_mldb_001` to `lt_mldb_010`
- Sub-Main Distribution Boards: `lt_smdb_001` to `lt_smdb_020`
- VFD Panels: `lt_vfd_001` to `lt_vfd_025`
- PLC Panels: `lt_plc_001` to `lt_plc_020`
- Auto Transfer Switches: `lt_ats_001` to `lt_ats_010`
- Changeover Switches: `lt_changeover_001` to `lt_changeover_005`

**Major Equipment** (117 tables):
- Transformers: `trf_001` to `trf_010` (315-2000 kVA)
- DG Sets: `dg_001` to `dg_006` (200-1200 kW)
- UPS Systems: `ups_001` to `ups_008` (20-200 kVA)
- Chillers: `chiller_001` to `chiller_006` (50-300 TR)
- Air Handling Units: `ahu_001` to `ahu_023` (5,000-25,000 CFM)
- Cooling Towers: `ct_001` to `ct_004` (150-300 TR)
- Pumps: `pump_001` to `pump_020` (0.18-55 kW)
- Compressors: `compressor_001` to `compressor_005` (22-75 kW)
- Motors: `motor_001` to `motor_015` (3.7-45 kW)
- Energy Meters: `em_001` to `em_020`

## Architecture

### Multi-Database Setup

The system uses Django's multi-database routing:

1. **`default` (SQLite)**: Django admin, auth, RAG models, user memory
2. **`timeseries` (PostgreSQL)**: Historical equipment time-series data

Configuration in `settings.py`:
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    },
    'timeseries': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'command_center_data',
        'USER': 'postgres',
        'PASSWORD': '',
        'HOST': 'localhost',
        'PORT': '5432',
        'CONN_MAX_AGE': 600,
    }
}

DATABASE_ROUTERS = ['command_center.db_router.TimeSeriesRouter']
```

### Components

1. **Database Router** ([command_center/db_router.py](command_center/db_router.py))
   - Routes Django ORM queries to appropriate database
   - Keeps time-series data read-only for the AI system

2. **Time-Series Data Access** ([industrial/timeseries_access.py](industrial/timeseries_access.py))
   - Low-level query interface for PostgreSQL equipment tables
   - Type-safe query methods with connection pooling
   - Support for aggregations, trends, anomalies, and statistics

3. **RAG Integration** ([layer2/timeseries_rag.py](layer2/timeseries_rag.py))
   - Formats time-series data as RAG context for LLM queries
   - Provides equipment summaries, trends, comparisons, anomalies
   - Integrates with existing RAG pipeline

4. **RL Data Provider** ([rl/timeseries_data_provider.py](rl/timeseries_data_provider.py))
   - Provides training data for reinforcement learning
   - Supports DPO (Direct Preference Optimization)
   - Balanced sampling with anomaly enrichment

## Usage

### 1. Time-Series Data Access

#### Basic Queries

```python
from industrial.timeseries_access import get_timeseries_access, TimeSeriesQuery, IST
from datetime import datetime, timedelta

tsa = get_timeseries_access()

# Get list of all equipment
equipment_list = tsa.get_equipment_list()
# ['chiller_001', 'chiller_002', ..., 'lt_mcc_070']

# Get list of chillers only
chillers = tsa.get_equipment_list(prefix='chiller')
# ['chiller_001', 'chiller_002', 'chiller_003', 'chiller_004', 'chiller_005', 'chiller_006']

# Get table columns
columns = tsa.get_table_columns('chiller_001')
# ['ts', 'id', 'active_power_kw', 'voltage_v', 'current_a', ...]

# Get latest reading
latest = tsa.get_latest_reading('chiller_001')
# {'ts': datetime(...), 'active_power_kw': 45.2, 'voltage_v': 415.3, ...}
```

#### Time-Series Queries

```python
# Query 24 hours of data with hourly aggregation
query = TimeSeriesQuery(
    equipment_id='chiller_001',
    start_time=datetime(2024, 6, 15, 0, 0, tzinfo=IST),
    end_time=datetime(2024, 6, 16, 0, 0, tzinfo=IST),
    columns=['ts', 'active_power_kw', 'water_flow_lpm'],
    aggregation='avg',
    interval='1 hour'
)

result = tsa.query_timeseries(query)
# result.data: [{'ts': ..., 'active_power_kw': 42.1, 'water_flow_lpm': 150.3}, ...]
# result.row_count: 24
# result.query_time_ms: 125.4
```

#### Aggregated Statistics

```python
# Get min/max/avg/sum for a time period
stats = tsa.get_aggregated_stats(
    'chiller_001',
    start_time=datetime(2024, 6, 15, tzinfo=IST),
    end_time=datetime(2024, 6, 22, tzinfo=IST),
    columns=['active_power_kw', 'efficiency_percent']
)
# {
#     'row_count': 10080,
#     'active_power_kw_min': 30.2,
#     'active_power_kw_max': 55.8,
#     'active_power_kw_avg': 44.5,
#     'active_power_kw_sum': 448560.0,
#     'efficiency_percent_min': 85.2,
#     'efficiency_percent_max': 92.1,
#     'efficiency_percent_avg': 88.7,
#     'efficiency_percent_sum': 893976.0
# }
```

#### Anomaly Detection

```python
# Find readings exceeding a threshold
anomalies = tsa.get_anomalies(
    'chiller_001',
    start_time=datetime(2024, 6, 15, tzinfo=IST),
    end_time=datetime(2024, 6, 16, tzinfo=IST),
    threshold_column='active_power_kw',
    threshold_value=50.0,
    operator='>'
)
# [{'ts': ..., 'active_power_kw': 52.3, ...}, ...]
```

#### Equipment Metadata and Alerts

```python
# Get equipment metadata
metadata = tsa.get_equipment_metadata('chiller_001')
# {'equipment_id': 'chiller_001', 'name': 'Chiller 1', 'location': 'Chiller Room', ...}

# Get recent alerts
alerts = tsa.get_alerts(
    equipment_id='chiller_001',
    start_time=datetime(2024, 6, 15, tzinfo=IST),
    end_time=datetime(2024, 6, 16, tzinfo=IST),
    severity='critical'
)
# [{'timestamp': ..., 'equipment_id': 'chiller_001', 'message': 'High temperature', ...}, ...]
```

### 2. RAG Integration

#### Equipment Summary for LLM Context

```python
from layer2.timeseries_rag import get_timeseries_rag

rag = get_timeseries_rag()

# Get current equipment status summary
summary = rag.get_equipment_summary('chiller_001')
# Returns formatted text suitable for LLM context:
# """
# Equipment: chiller_001
# Name: Chiller 1
# Location: Chiller Room
# Type: Water Chiller
#
# Latest Reading (2024-06-15 14:30:00+05:30):
#   active_power_kw: 45.20
#   voltage_v: 415.30
#   current_a: 65.40
#   water_flow_lpm: 150.30
#   ...
# """
```

#### Historical Trends

```python
# Get 24-hour trend data
trend = rag.get_historical_trend(
    equipment_id='chiller_001',
    column='active_power_kw',
    hours=24,
    interval='1 hour'
)

# Format for RAG context
formatted = rag.format_trend_for_rag(trend)
# Returns formatted text with statistics and sample data points
```

#### Anomaly Detection for RAG

```python
# Find and format anomalies
anomalies_text = rag.find_anomalies_context(
    equipment_id='chiller_001',
    column='active_power_kw',
    hours=24,
    threshold_multiplier=2.0
)
# Returns formatted anomaly report suitable for LLM context
```

#### Equipment Comparison

```python
# Compare multiple equipment
comparison = rag.get_comparison_context(
    equipment_ids=['chiller_001', 'chiller_002', 'chiller_003'],
    column='active_power_kw',
    hours=24
)
# Returns formatted comparison with averages, min/max for each equipment
```

#### Alerts Context

```python
# Get recent alerts
alerts_ctx = rag.get_alerts_context(
    equipment_id='chiller_001',
    hours=24,
    severity='high'
)
# Returns formatted list of alerts for LLM context
```

### 3. RL Training Data Access

#### Dataset Statistics

```python
from rl.timeseries_data_provider import get_rl_data_provider

provider = get_rl_data_provider()

# Get dataset statistics
stats = provider.get_training_statistics()
# {
#     'total_equipment': 357,
#     'equipment_types': 29,
#     'type_breakdown': {'chiller': 6, 'ahu': 23, ...},
#     'total_timepoints_per_equipment': 1578240,
#     'total_rows': 563423680,
#     'time_range': '2023-02-01 to 2026-02-01',
#     'interval': '1 minute',
#     'database_size_gb': 276
# }
```

#### Sampling Random States

```python
# Sample a random equipment state
state = provider.sample_equipment_state(equipment_type='chiller')
# {
#     'equipment_id': 'chiller_003',
#     'timestamp': datetime(2024, 8, 15, 14, 23, tzinfo=IST),
#     'state': {'active_power_kw': 42.5, 'voltage_v': 415.2, ...}
# }

# Sample a specific equipment at a specific time
state = provider.sample_equipment_state(
    equipment_id='chiller_001',
    timestamp=datetime(2024, 6, 15, 12, 0, tzinfo=IST)
)
```

#### Sampling Trajectories

```python
# Sample a 1-hour trajectory (sequence of states)
trajectory = provider.sample_equipment_trajectory(
    equipment_id='chiller_001',
    duration_hours=1,
    interval_minutes=15
)
# [
#     {'equipment_id': 'chiller_001', 'timestamp': ..., 'state': {...}},
#     {'equipment_id': 'chiller_001', 'timestamp': ..., 'state': {...}},
#     ...  # 4 data points (15-min intervals)
# ]
```

#### DPO Preference Pairs

```python
# Sample a comparison pair for Direct Preference Optimization
pair = provider.sample_comparison_pair(
    equipment_type='chiller',
    metric='active_power_kw',
    duration_hours=1
)

if pair:
    state_a, state_b, preference = pair
    # preference is 'a' or 'b' indicating which is better (lower power = better)
```

#### Anomaly-Enriched Training

```python
# Sample anomalous examples
anomalies = provider.sample_anomaly_examples(
    equipment_type='chiller',
    count=100,
    threshold_multiplier=2.0
)
# Returns 100 anomalous states for robust training

# Create a balanced training batch
batch = provider.create_training_batch(
    batch_size=32,
    equipment_types=['chiller', 'ahu', 'pump'],
    include_anomalies=True,
    anomaly_ratio=0.2  # 20% anomalies
)
# Returns 32 examples: 26 normal + 6 anomalies, shuffled
```

## Testing

### Prerequisites

```bash
# Install PostgreSQL driver
pip install psycopg2-binary

# Verify database is running
psql -U postgres -d command_center_data -c "SELECT COUNT(*) FROM chiller_001;"
```

### Test Commands

```bash
# Test database connection and basic queries
python manage.py test_timeseries_db

# Test specific equipment
python manage.py test_timeseries_db --equipment chiller_001

# Quick test (skip large queries)
python manage.py test_timeseries_db --quick

# Test RAG integration
python manage.py test_rag_integration --equipment chiller_001

# Test RL data provider
python manage.py test_rl_data_provider
```

### Expected Output

```
======================================================================
PostgreSQL Time-Series Database Test
======================================================================

[1] Testing database connection...
✓ Connected to PostgreSQL
   Version: PostgreSQL 16.1 on x86_64-pc-linux-gnu...

[2] Listing equipment tables...
✓ Found 357 equipment tables

   Equipment breakdown:
     chiller: 6
     ahu: 23
     lt_mcc: 70
     ...

[3] Testing queries for chiller_001...
✓ Table has 55 columns
   Columns: ts, id, active_power_kw, voltage_v, current_a...
✓ Latest reading retrieved
   Timestamp: 2026-02-01 00:00:00+05:30
   active_power_kw: 45.20
   ...

✓ All core tests passed!
PostgreSQL time-series database is operational.
======================================================================
```

## Integration with Existing AI System

### Layer 2 RAG Pipeline

The time-series RAG provider integrates seamlessly with the existing RAG pipeline:

```python
# In layer2/data_collector.py or similar

from layer2.timeseries_rag import get_timeseries_rag

def collect_industrial_data(query: str, intent: dict) -> str:
    """Collect industrial equipment data for RAG context."""
    rag = get_timeseries_rag()

    # Extract equipment from intent
    equipment_id = intent.get('equipment_id', 'chiller_001')

    # Build context based on query type
    if 'trend' in query.lower():
        return rag.format_trend_for_rag(
            rag.get_historical_trend(equipment_id, column='active_power_kw', hours=24)
        )
    elif 'anomal' in query.lower():
        return rag.find_anomalies_context(equipment_id, column='active_power_kw', hours=24)
    elif 'compare' in query.lower():
        equipment_ids = intent.get('equipment_ids', [equipment_id])
        return rag.get_comparison_context(equipment_ids, column='active_power_kw', hours=24)
    else:
        return rag.get_equipment_summary(equipment_id)
```

### RL Training Pipeline

Integrate with existing RL training:

```python
# In rl/trainer.py or similar

from rl.timeseries_data_provider import get_rl_data_provider

def create_training_dataset(num_batches: int = 100, batch_size: int = 32):
    """Create training dataset from historical data."""
    provider = get_rl_data_provider()

    dataset = []
    for _ in range(num_batches):
        batch = provider.create_training_batch(
            batch_size=batch_size,
            equipment_types=['chiller', 'ahu', 'pump', 'transformer'],
            include_anomalies=True,
            anomaly_ratio=0.15
        )
        dataset.extend(batch)

    return dataset
```

## Performance Considerations

### Query Optimization

- **Use aggregations**: Aggregate data at the database level using `aggregation` and `interval` parameters
- **Limit columns**: Only select columns you need using the `columns` parameter
- **Connection pooling**: Enabled with `CONN_MAX_AGE: 600` in settings
- **Indexing**: All tables have indexes on `ts` column for fast time-range queries

### Expected Query Times

Based on 1.58M rows per table:

- Latest reading: < 5ms
- 1-day aggregated query (1-hour interval): 50-150ms
- 7-day aggregated query: 200-500ms
- 30-day aggregated query: 500-1500ms
- Anomaly detection (24-hour scan): 100-300ms

### Caching

Consider caching frequently accessed data:

```python
from functools import lru_cache

@lru_cache(maxsize=128)
def get_cached_equipment_list():
    tsa = get_timeseries_access()
    return tsa.get_equipment_list()
```

## Troubleshooting

### Connection Issues

```python
# Test database connection
from django.db import connections

with connections['timeseries'].cursor() as cursor:
    cursor.execute('SELECT version();')
    print(cursor.fetchone())
```

### Permission Issues

Ensure postgres user has SELECT permissions:

```sql
GRANT SELECT ON ALL TABLES IN SCHEMA public TO postgres;
```

### Missing psycopg2

```bash
pip install psycopg2-binary
# Or for production:
pip install psycopg2
```

## Future Enhancements

1. **Real-time streaming**: Integrate with `live_simulator.py` for real-time data
2. **Predictive analytics**: Use historical trends for forecasting
3. **Cross-equipment correlations**: Analyze dependencies between equipment
4. **Energy optimization**: Use RL to optimize equipment schedules
5. **Anomaly detection models**: Train ML models on historical anomalies

## References

- Main project: `/home/rohith/desktop/CommandCenter/`
- Data generation: `/home/rohith/desktop/CommandCenter/rl_training_data/`
- Documentation: `/home/rohith/desktop/CommandCenter/rl_training_data/README.md`
- Memory/RAG: `/home/rohith/.claude/projects/-home-rohith/memory/MEMORY.md`

## Support

For issues or questions:
1. Check logs: `python manage.py test_timeseries_db`
2. Verify database: `psql -U postgres -d command_center_data`
3. Review this documentation
