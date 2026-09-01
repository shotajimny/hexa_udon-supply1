# Bias_tourcar.pyのselect_spots関数で選ばれたスポットに対して、A*アルゴリズムを実行するためのコードを追加する

from receive.models2 import (
    preGameData,
    preDateData,
    Convert_Cells
)
from tour_car.Bias_tourcar import select_spots
from tour_car.compute_astar import AstarAlgorithm


class calculate_tourcar:
    def __init__(self, data):
        self.pre_game = preGameData(data)
        self.pre_date = preDateData(data)
        self.convert_cells = Convert_Cells(data)

    def Bias(self, pre_filter_count):
        result = select_spots(self.pre_game.agents, self.pre_game.spots, pre_filter_count)
        return result

    def compute_astar(self, result):
        # 各 tourcar - spot ペアについて A* 実行し、すべての経路とコスト情報を保持する
        all_paths = []  # [(agent_id, spot_number, path_info, total_cost), ...]

        for agent_idx, agent in enumerate(self.pre_date.agents):
            for spot_result in result[agent_idx]:
                spot_number = spot_result["spot_number"]
                spot_position = self.pre_game.spots[spot_number].pos
                agent_position = agent.pos
                agent_fuel = agent.fuel

                astar = AstarAlgorithm()
                astar.map_input(self.convert_cells, self.pre_game.spots)

                path_result = astar.search_astar(
                    agent_position=agent_position,
                    goal_position=spot_position,
                    agent_fuel=agent_fuel
                )

                # パス情報が存在する場合のみ追加
                if path_result["path"]:
                    # コスト計算：最終的な残燃料が少ないほど（消費が多いほど）コストが大きい
                    path_info = path_result["path"]
                    total_fuel_used = agent_fuel - path_info[-1]["remaining_fuel"]
                    total_steps = path_info[-1]["step"]

                    all_paths.append({
                        "agent_id": agent_idx,
                        "spot_number": spot_number,
                        "path": path_info,
                        "fuel_used": total_fuel_used,
                        "steps": total_steps,
                        "combined_cost": total_fuel_used + total_steps * 0.1  # 燃料と距離の加重
                    })

        return all_paths

    def prioritize_and_assign(self, all_paths):
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
                    "cost": candidate["combined_cost"]
                })
                assigned_spots.add(spot_number)
                assigned_agents.add(agent_id)

        return {
            "assignments": assignments,
            "unassigned_spots": set(range(len(self.pre_game.spots))) - assigned_spots,
            "unassigned_agents": set(range(len(self.pre_date.agents))) - assigned_agents
        }

    def calculate_path_tourcar(self, pre_filter_count):
        # Bias: 各巡回車から近そうなスポットを複数取得
        result = self.Bias(pre_filter_count)

        # A*実行: すべての（巡回車, スポット）ペアで経路を計算
        all_paths = self.compute_astar(result)

        # 優先度付けと割り当て: コスト順に、各スポット・巡回車は1度だけ割り当て
        assignment_result = self.prioritize_and_assign(all_paths)

        return assignment_result