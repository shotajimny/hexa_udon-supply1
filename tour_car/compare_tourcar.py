# Bias_tourcar.pyのselect_spots関数で選ばれたスポットに対して、A*アルゴリズムを実行するためのコードを追加する

from tour_car.Bias_tourcar import select_spots, prediction_spots
from tour_car.compute_astar import AstarAlgorithm, FUEL_WEIGHT


class calculate_tourcar:
    def __init__(self, pre_game):
        # インスタンスを受け取って初期化する
        self.pre_game = pre_game

    def Update_Date(self, pre_date, converted_map):
        # 日毎のデータを更新する
        self.pre_date = pre_date
        self.converted_map = converted_map

    def Bias(self, pre_filter_count):
        # 各巡回車から近そうなスポットをpre_filter_count個取得する
        # 巡回車のIDを取得
        bias_agents = [
            prediction_spots(
                id=agent_id,
                position=self.converted_map.cells[agent.pos - 1].position
            )
            for agent_id, agent in enumerate(self.pre_date.agents) if agent.kind == 0
        ]

        spot_positions = [
            self.converted_map.cells[spot.pos - 1].position
            for spot in self.converted_map.spots
        ]

        return select_spots(bias_agents, spot_positions, pre_filter_count)

    def compute_astar(self, result):
        # 各 tourcar - spot ペアについて A* 実行し、すべての経路とコスト情報を保持する
        all_paths = []  # [(agent_id, spot_number, path_info, total_cost), ...]

        # resultの要素数(巡回車の数)分ループする
        for tour_results in result:
            if not tour_results:
                continue

            # 巡回車のID, 場所、残り燃料を取得
            agent_id = tour_results[0]["tourcar_id"]
            agent = self.pre_date.agents[agent_id]

            for spot_result in tour_results:

                # スポット番号と位置を取得
                spot_number = spot_result["spot_number"]
                spot_position = self.converted_map.spots[spot_number].pos

                # 巡回車の位置と残り燃料を取得
                agent_position = agent.pos
                agent_fuel = agent.fuel

                astar = AstarAlgorithm()
                astar.map_input(self.converted_map.cells)  # A*アルゴリズムにマップデータを入力

                # A*アルゴリズムを実行して経路を計算
                path_result = astar.search_astar(
                    agent_position=agent_position,
                    goal_position=spot_position,
                    agent_fuel=agent_fuel
                )

                # パス情報が存在する場合のみ追加
                if path_result["status"] != "unreachable":
                    # コスト計算：最終的な残燃料が少ないほど（消費が多いほど）コストが大きい
                    path_info = path_result["path"]
                    total_fuel_used = agent_fuel - path_info[-1]["remaining_fuel"]
                    total_steps = path_info[-1]["step"]

                    all_paths.append({
                        "agent_id": agent_id, #巡回車のIDを格納するキー
                        "spot_number": spot_number, #スポットの番号を格納するキー
                        "path": path_info, #経路情報を格納するキー
                        "fuel_used": total_fuel_used, #消費燃料量を格納するキー
                        "steps": total_steps, #経過ステップ数を格納するキー
                        "status": path_result["status"], #経路のステータスを格納するキー
                        "refuel_position": (
                            path_info[-1]["position"]
                            if path_result["status"] == "fuel_shortage"
                            else None
                        ), #燃料不足になる位置を格納するキー
                        "combined_cost": total_fuel_used + total_steps * FUEL_WEIGHT  # 燃料と距離の加重
                    })

        return all_paths

    def prioritize_and_assign(self, all_paths):
        # すべての経路候補をコスト順にソートし、各スポット・各巡回車は1度だけ割り当てる

        # 1. コストでソート（低い順）
        sorted_paths = sorted(all_paths, key=lambda x: x["combined_cost"])

        # 2. 割り当て結果を管理
        assignments = []  # [(agent_id, spot_number, path_info, cost), ...]
        assigned_spots = set()  # すでに割り当てられたスポット
        assigned_agents = set()  # すでに割り当てられた巡回車

        # 3. コストが低い順に割り当てを確定（各スポット・各巡回車は1度だけ）
        for candidate in sorted_paths:
            agent_id = candidate["agent_id"]
            spot_number = candidate["spot_number"]

            # スポットと巡回車がまだ割り当てられていない場合のみ追加
            if spot_number not in assigned_spots and agent_id not in assigned_agents:
                assignments.append({
                    "agent_id": agent_id,
                    "spot_number": spot_number,
                    "path": candidate["path"],
                    "fuel_used": candidate["fuel_used"],
                    "steps": candidate["steps"],
                    "status": candidate["status"],
                    "refuel_position": candidate["refuel_position"],
                    "cost": candidate["combined_cost"]
                })
                assigned_spots.add(spot_number)
                assigned_agents.add(agent_id)

        # 4. 割り当てられた組み合わせと割り当てられなかったスポットと巡回車のリストを作成
        # assignments : 割り当てられた巡回車とスポットの組み合わせのリスト
        # unassigned_spots : 割り当てられなかったスポットの番号のリスト
        # unassigned_agents : 割り当てられなかった巡回車のIDのリスト

        # 巡回車だけのIDを格納
        tourcar_ids = {
            agent_id
            for agent_id, agent in enumerate(self.pre_date.agents)
            if agent.kind == 0
        }

        return {
            "assignments": assignments,
            "unassigned_spots": list(set(range(len(self.pre_game.spots))) - assigned_spots),
            "unassigned_agents": list(tourcar_ids - assigned_agents)
        }

    def calculate_path_tourcar(self, pre_filter_count):
        # Bias: 各巡回車から近そうなスポットを複数取得
        result = self.Bias(pre_filter_count)

        # A*実行: すべての（巡回車, スポット）ペアで経路を計算
        all_paths = self.compute_astar(result)

        # 優先度付けと割り当て: コスト順に、各スポット・巡回車は1度だけ割り当て
        assignment_result = self.prioritize_and_assign(all_paths)

        return assignment_result