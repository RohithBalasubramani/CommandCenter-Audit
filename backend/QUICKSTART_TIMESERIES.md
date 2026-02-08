# Quick Start: PostgreSQL Time-Series Integration

## ✅ Integration Complete!

The AI system now has full access to 363 equipment tables with 3 years of historical data (564M rows, 276 GB).

## Verify Installation

```bash
cd /home/rohith/desktop/CommandCenter/backend
source venv/bin/activate
python manage.py test_timeseries_db --quick
```

Expected output: `✓ All core tests passed!`

## 5-Minute Tutorial

### 1. Query Equipment Data

```python
from industrial.timeseries_access import get_timeseries_access, TimeSeriesQuery, IST
from datetime import datetime, timedelta

tsa = get_timeseries_access()

# Get list of all chillers
chillers = tsa.get_equipment_list(prefix='chiller')
# ['chiller_001', 'chiller_002', 'chiller_003', 'chiller_004', 'chiller_005', 'chiller_006']

# Get latest reading
latest = tsa.get_latest_reading('chiller_001')
print(latest['timestamp'])  # Latest timestamp
print(latest['chw_supply_temp_c'])  # Current temperature
```

### 2. Query Historical Trends

```python
# Get 24 hours of data (hourly averages)
query = TimeSeriesQuery(
    equipment_id='chiller_001',
    start_time=datetime(2024, 6, 15, 0, 0, tzinfo=IST),
    end_time=datetime(2024, 6, 16, 0, 0, tzinfo=IST),
    columns=['timestamp', 'chw_supply_temp_c', 'power_kw'],
    aggregation='avg',
    interval='1 hour'
)

result = tsa.query_timeseries(query)
print(f"Retrieved {result.row_count} rows in {result.query_time_ms:.2f}ms")

for row in result.data[:5]:
    print(f"{row['timestamp']}: {row['chw_supply_temp_c']:.1f}°C, {row['power_kw']:.1f} kW")
```

### 3. Use with RAG/LLM

```python
from layer2.timeseries_rag import get_timeseries_rag

rag = get_timeseries_rag()

# Generate context for LLM query: "How is chiller 1 performing?"
context = rag.get_equipment_summary('chiller_001')

# Add trend analysis
trend = rag.get_historical_trend('chiller_001', 'chw_supply_temp_c', hours=24)
context += "\n\n" + rag.format_trend_for_rag(trend)

# Now pass `context` to your LLM
print(context)
```

### 4. Sample Training Data for RL

```python
from rl.timeseries_data_provider import get_rl_data_provider

provider = get_rl_data_provider()

# Create training batch (32 examples, 20% anomalies)
batch = provider.create_training_batch(
    batch_size=32,
    equipment_types=['chiller', 'ahu'],
    include_anomalies=True,
    anomaly_ratio=0.2
)

print(f"Created batch with {len(batch)} examples")
# Use `batch` for RL training
```

## Test All Features

```bash
# Test database connection
python manage.py test_timeseries_db

# Test RAG integration
python manage.py test_rag_integration --equipment chiller_001

# Test RL data provider
python manage.py test_rl_data_provider

# Run all examples
python TIMESERIES_EXAMPLES.py
```

## Common Queries

### Get Statistics
```python
stats = tsa.get_aggregated_stats(
    'chiller_001',
    start_time=datetime(2024, 6, 1, tzinfo=IST),
    end_time=datetime(2024, 7, 1, tzinfo=IST),
    columns=['power_kw']
)
print(f"Min: {stats['power_kw_min']:.1f} kW")
print(f"Max: {stats['power_kw_max']:.1f} kW")
print(f"Avg: {stats['power_kw_avg']:.1f} kW")
```

### Find Anomalies
```python
anomalies = tsa.get_anomalies(
    'chiller_001',
    start_time=datetime(2024, 6, 15, tzinfo=IST),
    end_time=datetime(2024, 6, 16, tzinfo=IST),
    threshold_column='chw_supply_temp_c',
    threshold_value=8.0,  # Above 8°C is anomalous
    operator='>'
)
print(f"Found {len(anomalies)} anomalies")
```

### Compare Equipment
```python
comparison = rag.get_comparison_context(
    equipment_ids=['chiller_001', 'chiller_002', 'chiller_003'],
    column='power_kw',
    hours=24
)
print(comparison)
```

## Important Notes

### ⚠️ Column Names
- Use `timestamp` (NOT `ts`) for time filtering
- Database uses `timestamp`, code accepts both for compatibility

### ⚠️ Data Range
- Historical data: **Feb 2023 to Feb 2026**
- When querying "last 24 hours", use actual dates from 2023-2026
- Example: `datetime(2024, 6, 15, tzinfo=IST)` not `datetime.now()`

### ⚠️ Timezone
- All timestamps are in **IST (Asia/Kolkata)**
- Always use: `from industrial.timeseries_access import IST`

### ⚠️ Performance
- Use **aggregations** for large time ranges
- Limit to specific **columns** when possible
- Queries are fast: 50-500ms for 24h-7d aggregated data

## Files to Know

| File | Purpose |
|------|---------|
| [`TIMESERIES_INTEGRATION.md`](TIMESERIES_INTEGRATION.md) | Complete documentation |
| [`INTEGRATION_SUMMARY.md`](INTEGRATION_SUMMARY.md) | Integration summary |
| [`TIMESERIES_EXAMPLES.py`](TIMESERIES_EXAMPLES.py) | 8 practical examples |
| [`industrial/timeseries_access.py`](industrial/timeseries_access.py) | Data access layer |
| [`layer2/timeseries_rag.py`](layer2/timeseries_rag.py) | RAG integration |
| [`rl/timeseries_data_provider.py`](rl/timeseries_data_provider.py) | RL data provider |

## Get Help

```bash
# Test connection
python manage.py test_timeseries_db

# Check database directly
psql -U postgres -d command_center_data -c "SELECT COUNT(*) FROM chiller_001;"

# List all equipment
psql -U postgres -d command_center_data -c "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE' ORDER BY table_name;" | head -30
```

## Next Steps

1. **Integrate with your AI pipeline**: Add time-series context to RAG queries
2. **Build analytics**: Use the data access layer for custom dashboards
3. **Train RL models**: Use historical data for reinforcement learning
4. **Explore examples**: Run `python TIMESERIES_EXAMPLES.py`

---

📚 **Full Documentation**: [TIMESERIES_INTEGRATION.md](TIMESERIES_INTEGRATION.md)
🎯 **Summary**: [INTEGRATION_SUMMARY.md](INTEGRATION_SUMMARY.md)
💻 **Examples**: [TIMESERIES_EXAMPLES.py](TIMESERIES_EXAMPLES.py)
✅ **Status**: Integration complete and operational
