"""実測日開始状態と同期補給記録から比較指標を作る。"""
from collections import Counter


def summarize_supply_metrics(source, result):
    snapshots = {e['day']: e for e in result.get('events', []) if e['type'] == 'day'}
    stopped = Counter()
    for snapshot in snapshots.values():
        for aid, agent in enumerate(snapshot['agents']):
            if agent['kind'] != 0:
                continue
            row, col = divmod(agent['pos'], source['map']['width'])
            cost = {0: 1, 1: 2, 2: 2}.get(source['map']['cells'][row][col])
            if cost is not None and 'fuel' in agent and agent['fuel'] < cost:
                stopped[aid] += 1
    refuels = Counter()
    last, streak = {}, {}
    maximum = 0
    for event in result.get('events', []):
        if event['type'] != 'sync':
            continue
        for assignment in event.get('supplies', []):
            sid, tid = assignment['supply_id'], assignment['tourcar_id']
            refuels[tid] += 1
            streak[sid] = streak.get(sid, 0) + 1 if last.get(sid) == tid else 1
            last[sid] = tid
            maximum = max(maximum, streak[sid])
    return {'stopped_car_days': sum(stopped.values()), 'stopped_by_car': dict(stopped),
            'observed_days': len(snapshots), 'planned_refuels': sum(refuels.values()),
            'refuels_by_car': dict(refuels), 'max_same_target_streak': maximum}
