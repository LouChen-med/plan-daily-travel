"""Check door-to-door timing; no network or booking functionality.

Run with a verified Python environment:
  python check_itinerary.py --input itinerary.json
  python check_itinerary.py --input itinerary.json --delay-minutes 30 --delay-segment 0
  python check_itinerary.py --self-test
Input schema and limitations: ../references/output-format.md
"""
import argparse
import json
from datetime import datetime, timedelta
from pathlib import Path


def timestamp(value):
    dt = datetime.fromisoformat(value)
    if dt.tzinfo is None or dt.utcoffset() is None:
        raise ValueError('Timestamps must include a UTC offset')
    return dt


def minutes(value, field):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or value < 0:
        raise ValueError(field + ' must be a non-negative number')
    return timedelta(minutes=value)


def check(segments, delay=0, delay_segment=0):
    if not isinstance(segments, list) or not segments:
        raise ValueError('segments must be a non-empty list')
    extra = minutes(delay, 'delay')
    if not isinstance(delay_segment, int) or not 0 <= delay_segment < len(segments):
        raise ValueError('delay_segment is outside segments')
    results = []
    previous_arrival = None
    previous_available = None
    for index, segment in enumerate(segments):
        available = timestamp(segment['available_at'])
        event = timestamp(segment['event_start'])
        if previous_available is not None and available < previous_available:
            raise ValueError('segments must be in chronological order')
        previous_available = available
        travel = minutes(segment['travel_minutes'], 'travel_minutes')
        early = minutes(segment.get('early_minutes', 0), 'early_minutes')
        buffer = minutes(segment.get('buffer_minutes', 0), 'buffer_minutes')
        deadline = event - early
        latest = deadline - travel - buffer
        depart = max(available, previous_arrival) if previous_arrival else available
        if index == delay_segment:
            depart += extra
        arrival = depart + travel + buffer
        slack = (deadline - arrival).total_seconds() / 60
        results.append({
            'name': segment['name'], 'depart_at': depart.isoformat(),
            'latest_departure': latest.isoformat(), 'arrival_with_buffer': arrival.isoformat(),
            'required_arrival': deadline.isoformat(), 'slack_minutes': slack,
            'feasible': slack >= 0,
        })
        previous_arrival = arrival
    return {'feasible': all(row['feasible'] for row in results), 'segments': results}


def self_test():
    seg = {'name': 'synthetic', 'available_at': '2026-10-06T12:00:00+08:00',
           'event_start': '2026-10-06T14:00:00+08:00', 'travel_minutes': 90,
           'early_minutes': 15, 'buffer_minutes': 10}
    assert check([seg])['segments'][0]['slack_minutes'] == 5
    assert not check([seg], 30)['feasible']
    next_seg = {'name': 'propagation', 'available_at': '2026-10-06T14:00:00+08:00',
                'event_start': '2026-10-06T14:15:00+08:00', 'travel_minutes': 10}
    assert not check([seg, next_seg], 30)['segments'][1]['feasible']
    try:
        timestamp('2026-10-06T12:00:00')
    except ValueError:
        pass
    else:
        raise AssertionError('Naive timestamp accepted')
    print('PASS: baseline, delay, propagation, timezone validation (synthetic data)')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path)
    parser.add_argument('--delay-minutes', type=float, default=0)
    parser.add_argument('--delay-segment', type=int, default=0)
    parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args()
    if args.self_test:
        self_test()
    elif args.input:
        data = json.loads(args.input.read_text(encoding='utf-8'))
        print(json.dumps(check(data['segments'], args.delay_minutes, args.delay_segment),
                         ensure_ascii=False, indent=2))
    else:
        parser.error('--input or --self-test is required')
