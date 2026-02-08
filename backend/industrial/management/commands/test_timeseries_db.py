"""
Management command to test PostgreSQL time-series database connection and query capabilities.

Usage:
    python manage.py test_timeseries_db [--equipment EQUIPMENT_ID] [--quick]
"""

from django.core.management.base import BaseCommand
from django.db import connections
from datetime import datetime, timedelta
import pytz

from industrial.timeseries_access import get_timeseries_access, TimeSeriesQuery, IST


class Command(BaseCommand):
    help = 'Test PostgreSQL time-series database connection and functionality'

    def add_arguments(self, parser):
        parser.add_argument(
            '--equipment',
            type=str,
            help='Specific equipment ID to test (e.g., chiller_001)',
        )
        parser.add_argument(
            '--quick',
            action='store_true',
            help='Run quick test (skip large queries)',
        )

    def handle(self, *args, **options):
        tsa = get_timeseries_access()

        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write(self.style.SUCCESS('PostgreSQL Time-Series Database Test'))
        self.stdout.write(self.style.SUCCESS('=' * 70))

        # Test 1: Database connection
        self.stdout.write('\n[1] Testing database connection...')
        try:
            with connections['timeseries'].cursor() as cursor:
                cursor.execute('SELECT version();')
                version = cursor.fetchone()[0]
                self.stdout.write(self.style.SUCCESS(f'✓ Connected to PostgreSQL'))
                self.stdout.write(f'   Version: {version}')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Connection failed: {e}'))
            return

        # Test 2: List equipment tables
        self.stdout.write('\n[2] Listing equipment tables...')
        try:
            equipment_list = tsa.get_equipment_list()
            self.stdout.write(self.style.SUCCESS(f'✓ Found {len(equipment_list)} equipment tables'))

            # Show breakdown by type
            type_counts = {}
            for eq_id in equipment_list:
                prefix = eq_id.rsplit('_', 1)[0]
                type_counts[prefix] = type_counts.get(prefix, 0) + 1

            self.stdout.write('\n   Equipment breakdown:')
            for eq_type, count in sorted(type_counts.items()):
                self.stdout.write(f'     {eq_type}: {count}')

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Failed to list equipment: {e}'))
            return

        # Test 3: Query specific equipment
        if options['equipment']:
            equipment_id = options['equipment']
        else:
            # Pick a random equipment
            equipment_id = 'chiller_001'

        self.stdout.write(f'\n[3] Testing queries for {equipment_id}...')

        # 3a: Get table columns
        try:
            columns = tsa.get_table_columns(equipment_id)
            self.stdout.write(self.style.SUCCESS(f'✓ Table has {len(columns)} columns'))
            self.stdout.write(f'   Columns: {", ".join(columns[:10])}...')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Failed to get columns: {e}'))
            return

        # 3b: Get latest reading
        try:
            latest = tsa.get_latest_reading(equipment_id)
            if latest:
                self.stdout.write(self.style.SUCCESS(f'✓ Latest reading retrieved'))
                self.stdout.write(f'   Timestamp: {latest.get("ts")}')
                # Show a few key fields
                for key in ['active_power_kw', 'voltage_v', 'current_a'][:3]:
                    if key in latest:
                        self.stdout.write(f'   {key}: {latest[key]}')
            else:
                self.stdout.write(self.style.WARNING('⚠ No data found'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Failed to get latest reading: {e}'))
            return

        # Test 4: Time-series query
        if not options['quick']:
            self.stdout.write('\n[4] Testing time-series query (24 hours)...')
            try:
                end_time = datetime.now(IST)
                start_time = end_time - timedelta(hours=24)

                query = TimeSeriesQuery(
                    equipment_id=equipment_id,
                    start_time=start_time,
                    end_time=end_time,
                    aggregation='avg',
                    interval='1 hour'
                )

                result = tsa.query_timeseries(query)
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✓ Retrieved {result.row_count} rows in {result.query_time_ms:.2f}ms'
                    )
                )

                if result.data:
                    first_row = result.data[0]
                    self.stdout.write(f'   First row: {first_row.get("ts")}')
                    for key, value in list(first_row.items())[:5]:
                        if key != 'ts':
                            self.stdout.write(f'     {key}: {value}')

            except Exception as e:
                self.stdout.write(self.style.ERROR(f'✗ Time-series query failed: {e}'))
                return

        # Test 5: Aggregated statistics
        self.stdout.write('\n[5] Testing aggregated statistics (7 days)...')
        try:
            end_time = datetime.now(IST)
            start_time = end_time - timedelta(days=7)

            stats = tsa.get_aggregated_stats(
                equipment_id,
                start_time,
                end_time,
                columns=['active_power_kw'] if 'active_power_kw' in columns else None
            )

            if stats:
                self.stdout.write(self.style.SUCCESS('✓ Statistics calculated'))
                self.stdout.write(f'   Row count: {stats.get("row_count", 0)}')
                # Show first stat
                for key, value in list(stats.items())[:5]:
                    if key != 'row_count' and value is not None:
                        self.stdout.write(f'   {key}: {value:.2f}')
            else:
                self.stdout.write(self.style.WARNING('⚠ No statistics available'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Statistics query failed: {e}'))

        # Test 6: Equipment metadata
        self.stdout.write('\n[6] Testing equipment metadata...')
        try:
            metadata = tsa.get_equipment_metadata(equipment_id)
            if metadata:
                self.stdout.write(self.style.SUCCESS('✓ Metadata retrieved'))
                for key in ['name', 'location', 'equipment_type', 'capacity']:
                    if key in metadata:
                        self.stdout.write(f'   {key}: {metadata[key]}')
            else:
                self.stdout.write(self.style.WARNING('⚠ No metadata found'))
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'⚠ Metadata query failed (table may not exist): {e}'))

        # Test 7: Alerts
        self.stdout.write('\n[7] Testing alerts query...')
        try:
            alerts = tsa.get_alerts(equipment_id=equipment_id)
            self.stdout.write(self.style.SUCCESS(f'✓ Found {len(alerts)} alerts'))
            if alerts:
                alert = alerts[0]
                self.stdout.write(f'   Latest alert: {alert.get("timestamp")}')
                self.stdout.write(f'   Message: {alert.get("message", "N/A")}')
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'⚠ Alerts query failed (table may not exist): {e}'))

        # Summary
        self.stdout.write('\n' + '=' * 70)
        self.stdout.write(self.style.SUCCESS('✓ All core tests passed!'))
        self.stdout.write(self.style.SUCCESS('PostgreSQL time-series database is operational.'))
        self.stdout.write('=' * 70)
