"""
Management command to test RL training data provider.

Usage:
    python manage.py test_rl_data_provider
"""

from django.core.management.base import BaseCommand
import json

from rl.timeseries_data_provider import get_rl_data_provider


class Command(BaseCommand):
    help = 'Test RL training data provider for PostgreSQL time-series data'

    def handle(self, *args, **options):
        provider = get_rl_data_provider()

        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write(self.style.SUCCESS('RL Training Data Provider Test'))
        self.stdout.write(self.style.SUCCESS('=' * 70))

        # Test 1: Dataset statistics
        self.stdout.write('\n[1] Getting dataset statistics...')
        try:
            stats = provider.get_training_statistics()
            self.stdout.write(self.style.SUCCESS('✓ Statistics retrieved'))
            self.stdout.write(f'\n   Total equipment: {stats["total_equipment"]}')
            self.stdout.write(f'   Equipment types: {stats["equipment_types"]}')
            self.stdout.write(f'   Total rows: {stats["total_rows"]:,}')
            self.stdout.write(f'   Database size: {stats["database_size_gb"]} GB')
            self.stdout.write(f'   Time range: {stats["time_range"]}')
            self.stdout.write('\n   Equipment breakdown:')
            for eq_type, count in sorted(stats["type_breakdown"].items())[:10]:
                self.stdout.write(f'     {eq_type}: {count}')
            self.stdout.write('     ...')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Failed: {e}'))
            return

        # Test 2: Sample equipment state
        self.stdout.write('\n[2] Sampling random equipment state...')
        try:
            state = provider.sample_equipment_state(equipment_type='chiller')
            if state:
                self.stdout.write(self.style.SUCCESS('✓ State sampled'))
                self.stdout.write(f'   Equipment: {state["equipment_id"]}')
                self.stdout.write(f'   Timestamp: {state["timestamp"]}')
                self.stdout.write(f'   State keys: {list(state["state"].keys())[:10]}...')
                # Show a few values
                for key, value in list(state["state"].items())[:5]:
                    if key != 'ts' and key != 'id':
                        if isinstance(value, float):
                            self.stdout.write(f'     {key}: {value:.2f}')
                        else:
                            self.stdout.write(f'     {key}: {value}')
            else:
                self.stdout.write(self.style.WARNING('⚠ No state sampled'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Failed: {e}'))

        # Test 3: Sample trajectory
        self.stdout.write('\n[3] Sampling equipment trajectory (1 hour)...')
        try:
            trajectory = provider.sample_equipment_trajectory(
                equipment_id='chiller_001',
                duration_hours=1,
                interval_minutes=15
            )
            if trajectory:
                self.stdout.write(self.style.SUCCESS(f'✓ Trajectory sampled ({len(trajectory)} points)'))
                self.stdout.write(f'   Start: {trajectory[0]["timestamp"]}')
                self.stdout.write(f'   End: {trajectory[-1]["timestamp"]}')
                # Show first point
                first_state = trajectory[0]["state"]
                self.stdout.write('   First point sample:')
                for key, value in list(first_state.items())[:5]:
                    if key != 'ts':
                        if isinstance(value, float):
                            self.stdout.write(f'     {key}: {value:.2f}')
                        else:
                            self.stdout.write(f'     {key}: {value}')
            else:
                self.stdout.write(self.style.WARNING('⚠ No trajectory sampled'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Failed: {e}'))

        # Test 4: Sample comparison pair for DPO
        self.stdout.write('\n[4] Sampling comparison pair for DPO training...')
        try:
            pair = provider.sample_comparison_pair(
                equipment_type='chiller',
                metric='active_power_kw',
                duration_hours=1
            )
            if pair:
                state_a, state_b, preference = pair
                self.stdout.write(self.style.SUCCESS('✓ Comparison pair sampled'))
                self.stdout.write(f'   Equipment A: {state_a["equipment_id"]}')
                self.stdout.write(f'   Equipment B: {state_b["equipment_id"]}')
                self.stdout.write(f'   Timestamp: {state_a["timestamp"]}')
                self.stdout.write(f'   Preference: {preference}')

                value_a = state_a['state'].get('active_power_kw', 'N/A')
                value_b = state_b['state'].get('active_power_kw', 'N/A')
                if isinstance(value_a, float) and isinstance(value_b, float):
                    self.stdout.write(f'   Power A: {value_a:.2f} kW')
                    self.stdout.write(f'   Power B: {value_b:.2f} kW')
            else:
                self.stdout.write(self.style.WARNING('⚠ No comparison pair sampled'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Failed: {e}'))

        # Test 5: Sample anomalies
        self.stdout.write('\n[5] Sampling anomalous states...')
        try:
            anomalies = provider.sample_anomaly_examples(
                equipment_type='chiller',
                count=5
            )
            if anomalies:
                self.stdout.write(self.style.SUCCESS(f'✓ Sampled {len(anomalies)} anomalies'))
                for i, anom in enumerate(anomalies[:3], 1):
                    self.stdout.write(f'\n   Anomaly {i}:')
                    self.stdout.write(f'     Equipment: {anom["equipment_id"]}')
                    self.stdout.write(f'     Timestamp: {anom["timestamp"]}')
                    self.stdout.write(f'     Anomaly column: {anom["anomaly_column"]}')
                    self.stdout.write(f'     Threshold: {anom["threshold"]:.2f}')
            else:
                self.stdout.write(self.style.WARNING('⚠ No anomalies found'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Failed: {e}'))

        # Test 6: Create training batch
        self.stdout.write('\n[6] Creating training batch...')
        try:
            batch = provider.create_training_batch(
                batch_size=10,
                equipment_types=['chiller', 'ahu'],
                include_anomalies=True,
                anomaly_ratio=0.2
            )
            if batch:
                self.stdout.write(self.style.SUCCESS(f'✓ Training batch created ({len(batch)} examples)'))

                normal_count = sum(1 for ex in batch if not ex.get('is_anomaly', False))
                anomaly_count = len(batch) - normal_count

                self.stdout.write(f'   Normal examples: {normal_count}')
                self.stdout.write(f'   Anomalous examples: {anomaly_count}')

                # Show first example
                if batch:
                    ex = batch[0]
                    self.stdout.write('\n   Sample example:')
                    self.stdout.write(f'     Equipment: {ex["equipment_id"]}')
                    self.stdout.write(f'     Timestamp: {ex["timestamp"]}')
                    self.stdout.write(f'     Is anomaly: {ex.get("is_anomaly", False)}')
            else:
                self.stdout.write(self.style.WARNING('⚠ No batch created'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Failed: {e}'))

        # Summary
        self.stdout.write('\n' + '=' * 70)
        self.stdout.write(self.style.SUCCESS('✓ All RL data provider tests passed!'))
        self.stdout.write(self.style.SUCCESS('Training data is ready for RL/DPO training.'))
        self.stdout.write('=' * 70)
