# Bias_tourcar.pyのselect_spots関数で選ばれたスポットに対して、A*アルゴリズムを実行するためのコードを追加する

#from tour_car.Bias_tourcar import select_spots
#from tour_car.Bias_tourcar import TOUR_CAR, SPOT_DATA
#from compute_astar import AstarAlgorithm


# recieveからゲーム情報を取得 
from receive import receive

# 巡回車の情報、マップデータ、スポットの情報を取得するためのモジュールをインポート
from receive.parser import 
#ここでTOURCAR,SPOT_DATAを定義する

# Bias_tourcar.pyのselect_spots関数を使用して、各巡回車から近そうなスポットを数個ずつ取得する
from tour_car.Bias_tourcar import select_spots
result = select_spots(TOURCAR,SPOT_DATA)

# compute_astar.pyを用いて実際に計算
# 各 tourcar - spot ペアについて A* 実行(compare_tourcar.pyを実行してもらう)
from tour_car.compute_astar import AstarAlgorithm
astar = AstarAlgorithm()
for tourcar, spot in result.items():
    # A*アルゴリズムの実行
    astar.map_input(map_data) 
    path = astar.search_astar(tourcar.position, spot.position, tourcar.fuel)
    print(f"Tourcar {tourcar.id} to Spot {spot.id}: Path: {path}")


# 結果をexportするために、export_result関数を使用してJSON形式で出力する)
from transmit.export.py import exportt_result
export_result(result)