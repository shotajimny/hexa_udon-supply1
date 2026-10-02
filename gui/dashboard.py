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
from urllib.parse import urlparse
from result_stats import summarize_acquisitions, replay_acquisitions

REPO = Path(__file__).resolve().parents[1]
ASSETS = Path(__file__).resolve().parent


def save(path, value):
    path = Path(path)
    temp = path.with_suffix('.tmp')
    temp.write_text(json.dumps(value, ensure_ascii=False), encoding='utf-8')
    temp.replace(path)


def worker(port, output):
    import requests
    sys.path.insert(0, str(REPO))
    os.chdir(REPO)
    from PathSynchronizer import PathSynchronizer
    data = {'events': [], 'completed': False, 'running': True}
    original = requests.sessions.Session.request
    original_sync = PathSynchronizer.synchronize_paths
    day = -1

    def sync(self, *args, **kwargs):
        tours, supplies = original_sync(self, *args, **kwargs)
        data['events'].append({'type': 'sync', 'day': day,
                               'tours': tours, 'supplies': supplies})
        save(output, data)
        return tours, supplies

    def observe(session, method, url, **kwargs):
        nonlocal day
        routed = url.replace('http://127.0.0.1:8080', f'http://127.0.0.1:{port}')
        response = original(session, method, routed, **kwargs)
        endpoint = urlparse(url).path
        if method.upper() == 'POST':
            data['events'].append({'type': 'post', 'day': day, 'endpoint': endpoint,
                                   'http': response.status_code, 'body': response.text,
                                   'payload': kwargs.get('json')})
        elif endpoint == '/' and response.status_code == 200:
            snapshot = response.json()
            day = snapshot['day']
            data['events'].append({'type': 'day', **snapshot})
        save(output, data)
        return response

    requests.sessions.Session.request = observe
    PathSynchronizer.synchronize_paths = sync
    try:
        runpy.run_path(str(REPO / 'main.py'), run_name='__main__')
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

    def listing(self):
        return {'maps': [{'id': name, 'width': s['map']['width'], 'height': s['map']['height'],
                          'agents': len(s['agents']), 'days': len(s['daySteps'])}
                         for name, s in sorted(self.maps.items())],
                'can_run': bool(self.args.server), 'running': list(self.jobs)}

    def get(self, name):
        if name not in self.maps:
            raise ValueError('未知のマップです')
        source = self.maps[name]
        path = self.root / (name + '-result.json')
        data = json.loads(path.read_text()) if path.exists() else {'events': [], 'completed': False}
        data['running'] = name in self.jobs
        # Earlier observations omitted traffic information: read matching server snapshots.
        if any(e['type'] == 'day' and 'traffics' not in e for e in data['events']):
            import ast
            log = self.root / (name + '-client.log')
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
        acquisitions = self.root / (name + '-acquisitions.json')
        stats = None
        if acquisitions.exists():
            stats = summarize_acquisitions(json.loads(acquisitions.read_text()), len(source['daySteps']))
            stats['method'] = 'imported'
            stats['complete'] = True
        else:
            stats = replay_acquisitions(source, data)
        return {'source': source, 'result': data, 'stats': stats}

    def import_result(self, name, records):
        if name not in self.maps:
            raise ValueError('未知のマップです')
        if name in self.jobs:
            raise ValueError('試合が終了してから獲得履歴を読み込んでください')
        stats = summarize_acquisitions(records, len(self.maps[name]['daySteps']))
        save(self.root / (name + '-acquisitions.json'), records)
        return stats

    def start(self, name, fast):
        with self.lock:
            if self.stopping:
                raise ValueError('終了処理中です')
            if self.jobs:
                raise ValueError('実行中の試合が終わるまで待ってください')
            if name not in self.maps or not self.args.server:
                raise ValueError('マップまたはゲームサーバーが指定されていません')
            self.jobs[name] = True
        threading.Thread(target=self.run, args=(name, fast), daemon=True).start()

    def run(self, name, fast):
        processes = []
        resultpath = self.root / (name + '-result.json')
        # 再実行しても以前の観測結果を失わない。
        previous = [self.root / (name + suffix) for suffix in
                    ('-result.json', '-config.json', '-client.log', '-server.log', '-acquisitions.json')]
        if any(p.exists() for p in previous):
            archive = self.root / 'archives' / (name + '-' + str(time.time_ns()))
            archive.mkdir(parents=True)
            for path in previous:
                if path.exists():
                    shutil.copy2(path, archive / path.name)
            acquisitions = self.root / (name + '-acquisitions.json')
            acquisitions.unlink(missing_ok=True)
        save(resultpath, {'events': [], 'running': True, 'completed': False})
        try:
            s = self.maps[name]
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
                client = subprocess.Popen([sys.executable, '-u', str(ASSETS / 'dashboard.py'),
                                           '--worker', str(port), str(resultpath)],
                                          cwd=REPO, stdout=cl, stderr=cl,
                                          env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'})
                processes.append(client)
                limit = sum(p['daySeconds']) + 90
                started = time.monotonic()
                while client.poll() is None:
                    if self.stopping or time.monotonic() - started > limit:
                        raise RuntimeError('試合を中断しました、または実行がタイムアウトしました')
                    time.sleep(.2)
                if client.returncode != 0:
                    raise RuntimeError('クライアントが異常終了しました。詳細はイベントとclient.logを確認してください')
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
                self.send_json(self.server.store.get(path.removeprefix('/api/run/')))
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
                stats = self.server.store.import_result(body['map'], body['records'])
                self.send_json({'stats': stats})
                return
            self.server.store.start(body['map'], bool(body.get('fast', False)))
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
    parser.add_argument('--worker', nargs=2, metavar=('PORT', 'OUTPUT'), help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.worker:
        worker(int(args.worker[0]), args.worker[1]); return
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
