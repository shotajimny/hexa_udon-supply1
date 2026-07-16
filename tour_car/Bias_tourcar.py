import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from transmit.export import export_result #JSON形式で結果を出力する関数をインポート

class prediction_spots: #巡回車のクラスを定義
    def __init__ (self, id, position):
        #巡回車のID、位置を初期化
        self.id = id
        self.position = position

    def distance_measurement(self, spot_data, pre_filter_count): #距離測定により選択肢となるスポットを選ぶメソッドを定義
        
        self.distance = [[0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0]] #測定結果を格納するリスト

        for i in range(len(spot_data)): #仮のループでスポットデータを処理  
            for j in range(len(self.position)): #仮のループで位置データを処理
                self.distance[i][j] = spot_data[i][j] - self.position[j] #仮の測定結果
                
        #測定結果を距離の絶対値の合計でソートして、上位pre_filter_count件を選択する処理を追加する
        distances = []
        for i in range(len(self.distance)):
            total_distance = sum(abs(d) for d in self.distance[i])
            distances.append((total_distance, i, self.distance[i]))
        distances.sort()
        selected_results = distances[:pre_filter_count]
        self.distance = [(i + 1, distance) for _, i, distance in selected_results]

        return self.distance #測定結果を返す
    

#巡回車とスポットのデータ作成、仮サーバー完成後はサーバーからデータを受け取る形に変更する予定

TOUR_CAR = [] #巡回車のリストを作成
TOUR_CAR.append(prediction_spots(1, [0, 0, 0])) #巡回車のインスタンスを作成
TOUR_CAR.append(prediction_spots(2, [3, 1, -4])) #巡回車のインスタンスを作成
TOUR_CAR.append(prediction_spots(3, [0, -3, 3])) #巡回車のインスタンスを作成

# tour_car/Bias_tourcar.py
def select_spots(tour_cars, spot_data, pre_filter_count=2):
    """各tourcar ごとに候補スポットを選別して返す"""
    results = []
    for tour in enumerate(tour_cars):
        measurement = tour.distance_measurement(spot_data, pre_filter_count)
        for spot_number, distance in measurement:
            results.append({
                'tourcar_id': tour.id,
                'spot_number': spot_number,
                'distance': distance
            })
    return results

# if __name__ == "__main__" でテスト用に実行
if __name__ == "__main__":
    tour_cars = [...]  # 既存コード
    spot_data = [...]  # 既存コード
    selected = select_spots(tour_cars, spot_data, pre_filter_count=2)
    for item in selected:
        export_result(item['tourcar_id'], item['spot_number'], item['distance'])