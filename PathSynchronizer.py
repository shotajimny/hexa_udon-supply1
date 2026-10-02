"""採択経路を合流時刻と実際の燃料で制限し、途中待機を行動列にする。"""
from copy import deepcopy
from math import isfinite


class PathSynchronizer:
    def __init__(self, tourcar_assignments, supplycar_assignments):
        self.tourcar_assignments = deepcopy(tourcar_assignments)
        self.supplycar_assignments = deepcopy(supplycar_assignments)

    def synchronize_paths(self, current_tourcars, current_supplycars,
                          converted_map, fuel_limit, day_steps):
        """時刻は日内の絶対時刻、返す path.step は今回の消費量。

        合流地点で両車が1step待機する計画を作る。合流に間に合わない、
        燃料で到達できない場合は補給を成立させず、安全な経路に制限する。
        current_* は変更せず、呼び出し側が返却経路で更新する。
        """
        cells = {tuple(c.position): c for c in converted_map.cells}
        tours = {c['id']: c for c in current_tourcars}
        supplies = {c['id']: c for c in current_supplycars}
        reservations = {}
        supply_results = []
        for assignment in self.supplycar_assignments:
            sid, tid = assignment['supply_id'], assignment['tourcar_id']
            if sid not in supplies or tid not in tours or tid in reservations:
                continue
            tour_assignment = next((a for a in self.tourcar_assignments
                                    if a['agent_id'] == tid), None)
            if tour_assignment is None:
                continue
            target = tuple(assignment['meeting_point'])
            index = assignment.get('path_index')
            tour_path = tour_assignment['path']
            if index is None or not 0 <= index < len(tour_path):
                continue
            if tuple(tour_path[index]['position']) != target:
                continue
            tour = tours[tid]
            preview = self._walk(tour_path[:index + 1], tour, cells)
            if len(preview['path']) != index + 1:
                continue
            supply = supplies[sid]
            route = self._walk(assignment['path'], supply, cells, supply=True)
            if not route['path'] or tuple(route['path'][-1]['position']) != target:
                continue
            tour_start = day_steps - tour['remaining_steps']
            supply_start = day_steps - supply['remaining_steps']
            meet_end = max(tour_start + preview['steps'],
                           supply_start + route['steps']) + 1
            if meet_end > day_steps:
                continue
            tour_wait = meet_end - tour_start - preview['steps']
            supply_wait = meet_end - supply_start - route['steps']
            reservations[tid] = (index, tour_wait)
            self._wait(route, supply_wait)
            adjusted = dict(assignment, **route)
            adjusted['refuel_at'] = meet_end
            supply_results.append(adjusted)

        tour_results = []
        for assignment in self.tourcar_assignments:
            car = tours[assignment['agent_id']]
            limit = fuel_limit[car['id']] if isinstance(fuel_limit, dict) else fuel_limit
            route = self._walk(assignment['path'], car, cells,
                               refuel=reservations.get(car['id']), fuel_limit=limit)
            adjusted = dict(assignment, **route)
            adjusted['status'] = ('reached_goal' if route['complete'] else 'stopped')
            tour_results.append(adjusted)
        return tour_results, supply_results

    @staticmethod
    def _wait(route, steps):
        if steps <= 0:
            return
        if not float(steps).is_integer():
            raise ValueError('待機stepは整数である必要があります')
        route['steps'] += steps
        point = dict(route['path'][-1], step=route['steps'])
        route['path'].append(point)
        route['actions'].append({'status': 'wait', 'waiting_time': int(steps)})

    def _walk(self, path, car, cells, supply=False, refuel=None, fuel_limit=None):
        position = list(car['position'])
        fuel = car.get('remaining_fuel', 0)
        route = {'path': [{'position': position, 'step': 0,
                           'remaining_fuel': fuel}], 'actions': [],
                 'steps': 0, 'remaining_fuel': fuel, 'complete': False}
        if not path or list(path[0]['position']) != position:
            return route
        for index, point in enumerate(path):
            if refuel and index == refuel[0]:
                wait = refuel[1]
                if route['steps'] + wait > car['remaining_steps']:
                    break
                self._wait(route, wait)
                fuel = fuel_limit
                route['path'][-1]['remaining_fuel'] = fuel
            if index == len(path) - 1:
                route['complete'] = True
                break
            cell = cells[tuple(position)]
            destination = list(path[index + 1]['position'])
            difference = [b - a for a, b in zip(position, destination)]
            adjacent = sorted(difference) == [-1, 0, 1]
            target = cells.get(tuple(destination))
            if (not adjacent or target is None or target.terrain_type == 'lake'
                    or not isfinite(cell.step_cost)
                    or route['steps'] + cell.step_cost > car['remaining_steps']
                    or (not supply and fuel < cell.fuel_cost)):
                break
            route['steps'] += cell.step_cost
            if not supply:
                fuel -= cell.fuel_cost
            position = destination
            route['path'].append({'position': position, 'step': route['steps'],
                                  'remaining_fuel': fuel})
            route['actions'].append({'status': 'move', 'position': position})
        route['remaining_fuel'] = fuel
        return route
