import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'gui'))
from result_stats import summarize_acquisitions, replay_acquisitions


class ResultStatsTests(unittest.TestCase):
    def test_duplicates_across_days_and_cars_do_not_increase_type_count(self):
        r = summarize_acquisitions([
            {'day': 0, 'brand': 0, 'count': 2},
            {'day': 0, 'brand': 0, 'count': 1},
            {'day': 0, 'brand': 1, 'count': 3},
            {'day': 1, 'brand': 1, 'count': 2},
            {'day': 1, 'brand': 2, 'count': 1},
        ], 3)
        self.assertEqual(r['total_types'], 3)
        self.assertEqual(r['total_count'], 9)
        self.assertEqual(r['cumulative_types'], 4)
        self.assertEqual([d['types'] for d in r['days']], [2, 2, 0])
        self.assertEqual([d['total_count'] for d in r['days']], [6, 3, 0])

    def test_missing_brands_use_map_brands_with_duplicates_removed(self):
        r = summarize_acquisitions([
            {'day': 0, 'brand': 7, 'count': 1},
            {'day': 1, 'brand': 9, 'count': 1},
        ], 3, [7, 9, 12, 12])
        self.assertEqual(r['missing_brands'], [12])
        self.assertEqual([d['missing_brands'] for d in r['days']],
                         [[9, 12], [7, 12], [7, 9, 12]])

    def test_known_empty_history_is_zero(self):
        self.assertEqual(summarize_acquisitions([], 2)['total_count'], 0)

    def test_invalid_history_is_rejected(self):
        for record in [{'day': 2, 'brand': 0, 'count': 1},
                       {'day': 0, 'brand': 0, 'count': -1},
                       {'day': True, 'brand': 0, 'count': 1}]:
            with self.subTest(record=record), self.assertRaises(ValueError):
                summarize_acquisitions([record], 2)


class ReplayResultTests(unittest.TestCase):
    def source(self):
        return {'map': {'width': 2, 'height': 1, 'cells': [[0, 0]]},
                'spots': [{'pos': 1, 'brand': 7, 'stocks': 1}],
                'daySteps': [4, 4]}

    def day(self, day, positions=(0, 0), kinds=(0, 0)):
        return {'type': 'day', 'day': day, 'agents': [
            {'pos': pos, 'kind': kind, 'fuel': 20}
            for pos, kind in zip(positions, kinds)], 'traffics': []}

    def answer(self, payload, revision=1):
        return {'type': 'post', 'endpoint': '/', 'body':
                '{"revision":' + str(revision) + '}', 'payload': payload}

    def test_stock_limit_and_daily_restock(self):
        r = replay_acquisitions(self.source(), {'completed': True, 'events': [
            self.day(0), self.answer([[2, 5], [2, 5]]),
            self.day(1), self.answer([[2, 5], [2, 5]])]})
        self.assertTrue(r['complete'])
        self.assertEqual(r['total_count'], 2)
        self.assertEqual(r['total_types'], 1)
        self.assertEqual(r['cumulative_types'], 2)

    def test_supply_car_does_not_collect_and_rejection_keeps_valid_answer(self):
        s = self.source();s['spots'][0]['stocks'] = 2
        r = replay_acquisitions(s, {'completed': True, 'events': [
            self.day(0, kinds=(0, 1)), self.answer([[2, 5], [2, 5]]),
            self.answer([[99], [99]], -1)]})
        self.assertEqual(r['total_count'], 1)
        self.assertFalse(r['complete'])
        self.assertIsNone(r['days'][1]['types'])

    def test_starting_on_a_spot_collects_with_stock_limit(self):
        r = replay_acquisitions(self.source(), {'completed': True, 'events': [
            self.day(0, positions=(1, 1)), self.answer([[-4], [-4]])]})
        self.assertEqual(r['total_count'], 1)

    def test_starting_car_leaving_and_returning_collects_once(self):
        s = self.source(); s['spots'][0]['stocks'] = 2
        r = replay_acquisitions(s, {'completed': True, 'events': [
            self.day(0, positions=(1, 0), kinds=(0, 1)),
            self.answer([[5, 2], [-4]])]})
        self.assertEqual(r['total_count'], 1)

    def test_starting_supply_car_does_not_collect(self):
        r = replay_acquisitions(self.source(), {'completed': True, 'events': [
            self.day(0, positions=(1, 1), kinds=(1, 1)),
            self.answer([[-4], [-4]])]})
        self.assertEqual(r['total_count'], 0)

    def test_no_valid_answer_still_collects_at_start_each_day(self):
        r = replay_acquisitions(self.source(), {'completed': True, 'events': [
            self.day(0, positions=(1, 1)), self.answer([[99], [99]], -1),
            self.day(1, positions=(1, 1))]})
        self.assertTrue(r['complete'])
        self.assertEqual([d['total_count'] for d in r['days']], [1, 1])
        self.assertEqual(r['total_count'], 2)

    def test_repeat_arrivals_by_same_car_are_counted_once(self):
        s = self.source();s['daySteps'] = [8];s['spots'][0]['stocks'] = 2
        r = replay_acquisitions(s, {'completed': True, 'events': [
            self.day(0), self.answer([[2, 5, 2, 5], [-8]])]})
        self.assertEqual(r['total_count'], 1)

    def test_unsettled_day_and_state_mismatch_are_not_reported_as_zero(self):
        r = replay_acquisitions(self.source(), {'completed': False, 'events': [
            self.day(0), self.answer([[2, -2], [2, -2]])]})
        self.assertIsNone(r['missing_brands'])
        self.assertIsNone(r['days'][0]['missing_brands'])
        self.assertEqual(r['known_days'], [])
        self.assertIsNone(r['days'][0]['types'])
        r = replay_acquisitions(self.source(), {'completed': False, 'events': [
            self.day(0), self.answer([[2, -2], [2, -2]]), self.day(1)]})
        self.assertIsNone(r['missing_brands'])
        self.assertIsNone(r['days'][0]['missing_brands'])
        self.assertEqual(r['known_days'], [])
        self.assertTrue(r['notes'])


if __name__ == '__main__':
    unittest.main()
