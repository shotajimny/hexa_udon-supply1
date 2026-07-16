from tour_car.Bias_tourcar import select_spots
from tour_car.Bias_tourcar import TOUR_CAR, SPOT_DATA
from Astar_algorithm import compute_astar
from transmit.export import export_result

# Bias の結果を取得
selected_spots = select_spots(TOUR_CAR, SPOT_DATA)



# 各 tourcar-spot ペアについて A* 実行
for item in selected_spots:
    tourcar_id = item['tourcar_id']
    spot_number = item['spot_number']
    path, cost = compute_astar(tourcar_id, spot_number, map_data)
    # 結果を export