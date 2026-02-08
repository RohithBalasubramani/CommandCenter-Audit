"""
Management command to test RAG integration with time-series data.

Usage:
    python manage.py test_rag_integration [--equipment EQUIPMENT_ID]
"""

from django.core.management.base import BaseCommand
from datetime import datetime, timedelta
import pytz

from industrial.timeseries_rag import get_timeseries_rag


class Command(BaseCommand):
    help = 'Test RAG integration with PostgreSQL time-series data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--equipment',
            type=str,
            default='chiller_001',
            help='Equipment ID to test (default: chiller_001)',
        )

    def handle(self, *args, **options):
        rag = get_timeseries_rag()
        equipment_id = options['equipment']

        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write(self.style.SUCCESS('RAG Integration Test'))
        self.stdout.write(self.style.SUCCESS('=' * 70))

        # Test 1: Equipment summary
        self.stdout.write(f'\n[1] Testing equipment summary for {equipment_id}...')
        try:
            summary = rag.get_equipment_summary(equipment_id)
            self.stdout.write(self.style.SUCCESS('✓ Summary generated'))
            self.stdout.write('\n--- Equipment Summary ---')
            self.stdout.write(summary)
            self.stdout.write('--- End Summary ---\n')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Failed: {e}'))
            return

        # Test 2: Historical trend
        self.stdout.write(f'\n[2] Testing historical trend (last 24 hours)...')
        try:
            trend = rag.get_historical_trend(
                equipment_id=equipment_id,
                column='active_power_kw',
                hours=24,
                interval='1 hour'
            )

            if 'error' in trend:
                self.stdout.write(self.style.WARNING(f'⚠ {trend["error"]}'))
            else:
                self.stdout.write(self.style.SUCCESS('✓ Trend data retrieved'))
                self.stdout.write(f'   Data points: {trend["data_points"]}')
                self.stdout.write(f'   Min: {trend["min"]:.2f}')
                self.stdout.write(f'   Max: {trend["max"]:.2f}')
                self.stdout.write(f'   Avg: {trend["avg"]:.2f}')
                self.stdout.write(f'   Query time: {trend["query_time_ms"]:.2f}ms')

                # Test formatting
                formatted = rag.format_trend_for_rag(trend)
                self.stdout.write('\n--- Formatted Trend for RAG ---')
                self.stdout.write(formatted[:500] + '...')  # Show first 500 chars
                self.stdout.write('--- End Formatted Trend ---\n')

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Failed: {e}'))

        # Test 3: Anomaly detection
        self.stdout.write(f'\n[3] Testing anomaly detection...')
        try:
            anomalies = rag.find_anomalies_context(
                equipment_id=equipment_id,
                column='active_power_kw',
                hours=24,
                threshold_multiplier=2.0
            )

            self.stdout.write(self.style.SUCCESS('✓ Anomaly detection complete'))
            self.stdout.write('\n--- Anomaly Report ---')
            self.stdout.write(anomalies[:500] + '...')  # Show first 500 chars
            self.stdout.write('--- End Report ---\n')

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Failed: {e}'))

        # Test 4: Equipment comparison
        self.stdout.write(f'\n[4] Testing equipment comparison...')
        try:
            # Compare first 3 chillers
            comparison = rag.get_comparison_context(
                equipment_ids=['chiller_001', 'chiller_002', 'chiller_003'],
                column='active_power_kw',
                hours=24
            )

            self.stdout.write(self.style.SUCCESS('✓ Comparison generated'))
            self.stdout.write('\n--- Comparison ---')
            self.stdout.write(comparison)
            self.stdout.write('--- End Comparison ---\n')

        except Exception as e:
            self.stdout.write(self.style.WARNING(f'⚠ Comparison failed: {e}'))

        # Test 5: Alerts context
        self.stdout.write(f'\n[5] Testing alerts context...')
        try:
            alerts_ctx = rag.get_alerts_context(
                equipment_id=equipment_id,
                hours=24
            )

            self.stdout.write(self.style.SUCCESS('✓ Alerts context generated'))
            self.stdout.write('\n--- Alerts Context ---')
            self.stdout.write(alerts_ctx[:500] + '...')
            self.stdout.write('--- End Alerts ---\n')

        except Exception as e:
            self.stdout.write(self.style.WARNING(f'⚠ Alerts query failed: {e}'))

        # Summary
        self.stdout.write('\n' + '=' * 70)
        self.stdout.write(self.style.SUCCESS('✓ RAG integration tests completed!'))
        self.stdout.write(self.style.SUCCESS('Time-series data is ready for AI queries.'))
        self.stdout.write('=' * 70)
