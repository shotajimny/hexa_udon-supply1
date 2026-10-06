"""Hexa Udon observer. Run: python gui/dashboard.py --help."""
import argparse
import json
import os
from pathlib import Path
import runpy
import shutil
import socket
import subprocess
import sys
import threading
import time
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs
from result_stats import summarize_acquisitions, replay_acquisitions
from response_timing import summarize_response_times
from supply_metrics import summarize_supply_metrics

REPO = Path(__file__).resolve().parents[1]
ASSETS = Path(__file__).resolve().parent


def save(path, value):
    path = Path(path)
    temp = path.with_suffix('.tmp')
    temp.write_text(json.dumps(value, ensure_ascii=False), encoding='utf-8')
    temp.replace(path)


def worker(port, output, project=REPO, token="token-p0"):
    project = Path(project).resolve()
    import requests
    sys.path.insert(0, str(project))
    os.chdir(project)
    try:
        from PathSynchronizer import PathSynchronizer
    except ImportError:
        PathSynchronizer = None
    data = {'events': [], 'completed': False, 'running': True}
    original = requests.sessions.Session.request
    original_sync = PathSynchronizer.synchronize_paths if PathSynchronizer else None
    day = -1
    day_received = {}

    def sync(self, *args, **kwargs):
        tours, supplies = original_sync(self, *args, **kwargs)
        data['events'].append({'type': 'sync', 'day': day,
                               'tours': tours, 'supplies': supplies})
        save(output, data)
        return tours, supplies

    def observe(session, method, url, **kwargs):
        nonlocal day
        routed = url.replace('http://127.0.0.1:8080', f'http://127.0.0.1:{port}')
        if url.startswith('http://127.0.0.1:8080'):
            params = dict(kwargs.get('params') or {})
            params['token'] = token
            kwargs['params'] = params
        sent_at = time.perf_counter()
        response = original(session, method, routed, **kwargs)
        received_at = time.perf_counter()
        endpoint = urlparse(url).path
        if method.upper() == 'POST':
            data['events'].append({'type': 'post', 'day': day, 'endpoint': endpoint,
                                   'http': response.status_code, 'body': response.text,
                                   'payload': kwargs.get('json'),
                                   'request_ms': (received_at - sent_at) * 1000,
                                   'compute_ms': ((sent_at - day_received[day]) * 1000
                                                  if endpoint == '/' and day in day_received else None),
                                   'response_ms': ((received_at - day_received[day]) * 1000
                                                   if endpoint == '/' and day in day_received else None)})
        elif endpoint == '/' and response.status_code == 200:
            snapshot = response.json()
            day = snapshot['day']
            day_received.setdefault(day, received_at)
            data['events'].append({'type': 'day', **snapshot})
        save(output, data)
        return response

    requests.sessions.Session.request = observe
    if PathSynchronizer:
        PathSynchronizer.synchronize_paths = sync
    try:
        runpy.run_path(str(project / 'main.py'), run_name='__main__')
        data['completed'] = True
    except BaseException:
        data['error'] = traceback.format_exc()
        raise
    finally:
        data['running'] = False
        save(output, data)


class Store:
    def __init__(self, args):
        self.args = args
        self.root = Path(args.runs).resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.lock = threading.Lock()
        self.jobs = {}
        self.stopping = False
        self.projects = self.validate_projects(getattr(args, "projects", None) or [str(REPO)])
        self.maps = {}
        for path in args.maps:
            path = Path(path).resolve()
            name = path.stem
            if name in self.maps:
                raise ValueError(f'同名のマップです: {name}')
            config = json.loads(path.read_text())
            if 'problem' in config:
                problem = config['problem']
                source = {'map': {k: problem[k] for k in ('width', 'height', 'cells')},
                          **{k: problem[k] for k in ('spots', 'fuelLimits', 'daySteps', 'daySeconds', 'busyThreshold', 'jammedThreshold')},
                          'agents': problem['agentStarts'], 'players': len(config['teams'])}
            else:
                source = config
            self.maps[name] = source
        # Recorded runs can be opened even when original uploaded maps are absent.
        for path in self.root.glob('*-config.json'):
            name = path.name.removesuffix('-config.json')
            if name in self.maps:
                continue
            p = json.loads(path.read_text())['problem']
            self.maps[name] = {'map': {k: p[k] for k in ('width', 'height', 'cells')},
                               **{k: p[k] for k in ('spots', 'fuelLimits', 'daySteps', 'daySeconds', 'busyThreshold', 'jammedThreshold')},
                               'agents': p['agentStarts'], 'players': len(json.loads(path.read_text())['teams'])}

    @staticmethod
    def validate_projects(projects):
        if not isinstance(projects, list) or not projects or any(not isinstance(p, str) for p in projects):
            raise ValueError('参加プロジェクトを1件以上指定してください')
        paths = [Path(p).expanduser().resolve() for p in projects]
        for path in paths:
            if not (path / 'main.py').is_file():
                raise ValueError(f'main.pyがありません: {path}')
        return [str(path) for path in paths]

    def team_prefix(self, name, team):
        return name if team == 0 else f'{name}-team-{team}'

    def listing(self):
        return {'maps': [{'id': name, 'width': s['map']['width'], 'height': s['map']['height'],
                          'agents': len(s['agents']), 'days': len(s['daySteps'])}
                         for name, s in sorted(self.maps.items())],
                'projects': self.projects, 'can_run': bool(self.args.server), 'running': list(self.jobs)}

    def get(self, name, team=0):
        manifest = self.root / (name + '-teams.json')
        participants = json.loads(manifest.read_text()) if manifest.exists() else [
            {'id': 0, 'name': REPO.name, 'project': str(REPO)}]
        if not 0 <= team < len(participants):
            raise ValueError('未知のチームです')
        teams = []
        selected = None
        for participant in participants:
            detail = self.get_team(name, participant['id'])
            teams.append({**participant, 'stats': detail['stats'], 'timing': detail['timing'], 'supply_metrics': detail['supply_metrics'],
                          'running': detail['result'].get('running', False),
                          'completed': detail['result'].get('completed', False),
                          'error': detail['result'].get('error')})
            if participant['id'] == team:
                selected = detail
        return {**selected, 'teams': teams, 'team': team}

    def get_team(self, name, team=0):
        if name not in self.maps:
            raise ValueError('未知のマップです')
        source = self.maps[name]
        prefix = self.team_prefix(name, team)
        path = self.root / (prefix + '-result.json')
        data = json.loads(path.read_text()) if path.exists() else {'events': [], 'completed': False}
        data['running'] = name in self.jobs
        # Earlier observations omitted traffic information: read matching server snapshots.
        if any(e['type'] == 'day' and 'traffics' not in e for e in data['events']):
            import ast
            log = self.root / (prefix + '-client.log')
            if log.exists():
                snapshots = {}
                for line in log.read_text(errors='replace').splitlines():
                    if line.startswith('get_day_data response: '):
                        try:
                            s = ast.literal_eval(line.split(': ', 1)[1]); snapshots[s['day']] = s
                        except (ValueError, SyntaxError, KeyError):
                            pass
                for e in data['events']:
                    if e['type'] == 'day' and e['day'] in snapshots:
                        e.update(snapshots[e['day']])
        acquisitions = self.root / (prefix + '-acquisitions.json')
        stats = None
        if acquisitions.exists():
            stats = summarize_acquisitions(json.loads(acquisitions.read_text()), len(source['daySteps']),
                                           (spot['brand'] for spot in source['spots']))
            stats['method'] = 'imported'
            stats['complete'] = True
        else:
            stats = replay_acquisitions(source, data)
        return {'source': source, 'result': data, 'stats': stats,
                'timing': summarize_response_times(data['events'], len(source['daySteps'])),
                'supply_metrics': summarize_supply_metrics(source, data)}

    def import_result(self, name, records, team=0):
        self.get(name, team)
        if name not in self.maps:
            raise ValueError('未知のマップです')
        if name in self.jobs:
            raise ValueError('試合が終了してから獲得履歴を読み込んでください')
        stats = summarize_acquisitions(records, len(self.maps[name]['daySteps']),
                                       (spot['brand'] for spot in self.maps[name]['spots']))
        save(self.root / (self.team_prefix(name, team) + '-acquisitions.json'), records)
        return stats

    def start(self, name, fast, projects=None):
        projects = self.validate_projects(self.projects if projects is None else projects)
        if name in self.maps and len(projects) > self.maps[name]["players"]:
            raise ValueError("参加プロジェクト数がマップのチーム数を超えています")
        with self.lock:
            if self.stopping:
                raise ValueError('終了処理中です')
            if self.jobs:
                raise ValueError('実行中の試合が終わるまで待ってください')
            if name not in self.maps or not self.args.server:
                raise ValueError('マップまたはゲームサーバーが指定されていません')
            self.jobs[name] = True
        threading.Thread(target=self.run, args=(name, fast, projects), daemon=True).start()

    def run(self, name, fast, projects=None):
        processes, logfiles = [], []
        resultpath = self.root / (name + '-result.json')
        previous = list(self.root.glob(name + '-*.json')) + list(self.root.glob(name + '-*.log'))
        if previous:
            archive = self.root / 'archives' / (name + '-' + str(time.time_ns()))
            archive.mkdir(parents=True)
            for path in previous:
                shutil.copy2(path, archive / path.name)
                path.unlink()
        save(resultpath, {'events': [], 'running': True, 'completed': False})
        try:
            s = self.maps[name]
            projects = self.validate_projects(self.projects if projects is None else projects)
            if len(projects) > s['players']:
                raise ValueError('参加プロジェクト数がマップのチーム数を超えています')
            participants = [{'id': i, 'name': Path(project).name, 'project': project}
                            for i, project in enumerate(projects)]
            save(self.root / (name + '-teams.json'), participants)
            p = dict(s['map'])
            p.update({k: s[k] for k in ('spots', 'fuelLimits', 'daySteps', 'busyThreshold', 'jammedThreshold')})
            p['daySeconds'] = [3] * len(s['daySteps']) if fast else s['daySeconds']
            p['agentStarts'] = s['agents']
            config = {'problem': p, 'teams': [{'token': f'token-p{i}'} for i in range(s['players'])]}
            configpath = self.root / (name + '-config.json')
            save(configpath, config)
            with socket.socket() as sock:
                sock.bind(('127.0.0.1', 0)); port = sock.getsockname()[1]
            with (self.root / (name + '-server.log')).open('w') as sl, (self.root / (name + '-client.log')).open('w') as cl:
                server = subprocess.Popen([str(Path(self.args.server).resolve()), '-config', str(configpath),
                                           '-addr', f'127.0.0.1:{port}', '-kind-deadline', '5s',
                                           '-match-start-delay', '1s'], stdout=sl, stderr=sl)
                processes.append(server)
                import requests
                for _ in range(50):
                    if server.poll() is not None:
                        raise RuntimeError('ゲームサーバーが終了しました。server.log を確認してください')
                    try:
                        r = requests.get(f'http://127.0.0.1:{port}/setting', params={'token': 'token-p0'}, timeout=1)
                        if r.status_code == 200:
                            break
                    except requests.ConnectionError:
                        pass
                    time.sleep(.1)
                else:
                    raise RuntimeError('ゲームサーバーの起動がタイムアウトしました')
                clients = []
                for participant in participants:
                    team = participant['id']
                    prefix = self.team_prefix(name, team)
                    output = self.root / (prefix + '-result.json')
                    save(output, {'events': [], 'running': True, 'completed': False})
                    log = cl if team == 0 else (self.root / (prefix + '-client.log')).open('w')
                    if team != 0:
                        logfiles.append(log)
                    python = Path(participant['project']) / 'venv' / 'bin' / 'python'
                    interpreter = str(python) if python.is_file() else sys.executable
                    client = subprocess.Popen([interpreter, '-u', str(ASSETS / 'dashboard.py'),
                                               '--worker', str(port), str(output),
                                               '--project-root', participant['project'],
                                               '--team-token', f'token-p{team}'],
                                              cwd=participant['project'], stdout=log, stderr=log,
                                              env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'})
                    clients.append(client)
                    processes.append(client)
                limit = sum(p['daySeconds']) + 90
                started = time.monotonic()
                while any(client.poll() is None for client in clients):
                    if self.stopping or time.monotonic() - started > limit:
                        raise RuntimeError('試合を中断しました、または実行がタイムアウトしました')
                    time.sleep(.2)
                if any(client.returncode != 0 for client in clients):
                    raise RuntimeError('参加プロジェクトが異常終了しました。各チームのclient.logを確認してください')
        except Exception as exc:
            data = json.loads(resultpath.read_text())
            data['error'] = data.get('error') or str(exc)
            data['running'] = False
            save(resultpath, data)
        finally:
            for proc in reversed(processes):
                if proc.poll() is None:
                    proc.terminate()
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.kill(); proc.wait()
            for log in logfiles:
                log.close()
            with self.lock:
                self.jobs.pop(name, None)


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def send_json(self, value, status=200):
        body = json.dumps(value, ensure_ascii=False).encode()
        self.send_response(status); self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Cache-Control', 'no-store'); self.send_header('Content-Length', str(len(body)))
        self.end_headers(); self.wfile.write(body)

    def do_GET(self):
        path = urlparse(self.path).path
        try:
            if path == '/api/maps':
                self.send_json(self.server.store.listing())
            elif path.startswith('/api/run/'):
                self.send_json(self.server.store.get(path.removeprefix('/api/run/'),
                                                     int(parse_qs(urlparse(self.path).query).get('team', ['0'])[0])))
            elif path in ('/', '/index.html', '/app.js', '/style.css'):
                asset = ASSETS / ('index.html' if path == '/' else path[1:])
                body = asset.read_bytes()
                mime = {'.html': 'text/html', '.js': 'text/javascript', '.css': 'text/css'}[asset.suffix]
                self.send_response(200); self.send_header('Content-Type', mime + '; charset=utf-8')
                self.send_header('Content-Length', str(len(body))); self.end_headers(); self.wfile.write(body)
            else:
                self.send_json({'error': '見つかりません'}, 404)
        except (ValueError, OSError) as exc:
            self.send_json({'error': str(exc)}, 400)

    def do_POST(self):
        # Only the local UI may start a process; reject cross-origin browser requests.
        origin = self.headers.get('Origin')
        if origin and urlparse(origin).netloc != self.headers.get('Host'):
            self.send_json({'error': '異なるオリジンからは実行できません'}, 403); return
        try:
            if self.path not in ('/api/start', '/api/result'):
                self.send_json({'error': '見つかりません'}, 404); return
            length = int(self.headers.get('Content-Length', '0'))
            if not 0 < length <= 262144:
                raise ValueError('不正なリクエストです')
            body = json.loads(self.rfile.read(length))
            if self.path == '/api/result':
                stats = self.server.store.import_result(body['map'], body['records'], int(body.get('team', 0)))
                self.send_json({'stats': stats})
                return
            self.server.store.start(body['map'], bool(body.get('fast', False)), body.get('projects'))
            self.send_json({'started': True}, 202)
        except (ValueError, KeyError) as exc:
            self.send_json({'error': str(exc)}, 400)


def main():
    parser = argparse.ArgumentParser(description='ヘキサうどんの試合観測・経路再生GUI')
    parser.add_argument('--host', default='127.0.0.1')
    parser.add_argument('--port', type=int, default=8765)
    parser.add_argument('--server', help='OSに対応するprocon-serverのパス（試合実行に必要）')
    parser.add_argument('--maps', nargs='*', default=[], help='/setting形式またはサーバー設定JSONのパス')
    parser.add_argument('--runs', default=str(REPO / 'gui-runs'), help='試合記録ディレクトリ')
    parser.add_argument('--projects', nargs='+', help='参加するプロジェクトのディレクトリ（main.pyを実行）')
    parser.add_argument('--project-root', default=str(REPO), help=argparse.SUPPRESS)
    parser.add_argument('--team-token', default='token-p0', help=argparse.SUPPRESS)
    parser.add_argument('--worker', nargs=2, metavar=('PORT', 'OUTPUT'), help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.worker:
        worker(int(args.worker[0]), args.worker[1], args.project_root, args.team_token); return
    store = Store(args)
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    server.store = store
    print(f'GUI listening on {args.host}:{server.server_port}', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        store.stopping = True
        server.server_close()


if __name__ == '__main__':
    main()
