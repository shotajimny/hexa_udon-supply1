# Bias_tourcar.pyのselect_spots関数で選ばれたスポットに対して、A*アルゴリズムを実行するためのコードを追加する

from parser import (
    parse_pre_game_data, 
    parse_pre_date_data
)
from tour_car.Bias_tourcar import select_spots
from tour_car.compute_astar import AstarAlgorithm


class calculate_tourcar:
    def __init__(self, data):
        # 計算に必要なデータを用意する
        self.pre_game = parse_pre_game_data(data)
        self.pre_date = parse_pre_date_data(data)

    def Bias(self, pre_filter_count):
        # Bias_tourcar.pyのselect_spots関数を使用して、各巡回車から近そうなスポットを数個ずつ取得する
        result = select_spots(self.pre_game.agents, self.pre_game.spots, pre_filter_count)

        # 各 tourcar - spot ペアについて tourcarのID、spotの番号、距離の差分が返ってくる
        return result


    def compute_astar(self, result):
        # 各 tourcar - spot ペアについて A* 実行(compare_tourcar.pyを実行してもらう)
        for i in enumerate(self.pre_date.agents):
            for spot_result in enumerate(result[i]):

                spot_number = spot_result[1]["spot_number"]
                spot_position = self.pre_game.spots[spot_number].pos  # スポットの位置情報を取得する
                agent_position = self.pre_date.agents[i].pos  # 巡回車の位置情報を取得する

                
                astar = AstarAlgorithm()
                astar.map_input(self.pre_game.map)

                path = astar.search_astar(
                    agent_position=agent_position,
                    goal_position=spot_position,
                    agent_fuel=self.pre_date.agents[i].fuel
                )

        return path  # 結果を返す

    def calculate_path_tourcar(self, pre_filter_count):
        # Bias_tourcar.pyのselect_spots関数を使用して、各巡回車から近そうなスポットを数個ずつ取得する
        result = self.Bias(pre_filter_count)

        # 各 tourcar - spot ペアについて A* 実行(compare_tourcar.pyを実行してもらう)
        path = self.compute_astar(result)

        return path  # 結果を返す