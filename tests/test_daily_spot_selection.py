import unittest

from api.models2 import CellConverter, PreDateData, PreGameData
from tour_car.compare_tourcar import calculate_tourcar


class DailySpotSelectionTests(unittest.TestCase):
    def setUp(self):
        self.game = PreGameData({
            "map": {"width": 3, "height": 1, "cells": [[1, 1, 1]]},
            "spots": [{"pos": 0, "brand": 0}, {"pos": 1, "brand": 1},
                      {"pos": 2, "brand": 2}],
            "daySteps": [20, 20],
        })
        self.map = CellConverter(self.game.raw_map, self.game.spots)
        self.calculator = calculate_tourcar(self.game)
        self.start_day(0)

    def start_day(self, day):
        self.calculator.Update_Date(PreDateData({
            "day": day,
            "agents": [{"kind": 0, "pos": 0, "fuel": 20}],
        }), self.map)

    def test_selected_goal_is_excluded_before_candidate_limit(self):
        selected = []
        for _ in range(3):
            result = self.calculator.calculate_path_tourcar(pre_filter_count=1)
            self.assertEqual(len(result["assignments"]), 1)
            selected.append(result["assignments"][0]["spot_number"])
        self.assertEqual(selected, [0, 1, 2])
        self.assertEqual(self.calculator.selected_spots_today, {0, 1, 2})
        self.assertEqual(
            self.calculator.calculate_path_tourcar(1)["assignments"], []
        )

    def test_next_day_allows_previous_goals_again(self):
        self.calculator.calculate_path_tourcar(1)
        self.start_day(1)
        self.assertEqual(self.calculator.selected_spots_today, set())
        result = self.calculator.calculate_path_tourcar(1)
        self.assertEqual(result["assignments"][0]["spot_number"], 0)

    def test_match_missing_brand_survives_candidate_limit_and_wins(self):
        self.calculator.acquired_brands_match = {0, 1}
        result = self.calculator.calculate_path_tourcar(1)
        self.assertEqual(result['assignments'][0]['spot_number'], 2)

    def test_daily_acquisition_excludes_other_spots_of_same_brand(self):
        self.game.spots[2].brand = 1
        self.calculator.acquired_brands_today.add(1)
        candidates = self.calculator.Bias(5)
        self.assertEqual([c['spot_number'] for c in candidates[0]], [0])

    def test_truncated_path_does_not_acquire_goal_brand(self):
        self.game.spots[2].stocks = 1
        self.start_day(0)
        path = [{'position': self.map.cells[1].position, 'step': 1}]
        self.calculator.record_synchronized_arrivals([
            {'agent_id': 0, 'spot_number': 2, 'path': path}])
        self.assertNotIn(2, self.calculator.acquired_brands_today)
        self.assertEqual(self.calculator.acquired_brands_match, set())

    def test_missing_brand_goes_to_car_that_can_reach_with_fuel(self):
        self.calculator.acquired_brands_today = {0, 1}
        self.calculator.current_tourcars = [
            {'id': 0, 'position': self.map.cells[1].position,
             'remaining_fuel': 0, 'remaining_steps': 20},
            {'id': 1, 'position': self.map.cells[0].position,
             'remaining_fuel': 20, 'remaining_steps': 20},
        ]
        result = self.calculator.calculate_path_tourcar(1)
        self.assertEqual(result['assignments'][0]['agent_id'], 1)
        self.assertEqual(result['assignments'][0]['spot_number'], 2)

    def test_actual_arrival_and_daily_reset_keep_match_history(self):
        self.game.spots[2].stocks = 1
        self.start_day(0)
        self.calculator.acquired_brands_match = {1}
        self.calculator.record_synchronized_arrivals([{'agent_id': 0, 'path': [
            {'position': self.map.cells[2].position, 'step': 2}]}])
        self.assertEqual(self.calculator.acquired_brands_today, {2})
        self.start_day(1)
        self.assertEqual(self.calculator.acquired_brands_today, set())
        self.assertEqual(self.calculator.missing_brands_match, {0, 2})


if __name__ == "__main__":
    unittest.main()
