"""獲得履歴と採用済み行動列を、募集要項の獲得ルールに従って集計する。"""
import json


def summarize_acquisitions(records, day_count):
    if not isinstance(records, list):
        raise ValueError('獲得履歴は配列で指定してください')
    daily = [{'day': day, 'brands': set(), 'total_count': 0}
             for day in range(day_count)]
    for record in records:
        if not isinstance(record, dict):
            raise ValueError('各履歴には day・brand・count が必要です')
        day, brand, count = (record.get(k) for k in ('day', 'brand', 'count'))
        if any(type(v) is not int for v in (day, brand, count)):
            raise ValueError('day・brand・count は整数で指定してください')
        if not 0 <= day < day_count or brand < 0 or count <= 0:
            raise ValueError('dayは試合の日数内、brandは0以上、countは1以上で指定してください')
        daily[day]['brands'].add(brand)
        daily[day]['total_count'] += count
    brands = set().union(*(d['brands'] for d in daily))
    return {
        'total_types': len(brands),
        'total_count': sum(d['total_count'] for d in daily),
        'cumulative_types': sum(len(d['brands']) for d in daily),
        'brands': sorted(brands),
        'days': [{'day': d['day'], 'types': len(d['brands']),
                  'total_count': d['total_count'], 'brands': sorted(d['brands'])}
                 for d in daily],
    }


def replay_acquisitions(source, result):
    """募集要項9〜12ページの到着・個別在庫ルールで採用回答を再生する。

    公式スコアAPIではなく、採用回答による計算。日開始時にスポットに
    いる巡回車も、待機・移動にかかわらず在庫の範囲内で獲得する。
    """
    snapshots, accepted = {}, {}
    current_day = None
    for event in result.get('events', []):
        if event['type'] == 'day':
            current_day = event['day']
            snapshots[current_day] = event
        elif event['type'] == 'post' and event.get('endpoint') == '/':
            try:
                body = json.loads(event.get('body', '{}'))
            except ValueError:
                continue
            if body.get('revision', -1) > 0:
                day = event.get('day', current_day)
                if day is not None:
                    accepted[day] = event['payload']
    if not snapshots:
        return None
    width = source['map']['width']
    height = source['map']['height']
    directions = [(0, 1, -1), (1, 0, -1), (1, -1, 0),
                  (0, -1, 1), (-1, 0, 1), (-1, 1, 0)]
    spots = {s['pos']: s for s in source['spots']}
    records, known = [], []
    notes = []
    for day, budget in enumerate(source['daySteps']):
        snapshot = snapshots.get(day)
        settled = any(d > day for d in snapshots) or result.get('completed', False)
        if snapshot is None or not settled:
            continue
        payload = accepted.get(day)
        if payload is None:
            # 有効回答なしなら全車待機。開始地点での獲得も再生する。
            payload = [[-budget] for _ in snapshot['agents']]
        traffic = {t['pos']: t['status'] for t in snapshot.get('traffics', [])}
        if (day > 0 and 'traffics' not in snapshot
                and any(action >= 0 for actions in payload for action in actions
                        if type(action) is int)):
            notes.append(f'{day + 1}日目の渋滞情報がないため未集計')
            continue
        arrivals = []
        predicted = []
        valid = len(payload) == len(snapshot['agents'])
        for agent_id, agent in enumerate(snapshot['agents']):
            pos, step = agent['pos'], 0
            if agent['kind'] == 0 and pos in spots:
                arrivals.append((0, agent_id, pos))
            for action in payload[agent_id] if valid else []:
                if type(action) is not int:
                    valid = False; break
                if action < 0:
                    step -= action
                    continue
                if action > 5:
                    valid = False; break
                row, col = divmod(pos, width)
                terrain = source['map']['cells'][row][col]
                cost = [1, 2, 4][traffic.get(pos, 0)] if terrain == 1 else {0: 2, 2: 3}.get(terrain)
                if cost is None:
                    valid = False; break
                step += cost
                x = col - (row + (row & 1)) // 2
                dx, _, dz = directions[action]
                next_row = row + dz
                next_col = x + dx + (next_row + (next_row & 1)) // 2
                if not (0 <= next_row < height and 0 <= next_col < width):
                    valid = False; break
                pos = next_row * width + next_col
                if source['map']['cells'][next_row][next_col] == 3 or step > budget:
                    valid = False; break
                if agent['kind'] == 0 and pos in spots:
                    arrivals.append((step, agent_id, pos))
            predicted.append(pos)
            if step != budget:
                valid = False
        next_snapshot = snapshots.get(day + 1)
        if next_snapshot and predicted != [a['pos'] for a in next_snapshot['agents']]:
            valid = False
        if not valid:
            notes.append(f'{day + 1}日目は採用回答の再生と実状態が一致しないため未集計')
            continue
        inventory = {pos: spot['stocks'] for pos, spot in spots.items()}
        visited = set()
        for _, agent_id, pos in sorted(arrivals):
            key = (agent_id, pos)
            if key in visited:
                continue
            visited.add(key)
            if inventory[pos] <= 0:
                continue
            inventory[pos] -= 1
            records.append({'day': day, 'brand': spots[pos]['brand'], 'count': 1})
        known.append(day)
    stats = summarize_acquisitions(records, len(source['daySteps']))
    for day in stats['days']:
        if day['day'] not in known:
            day.update(types=None, total_count=None, brands=None)
    stats.update(method='replay', known_days=known,
                 complete=len(known) == len(source['daySteps']), notes=notes,
                 start_spot_policy='include_start')
    return stats
