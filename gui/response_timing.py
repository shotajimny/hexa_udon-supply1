"""採用された各日の回答時間を集計する。単位はミリ秒。"""
import json


def summarize_response_times(events, day_count):
    accepted = {}
    for event in events:
        if event.get('type') != 'post' or event.get('endpoint') != '/':
            continue
        try:
            revision = json.loads(event.get('body', '{}')).get('revision', -1)
        except (ValueError, AttributeError):
            continue
        day = event.get('day')
        if revision > 0 and type(day) is int and 0 <= day < day_count:
            accepted[day] = event
    days = []
    for day in range(day_count):
        event = accepted.get(day, {})
        days.append({'day': day, 'accepted': day in accepted,
                     'compute_ms': event.get('compute_ms'),
                     'request_ms': event.get('request_ms'),
                     'response_ms': event.get('response_ms')})
    measured = [d for d in days if d['response_ms'] is not None]
    total = sum(d['response_ms'] for d in measured) if measured else None
    return {'days': days, 'measured_days': len(measured),
            'total_ms': total, 'average_ms': total / len(measured) if measured else None,
            'complete': len(measured) == day_count}
