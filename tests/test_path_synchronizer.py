import unittest
from api.models2 import CellConverter
from PathSynchronizer import PathSynchronizer


class PathSynchronizerTests(unittest.TestCase):
    def setUp(self):
        self.map = CellConverter({'width': 4, 'height': 1, 'cells': [[1]*4]})
        self.path = [{'position': c.position, 'step': i} for i, c in enumerate(self.map.cells)]
        self.tour = {'id': 0, 'position': self.path[0]['position'],
                     'remaining_steps': 10, 'remaining_fuel': 2}
        self.supply = {'id': 2, 'position': self.path[3]['position'],
                       'remaining_steps': 10}
        self.assignment = {'agent_id': 0, 'path': self.path}
        self.supply_assignment = {
            'supply_id': 2, 'tourcar_id': 0, 'meeting_point': self.path[1]['position'],
            'path_index': 1, 'path': list(reversed(self.path[1:]))}

    def sync(self, supply=None, day_steps=10):
        return PathSynchronizer([self.assignment], supply or []).synchronize_paths(
            [self.tour], [self.supply], self.map, 10, day_steps)

    def test_no_supply_stops_before_fuel_runs_out(self):
        tours, supplies = self.sync()
        self.assertEqual(len(tours[0]['path']), 2)
        self.assertEqual(tours[0]['remaining_fuel'], 0)
        self.assertFalse(tours[0]['complete'])
        self.assertEqual(supplies, [])

    def test_late_supply_adds_wait_and_restores_fuel(self):
        tours, supplies = self.sync([self.supply_assignment])
        self.assertTrue(tours[0]['complete'])
        self.assertEqual(tours[0]['actions'][1], {'status': 'wait', 'waiting_time': 2})
        self.assertEqual(tours[0]['remaining_fuel'], 6)
        self.assertEqual(tours[0]['steps'], 5)
        self.assertEqual(supplies[0]['refuel_at'], 3)
        self.assertEqual(supplies[0]['actions'][-1]['waiting_time'], 1)
        self.assertEqual(self.tour['remaining_fuel'], 2)
        self.assertEqual(len(self.assignment['path']), 4)

    def test_early_supply_waits_for_tour(self):
        self.supply['position'] = self.path[1]['position']
        self.supply_assignment['path'] = [self.path[1]]
        tours, supplies = self.sync([self.supply_assignment])
        self.assertEqual(supplies[0]['actions'][0]['waiting_time'], 2)
        self.assertEqual(tours[0]['actions'][1]['waiting_time'], 1)

    def test_unreachable_meeting_does_not_restore_fuel(self):
        self.supply_assignment['path_index'] = 2
        self.supply_assignment['meeting_point'] = self.path[2]['position']
        self.supply_assignment['path'] = list(reversed(self.path[2:]))
        tours, supplies = self.sync([self.supply_assignment])
        self.assertEqual(supplies, [])
        self.assertEqual(tours[0]['remaining_fuel'], 0)

    def test_absolute_clock_and_day_boundary(self):
        self.tour['remaining_steps'] = 1
        tours, supplies = self.sync([self.supply_assignment])
        self.assertEqual(supplies, [])  # 合流後の1step待機まで日内に収まらない
        self.assertLessEqual(tours[0]['steps'], 1)


if __name__ == '__main__':
    unittest.main()
