import sys
from pathlib import Path
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'gui'))
from supply_metrics import summarize_supply_metrics

class SupplyMetricsTests(unittest.TestCase):
    def test_actual_snapshots_and_per_supply_streak(self):
        source = {'map': {'width': 2, 'cells': [[0, 1]]}}
        events = [dict(type='day', day=d, agents=[
            {'kind': 0, 'pos': 0, 'fuel': 0}, {'kind': 0, 'pos': 1, 'fuel': 1},
            {'kind': 1, 'pos': 0, 'fuel': 0}]) for d in [0, 1]]
        events += [dict(type='sync', supplies=[{'supply_id': 2, 'tourcar_id': target}])
                   for target in [0, 0, 1, 0]]
        r = summarize_supply_metrics(source, {'events': events})
        self.assertEqual(r['stopped_car_days'], 4)
        self.assertEqual(r['refuels_by_car'], {0: 3, 1: 1})
        self.assertEqual(r['max_same_target_streak'], 2)
