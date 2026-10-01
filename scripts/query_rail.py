"""Local Codex adapter for https://github.com/Joooook/12306-skill.

Upstream is kept unchanged; avoid unrelated interline initialization for direct trains.
"""
import importlib.util
import json
from pathlib import Path
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

vendor = Path(__file__).resolve().parent / 'rail_vendor/12306_apis.py'
spec = importlib.util.spec_from_file_location('rail_backend', vendor)
rail = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rail)
original_get = rail.requests.get

def bounded_get(*args, **kwargs):
    kwargs.setdefault('timeout', 25)
    response = original_get(*args, **kwargs)
    response.raise_for_status()
    return response

rail.requests.get = bounded_get

def main():
    options = vars(rail._build_parser().parse_args())
    tool = options.pop('tool')
    if tool == 'list-tools':
        print(json.dumps({'tools': ['get-tickets', 'list-tools', 'get-current-date'],
                          'backend_version': rail.VERSION}, ensure_ascii=False))
        return
    if tool == 'get-current-date':
        print(rail.tool_get_current_date())
        return
    if tool != 'get-tickets':
        raise ValueError('本适配器仅验证直达查询、日期和工具列表；其他功能请使用原版入口。')
    rail.STATIONS = rail.get_stations()
    rail.NAME_STATIONS = {item['station_name']: item for item in rail.STATIONS.values()}
    origin = rail.parse_station_code(options['from_station'])
    destination = rail.parse_station_code(options['to_station'])
    if origin is None or destination is None:
        raise ValueError('未识别具体车站，请核对站名。')
    requested_limit = options['limited_num']
    options.update(format='json', limited_num=0)
    raw = rail.tool_get_tickets(**options)
    if raw.startswith('Error:'):
        raise RuntimeError(raw)
    tickets = json.loads(raw)
    if not isinstance(tickets, list):
        raise ValueError('接口未返回车次列表。')
    exact = [ticket for ticket in tickets
             if ticket['from_station_telecode'] == origin
             and ticket['to_station_telecode'] == destination]
    print(json.dumps({
        'source': '12306',
        'queried_at': datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(),
        'travel_date_requested': options['date'],
        'from_station': options['from_station'], 'to_station': options['to_station'],
        'excluded_other_station_results': len(tickets) - len(exact),
        'matched_count': len(exact),
        'tickets': exact[:requested_limit] if requested_limit > 0 else exact,
        'note': '余票和票价为本次查询结果，可能随时变化；仅提供查询，不购票。',
    }, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        print(f'查询失败：{error}', file=sys.stderr)
        sys.exit(1)
