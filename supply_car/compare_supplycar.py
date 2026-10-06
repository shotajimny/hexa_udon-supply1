"""補給車の候補比較・割当・状態管理。"""

from itertools import product

try:
    from supply_car.Bias_supplycar import SupplyBias
    from supply_car.compute_astar_supply import SupplyAstarAlgorithm
except ImportError:
    # 単体テストや同一ディレクトリ実行用
    from Bias_supplycar import SupplyBias
    from compute_astar_supply import SupplyAstarAlgorithm


class calculate_supplycar:
    def __init__(self, pre_game):
        self.pre_game = pre_game
        self.current_supplycars = []
        self.bias = SupplyBias()
        self.astar = SupplyAstarAlgorithm()
        self.day_total_steps = 0.0

    def Update_Date(self, pre_date, converted_map):
        self.pre_date = pre_date
        self.converted_map = converted_map
        self.astar.map_input(self.converted_map.cells)
        self.day_total_steps = float(self.pre_game.daySteps[pre_date.day])

        self.current_supplycars = [
            {
                "id": agent_id,
                "position": list(self.converted_map.cells[agent.pos].position),
                "remaining_steps": self.day_total_steps,
            }
            for agent_id, agent in enumerate(self.pre_date.agents)
            if agent.kind == 1
        ]

    def has_remaining_supplycar_steps(self):
        return any(car["remaining_steps"] > 0 for car in self.current_supplycars)

    def _elapsed_steps(self, car):
        return self.day_total_steps - float(car["remaining_steps"])

    def create_supply_candidates(self, tour_assignments, tour_elapsed_steps=None):
        return self.bias.create_candidates(tour_assignments, tour_elapsed_steps)

    def _cell_stay_steps(self, position):
        """そのセルから次セルへ動く際、そのセルに留まる step 数。"""
        cell = self.astar._get_cell(position)
        if cell is None:
            return 0.0
        return float(cell.step_cost)

    def compute_astar(self, candidates):
        """active 補給車 × 補給候補地点の実経路と日内時刻を計算する。"""
        all_paths = []

        for supplycar in self.current_supplycars:
            if supplycar["remaining_steps"] <= 0:
                continue

            supply_elapsed = self._elapsed_steps(supplycar)

            for candidate in candidates:
                path_result = self.astar.search_astar(
                    supplycar["position"],
                    candidate["meeting_point"],
                )
                if path_result["status"] == "unreachable":
                    continue

                travel_steps = float(path_result["steps"])
                if travel_steps > supplycar["remaining_steps"]:
                    continue

                supply_arrival = supply_elapsed + travel_steps
                tour_arrival = float(candidate["tour_arrival_step"])

                # 同じセルにいる時間帯を求める。
                # 「到着しただけで +1」はせず、そのセルから次へ動くために
                # 消費する step を滞在時間として扱う。
                stay_steps = self._cell_stay_steps(candidate["meeting_point"])
                tour_leave = tour_arrival + stay_steps
                supply_leave = supply_arrival + stay_steps
                overlap_steps = max(
                    0.0,
                    min(tour_leave, supply_leave) - max(tour_arrival, supply_arrival),
                )

                # 自然な移動だけでは重ならない場合、巡回車が補給車を待つ量。
                # daily_paths の途中待機表現は後で統合する。
                waiting_steps = max(0.0, supply_arrival - tour_leave)

                all_paths.append({
                    "supply_id": supplycar["id"],
                    "tourcar_id": candidate["tourcar_id"],
                    "status": candidate["status"],
                    "meeting_point": list(candidate["meeting_point"]),
                    "tour_path_step": candidate["tour_path_step"],
                    "tour_arrival_step": tour_arrival,
                    "supply_travel_steps": travel_steps,
                    "supply_arrival_step": supply_arrival,
                    "tour_leave_step": tour_leave,
                    "supply_leave_step": supply_leave,
                    "overlap_steps": overlap_steps,
                    "waiting_steps": waiting_steps,
                    "remaining_fuel": candidate["remaining_fuel"],
                    "path_index": candidate["path_index"],
                    "path": path_result["path"],
                    "steps": travel_steps,
                })

        return all_paths

    def _priority_key(self, candidate):
        """先読み・加重スコアなしの辞書式比較。"""
        return (
            candidate["waiting_steps"],
            candidate["remaining_fuel"],
            candidate["supply_arrival_step"],
            0 if candidate["status"] == "fuel_shortage" else 1,
        )

    def create_choices_per_supply(self, all_paths, choices_per_supply=5):
        """補給車ごとに上位 N 個の選択肢を残す。"""
        choices = {}
        for supplycar in self.current_supplycars:
            supply_id = supplycar["id"]
            car_choices = [p for p in all_paths if p["supply_id"] == supply_id]
            car_choices.sort(key=self._priority_key)
            choices[supply_id] = car_choices[:choices_per_supply]
        return choices

    def _combination_key(self, combination):
        """複数補給車の組み合わせ比較。

        まず担当できる巡回車数を最大化し、その後に
        待機量・残燃料・到着時刻を辞書式に比較する。
        """
        assigned = [c for c in combination if c is not None]
        return (
            -len(assigned),
            sum(c["waiting_steps"] for c in assigned),
            sum(c["remaining_fuel"] for c in assigned),
            sum(c["supply_arrival_step"] for c in assigned),
            sum(0 if c["status"] == "fuel_shortage" else 1 for c in assigned),
        )

    def prioritize_and_assign(self, all_paths, choices_per_supply=5):
        """各補給車の上位候補から、巡回車が重複しない組み合わせを選ぶ。"""
        choices = self.create_choices_per_supply(all_paths, choices_per_supply)
        active_supply_ids = [
            car["id"]
            for car in self.current_supplycars
            if car["remaining_steps"] > 0
        ]

        if not active_supply_ids:
            return {"assignments": [], "choices": choices, "unassigned_supplycars": []}

        # None は「今回はこの補給車を割り当てない」という選択肢。
        option_lists = [[None] + choices.get(sid, []) for sid in active_supply_ids]
        best = None
        best_key = None

        for combination in product(*option_lists):
            assigned = [c for c in combination if c is not None]
            tour_ids = [c["tourcar_id"] for c in assigned]
            if len(tour_ids) != len(set(tour_ids)):
                continue

            key = self._combination_key(combination)
            if best_key is None or key < best_key:
                best_key = key
                best = assigned

        assignments = [c.copy() for c in (best or [])]
        assigned_supply_ids = {a["supply_id"] for a in assignments}

        return {
            "assignments": assignments,
            "choices": choices,
            "unassigned_supplycars": [
                sid for sid in active_supply_ids if sid not in assigned_supply_ids
            ],
        }

    def limit_path_by_remaining_steps(self, path, remaining_steps):
        return [point for point in path if point["step"] <= remaining_steps]

    def calculate_path_supplycar(
        self,
        tour_assignments,
        tour_elapsed_steps=None,
        choices_per_supply=5,
    ):
        candidates = self.create_supply_candidates(
            tour_assignments,
            tour_elapsed_steps=tour_elapsed_steps,
        )
        all_paths = self.compute_astar(candidates)
        result = self.prioritize_and_assign(
            all_paths,
            choices_per_supply=choices_per_supply,
        )

        for assignment in result["assignments"]:
            supplycar = next(
                car for car in self.current_supplycars
                if car["id"] == assignment["supply_id"]
            )
            assignment["path"] = self.limit_path_by_remaining_steps(
                assignment["path"], supplycar["remaining_steps"]
            )

        return result

    def Update_current_supplycars(self, assignment_result):
        """採択された移動分だけ補給車状態を進める。強制 +1 step はしない。"""
        for assignment in assignment_result["assignments"]:
            supplycar = next(
                car for car in self.current_supplycars
                if car["id"] == assignment["supply_id"]
            )

            if assignment["path"]:
                supplycar["position"] = list(assignment["path"][-1]["position"])

            supplycar["remaining_steps"] -= float(assignment["steps"])
            if supplycar["remaining_steps"] < 0:
                supplycar["remaining_steps"] = 0.0

    def apply_refuels(self, assignment_result, current_tourcars, fuel_limit_by_agent):
        """成立した補給を巡回車状態へ反映する。

        fuel_limit_by_agent は {agent_id: 満タン燃料量} を渡す。
        pre_game.fuelLimits の構造をこのクラス側で推測しないため明示引数にしている。

        現時点では、自然な滞在 overlap が1step以上ある候補を成立扱いにする。
        waiting_steps > 0 の候補は daily_paths に途中待機を実装した後で成立判定へ統合する。
        """
        refueled = []
        for assignment in assignment_result["assignments"]:
            if assignment["overlap_steps"] < 1.0:
                continue

            tourcar_id = assignment["tourcar_id"]
            tourcar = next(
                (car for car in current_tourcars if car["id"] == tourcar_id),
                None,
            )
            if tourcar is None or tourcar_id not in fuel_limit_by_agent:
                continue

            tourcar["remaining_fuel"] = float(fuel_limit_by_agent[tourcar_id])
            refueled.append(tourcar_id)

        return refueled



# 既存の探索・状態更新は共有し、補給対象の評価だけを差し替える。
LegacySupplyCalculator = calculate_supplycar


class calculate_supplycar(LegacySupplyCalculator):
    def __init__(self, pre_game):
        super().__init__(pre_game)
        self.stopped_days = {}
        self.last_refuel = {}
        self.context = {}

    def Update_Date(self, pre_date, converted_map):
        super().Update_Date(pre_date, converted_map)
        for aid, agent in enumerate(pre_date.agents):
            if agent.kind == 0:
                cost = converted_map.cells[agent.pos].fuel_cost
                self.stopped_days[aid] = (self.stopped_days.get(aid, 0) + 1
                                          if agent.fuel < cost else 0)

    def set_tour_context(self, cars, acquired_today, acquired_match):
        self.context = {car['id']: car for car in cars}
        self.acquired_today = set(acquired_today)
        self.acquired_match = set(acquired_match)

    def _fuel_limit(self, aid):
        limits = self.pre_game.fuelLimits
        return limits[aid] if isinstance(limits, dict) else limits

    def _benefit(self, candidate, remaining_steps):
        """補給により到達可能になるスポット数をA*で見積もる（巡回の保証値ではない）。"""
        from tour_car.compute_astar import AstarAlgorithm
        astar = AstarAlgorithm(fuel_weight=0)
        astar.map_input(self.converted_map.cells)
        aid = candidate['tourcar_id']
        limit = self._fuel_limit(aid)
        benefit = 0
        for spot in self.pre_game.spots:
            if spot.brand in self.acquired_today or spot.stocks <= 0:
                continue
            route = astar.search_astar({'position': candidate['meeting_point'], 'fuel': limit}, spot.pos)
            if route['status'] != 'reached_goal' or route['path'][-1]['step'] > remaining_steps:
                continue
            used = limit - route['path'][-1]['remaining_fuel']
            if used > candidate['remaining_fuel']:
                benefit += 2 if spot.brand not in self.acquired_match else 1
        return benefit

    def _priority_key(self, candidate):
        return (candidate['urgency'], -candidate['stopped_days'],
                -candidate['benefit_per_step'], candidate['meet_end'],
                candidate['remaining_fuel'])

    def _combination_key(self, combination):
        selected = [c for c in combination if c is not None]
        return (-sum(c['urgency'] == 0 for c in selected),
                -sum(c['stopped_days'] for c in selected if c['urgency'] == 0),
                -sum(c['urgency'] == 1 for c in selected),
                -sum(c['benefit_per_step'] for c in selected),
                sum(c['service_steps'] for c in selected), -len(selected))

    def create_choices_per_supply(self, all_paths, choices_per_supply=5):
        # 同じ巡回車の複数合流地点で候補枠を埋めず、車ごとの最良候補を残す。
        choices = {}
        for car in self.current_supplycars:
            best = {}
            for candidate in sorted((p for p in all_paths if p['supply_id'] == car['id']),
                                    key=self._priority_key):
                best.setdefault(candidate['tourcar_id'], candidate)
            choices[car['id']] = list(best.values())
        return choices

    def calculate_path_supplycar(self, tour_assignments, tour_elapsed_steps=None, choices_per_supply=5):
        tour_elapsed_steps = tour_elapsed_steps or {}
        candidates = self.create_supply_candidates(tour_assignments, tour_elapsed_steps)
        assignments = {a['agent_id']: a for a in tour_assignments}
        evaluated = []
        benefit_cache = {}
        for candidate in self.compute_astar(candidates):
            aid = candidate['tourcar_id']
            tour = self.context[aid]
            path = assignments[aid]['path']
            index = candidate['path_index']
            # 燃料で辿り着けない地点と、同期時に日内に成立しない合流を除く。
            if any(point['remaining_fuel'] < 0 for point in path[:index + 1]):
                continue
            meet_end = max(candidate['supply_arrival_step'], candidate['tour_arrival_step']) + 1
            if meet_end > self.day_total_steps:
                continue
            cell = self.astar._get_cell(tour['position'])
            stopped = tour['remaining_fuel'] < cell.fuel_cost
            urgent = assignments[aid]['status'] == 'fuel_shortage'
            urgency = 0 if stopped else 1 if urgent else 2
            limit = self._fuel_limit(aid)
            if urgency == 2 and candidate['remaining_fuel'] > limit * .5:
                continue
            absolute_now = sum(self.pre_game.daySteps[:self.pre_date.day]) + tour_elapsed_steps.get(aid, 0)
            recent = absolute_now - self.last_refuel.get(aid, float('-inf')) < 20
            if urgency == 2 and recent and candidate['remaining_fuel'] > limit * .25:
                continue
            service_steps = max(candidate['supply_travel_steps'],
                                candidate['tour_arrival_step'] - tour_elapsed_steps.get(aid, 0)) + 1
            candidate.update(urgency=urgency, stopped_days=self.stopped_days.get(aid, 0) if stopped else 0,
                             meet_end=meet_end, service_steps=service_steps)
            evaluated.append(candidate)
        # まず各補給車×巡回車で最短の成立合流を選び、効果の先読みはこの組だけに行う。
        best_pairs = {}
        for candidate in sorted(evaluated, key=lambda c: (c['meet_end'], c['service_steps'])):
            best_pairs.setdefault((candidate['supply_id'], candidate['tourcar_id']), candidate)
        evaluated = []
        for candidate in best_pairs.values():
            aid = candidate['tourcar_id']
            remaining = self.day_total_steps - candidate['meet_end']
            cache_key = (aid, tuple(candidate['meeting_point']), candidate['remaining_fuel'], remaining)
            if cache_key not in benefit_cache:
                benefit_cache[cache_key] = self._benefit(candidate, remaining)
            benefit = benefit_cache[cache_key]
            if candidate['urgency'] == 2 and benefit == 0:
                continue
            candidate.update(benefit=benefit, benefit_per_step=benefit / candidate['service_steps'])
            evaluated.append(candidate)
        return self.prioritize_and_assign(evaluated, choices_per_supply)

    def Update_current_supplycars(self, assignment_result):
        super().Update_current_supplycars(assignment_result)
        for assignment in assignment_result['assignments']:
            if 'refuel_at' in assignment:
                self.last_refuel[assignment['tourcar_id']] = (
                    sum(self.pre_game.daySteps[:self.pre_date.day]) + assignment['refuel_at'])
