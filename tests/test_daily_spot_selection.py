import unittest

from api.models2 import CellConverter, PreDateData, PreGameData
from tour_car.compare_tourcar import calculate_tourcar


class DailySpotSelectionTests(unittest.TestCase):
    def setUp(self):
        self.game = PreGameData({
            "map": {"width": 3, "height": 1, "cells": [[1, 1, 1]]},
            "spots": [{"pos": 0}, {"pos": 1}, {"pos": 2}],
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


if __name__ == "__main__":
    unittest.main()
