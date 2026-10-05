import sys
from pathlib import Path
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'gui'))
from response_timing import summarize_response_times


class ResponseTimingTests(unittest.TestCase):
    def event(self, day, revision, value):
        return {'type': 'post', 'endpoint': '/', 'day': day,
                'body': '{"revision":' + str(revision) + '}',
                'compute_ms': value - 2, 'request_ms': 2, 'response_ms': value}

    def test_last_accepted_answer_and_rejections(self):
        r = summarize_response_times([self.event(0, 1, 10), self.event(0, 2, 20),
                                      self.event(0, -1, 99), self.event(1, 3, 40)], 2)
        self.assertEqual(r['total_ms'], 60)
        self.assertEqual(r['average_ms'], 30)
        self.assertTrue(r['complete'])
        self.assertEqual(r['days'][0]['compute_ms'], 18)

    def test_old_records_and_missing_days_are_unmeasured(self):
        event = self.event(0, 1, 10)
        for key in ['compute_ms', 'request_ms', 'response_ms']:
            event.pop(key)
        r = summarize_response_times([event], 2)
        self.assertIsNone(r['total_ms'])
        self.assertEqual(r['measured_days'], 0)
        self.assertTrue(r['days'][0]['accepted'])
        self.assertFalse(r['days'][1]['accepted'])

    def test_partial_measurement_and_ignored_other_endpoints(self):
        event = self.event(0, 1, 500)
        event['endpoint'] = '/agent'
        r = summarize_response_times([event, self.event(1, 2, 4)], 3)
        self.assertEqual(r['total_ms'], 4)
        self.assertEqual(r['measured_days'], 1)
        self.assertFalse(r['complete'])
