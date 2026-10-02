import unittest

from api.models2 import PreGameData
from divide_agent_type.car_divide import divide_car_kinds, divide_initial_agents


class CarDivideTests(unittest.TestCase):
    def data(self, agents, spots, width=10):
        return PreGameData({
            "map": {"width": width}, "agents": agents,
            "spots": [{"pos": pos} for pos in spots],
        })

    def test_even_and_odd_car_counts(self):
        for count in range(8):
            with self.subTest(count=count):
                kinds = divide_car_kinds(count)
                self.assertEqual(kinds.count(0), (count + 1) // 2)
                self.assertEqual(kinds.count(1), count // 2)

    def test_nearest_agents_selected_without_reordering_ids(self):
        self.assertEqual(divide_initial_agents(
            self.data([9, 1, 8, 2], [0]))['kinds'], [1, 0, 1, 0])
        self.assertEqual(divide_initial_agents(
            self.data([9, 1, 8, 2, 3], [0]))['kinds'], [1, 0, 1, 0, 0])

    def test_nearest_of_all_spots_and_ties_use_agent_id(self):
        self.assertEqual(divide_initial_agents(
            self.data([4, 8, 1, 5], [0, 9]))['kinds'], [1, 0, 0, 1])

    def test_odd_row_hex_distance(self):
        # pos 4 is diagonally adjacent to pos 1, just like pos 0.
        # Their tie is resolved by agent ID rather than rectangular distance.
        self.assertEqual(divide_initial_agents(
            self.data([4, 0], [1], width=3))['kinds'], [0, 1])

    def test_no_spots_falls_back_to_id_order(self):
        self.assertEqual(divide_initial_agents(
            self.data([3, 1, 2], []))['kinds'], [0, 0, 1])


if __name__ == '__main__':
    unittest.main()
