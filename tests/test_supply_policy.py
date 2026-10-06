import unittest
from api.models2 import PreGameData
from supply_car.compare_supplycar import calculate_supplycar


class SupplyPolicyTests(unittest.TestCase):
    def setUp(self):
        self.policy = calculate_supplycar(PreGameData({'fuelLimits': 120}))
        self.policy.current_supplycars = [{'id': 3, 'remaining_steps': 100}]

    def candidate(self, tid, urgency=2, benefit=1, stopped=0, cost=10):
        return dict(supply_id=3, tourcar_id=tid, urgency=urgency,
                    stopped_days=stopped, benefit_per_step=benefit,
                    meet_end=cost, remaining_fuel=10, service_steps=cost)

    def test_stopped_car_beats_large_benefit_and_wait(self):
        result = self.policy.prioritize_and_assign([
            self.candidate(0, urgency=0, cost=50), self.candidate(1, benefit=100)])
        self.assertEqual(result['assignments'][0]['tourcar_id'], 0)

    def test_longer_stopped_car_wins(self):
        result = self.policy.prioritize_and_assign([
            self.candidate(0, urgency=0, stopped=4),
            self.candidate(1, urgency=0, stopped=1, benefit=100)])
        self.assertEqual(result['assignments'][0]['tourcar_id'], 0)

    def test_imminent_shortage_beats_preventive_benefit(self):
        result = self.policy.prioritize_and_assign([
            self.candidate(0, urgency=1), self.candidate(1, benefit=100)])
        self.assertEqual(result['assignments'][0]['tourcar_id'], 0)

    def test_productive_car_wins_normal_priority(self):
        result = self.policy.prioritize_and_assign([
            self.candidate(0, benefit=1), self.candidate(1, benefit=2)])
        self.assertEqual(result['assignments'][0]['tourcar_id'], 1)

    def test_many_meeting_points_do_not_hide_other_cars(self):
        candidates = [self.candidate(0, benefit=10-i) for i in range(6)]
        candidates.append(self.candidate(1))
        choices = self.policy.create_choices_per_supply(candidates, 5)
        self.assertEqual([c['tourcar_id'] for c in choices[3]], [0, 1])

class SupplyFilteringTests(unittest.TestCase):
    def setUp(self):
        from api.models2 import CellConverter, PreDateData
        from unittest.mock import Mock
        game = PreGameData({'map': {'width': 2, 'height': 1, 'cells': [[0, 0]]},
                            'daySteps': [40, 40], 'fuelLimits': 10,
                            'spots': [{'pos': 1, 'brand': 1, 'stocks': 1}]})
        self.policy = calculate_supplycar(game)
        self.policy.Update_Date(PreDateData({'day': 0, 'agents': [
            {'kind': 0, 'pos': 0, 'fuel': 5}, {'kind': 1, 'pos': 1, 'fuel': 10}]}),
            CellConverter(game.raw_map, game.spots))
        self.policy.set_tour_context([{'id': 0, 'position': [0, 0, 0],
                                      'remaining_fuel': 5, 'remaining_steps': 40}], set(), set())
        self.path = [{'position': [0, 0, 0], 'remaining_fuel': 5, 'step': 0}]
        self.assignment = {'agent_id': 0, 'status': 'reached_goal', 'path': self.path}
        self.candidate = dict(supply_id=1, tourcar_id=0, path_index=0,
                              remaining_fuel=5, meeting_point=[0, 0, 0],
                              supply_arrival_step=2, tour_arrival_step=0,
                              supply_travel_steps=2)
        self.policy.compute_astar = Mock(return_value=[self.candidate])
        self.policy._benefit = Mock(return_value=1)

    def test_recent_refuel_suppresses_nonurgent_following(self):
        self.policy.last_refuel[0] = 0
        self.assertEqual(self.policy.calculate_path_supplycar([self.assignment])['assignments'], [])

    def test_recent_refuel_does_not_block_emergency(self):
        self.policy.last_refuel[0] = 0
        self.assignment['status'] = 'fuel_shortage'
        self.assertEqual(len(self.policy.calculate_path_supplycar([self.assignment])['assignments']), 1)

    def test_full_fuel_is_not_a_preventive_target(self):
        self.candidate['remaining_fuel'] = 10
        self.assertEqual(self.policy.calculate_path_supplycar([self.assignment])['assignments'], [])

    def test_unreachable_fuel_point_and_late_meeting_are_excluded(self):
        self.path[0]['remaining_fuel'] = -1
        self.assertEqual(self.policy.calculate_path_supplycar([self.assignment])['assignments'], [])
        self.path[0]['remaining_fuel'] = 5
        self.candidate['supply_arrival_step'] = 40
        self.assertEqual(self.policy.calculate_path_supplycar([self.assignment])['assignments'], [])

    def test_only_synchronized_refuel_updates_history(self):
        self.policy.Update_current_supplycars({'assignments': []})
        self.assertEqual(self.policy.last_refuel, {})
        self.policy.Update_current_supplycars({'assignments': [
            {'supply_id': 1, 'tourcar_id': 0, 'path': [], 'steps': 0, 'refuel_at': 3}]})
        self.assertEqual(self.policy.last_refuel, {0: 3})
