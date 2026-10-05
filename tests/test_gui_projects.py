import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'gui'))
from dashboard import Store, save


class GuiProjectsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.projects = []
        for name in ['balanced', 'single']:
            project = root / name
            project.mkdir()
            (project / 'main.py').write_text('')
            self.projects.append(str(project))
        self.source = {
            'map': {'width': 2, 'height': 1, 'cells': [[0, 0]]},
            'spots': [{'pos': 1, 'brand': 7, 'stocks': 1}],
            'daySteps': [4], 'players': 2,
        }
        path = root / 'map.json'
        path.write_text(json.dumps(self.source))
        self.store = Store(SimpleNamespace(maps=[path], projects=self.projects,
                                          runs=str(root / 'runs'), server='server'))

    def test_selected_team_keeps_separate_snapshots_and_stats(self):
        save(self.store.root / 'map-teams.json', [
            {'id': i, 'name': str(i), 'project': p} for i, p in enumerate(self.projects)])
        for team, pos in [(0, 0), (1, 1)]:
            save(self.store.root / (self.store.team_prefix('map', team) + '-result.json'), {
                'completed': True, 'events': [{'type': 'day', 'day': 0,
                                             'agents': [{'pos': pos, 'kind': 0}], 'traffics': []}]})
        first = self.store.get('map', 0)
        second = self.store.get('map', 1)
        self.assertEqual(first['stats']['total_count'], 0)
        self.assertEqual(second['stats']['total_count'], 1)
        self.assertEqual([t['stats']['total_count'] for t in second['teams']], [0, 1])
        self.store.import_result('map', [{'day': 0, 'brand': 7, 'count': 3}], team=1)
        self.assertEqual(self.store.get('map', 1)['stats']['total_count'], 3)
        self.assertEqual(self.store.get('map', 0)['stats']['total_count'], 0)

    def test_rejects_too_many_projects_before_starting(self):
        with self.assertRaises(ValueError):
            self.store.start('map', True, self.projects + self.projects)
        self.assertEqual(self.store.jobs, {})

    def test_invalid_project_or_team_is_rejected(self):
        for projects in [[], ['missing'], 'not a list']:
            with self.subTest(projects=projects), self.assertRaises(ValueError):
                self.store.validate_projects(projects)
        with self.assertRaises(ValueError):
            self.store.get('map', 1)
