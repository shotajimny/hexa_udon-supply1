# Bias_tourcar.pyのselect_spots関数で選ばれたスポットに対して、A*アルゴリズムを実行するためのコードを追加する

#from tour_car.Bias_tourcar import select_spots
#from tour_car.Bias_tourcar import TOUR_CAR, SPOT_DATA
#from compute_astar import AstarAlgorithm


# recieveからゲーム情報を取得 
from receive.parser import parse_map_data

# 巡回車の情報、マップデータ、スポットの情報を取得するためのモジュールをインポート
from receive.parser import parse_spot_data,parse_agent_data
#ここでTOURCAR,SPOT_DATAを定義する

# Bias_tourcar.pyのselect_spots関数を使用して、各巡回車から近そうなスポットを数個ずつ取得する
from tour_car.Bias_tourcar import select_spots
result = select_spots(parse_agent_data,parse_spot_data)

# compute_astar.pyを用いて実際に計算
# 各 tourcar - spot ペアについて A* 実行(compare_tourcar.pyを実行してもらう)
from tour_car.compute_astar import AstarAlgorithm
from receive.parser import parse_pre_game_data
from receive.api_client import get_pre_game_data
raw_data = get_pre_game_data()
pre_game = parse_pre_game_data(raw_data)
for i, agent in enumerate(pre_game.agents):
    for j, spot in enumerate(result.spot_number):
        astar = AstarAlgorithm()
        astar.map_input(pre_game.map)

        path = astar.search_astar(
            agent_position=agent.pos,
            goal_position=spot.pos,
            agent_fuel=pre_game.fuelLimits
        )

# 結果をexportするために、export_result関数を使用してJSON形式で出力する)
from transmit.export import export_result
export_result(result)